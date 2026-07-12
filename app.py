import streamlit as st
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

def get_brasilia_time():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")

# 2. ENDEREÇOS DA PLANILHA E DO API SCRIPT
url_base = "https://docs.google.com/spreadsheets/d/1pYPTKhLBiqX8JtRU1A9eC94LC5zFI0F4BpPflJsXchc"
url_script = "https://script.google.com/macros/s/AKfycbyQj9UP5wGN20kTK7E4yI7T0C3o99MQMndf1ENn9n8mnM6J5ADlB-zeeCAbEVjTAyF3/exec"

# Endereços em formato leve para o Google Sheets
tsv_url_dados = f"{url_base}/gviz/tq?tqx=out:tsv&tq=SELECT+A,B,C,D,E,F+WHERE+H+=+'Aberta'"
tsv_url_unidades = f"{url_base}/gviz/tq?tqx=out:csv&sheet=Unidades"

# 3. FUNÇÃO AUXILIAR DE REQUISIÇÃO (Ultra-leve)
def ler_url_linhas(url, usar_tsv=False):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            conteudo = response.read().decode('utf-8').splitlines()
            if not conteudo:
                return []
            
            separador = '\t' if usar_tsv else ','
            linhas_processadas = []
            
            for i, linha in enumerate(conteudo):
                if i == 0:  # Ignora a linha de cabeçalhos
                    continue
                partes = linha.split(separador)
                partes_limpas = [p.strip('"') for p in partes]
                if partes_limpas and partes_limpas[0]:
                    linhas_processadas.append(partes_limpas)
            return linhas_processadas
    except:
        return []

# Carrega a lista de unidades para os formulários
lista_linhas_unidades = ler_url_linhas(tsv_url_unidades, usar_tsv=False)
lista_unidades = [l[0] for l in lista_linhas_unidades if l]

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
                            resposta_texto = res.read().decode('utf-8')
                        if "Sucesso" in resposta_texto:
                            st.success("OS gravada com sucesso! Atualize a página para atualizar.")
                        else:
                            st.error(f"Erro no servidor: {resposta_texto}")
                    except Exception as env_err:
                        st.error(f"🚨 Falha de comunicação: {env_err}")

# 6. MÓDULO: VER/ENCERRAR OS
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    # CORRIGIDO: Agora usando o nome correto da variável (tsv_url_dados)
    chamados_abertos = ler_url_linhas(tsv_url_dados, usar_tsv=True)
    
    if not chamados_abertos:
        st.info("Não existem ordens de serviço abertas no momento.")
    else:
        opcoes_filtro = ["Todas"] + lista_unidades
        unidade_sel = st.selectbox("Filtrar por Unidade", opcoes_filtro)
        
        exibicao = []
        for c in chamados_abertos:
            if len(c) >= 6:
                if unidade_sel == "Todas" or c[2] == unidade_sel:
                    exibicao.append({
                        "ID": c[0], "Data Abertura": c[1], "Unidade": c[2],
                        "Responsável": c[3], "Tipo": c[4], "Descrição": c[5]
                    })
        
        if exibicao:
            st.table(exibicao)
            
            st.write("---")
