import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Gestão de OS", layout="wide")

# Conexão com o Google Sheets
url = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler dados
df = conn.read(spreadsheet=url, worksheet="dados")

menu = ["Abrir OS", "Ver/Encerrar OS", "Dashboard"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Abrir OS":
    st.header("Abertura de Ordem de Serviço")
    
    with st.form("form_os"):
        unidade = st.selectbox("Unidade", ["Unidade A", "Unidade B", "Unidade C"])
        responsavel = st.text_input("Seu Nome")
        tipo = st.selectbox("Tipo de Manutenção", ["Elétrica", "Hidráulica", "Mecânica", "Civil"])
        descricao = st.text_area("Descrição do Problema")
        # Para fotos sem Google Cloud, usamos link ou base64 simples (neste exemplo, texto para simplificar)
        foto = st.text_input("Link da Foto (ou use a câmera do celular)")
        
        submetido = st.form_submit_button("Abrir Ordem de Serviço")
        
        if submetido:
            nova_os = pd.DataFrame([{
                "ID": len(df) + 1,
                "Data_Abertura": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Unidade": unidade,
                "Responsavel": responsavel,
                "Tipo": tipo,
                "Descricao": descricao,
                "Foto_URL": foto,
                "Status": "Aberta"
            }])
            
            # Adicionar à planilha
            df_atualizado = pd.concat([df, nova_os], ignore_index=True)
            conn.update(spreadsheet=url, worksheet="dados", data=df_atualizado)
            st.success(f"OS Nº {len(df)+1} aberta com sucesso!")

elif escolha == "Ver/Encerrar OS":
    st.header("Ordens de Serviço Ativas")
    
    # Filtro por Unidade
    unidade_filtro = st.selectbox("Filtrar por Unidade", df["Unidade"].unique())
    os_filtradas = df[(df["Unidade"] == unidade_filtro) & (df["Status"] == "Aberta")]
    
    st.dataframe(os_filtradas)
    
    st.divider()
    st.subheader("Dar Baixa em uma OS")
    id_baixa = st.number_input("Digite o Número (ID) da OS para encerrar", step=1)
    nome_tecnico = st.text_input("Nome do Técnico Responsável")
    
    if st.button("Encerrar Ordem de Serviço"):
        if id_baixa in df["ID"].values:
            idx = df.index[df["ID"] == id_baixa][0]
            df.at[idx, "Status"] = "Finalizada"
            df.at[idx, "Tecnico_Encerramento"] = nome_tecnico
            df.at[idx, "Data_Encerramento"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            conn.update(spreadsheet=url, worksheet="dados", data=df)
            st.success(f"OS {id_baixa} encerrada com sucesso!")
            st.rerun()

elif escolha == "Dashboard":
    st.info("Para relatórios avançados, conecte esta planilha ao Looker Studio.")
    st.write("Resumo Rápido:")
    st.bar_chart(df["Unidade"].value_counts())
