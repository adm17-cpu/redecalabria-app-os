import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Gestão de OS", layout="wide")

# URLs (SUBSTITUA A URL_SCRIPT PELA QUE VOCÊ GEROU NO PASSO 1)
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# LER DADOS (Método CSV - Seguro e Gratuito)
csv_url = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
try:
    df = pd.read_csv(csv_url)
    # Lê a aba de Unidades para preencher o formulário automaticamente
url_unidades = url_planilha.replace('sheet=dados', 'sheet=Unidades')
try:
    df_unidades = pd.read_csv(url_unidades)
    lista_unidades = df_unidades["Nome_Unidade"].unique().tolist()
except:
    lista_unidades = ["Unidade A", "Unidade B"] # Caso a aba não exista, ele usa esses nomes
except:
    st.error("Erro ao ler a planilha. Verifique se o nome da aba é 'dados' e se ela está compartilhada como 'Qualquer pessoa com o link pode editar'.")
    st.stop()

menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Abrir OS":
    st.header("Abertura de Ordem de Serviço")
    
    with st.form("form_os"):
        unidade = st.selectbox("Unidade", lista_unidades)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil"])
        descricao = st.text_area("Descrição do Problema")
        foto_arquivo = st.camera_input("Tire uma foto da OS")
# Aqui, para simplificar sem Google Cloud, vamos apenas avisar se a foto foi tirada
foto = "Foto Capturada" if foto_arquivo else "Sem Foto"
        
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
    st.header("📊 Painel de Controle de Manutenção")
    
    if not df.empty:
        # Indicadores principais (Cards)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de OS", len(df))
        col2.metric("Em Aberto", len(df[df["Status"] == "Aberta"]))
        col3.metric("Finalizadas", len(df[df["Status"] == "Finalizada"]))

        st.divider()

        # Gráficos principais
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("OS por Unidade")
            st.bar_chart(df["Unidade"].value_counts())
        with c2:
            st.subheader("Tipos de Manutenção")
            st.write(df["Tipo"].value_counts())
    else:
        st.info("Aguardando dados para gerar o dashboard.")
