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
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"

# ⚠️ LINK ATUALIZADO BASEADO NO SEU ID ATIVO:
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

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
    
    # clear_on_submit=False para capturar o erro em tempo real sem limpar os campos
    with st.form("form_os", clear_on_submit=False):
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
                
                with st.spinner("Enviando dados para o Google..."):
                    try:
                        res = requests.post(url_script, json={"action": "add", "row": nova_linha}, timeout=15)
                        
                        # Exibe exatamente os códigos de rastreamento no ecrã para auditoria
                        st.info(f"Código de Resposta do Google: {res.status_code}")
                        st.info(f"Texto Retornado do Google: '{res.text}'")
                        
                        if res.status_code == 200 and "Sucesso" in res.text:
                            st.success(f"OS Nº {proximo_id} gravada com sucesso!")
                            st.balloons()
                        else:
                            st.warning("O Google recebeu a requisição, mas não respondeu com a confirmação esperada.")
                    except Exception as env_err:
                        st.error(f"🚨 Não foi possível alcançar o link do Google: {env_err}")

# 6. MÓDULO: VER/ENCERRAR OS
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    if df.empty:
        st.info("Nenhum registro encontrado na planilha.")
    else:
        df_abertas = df[df["Status"] == "Aberta"] if "Status" in df.columns else pd.DataFrame()
        if df_abertas.empty:
            st.info("Não existem ordens de serviço abertas.")
        else:
            opcoes_filtro = ["Todas"] + lista_unidades
            unidade_sel = st.selectbox("Filtrar por Unidade", opcoes_filtro)
            
            # LINHA 96 CORRIGIDA: Filtro de tabela limpo e sem erros de sintaxe
            if unidade_sel != "Todas":
                df_exibicao = df_abertas[df_abertas["Unidade"] == unidade_sel]
            else:
                df_exibicao = df_abertas
            
            if not df_exibicao.empty:
                st.dataframe(df_exibicao[['ID', 'Data_Abertura', 'Unidade', 'Responsavel', 'Tipo', 'Descricao']])

# 7. MÓDULO: DASHBOARD
elif escolha == "Dashboard":
    st.header("📊 Indicadores Gerais")
    if not df.empty and "Status" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Registrado", len(df))
        c2.metric("Pendentes (Abertas)", len(df[df["Status"] == "Aberta"]))
        c3.metric("Concluídas", len(df[df["Status"] == "Finalizada"]))
