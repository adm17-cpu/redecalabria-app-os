import streamlit as st
import json
import urllib.request
import urllib.parse
import csv
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

def get_brasilia_time():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")

# 2. ENDEREÇOS DA PLANILHA E DO API SCRIPT
url_base = "https://docs.google.com/spreadsheets/d/1pYPTKhLBiqX8JtRU1A9eC94LC5zFI0F4BpPflJsXchc"
url_script = "https://script.google.com/macros/s/AKfycbyQj9UP5wGN20kTK7E4yI7T0C3o99MQMndf1ENn9n8mnM6J5ADlB-zeeCAbEVjTAyF3/exec"

# URLs oficiais em formato CSV leve (filtrando apenas as abertas direto na origem)
csv_url_dados = f"{url_base}/gviz/tq?tqx=out:csv&tq=SELECT+A,B,C,D,E,F+WHERE+H+=+'Aberta'"
csv_url_unidades = f"{url_base}/gviz/tq?tqx=out:csv&sheet=Unidades"

# 3. LEITOR DE CSV NATIVO (Ultra-leve e imune a erros de quebra de texto)
def ler_dados_csv(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            linhas_cruas = response.read().decode('utf-8').splitlines()
            if not linhas_cruas:
                return []
            
            # Usamos o leitor padrão de CSV do Python, que separa vírgulas e aspas perfeitamente
            leitor = csv.reader(linhas_cruas)
            resultado = list(leitor)
            
            # Remove a linha de cabeçalho, se existir
            if resultado:
                resultado.pop(0)
            return resultado
    except Exception as e:
        return []

# Carrega a lista de unidades para os menus laterais
lista_linhas_unidades = ler_dados_csv(csv_url_unidades)
lista_unidades = [l[0] for l in lista_linhas_unidades if l and len(l) > 0]

# 4. INTERFACE LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS"]
escolha = st.sidebar.selectbox("Navegação", menu)

# 5. MÓDULO: ABRIR OS
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
                nova_linha = [0, agora, unidade, responsavel, tipo, descricao, "Sem foto", "Aberta"]
                
                with st.spinner("Enviando chamado..."):
                    try:
                        payload = json.dumps({"action": "add", "row": nova_linha}).encode('utf-8')
                        req = urllib.request.Request(url_script, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
                        with urllib.request.urlopen(req, timeout=10) as res:
                            resposta_texto =
