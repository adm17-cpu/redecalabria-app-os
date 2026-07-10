import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser estritamente o primeiro comando Streamlit)
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

def get_brasilia_time():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")

# 2. CONFIGURAÇÃO DE URLs
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# 3. LEITURA DOS DADOS (Com tratamento contra falhas)
csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

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

# 4. MENU LATERAL
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

if erro_conexao:
    st.sidebar.error(f"⚠️ Erro na Planilha: {erro_conexao}")

# 5. LÓGICA DO APLICATIVO
if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    opcoes_unidades_abertura = ["Selecione uma Unidade..."] + lista_unidades
    
    with st.form("form_os", clear_on_submit=True):
        unidade = st.selectbox("Selecione a Unidade", opcoes_unidades_abertura)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil", "TI", "Outros"])
        descricao = st.text_area("Descrição do problema")
        
        st.write("---")
        st.subheader("📸 Anexar Foto")
        foto_camera = st.camera_input("Tirar foto agora")
        foto_upload = st.file_uploader("Ou escolha uma foto da galeria", type=["jpg", "jpeg", "png"])
        st.write("---")
        
        submetido = st.form_submit_button("Enviar Ordem de Serviço")
        
        if submetido:
            if unidade == "Selecione uma Unidade...":
                st.error("Por favor, selecione uma Unidade válida antes de enviar!")
            elif not responsavel or not descricao:
                st.error("Preencha Nome e Descrição!")
            else:
                agora = get_brasilia_time()
                arquivo_final = foto_upload if foto_upload is not None else foto_camera
                
                if arquivo_final:
                    bytes_data = arquivo_final.getvalue()
                    foto_base64 = base64.b64encode(bytes_data).decode()
                    foto_string = f"data:image/png;base64,{foto_base64}"
                else:
                    foto_string = "Sem foto"
                
                nova_linha = [len(df)+1, agora, unidade, responsavel, tipo, descricao, foto_string, "Aberta"]
                
                with st.spinner("Gravando dados..."):
                    payload = {"action": "add", "row": nova_linha}
                    try:
                        res = requests.post(url_script, json=payload)
                        if res.status_code == 200:
                            st.success(f"OS Nº {len(df)+1} registrada com sucesso!")
                            st.balloons()
                        else:
                            st.error("Erro ao salvar no servidor do Google.")
                    except Exception as env_err:
                        st.error(f"Falha de rede: {env_err}")

elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    if df.empty:
        st.info("Nenhum dado encontrado ou planilha vazia.")
    else:
        if "Status" in df.columns:
            df_abertas = df[df["Status"] == "Aberta"]
        else:
            df_abertas = pd.DataFrame()
            st.error("Coluna 'Status' ausente na planilha.")
            
        if not df_abertas.empty:
            opcoes_filtro = ["Todas"] + lista_unidades
            unidade_selecionada = st.selectbox("Filtrar tabela por Unidade", opcoes_filtro)
            
            df_exibicao = df_abertas[df_abertas["Unidade"] == unidade_selecionada] if unidade_selecionada != "Todas" else df_abertas
            
            if not df_exibicao.empty:
                st.dataframe(df_exibicao[['ID', 'Data_Abertura', 'Unidade', 'Responsavel', 'Tipo', 'Descricao']], use_container_width=True)
                
                st.divider()
                st.subheader("🔍 Visualizar Detalhes e Foto")
                id_selecionado = st.selectbox("Selecione o ID da OS para detalhar", df_exibicao["ID"].tolist())
                detalhe = df_exibicao[df_exibicao["ID"] == id_selecionado].iloc[0]
                
                st.markdown(f"**Responsável Atual:** {detalhe['Responsavel']}")
                st.markdown(f"**Tipo de Manutenção:** {detalhe['Tipo']}")
                st.markdown(f"**Descrição:** {detalhe['Descricao']}")
                
                if "data:image" in str(detalhe.get('Foto_URL', '')):
                    st.image(detalhe['Foto_URL'], caption=f"Foto da OS {id_selecionado}", width=500)
                else:
                    st.info("Esta OS não possui foto.")

                # ENCERRAMENTO
                st.divider()
                st.subheader("🔒 Encerrar esta OS")
                tecnico = st.text_input("Técnico Responsável pelo fechamento")
                
                if st.button("Confirmar Encerramento"):
                    if tecnico:
                        agora_fim = get_brasilia_time()
                        payload = {
                            "action": "update", 
                            "id": str(id_selecionado), 
                            "status": "Finalizada", 
                            "tecnico": tecnico, 
                            "data_fim": agora_fim
                        }
                        with st.spinner("Encerrando..."):
                            try:
                                res = requests.post(url_script, json=payload)
                                if res.status_code == 200 and "Atualizado" in res.text:
                                    st.success(f"A OS Nº {id_selecionado} foi encerrada!")
                                    st.rerun()
                                else:
                                    st.error(f"Erro na planilha: {res.text}")
                            except Exception as err:
                                st.error(f"Erro de conexão: {err}")
                    else:
                        st.warning("Informe o nome do técnico.")
            else:
                st.info("Nenhuma OS aberta para esta unidade.")
        else:
            st.info("Não há ordens de serviço abertas no momento.")

elif escolha == "Dashboard":
    st.header("📊 Indicadores")
    if not df.empty and "Status" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Abertas", len(df[df["Status"] == "Aberta"]))
        c3.metric("Finalizadas", len(df[df["Status"] == "Finalizada"]))
