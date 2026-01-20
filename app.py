import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

def process_data(file):
    try:
        # 1. Identificar os Módulos (Linha 0)
        file.seek(0)
        df_header = pd.read_csv(file, nrows=0) 
        raw_headers = df_header.columns.tolist()
        
        # Lógica para preencher os nomes dos módulos (que vêm com Unnamed no CSV)
        modules = []
        current_mod = "Cadastro"
        for col in raw_headers:
            if "Unnamed" not in col:
                current_mod = col
            modules.append(current_mod)

        # 2. Carregar os dados reais (Pulando a primeira linha de módulos)
        file.seek(0)
        df = pd.read_csv(file, skiprows=1)
        
        # Colunas que não são atividades
        info_cols = ['Aluno', 'Equipe', 'Supervisor', 'Tutor', 'Último acesso na plataforma']
        
        pendencias = []
        
        # 3. Varredura de Pendências
        for _, row in df.iterrows():
            for i, col_name in enumerate(df.columns):
                if col_name not in info_cols and "Nota Final" not in col_name:
                    valor = str(row[col_name]).strip().upper()
                    
                    # Filtro de pendências
                    if valor in ['AG', 'NA', 'NAN', '']:
                        pendencias.append({
                            'Aluno': row.get('Aluno', 'N/A'),
                            'Tutor': row.get('Tutor', 'Sem Tutor'),
                            'Módulo': modules[i] if i < len(modules) else "Geral",
                            'Atividade': col_name,
                            'Status': 'AG' if valor == 'AG' else 'NA'
                        })
        
        return pd.DataFrame(pendencias)
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return pd.DataFrame()

# --- Interface Streamlit ---
st.title("📊 Monitoramento de Pendências (AG/NA)")

file = st.file_uploader("Arraste o arquivo CSV aqui", type=['csv'])

if file:
    df_pendencias = process_data(file)
    
    if not df_pendencias.empty:
        # --- CORREÇÃO DO TYPEERROR (SORTED) ---
        # Convertemos para string e removemos nulos antes de ordenar
        tutor_list = sorted(df_pendencias['Tutor'].dropna().unique().astype(str))
        
        st.sidebar.header("Filtros")
        tutor_sel = st.sidebar.multiselect("Filtrar Tutor", options=tutor_list)
        
        # Filtragem
        dff = df_pendencias.copy()
        if tutor_sel:
            dff = dff[dff['Tutor'].isin(tutor_sel)]

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pendências", len(dff))
        m2.metric("Status AG", len(dff[dff['Status'] == 'AG']))
        m3.metric("Status NA", len(dff[dff['Status'] == 'NA']))

        # Gráfico
        st.subheader("Pendências por Módulo")
        fig = px.histogram(dff, x="Módulo", color="Status", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

        # Tabela
        st.subheader("Lista Detalhada")
        st.dataframe(dff, use_container_width=True)
        
        # Download
        csv = dff.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar CSV", csv, "pendencias.csv", "text/csv")
    else:
        st.info("Nenhuma pendência encontrada no arquivo.")
