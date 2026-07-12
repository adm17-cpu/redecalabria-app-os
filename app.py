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

csv_url_dados = f"{url_base}/gviz/tq?tqx=out:csv"
csv_url_unidades = f"{url_base}/gviz/tq?tqx=out:csv&sheet=Unidades"

# 3. GERENCIAMENTO DE ESTADO E LEITURA LEVE
if 'dados_df' not in st.session_state or st.sidebar.button("🔄 Atualizar Dados"):
    try:
        st.session_state.dados_df = pd.read_csv(csv_url_dados)
        df_unidades = pd.read_csv(csv_url_unidades)
        st.session_state.lista_unidades = df_unidades.iloc[:, 0].dropna().unique().tolist() if not df_unidades.empty else []
        st.session_state.erro_conexao = None
    except Exception as e:
        st.session_state.dados_df = pd.DataFrame()
        st.session_state.lista_unidades = []
        st.session_state.erro_conexao = str(e)

df = st.session_state.dados_df
lista_unidades = st.session_state.lista_unidades
erro_conexao = st.session_state.erro_conexao

# 4. INTERFACE LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

if erro_conexao:
    st.sidebar.error(f"⚠️ Erro ao carregar dados: {erro_conexao}")

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
                proximo_id = len(df) + 1 if not df.empty else 1
                nova_linha = [proximo_id, agora, unidade, responsavel, tipo, descricao, "Sem foto", "Aberta"]
                
                with st.spinner("Gravando..."):
                    try:
                        res = requests.post(url_script, json={"action": "add", "row": nova_linha}, timeout=15)
                        if res.status_code == 200 and "Sucesso" in res.text:
                            st.success(f"OS Nº {proximo_id} enviada! Clique em 'Atualizar Dados' na lateral para sincronizar.")
                        else:
                            st.error(f"Erro: {res.text}")
                    except Exception as env_err:
                        st.error(f"🚨 Conexão falhou: {env_err}")

# 6. MÓDULO: VER/ENCERRAR OS
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    if df.empty:
        st.info("Nenhum registro ativo.")
    else:
        df_abertas = df[df["Status"].str.strip().str.lower() == "aberta"] if "Status" in df.columns else pd.DataFrame()
        
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
                lista_ids = df_exibicao['ID'].tolist()
                
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
                            
                            with st.spinner("Encerrando..."):
                                try:
                                    res = requests.post(url_script, json=dados_update, timeout=15)
                                    if res.status_code == 200 and "Atualizado" in res.text:
                                        st.success(f"OS Nº {os_selecionada} finalizada com sucesso! Se quiser atualizar a tabela agora, use o botão 'Atualizar Dados' à esquerda.")
                                    else:
                                        st.error(f"Resposta Google: {res.text}")
                                except Exception as err:
                                    st.error(f"Erro: {err}")
            else:
                st.info("Nenhuma OS aberta para esta unidade.")

# 7. MÓDULO: DASHBOARD
elif escolha == "Dashboard":
    st.header("📊 Indicadores Gerais")
    if not df.empty and "Status" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Registrado", len(df))
        c2.metric("Pendentes (Abertas)", len(df[df["Status"].str.strip().str.lower() == "aberta"]))
        c3.metric("Concluídas", len(df[df["Status"].str.strip().str.lower() == "finalizada"]))
