import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Monitoramento AG", layout="wide")

def process_data(file):
    try:
        file.seek(0)
        # Leitura bruta para evitar que o pandas ignore colunas ou mude nomes
        df_raw = pd.read_csv(
            file, 
            sep=';', 
            encoding='latin1', 
            dtype=str, 
            header=None,
            keep_default_na=False, 
            na_filter=False
        )
        
        # A linha 1 (índice 1) contém os nomes das atividades
        atividades_nomes = df_raw.iloc[1]
        
        # Os dados dos alunos começam na linha 2
        df_dados = df_raw.iloc[2:].reset_index(drop=True)
        
        lista_ag = []

        for _, row in df_dados.iterrows():
            # Coluna 3 costuma ser o Tutor, Coluna 0 o Aluno
            tutor_nome = str(row[3]).strip()
            aluno_nome = str(row[0]).strip()
            
            # Varre as colunas de atividades (da 5 em diante)
            for i in range(5, len(row)):
                valor = str(row[i]).strip().upper()
                nome_atividade = str(atividades_nomes[i]).upper()

                # FOCO EXCLUSIVO NO "AG"
                if valor == 'AG':
                    # Filtro para ignorar colunas que não são tarefas reais
                    if any(x in nome_atividade for x in ["NOTA", "TOTAL", "SOMA", "MÉDIA", "PRESENÇA", "NAN", "UNNAMED"]):
                        continue
                    
                    if nome_atividade == "" or nome_atividade == "NAN":
                        continue

                    lista_ag.append({
                        'Tutor': tutor_nome,
                        'Aluno': aluno_nome,
                        'Atividade': nome_atividade,
                        'Status': 'AG'
                    })
        
        return pd.DataFrame(lista_ag)
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return pd.DataFrame()

# --- Interface ---
st.title("📊 Monitoramento de Status: AG")

file = st.file_uploader("Suba o arquivo CSV (ponto e vírgula)", type=['csv'])

if file:
    df_ag = process_data(file)
    
    if not df_ag.empty:
        # Métrica Principal
        st.metric("Total de ocorrências 'AG'", len(df_ag))

        st.divider()

        # Ranking de Tutores (Decrescente)
        st.subheader("🏆 Ranking de AG por Tutor")
        ranking = df_ag['Tutor'].value_counts().reset_index()
        ranking.columns = ['Tutor', 'Quantidade']
        ranking = ranking.sort_values(by='Quantidade', ascending=False)

        fig = px.bar(
            ranking, 
            x='Tutor', 
            y='Quantidade', 
            text='Quantidade',
            color='Quantidade', 
            color_continuous_scale='Oranges'
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Visualização dos Dados
        st.subheader("📝 Detalhamento dos AGs encontrados")
        st.dataframe(df_ag, use_container_width=True, hide_index=True)
        
        # Download
        csv_export = df_ag.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório de AG", csv_export, "status_ag.csv")
    else:
        st.warning("Nenhum status 'AG' foi encontrado no arquivo com os filtros aplicados.")
else:
    st.info("Aguardando upload do arquivo para análise.")
