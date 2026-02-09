import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Contador de Pendências", layout="wide")

def process_data(file):
    try:
        file.seek(0)
        # Lemos o arquivo tratando TUDO como string e desativando conversões automáticas
        df = pd.read_csv(
            file, 
            sep=';', 
            encoding='latin1', 
            dtype=str, 
            keep_default_na=False, # Não deixa o 'NA' virar vazio
            na_filter=False        # Desativa qualquer detecção de nulo
        )
        
        # Identificar as colunas fixas (ajuste os nomes se forem diferentes no seu CSV)
        # Vamos assumir que as primeiras colunas são os dados do aluno/tutor
        col_aluno = df.columns[0]
        col_tutor = df.columns[3] # Geralmente a 4ª coluna (índice 3)
        
        pendencias = []

        # Varredura linha por linha, célula por célula
        for _, row in df.iterrows():
            tutor_nome = str(row[col_tutor]).strip()
            aluno_nome = str(row[col_aluno]).strip()
            
            for col_nome in df.columns[5:]: # Começa da 6ª coluna em diante
                valor = str(row[col_nome]).strip().upper()
                
                if valor == 'NA' or valor == 'AG':
                    pendencias.append({
                        'Tutor': tutor_nome,
                        'Aluno': aluno_nome,
                        'Atividade': col_nome,
                        'Status': valor
                    })
        
        return pd.DataFrame(pendencias)
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return pd.DataFrame()

st.title("📊 Contador de Status NA/AG")

file = st.file_uploader("Upload do CSV", type=['csv'])

if file:
    df_res = process_data(file)
    
    if not df_res.empty:
        # Métricas de conferência
        c1, c2 = st.columns(2)
        count_na = len(df_res[df_res['Status'] == 'NA'])
        count_ag = len(df_res[df_res['Status'] == 'AG'])
        
        c1.metric("Total de 'NA' encontrados", count_na)
        c2.metric("Total de 'AG' encontrados", count_ag)

        # Gráfico de Ranking por Tutor
        st.subheader("Ranking de Pendências por Tutor")
        ranking = df_res['Tutor'].value_counts().reset_index()
        ranking.columns = ['Tutor', 'Total']
        
        fig = px.bar(ranking, x='Tutor', y='Total', text='Total', color='Total', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

        # Tabela para conferência real
        st.subheader("Dados Extraídos")
        st.dataframe(df_res)
    else:
        st.error("O sistema não encontrou nenhum 'NA' ou 'AG'. Verifique se o separador do arquivo é mesmo ponto e vírgula (;)")
