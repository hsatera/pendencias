import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Contador de Pendências", layout="wide")

def process_data(file):
    try:
        file.seek(0)
        # Lemos o arquivo bruto sem cabeçalho primeiro para entender a estrutura
        df_raw = pd.read_csv(
            file, 
            sep=';', 
            encoding='latin1', 
            dtype=str, 
            header=None,        # Lemos sem cabeçalho para tratar as linhas 0 e 1 manualmente
            keep_default_na=False, 
            na_filter=False
        )
        
        # Linha 1 do CSV (índice 1) geralmente tem o nome das atividades
        atividades_nomes = df_raw.iloc[1]
        
        # Dados começam na linha 2 (índice 2)
        df_dados = df_raw.iloc[2:].reset_index(drop=True)
        
        pendencias = []

        # Varredura
        for _, row in df_dados.iterrows():
            # Pegamos o Tutor (coluna 3) e Aluno (coluna 0)
            tutor_nome = str(row[3]).strip()
            aluno_nome = str(row[0]).strip()
            
            # Percorremos apenas as colunas de atividades (da 5 em diante)
            for i in range(5, len(row)):
                valor = str(row[i]).strip().upper()
                nome_coluna = str(atividades_nomes[i]).upper()

                # FILTRO CRÍTICO: Só conta se o valor for NA/AG 
                # E se a coluna não for um resumo de notas ou vazia
                if valor in ['NA', 'AG']:
                    # Ignora colunas que geralmente somam notas ou estão vazias
                    if any(x in nome_coluna for x in ["NOTA", "TOTAL", "SOMA", "MÉDIA", "UNNAMED", "NAN", "PRESENÇA"]):
                        continue
                    
                    # Se o nome da coluna for vazio, também ignoramos (evita contar lixo no fim da linha)
                    if nome_coluna == "" or nome_coluna == "NAN":
                        continue

                    pendencias.append({
                        'Tutor': tutor_nome,
                        'Aluno': aluno_nome,
                        'Atividade': nome_coluna,
                        'Status': valor
                    })
        
        return pd.DataFrame(pendencias)
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return pd.DataFrame()

st.title("📊 Monitoramento de Pendências Real")

file = st.file_uploader("Suba o arquivo CSV", type=['csv'])

if file:
    df_res = process_data(file)
    
    if not df_res.empty:
        # Métricas
        c1, c2, c3 = st.columns(3)
        count_na = len(df_res[df_res['Status'] == 'NA'])
        count_ag = len(df_res[df_res['Status'] == 'AG'])
        
        c1.metric("Total de Pendências", len(df_res))
        c2.metric("Total de 'NA'", count_na, delta_color="inverse")
        c3.metric("Total de 'AG'", count_ag)

        # Ranking de Tutores (Decrescente)
        st.subheader("🏆 Ranking de Pendências por Tutor")
        ranking = df_res['Tutor'].value_counts().reset_index()
        ranking.columns = ['Tutor', 'Total']
        ranking = ranking.sort_values(by='Total', ascending=False)

        fig = px.bar(ranking, x='Tutor', y='Total', text='Total', 
                     color='Total', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

        # Tabela para você conferir se os nomes das atividades fazem sentido
        st.subheader("🔍 Conferência dos Dados (Primeiras 50 linhas)")
        st.dataframe(df_res.head(50), use_container_width=True)
        
        csv_export = df_res.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório Filtrado", csv_export, "pendencias_reais.csv")
    else:
        st.warning("Nenhum 'NA' ou 'AG' válido encontrado após os filtros.")
