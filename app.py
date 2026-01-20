import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

def process_data(file):
    try:
        file_extension = os.path.splitext(file.name)[1].lower()
        file.seek(0)
        
        # --- 1. LEITURA INTELIGENTE DO ARQUIVO ---
        if file_extension == '.csv':
            # Tenta ler CSV (pode precisar de encoding='latin1' dependendo do sistema)
            df_full = pd.read_csv(file)
        else:
            try:
                # Tenta ler como Excel padrão (XLSX ou XLS real)
                df_full = pd.read_excel(file)
            except Exception as e:
                # SE FALHAR (Erro Workbook corruption): Tenta ler como HTML
                # Isso resolve o problema de arquivos exportados que são HTML com extensão .xls
                if "Workbook corruption" in str(e) or "not supported" in str(e) or "Excel" in str(e):
                    file.seek(0)
                    tables = pd.read_html(file)
                    df_full = tables[0]
                else:
                    raise e

        # --- 2. IDENTIFICAÇÃO DOS MÓDULOS (Baseado no Cabeçalho) ---
        # No formato enviado, a primeira linha lida pelo pandas são os Módulos
        raw_headers = df_full.columns.tolist()
        modules = []
        current_mod = "Cadastro"
        for col in raw_headers:
            col_str = str(col)
            if "Unnamed" not in col_str:
                current_mod = col_str
            modules.append(current_mod)

        # --- 3. AJUSTE DE CABEÇALHO ---
        # A primeira linha de dados do DF na verdade contém os nomes das Atividades
        df = df_full.copy()
        df.columns = df.iloc[0]  # Transforma a primeira linha em cabeçalho das colunas
        df = df.drop(df.index[0]) # Remove essa linha dos dados reais
        
        # Colunas de informação que devem ser ignoradas na varredura de atividades
        info_cols = ['Aluno', 'Equipe', 'Supervisor', 'Tutor', 'Último acesso na plataforma']
        pendencias = []
        
        # --- 4. VARREDURA DE PENDÊNCIAS ---
        for _, row in df.iterrows():
            for i, col_name in enumerate(df.columns):
                col_str = str(col_name).strip()
                
                # Critérios para ser uma coluna de Atividade
                if col_str not in info_cols and "Nota Final" not in col_str and "Unnamed" not in col_str:
                    valor_bruto = row[col_name]
                    valor = str(valor_bruto).strip().upper()
                    
                    # Filtro de pendências: AG, NA, Vazio ou NaN
                    if valor in ['AG', 'NA', 'NAN', ''] or pd.isna(valor_bruto):
                        pendencias.append({
                            'Aluno': str(row.get('Aluno', 'N/A')),
                            'Tutor': str(row.get('Tutor', 'Sem Tutor')),
                            'Módulo': modules[i] if i < len(modules) else "Geral",
                            'Atividade': col_str,
                            'Status': 'AG' if valor == 'AG' else 'NA'
                        })
        
        return pd.DataFrame(pendencias)
        
    except Exception as e:
        st.error(f"Erro crítico no processamento: {e}")
        return pd.DataFrame()

# --- INTERFACE STREAMLIT ---
st.title("📊 Monitoramento de Pendências (CSV/XLS/XLSX)")
st.markdown("O sistema agora aceita arquivos CSV e Excel (incluindo exportações de sistemas antigos).")

# Suporte a múltiplos formatos no seletor
file = st.file_uploader("Arraste seu arquivo aqui", type=['csv', 'xlsx', 'xls'])

if file:
    with st.spinner('Processando dados...'):
        df_pendencias = process_data(file)
    
    if not df_pendencias.empty:
        # Tratamento de dados para filtros
        df_pendencias['Tutor'] = df_pendencias['Tutor'].fillna('Sem Tutor').replace('nan', 'Sem Tutor')
        tutor_list = sorted(df_pendencias['Tutor'].unique().astype(str))
        
        st.sidebar.header("Filtros")
        tutor_sel = st.sidebar.multiselect("Selecionar Tutor", options=tutor_list)
        
        # Aplicar Filtro
        dff = df_pendencias.copy()
        if tutor_sel:
            dff = dff[dff['Tutor'].isin(tutor_sel)]

        # Métricas Principais
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Pendências", len(dff))
        col2.metric("Aguardando (AG)", len(dff[dff['Status'] == 'AG']))
        col3.metric("Não Acessado (NA)", len(dff[dff['Status'] == 'NA']))

        # Gráfico de Pendências por Módulo
        st.subheader("Pendências por Módulo")
        fig = px.histogram(
            dff, 
            x="Módulo", 
            color="Status", 
            barmode="group",
            color_discrete_map={'AG': '#FFA500', 'NA': '#FF4B4B'}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabela Detalhada
        st.subheader("Lista para Acompanhamento")
        st.dataframe(dff, use_container_width=True)
        
        # Botão de Exportação
        csv_data = dff.to_csv(index=False).encode('utf-8-sig') # utf-8-sig para abrir direto no Excel sem erro de acento
        st.download_button(
            label="📥 Baixar Relatório de Pendências",
            data=csv_data,
            file_name="pendencias_extraidas.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma pendência detectada ou o formato do arquivo não é o esperado.")

# Rodapé informativo
st.divider()
st.caption("Dica: Se o erro de 'Workbook corruption' persistir, tente salvar o arquivo original como .xlsx no seu computador e suba novamente.")
