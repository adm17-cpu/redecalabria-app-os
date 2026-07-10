import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA (Precisa ser o primeiro comando Streamlit)
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

def get_brasilia_time():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")

# 2. ENDEREÇOS DA PLANILHA E DO API SCRIPT
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

# 3. FUNÇÃO DE LEITURA COM CACHE (Válido por 5 minutos)
@st.cache_data(ttl=300)
def carregar_dados_planilha(url_dados, url_unidades):
    dados_df = pd.read_csv(url_dados)
    unidades_df = pd.read_csv(url_unidades)
    unidades_lista = []
    if not unidades_df.empty:
        unidades_lista = unidades_df.iloc[:, 0].dropna().unique().tolist()
    return dados_df, unidades_lista

# Chamada da função com tratamento de erros
df = pd.DataFrame()
lista_unidades = []
erro_conexao = None

try:
    df, lista_unidades = carregar_dados_planilha(csv_url_dados, csv_url_unidades)
except Exception as e:
    erro_conexao = str(e)

# 4. INTERFACE LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

# Botão manual para limpar cache e buscar dados atualizados na hora
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sincronizar Planilha"):
    st.cache_data.clear()
    st.rerun()

if erro_conexao:
    st.sidebar.error(f"⚠️ Erro ao carregar dados: {erro_conexao}")

# 5. MÓDULO: ABRIR OS (Sem campos de Imagem)
if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    opcoes_unidades = ["Selecione uma Unidade..."] + lista_unidades
    
    with st.form("form_os", clear_on_submit=True):
        unidade = st.selectbox("Selecione a Unidade", opcoes_unidades)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Alvenaria", "Climatização", "Móveis", "TI", "Outros"])
        descricao = st.text_area("Descrição do problema")
        
        submetido = st.form_submit_button("Enviar Ordem de Serviço")
        
        if submetido:
            if unidade == "Selecione uma Unidade...":
                st.error("Selecione uma Unidade válida!")
            elif not responsavel or not descricao:
                st.error("Preencha o Nome e a Descrição!")
            else:
                agora = get_brasilia_time()
                
                # Registra "Sem foto" de forma automática na Coluna G para manter o alinhamento das colunas
                nova_linha = [len(df)+1, agora, unidade, responsavel, tipo, descricao, "Sem foto", "Aberta"]
                
                with st.spinner("Gravando dados..."):
                    try:
                        res = requests.post(url_script, json={"action": "
