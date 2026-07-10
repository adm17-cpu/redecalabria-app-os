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
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

# 3. FUNÇÕES DE LEITURA COM CACHE SEPARADO
@st.cache_data(ttl=300)
def obter_lista_unidades(url_unidades):
    try:
        unidades_df = pd.read_csv(url_unidades)
        if not unidades_df.empty:
            return unidades_df.iloc[:, 0].dropna().unique().tolist()
    except:
        pass
    return []

@st.cache_data(ttl=300)
def carregar_dados_os(url_dados):
    return pd.read_csv(url_dados)

# Carrega a lista de unidades primeiro (super leve, acelera o boot do app)
lista_unidades = obter_lista_unidades(csv_url_unidades)

# 4. INTERFACE LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sincronizar Planilha"):
    st.cache_data.clear()
    st.rerun()

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
                
                # Só puxa o histórico se for realmente gravar para validar o ID sequencial
                try:
                    df_temporario = carregar_dados_os(csv_url_dados)
                    proximo_id = len(df_temporario) + 1
                except:
                    proximo_id = 999 # Fallback de segurança
                
                nova_linha = [proximo_id, agora, unidade, responsavel, tipo, descricao, "Sem foto", "Aberta"]
                
                with st.spinner("Gravando dados..."):
                    try:
                        res = requests.post(url_script, json={"action": "add", "row": nova_linha}, timeout=15)
                        if res.status_code == 200:
                            st.success(f"OS Nº {proximo_id} registrada com sucesso!")
                            st.cache_data.clear()
                            st.balloons()
                        else:
                            st.error("Erro na comunicação com a API do Google.")
                    except Exception as env_err:
                        st.error(f"Falha na rede: {env_err}")

# 6. MÓDULO: VER/ENCERRAR OS
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    with st.spinner("Buscando dados atualizados..."):
        try:
            df = carregar_dados_os(csv_url_dados)
        except Exception as e:
            st.error(f"⚠️ Erro ao carregar dados: {e}")
            df = pd.DataFrame()

    if df.empty:
        st.info("Nenhum registro encontrado na planilha.")
    else:
        df_abertas = df[df["Status"] == "Aberta"] if "Status" in df.columns else pd.DataFrame()
        
        if df_abertas.empty:
            st.info("Não existem ordens de serviço abertas.")
        else:
            opcoes_filtro = ["Todas"] + lista_unidades
            unidade_sel = st.selectbox("Filtrar por Unidade", opcoes_filtro)
            
            df_exibicao = df_abertas[df_abertas["Unidade"] == unity_sel] if unidade_sel != "Todas" else df_abertas
            
            if not df_exibicao.empty:
                st.dataframe(df_exibicao[['ID', 'Data_Abertura', 'Unidade', 'Responsavel', 'Tipo', 'Descricao']], use_container_width=True)
                
                st.divider()
                st.subheader("🔍 Ações da Ordem de Serviço")
                id_selecionado = st.selectbox("Selecione o ID da OS", df_exibicao["ID"].tolist())
                detalhe = df_exibicao[df_exibicao["ID"] == id_selecionado].iloc[0]
                
                st.markdown(f"**Responsável Atual:** {detalhe['Responsavel']}")
                st.markdown(f"**Tipo:** {detalhe['Tipo']}")
                st.markdown(f"**Descrição:** {detalhe['Descricao']}")
                
                st.divider()
                tecnico = st.text_input("Técnico Responsável")
                
                if st.button("Confirmar Encerramento da OS"):
                    if tecnico:
                        payload = {
                            "action": "update", 
                            "id": str(id_selecionado), 
                            "status": "Finalizada", 
                            "tecnico": tecnico, 
                            "data_fim": get_brasilia_time()
                        }
                        with st.spinner("Atualizando base de dados..."):
                            try:
                                res = requests.post(url_script, json=payload, timeout=15)
                                if res.status_code == 200 and "Atualizado" in res.text:
                                    st.success(f"OS {id_selecionado} encerrada com sucesso!")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao processar: {res.text}")
                            except Exception as err:
                                st.error(f"Erro na conexão: {err}")
                    else:
                        st.warning("Insira o nome do técnico responsável.")
            else:
                st.info("Nenhuma OS aberta para a unidade selecionada.")

# 7. MÓDULO: DASHBOARD
elif escolha == "Dashboard":
    st.header("📊 Indicadores Gerais")
    
    with st.spinner("Calculando indicadores..."):
        try:
            df = carregar_dados_os(csv_url_dados)
        except:
            df = pd.DataFrame()

    if not df.empty and "Status" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Registrado", len(df))
        c2.metric("Pendentes (Abertas)", len(df[df["Status"] == "Aberta"]))
        c3.metric("Concluídas", len(df[df["Status"] == "Finalizada"]))
