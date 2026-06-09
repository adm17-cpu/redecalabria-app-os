import streamlit as st
import pandas as pd
import requests
import pytz
import base64
from datetime import datetime
from io import BytesIO

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

try:
    df = pd.read_csv(csv_url_dados)
    df_unidades = pd.read_csv(csv_url_unidades)
    lista_unidades = df_unidades.iloc[:, 0].unique().tolist()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 4. BARRA LATERAL / MENU
st.sidebar.title("Rede Calábria")
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

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
            else:
                agora = get_brasilia_time()
                
                # Processamento da Foto para Base64
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
    
    # Filtra apenas as ordens que estão abertas
    df_abertas = df[df["Status"] == "Aberta"]
    
    if not df_abertas.empty:
        # --- NOVO: FILTRO POR UNIDADE ---
        # Criamos uma lista de opções contendo "Todas" + as unidades da planilha
        opcoes_filtro = ["Todas"] + lista_unidades
        unidade_selecionada = st.selectbox("Filtrar por Unidade", opcoes_filtro)
        
        # Aplica o filtro de unidade no conjunto de dados se não for "Todas"
        if unidade_selecionada != "Todas":
            df_exibicao = df_abertas[df_abertas["Unidade"] == unidade_selecionada]
        else:
            df_exibicao = df_abertas
        # --------------------------------
        
        # Verifica se o filtro resultou em alguma OS encontrada
        if not df_exibicao.empty:
            # Exibe a tabela filtrada ocultando a coluna da imagem
            st.dataframe(df_exibicao[['ID', 'Data_Abertura', 'Unidade', 'Responsavel', 'Tipo', 'Descricao']], use_container_width=True)
            
            st.divider()
            st.subheader("🔍 Visualizar Detalhes e Foto")
            
            # O selectbox de detalhes agora mostra apenas os IDs que passaram pelo filtro de unidade
            id_selecionado = st.selectbox("Selecione o ID da OS para detalhar", df_exibicao["ID"].tolist())
            detalhe = df_exibicao[df_exibicao["ID"] == id_selecionado].iloc[0]
            
            col_txt
