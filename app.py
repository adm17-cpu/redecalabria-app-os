import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Gestão de OS", layout="wide")

# URLs (SUBSTITUA A URL_SCRIPT PELA QUE VOCÊ GEROU NO PASSO 1)
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/a/macros/calabria.com.br/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# LER DADOS (Método CSV - Seguro e Gratuito)
csv_url = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
try:
    df = pd.read_csv(csv_url)
except:
    st.error("Erro ao ler a planilha. Verifique se o nome da aba é 'dados' e se ela está compartilhada como 'Qualquer pessoa com o link pode editar'.")
    st.stop()

menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Abrir OS":
    st.header("Abertura de Ordem de Serviço")
    
    with st.form("form_os"):
        unidade = st.selectbox("Unidade", ["Unidade A", "Unidade B", "Unidade C"])
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil"])
        descricao = st.text_area("Descrição do Problema")
        foto = st.text_input("Link da Foto")
        
        submetido = st.form_submit_button("Abrir Ordem de Serviço")
        
        if submetido:
            # Prepara a linha para enviar ao Google
            nova_linha = [
                int(len(df) + 1), 
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                unidade, responsavel, tipo, descricao, foto, "Aberta"
            ]
            
            payload = {"action": "add", "row": nova_linha}
            
            with st.spinner('Gravando na planilha...'):
                res = requests.post(url_script, json=payload)
                if res.status_code == 200:
                    st.success(f"OS Nº {len(df)+1} aberta com sucesso!")
                else:
                    st.error("Erro ao gravar dados. Verifique a implantação do Apps Script.")

elif escolha == "Ver/Encerrar OS":
    st.header("Ordens de Serviço Ativas")
    
    # Filtro por Unidade
    if not df.empty:
        unidade_filtro = st.selectbox("Filtrar por Unidade", df["Unidade"].unique())
        os_filtradas = df[(df["Unidade"] == unidade_filtro) & (df["Status"] == "Aberta")]
        st.dataframe(os_filtradas)
        
        st.divider()
        st.subheader("Dar Baixa em uma OS")
        id_baixa = st.number_input("Digite o ID da OS para encerrar", step=1)
        nome_tecnico = st.text_input("Nome do Técnico Responsável")
        
        if st.button("Encerrar Ordem de Serviço"):
            payload = {
                "action": "update",
                "id": id_baixa,
                "status": "Finalizada",
                "tecnico": nome_tecnico,
                "data_fim": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            res = requests.post(url_script, json=payload)
            st.success(f"OS {id_baixa} encerrada!")
            st.rerun()
    else:
        st.warning("Nenhuma OS encontrada.")

elif escolha == "Dashboard":
    st.header("Resumo de Atividades")
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("OS por Unidade")
            st.bar_chart(df["Unidade"].value_counts())
        with col2:
            st.subheader("Status das OS")
            st.write(df["Status"].value_counts())
