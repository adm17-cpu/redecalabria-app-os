import streamlit as st
import pandas as pd
import requests
import pytz
import base64
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

# Função para capturar hora oficial de Brasília
def get_brasilia_time():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")

# 2. DEFINIÇÃO DE URLs
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# 3. LEITURA DOS DADOS
csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

df = pd.DataFrame()
lista_unidades = []
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

if erro_conexao:
    st.error(f"⚠️ Erro ao carregar dados da Planilha: {erro_conexao}")

# 5. LÓGICA DO APP

if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    
    opcoes_unidades_abertura = ["Selecione uma Unidade..."] + lista_unidades
    
    with st.form("form_os", clear_on_submit=True):
        unidade = st.selectbox("Selecione a Unidade", opcoes_unidades_abertura)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Climatização", "Alvenaria", "TI","Móveis", "Serralheria", "Outros"])
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
            elif erro_conexao:
                st.error("Sistema desconectado da planilha.")
            else:
                agora = get_brasilia_time()
                
                arquivo_final = None
                if foto_upload is not None:
                    arquivo_final = foto_upload
                elif foto_camera is not None:
                    arquivo_final = foto_camera
                
                if arquivo_final:
                    bytes_data = arquivo_final.getvalue()
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
                        st.error("Erro ao salvar no servidor.")

elif escolha == "Ver/Encerrar OS":
    st.header("📋 Ordens de Serviço Ativas")
    
    if not df.empty:
        df_abertas = df[df["Status"] == "Aberta"]
        
        if not df_abertas.empty:
            opcoes_filtro = ["Todas"] + lista_unidades
            unidade_selecionada = st.selectbox("Filtrar tabela por Unidade", opcoes_filtro)
            
            if unidade_selecionada != "Todas":
                df_exibicao = df_abertas[df_abertas["Unidade"] == unidade_selecionada]
            else:
                df_exibicao = df_abertas
            
            if not df_exibicao.empty:
                st.dataframe(df_exibicao[['ID', 'Data_Abertura', 'Unidade', 'Responsavel', 'Tipo', 'Descricao']], use_container_width=True)
                
                st.divider()
                st.subheader("🔍 Visualizar Detalhes e Foto")
                
                id_selecionado = st.selectbox("Selecione o ID da OS para detalhar ou realizar ações", df_exibicao["ID"].tolist())
                detalhe = df_exibicao[df_exibicao["ID"] == id_selecionado].iloc[0]
                
                st.markdown(f"**Responsável Atual:** {detalhe['Responsavel']}")
                st.markdown(f"**Tipo de Manutenção:** {detalhe['Tipo']}")
                st.markdown(f"**Descrição Atual:** {detalhe['Descricao']}")
                
                if "data:image" in str(detalhe['Foto_URL']):
                    st.image(detalhe['Foto_URL'], caption=f"Foto da OS {id_selecionado}", width=500)
                else:
                    st.info("Esta OS não possui foto.")

                # SEÇÃO PARA EDIÇÃO DA OS PELO USUÁRIO
                st.divider()
                with st.expander("✏️ Editar dados desta OS (Apenas para Ordens Abertas)"):
                    st.warning("Você pode alterar as informações iniciais abaixo caso tenham sido digitadas incorretamente.")
                    novo_responsavel = st.text_input("Alterar Nome do Responsável", value=str(detalhe['Responsavel']))
                    
                    lista_tipos = ["Elétrica", "Hidráulica", "Mecânica", "Civil", "TI", "Outros"]
                    idx_tipo = lista_tipos.index(detalhe['Tipo']) if detalhe['Tipo'] in lista_tipos else 0
                    novo_tipo = st.selectbox("Alterar Tipo de Manutenção", lista_tipos, index=idx_tipo)
                    
                    nova_descricao = st.text_area("Alterar Descrição do problema", value=str(detalhe['Descricao']))
                    
                    if st.button("Salvar Alterações da OS"):
                        if not novo_responsavel or not nova_descricao:
                            st.error("Os campos Responsável e Descrição não podem ficar vazios!")
                        else:
                            payload_edit = {
                                "action": "edit",
                                "id": int(id_selecionado),
                                "responsavel": novo_responsavel,
                                "tipo": novo_tipo,
                                "descricao": nova_descricao
                            }
                            with st.spinner("Atualizando dados da OS..."):
                                res_edit = requests.post(url_script, json=payload_edit)
                                if res_edit.status_code == 200:
                                    st.success("Ordem de Serviço atualizada com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar os dados no servidor.")

                st.divider()
                st.subheader("🔒 Encerrar esta OS")
                tecnico = st.text_input("Técnico Responsável pelo fechamento")
                
                if st.button("Confirmar Encerramento"):
                    if tecnico:
                        agora_fim = get_brasilia_time()
                        payload = {
                            "action": "update",
                            "id": int(id_selecionado),
                            "status": "Finalizada",
                            "tecnico": tecnico,
                            "data_fim": agora_fim
                        }
                        requests.post(url_script, json=payload)
                        st.success(f"OS {id_selecionado} encerrada!")
                        st.rerun()
                    else:
                        st.warning("Informe o nome do técnico.")
            else:
                st.info(f"Nenhuma OS em aberto encontrada para a unidade: {unidade_selecionada}")
        else:
            st.info("Nenhuma OS aberta no sistema.")
    else:
        st.info("Aguardando carregamento de dados.")

elif escolha == "Dashboard":
    st.header("📊 Indicadores")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Abertas", len(df[df["Status"] == "Aberta"]))
        c3.metric("Finalizadas", len(df[df["Status"] == "Finalizada"]))
        
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("### Por Unidade")
            st.bar_chart(df["Unidade"].value_counts())
        with col_b:
            st.write("### Por Tipo")
            col_tipo = "Tipo" if "Tipo" in df.columns else df.columns[4]
            st.bar_chart(df[col_tipo].value_counts())
