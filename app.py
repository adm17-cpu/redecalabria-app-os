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

# URLs com queries restritas para trazer o mínimo de dados possíveis
csv_url_dados_leves = f"{url_base}/gviz/tq?tqx=out:csv&tq=SELECT+A,B,C,D,E,F+WHERE+H+=+'Aberta'"
csv_url_unidades = f"{url_base}/gviz/tq?tqx=out:csv&sheet=Unidades"

# 3. INTERFACE LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS"]
escolha = st.sidebar.selectbox("Navegação", menu)

# Carregamento sob demanda direto (Não guarda lixo no session_state do servidor)
try:
    df_unidades = pd.read_csv(csv_url_unidades, keep_default_na=False)
    lista_unidades = df_unidades.iloc[:, 0].dropna().unique().tolist() if not df_unidades.empty else []
    erro_conexao = None
except Exception as e:
    lista_unidades = []
    erro_conexao = str(e)

if erro_conexao:
    st.sidebar.error(f"⚠️ Erro ao conectar: {erro_conexao}")

# 4. MÓDULO: ABRIR OS
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
                
                with st.spinner("Enviando..."):
                    try:
                        res = requests.post(url_script, json={"action": "add", "row": nova_linha}, timeout=10)
                        if res.status_code == 200 and "Sucesso" in res.text:
                            st.success("OS gravada com sucesso!")
                        else:
                            st.error(f"Erro: {res.text}")
                    except Exception as env_err:
                        st.error(f"🚨 Conexão falhou: {env_err}")

# 5. MÓDULO: VER/ENCERRAR OS
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    # Faz o download apenas se o usuário entrar nesta aba (Consumo zero nas demais abas)
    try:
        df_abertas = pd.read_csv(csv_url_dados_leves, keep_default_na=False)
    except:
        df_abertas = pd.DataFrame()

    if df_abertas.empty:
        st.info("Não existem ordens de serviço abertas no momento.")
    else:
        opcoes_filtro = ["Todas"] + lista_unidades
        unidade_sel = st.selectbox("Filtrar por Unidade", opcoes_filtro)
        
        if unidade_sel != "Todas":
            df_exibicao = df_abertas[df_abertas["Unidade"] == unidade_sel]
        else:
            df_exibicao = df_abertas
        
        if not df_exibicao.empty:
            st.dataframe(df_exibicao[['ID', 'Data_Abertura', 'Unidade', 'Responsavel', 'Tipo', 'Descricao']], use_container_width=True)
            
            st.write("---")
            st.subheader("🛠️ Encerrar Ordem de Serviço")
            
            lista_ids = [int(x) for x in df_exibicao['ID'].tolist() if str(x).isdigit()]
            
            with st.form("form_Camp_encerra", clear_on_submit=True):
                os_selecionada = st.selectbox("Selecione a ID da OS que deseja fechar", lista_ids)
                tecnico = st.text_input("Nome do Técnico / Responsável pela Execução")
                botao_encerrar = st.form_submit_button("Concluir e Encerrar OS")
                
                if botao_encerrar:
                    if not tecnico:
                        st.error("Digite o nome do responsável técnico!")
                    else:
                        agora_fim = get_brasilia_time()
                        dados_update = {
                            "action": "update",
                            "id": int(os_selecionada),
                            "status": "Finalizada",
                            "tecnico": tecnico,
                            "data_fim": agora_fim
                        }
                        
                        with st.spinner("Atualizando no Google..."):
                            try:
                                res = requests.post(url_script, json=dados_update, timeout=12)
                                if res.status_code == 200 and "Atualizado" in res.text:
                                    st.success(f"OS Nº {os_selecionada} encerrada com sucesso! A tabela será atualizada na próxima ação.")
                                else:
                                    st.error(f"Erro no servidor: {res.text}")
                            except Exception as err:
                                st.error(f"Erro de timeout: {err}")
        else:
            st.info("Nenhuma OS aberta cadastrada para esta unidade específica.")
