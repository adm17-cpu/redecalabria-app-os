import streamlit as st
import pandas as pd
import requests
import pytz
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de OS - Rede Calábria", layout="wide")

# Função para capturar hora oficial de Brasília (UTC-3)
def get_brasilia_time():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")

# 2. DEFINIÇÃO DE URLs
url_planilha = "https://docs.google.com/spreadsheets/d/1DdK87OaWuvztkmBonUAbrPu18rNKVQ2Ytpjsq64Bxos/edit?usp=sharing"
url_script = "https://script.google.com/macros/s/AKfycbxAnJNfpLIq4r5E2_Cof6McI3lidx7At-AseEMSvQzUyp5NGwRzStRczBuiWisAd366JA/exec"

# 3. LEITURA DOS DADOS (Com tratamento de erro)
csv_url_dados = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=dados')
csv_url_unidades = url_planilha.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Unidades')

try:
    # Lendo aba principal
    df = pd.read_csv(csv_url_dados)
    
    # Lendo aba de Unidades (pega a primeira coluna)
    df_unidades = pd.read_csv(csv_url_unidades)
    lista_unidades = df_unidades.iloc[:, 0].unique().tolist()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 4. BARRA LATERAL / MENU
st.sidebar.image("https://www.calabria.com.br/wp-content/uploads/2021/05/logo-calabria.png", width=150)
menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Navegação", menu)

# 5. LÓGICA DO APLICATIVO

# --- PÁGINA: ABRIR OS ---
if escolha == "Abrir OS":
    st.header("📝 Abertura de Ordem de Serviço")
    
    with st.form("form_os", clear_on_submit=True):
        unidade = st.selectbox("Selecione a Unidade", lista_unidades)
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil", "TI", "Outros"])
        descricao = st.text_area("Descrição detalhada do problema")
        
        # Opcional: Campo de Câmera (apenas para registro visual no app)
        foto_arquivo = st.camera_input("Foto da ocorrência (Opcional)")
        
        submetido = st.form_submit_button("Enviar Ordem de Serviço")
        
        if submetido:
            if not responsavel or not descricao:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                agora = get_brasilia_time()
                foto_status = "Foto enviada" if foto_arquivo else "Sem foto"
                
                # Prepara os dados para o Google Apps Script
                nova_linha = [
                    int(len(df) + 1), 
                    agora, 
                    unidade, 
                    responsavel, 
                    tipo, 
                    descricao, 
                    foto_status, 
                    "Aberta"
                ]
                
                with st.spinner("Gravando..."):
                    payload = {"action": "add", "row": nova_linha}
                    res = requests.post(url_script, json=payload)
                    
                    if res.status_code == 200:
                        st.success(f"✅ OS Nº {len(df)+1} registrada às {agora}!")
                        st.balloons()
                    else:
                        st.error("Falha na comunicação com o servidor. Tente novamente.")

# --- PÁGINA: VER/ENCERRAR OS ---
elif escolha == "Ver/Encerrar OS":
    st.header("📋 Gerenciamento de Ordens Ativas")
    
    df_abertas = df[df["Status"] == "Aberta"]
    
    if not df_abertas.empty:
        st.dataframe(df_abertas, use_container_width=True)
        
        st.divider()
        st.subheader("Dar Baixa em Ordem")
        
        c1, c2 = st.columns(2)
        with c1:
            id_baixa = st.number_input("Informe o ID da OS", min_value=1, step=1)
        with c2:
            tecnico = st.text_input("Técnico que realizou o serviço")
            
        if st.button("Finalizar Serviço"):
            if id_baixa in df["ID"].values:
                agora_fim = get_brasilia_time()
                payload = {
                    "action": "update",
                    "id": int(id_baixa),
                    "status": "Finalizada",
                    "tecnico": tecnico,
                    "data_fim": agora_fim
                }
                requests.post(url_script, json=payload)
                st.success(f"OS {id_baixa} encerrada com sucesso!")
                st.rerun()
            else:
                st.error("ID não localizado.")
    else:
        st.info("Não existem Ordens de Serviço abertas no momento.")

# --- PÁGINA: DASHBOARD ---
elif escolha == "Dashboard":
    st.header("📊 Painel de Indicadores")
    
    if not df.empty:
        # Métricas rápidas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Pedidos", len(df))
        m2.metric("Pendentes", len(df[df["Status"] == "Aberta"]))
        m3.metric("Concluídas", len(df[df["Status"] == "Finalizada"]))
        
        st.divider()
        
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.subheader("Chamados por Unidade")
            st.bar_chart(df["Unidade"].value_counts())
            
        with col_dir:
            st.subheader("Tipos de Manutenção")
            # Tenta achar a coluna 'Tipo', se não achar usa a 5ª coluna do DF
            col_tipo = "Tipo" if "Tipo" in df.columns else df.columns[4]
            st.bar_chart(df[col_tipo].value_counts())
    else:
        st.warning("A planilha ainda não possui dados para gerar gráficos.")
