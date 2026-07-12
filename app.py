import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

def get_brasilia_time():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")

# 2. ENDEREÇOS DA PLANILHA E DO API SCRIPT
url_base = "https://docs.google.com/spreadsheets/d/1pYPTKhLBiqX8JtRU1A9eC94LC5zFI0F4BpPflJsXchc"
url_script = "https://script.google.com/macros/s/AKfycbyQj9UP5wGN20kTK7E4yI7T0C3o99MQMndf1ENn9n8mnM6J5ADlB-zeeCAbEVjTAyF3/exec"

# Geração das URLs de exportação CSV
csv_url_dados = f"{url_base}/gviz/tq?tqx=out:csv"
csv_url_unidades = f"{url_base}/gviz/tq?tqx=out:csv&sheet=Unidades"

# 3. LEITURA DIRETA DOS DADOS
df = pd.DataFrame()
lista_unidades = []
erro_conexao = None

try:
    df = pd.read_csv(csv_url_dados)
    df_unidades = pd.read_csv(csv_url_unidades)
    if not df_unidades.empty:
        lista_unidades = df_unidades.iloc[:, 0].dropna().unique().tolist()
except Exception as e:
    erro_conexao = str(e)

# 4. INTERFACE LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

if erro_conexao:
    st.sidebar.error(f"⚠️ Erro ao carregar dados da Planilha: {erro_conexao}")

# 5. MÓDULO: ABRIR OS
if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    opcoes_unidades = ["Selecione uma Unidade..."] + lista_unidades
    
    with st.form("form_os", clear_on_submit=True):
        unidade = st.selectbox("Selecione a Unidade", opcoes_unidades)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Alvenaria", "Climatização", "Móveis", "TI", "Outros"])
        descricao = st.text_area("Descrição do problem")
        
        submetido = st.form_submit_button("Enviar Ordem de Serviço")
        
        if submetido:
            if unidade == "Selec
