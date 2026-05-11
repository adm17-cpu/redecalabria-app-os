import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de OS", layout="wide")

# 2. DEFINIÇÃO DE URLs
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
# RECOLOQUE SUA URL DO APPS SCRIPT ABAIXO
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# 3. PREPARAÇÃO DOS LINKS DE LEITURA
# Criamos os links CSV antes do bloco try para evitar erros
csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

# 4. LEITURA DOS DADOS
try:
    # Lê a aba principal de Ordens de Serviço
    df = pd.read_csv(csv_url_dados)
    
    # Lê a aba de Unidades para o formulário
    df_unidades = pd.read_csv(csv_url_unidades)
    lista_unidades = df_unidades["Nome_Unidade"].unique().tolist()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se as abas 'dados' e 'Unidades' existem na planilha.")
    st.stop()

# 5. BARRA LATERAL / MENU
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Menu", menu)

# 6. LÓGICA DAS PÁGINAS
if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    
    with st.form("form_os"):
        unidade = st.selectbox("Unidade", lista_unidades)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil", "Outros"])
        descricao = st.text_area("Descrição do Problema")
        
        foto_arquivo = st.camera_input("Tire uma foto da OS (Opcional)")
        
        submetido = st.form_submit_button("Abrir Ordem de Serviço")
        
        if submetido:
            if not responsavel or not descricao:
                st.warning("Por favor, preencha o nome e a descrição.")
            else:
                foto_status = "Com Foto" if foto_arquivo else "Sem Foto"
                nova_linha = [
                    int(len(df) + 1), 
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                    unidade, responsavel, tipo, descricao, foto_status, "Aberta"
                ]
                
                payload = {"action": "add", "row": nova_linha}
                res = requests.post(url_script, json=payload)
                
                if res.status_code == 200:
                    st.success(f"✅ OS Nº {len(df)+1} aberta com sucesso!")
                    st.balloons()
                else:
                    st.error("Erro ao gravar na planilha. Verifique o Apps Script.")

elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    if not df.empty:
        unidade_filtro = st.selectbox("Filtrar por Unidade", ["Todas"] + lista_unidades)
        
        if unidade_filtro == "Todas":
            exibir_df = df[df["Status"] == "Aberta"]
        else:
            exibir_df = df[(df["Unidade"] == unidade_filtro) & (df["Status"] == "Aberta")]
        
        st.dataframe(exibir_df, use_container_width=True)
        
        st.divider()
        st.subheader("Finalizar uma Ordem")
        
        col1, col2 = st.columns(2)
        with col1:
            id_baixa = st.number_input("Número (ID) da OS", min_value=1, step=1)
        with col2:
            nome_tecnico = st.text_input("Nome do Técnico")
        
        if st.button("Confirmar Encerramento"):
            if id_baixa in df["ID"].values:
                payload = {
                    "action": "update",
                    "id": int(id_baixa),
                    "status": "Finalizada",
                    "tecnico": nome_tecnico,
                    "data_fim": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
                requests.post(url_script, json=payload)
                st.success(f"OS {id_baixa} encerrada!")
                st.rerun()
            else:
                st.error("ID de Ordem de Serviço não encontrado.")
    else:
        st.info("Não há ordens de serviço registradas.")

elif escolha == "Dashboard":
    st.header("📊 Indicadores de Manutenção")
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de OS", len(df))
        c2.metric("Abertas", len(df[df["Status"] == "Aberta"]))
        c3.metric("Finalizadas", len(df[df["Status"] == "Finalizada"]))
        
        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("OS por Unidade")
            st.bar_chart(df["Unidade"].value_counts())
        with col_b:
            st.subheader("Tipos de Manutenção")
            st.bar_chart(df["Tipo"].value_counts())
    else:
        st.warning("Sem dados suficientes para o gráfico.")
