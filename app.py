import streamlit as st
import pandas as pd
import requests
import pytz
import base64
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

# Função para capturar hora oficial de Brasília
def get_brasilia_time():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")

# 2. DEFINIÇÃO DE URLs
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# 3. LEITURA DOS DADOS (Armazenados em variáveis padrão caso falhe)
csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

# Criamos estruturas vazias por padrão para o app não apagar a tela caso falhe a leitura
df = pd.DataFrame()
lista_unidades = ["Unidade Padrão"]
erro_conexao = None

try:
    df = pd.read_csv(csv_url_dados)
    df_unidades = pd.read_csv(csv_url_unidades)
    lista_unidades = df_unidades.iloc[:, 0].unique().tolist()
except Exception as e:
    erro_conexao = str(e)

# 4. BARRA LATERAL / MENU
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

# Se houve erro de conexão, mostra um aviso fixo no topo sem travar a tela inteira
if erro_conexao:
    st.error(f"⚠️ Erro ao carregar dados da Planilha: {erro_conexao}")
    st.info("Verifique se as abas 'dados' e 'Unidades' estão com os nomes corretos no Google Sheets.")

# 5. LÓGICA DO APP

if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    
    with st.form("form_os", clear_on_submit=True):
        unidade = st.selectbox("Selecione a Unidade", lista_unidades)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil", "TI", "Outros"])
        descricao = st.text_area("Descrição do problema")
        foto_arquivo = st.camera_input("Tire uma foto (Opcional)")
        
        submetido = st.form_submit_button("Enviar Ordem de Serviço")
        
        if submetido:
            if not responsavel or not descricao:
                st.error("Preencha Nome e Descrição!")
            elif erro_conexao:
                st.error("Não é possível enviar a OS porque o sistema está desconectado da planilha.")
            else:
                agora = get_brasilia_time()
                
                if foto_arquivo:
                    bytes_data = foto_arquivo.getvalue()
                    foto_base64 = base64.b64encode(bytes_data).decode()
                    foto_string = f"data:image/png;base64,{foto_base64}"
                else:
                    foto_string = "Sem foto"
                
                nova_linha = [len(df)+1, agora, unidade, responsavel, tipo, descricao, foto_string, "Aberta"]
                
                with st.spinner("Gravando dados..."):
                    payload = {"action": "add", "row": nova_linha}
                    res = requests.post(url_script, json=payload)
                    if res.status_code == 200:
                        st.success(f"OS Nº {len(df)+1} registrada com sucesso!")
                        st.balloons()
                    else:
                        st.error("Erro ao salvar. Verifique o Apps Script.")

elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    if not df.empty:
        df_abertas = df[df["Status"] == "Aberta"]
        
        if not df_abertas.empty:
