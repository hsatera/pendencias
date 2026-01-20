import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

def process_data(file):
    try:
        # 1. Identificar a extensão do arquivo
        file_extension = os.path.splitext(file.name)[1].lower()
        
        # 2. Ler o cabeçalho para identificar os Módulos
        file.seek(0)
        if file_extension == '.csv':
            df_header = pd.read_csv(file, nrows=0)
        else:
            # Lê Excel (.xls ou .xlsx)
            df_header = pd.read_excel(file, nrows=0)
            
        raw_headers = df_header.columns.tolist()
        
        # Lógica para preencher os nomes dos módulos
        modules = []
        current_mod = "Cadastro"
        for col in raw_headers:
            if "Unnamed" not in str(col):
                current_mod = col
            modules.append(current_mod)

        # 3. Carregar os dados reais
        file.seek(0)
        if file_extension == '.csv':
            df = pd.read_csv(file, skiprows=1)
        else:
            df = pd.read_excel(file, skiprows=1)
        
        info_cols = ['Aluno', 'Equipe', 'Supervisor', 'Tutor', 'Último acesso na plataforma']
        pendencias = []
        
        # 4. Varredura de Pendências
        for _, row in df.iterrows():
            for i, col_name in enumerate(df.columns):
                if col_name not in info_cols and "Nota Final" not in str(col_name):
                    valor_bruto = row[col_name]
                    valor = str(valor_bruto).strip().upper()
                    
                    # Filtro de pendências (AG, NA, Vazio ou Erro de leitura)
                    if valor in ['AG', 'NA', 'NAN', ''] or pd.isna(valor_bruto):
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
st.title("📊 Monitoramento de Pendências")

# AQUI ESTÁ A CORREÇÃO: Adicionado xlsx e xls no type
file = st.file_uploader("Selecione o arquivo (CSV ou Excel)", type=['csv', 'xlsx', 'xls'])

if file:
    df_pendencias = process_data(file)
    
    if not df_pendencias.empty:
        # Tratamento para evitar erro no sorted
        df_pendencias['Tutor'] = df_pendencias['Tutor'].fillna('Sem Tutor').astype(str)
        tutor_list = sorted(df_pendencias['Tutor'].unique())
        
        st.sidebar.header("Filtros")
        tutor_sel = st.sidebar.multiselect("Filtrar Tutor", options=tutor_list)
        
        dff = df_pendencias.copy()
        if tutor_sel:
            dff = dff[dff['Tutor'].isin(tutor_sel)]

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pendências", len(dff))
        m2.metric("Status AG", len(dff[dff['Status'] == 'AG']))
        m3.metric("Status NA", len(dff[dff['Status'] == 'NA']))

        # Gráfico e Tabela
        st.plotly_chart(px.histogram(dff, x="Módulo", color="Status", barmode="group"), use_container_width=True)
        st.dataframe(dff, use_container_width=True)
        
        # Download do resultado
        csv = dff.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Lista de Pendências (CSV)", csv, "pendencias.csv", "text/csv")
