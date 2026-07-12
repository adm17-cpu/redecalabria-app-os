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
            
            leitor = csv.reader(linhas_cruas)
            resultado = list(leitor)
            
            # Remove a linha de cabeçalho, se existir
            if resultado:
                resultado.pop(0)
            return resultado
    except Exception as e:
        return []

# Carrega a lista de unidades para os menus
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
                        with urllib.request.urlopen(req, timeout=12) as res:
                            resposta_texto = res.read().decode('utf-8')
                        
                        if "Sucesso" in resposta_texto:
                            st.success("OS gravada com sucesso! Alterne o menu para atualizar a lista.")
                        else:
                            st.error(f"Erro no servidor: {resposta_texto}")
                    except Exception as env_err:
                        st.error(f"🚨 Falha de comunicação: {env_err}")

# 6. MÓDULO: VER/ENCERRAR OS
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    # Carrega os chamados abertos usando o leitor robusto de CSV
    chamados_abertos = ler_dados_csv(csv_url_dados)
    
    opcoes_filtro = ["Todas"] + lista_unidades
    unidade_sel = st.selectbox("Filtrar por Unidade", opcoes_filtro)
    
    exibicao = []
    if chamados_abertos:
        for c in chamados_abertos:
            if len(c) >= 6:
                if unidade_sel == "Todas" or c[2].strip() == unidade_sel.strip():
                    exibicao.append({
                        "ID": c[0], "Data Abertura": c[1], "Unidade": c[2],
                        "Responsável": c[3], "Tipo": c[4], "Descrição": c[5]
                    })
    
    if exibicao:
        st.table(exibicao)
        
        st.write("---")
        st.subheader("🛠️ Encerrar Ordem de Serviço")
        
        lista_ids = [int(c["ID"]) for c in exibicao if str(c["ID"]).isdigit()]
        
        with st.form("form_Camp_encerra", clear_on_submit=True):
            os_selecionada = st.selectbox("Selecione a ID da OS que deseja fechar", lista_ids)
            tecnico = st.text_input("Nome do Técnico / Responsável pela Execução")
            botao_encerrar = st.form_submit_button("Concluir e Encerrar OS")
            
            if botao_encerrar:
                if not tecnico:
                    st.error("Por favor, digite o nome do técnico!")
                else:
                    agora_fim = get_brasilia_time()
                    dados_update = {
                        "action": "update",
                        "id": int(os_selecionada),
                        "status": "Finalizada",
                        "tecnico": tecnico,
                        "data_fim": agora_fim
                    }
                    
                    with st.spinner("Processando encerramento..."):
                        try:
                            payload = json.dumps(dados_update).encode('utf-8')
                            req = urllib.request.Request(url_script, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
                            with urllib.request.urlopen(req, timeout=12) as res:
                                resposta_texto = res.read().decode('utf-8')
                            
                            if "Atualizado" in resposta_texto:
                                st.success(f"OS Nº {os_selecionada} encerrada com sucesso! Modifique o filtro para atualizar.")
                            else:
                                st.error(f"Erro na folha: {resposta_texto}")
                        except Exception as err:
                            st.error(f"Erro de conexão: {err}")
    else:
        st.info("Não existem ordens de serviço abertas encontradas para os critérios selecionados.")
