import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

def process_data(file):
    try:
        # 1. Ler cabeçalhos
        file.seek(0)
        df_header = pd.read_csv(file, sep=';', nrows=2, header=None, encoding='latin1')
        
        modules_row = df_header.iloc[0].ffill()
        activities_row = df_header.iloc[1]

        # 2. Carregar dados
        file.seek(0)
        # O segredo: keep_default_na=False impede que o 'NA' vire um buraco vazio (NaN)
        df = pd.read_csv(
            file, 
            sep=';', 
            skiprows=2, 
            header=None, 
            encoding='latin1', 
            keep_default_na=False
        )
        
        columns_map = list(zip(modules_row, activities_row))
        pendencias = []

        # 3. Varredura
        for _, row in df.iterrows():
            aluno_info = {
                'Aluno': str(row[0]),
                'Equipe': str(row[1]),
                'Supervisor': str(row[2]),
                'Tutor': str(row[3])
            }
            
            for i in range(5, len(row)):
                if i >= len(columns_map): break
                
                atividade_nome = str(columns_map[i][1])
                modulo_nome = str(columns_map[i][0])
                
                # Convertendo para string e removendo espaços para garantir a comparação
                valor = str(row[i]).strip().upper()

                if any(x in atividade_nome.upper() for x in ["NOTA FINAL", "TOTAL DE", "SESSÕES", "PRESENÇA"]):
                    continue

                # Agora o 'NA' será detectado como string
                if valor in ['AG', 'NA']:
                    item = aluno_info.copy()
                    item.update({
                        'Módulo': modulo_nome,
                        'Atividade': atividade_nome,
                        'Status': valor
                    })
                    pendencias.append(item)
        
        return pd.DataFrame(pendencias)
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return pd.DataFrame()

# --- Interface ---
st.title("📊 Monitoramento de Pendências")

file = st.file_uploader("Arraste o arquivo CSV aqui", type=['csv'])

if file:
    df_pendencias = process_data(file)
    
    if not df_pendencias.empty:
        # Filtros
        tutor_list = sorted(df_pendencias['Tutor'].unique().astype(str))
        tutor_sel = st.sidebar.multiselect("Filtrar por Tutor", options=tutor_list)
        
        dff = df_pendencias.copy()
        if tutor_sel:
            dff = dff[dff['Tutor'].isin(tutor_sel)]

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Pendências", len(dff))
        m2.metric("Status AG", len(dff[dff['Status'] == 'AG']))
        m3.metric("Status NA", len(dff[dff['Status'] == 'NA']))

        st.divider()

        # Gráfico Ranking Tutor
        st.subheader("🏆 Ranking de Pendências por Tutor")
        tutor_ranking = dff['Tutor'].value_counts().reset_index()
        tutor_ranking.columns = ['Tutor', 'Qtd Pendências']
        tutor_ranking = tutor_ranking.sort_values(by='Qtd Pendências', ascending=False)

        fig_rank = px.bar(tutor_ranking, x='Tutor', y='Qtd Pendências', text='Qtd Pendências',
                          color='Qtd Pendências', color_continuous_scale='Reds')
        st.plotly_chart(fig_rank, use_container_width=True)

        st.divider()

        # Tabela
        st.subheader("📝 Lista Detalhada")
        st.dataframe(dff, use_container_width=True, hide_index=True)
        
        csv_export = dff.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório", csv_export, "pendencias.csv", "text/csv")
    else:
        st.warning("Nenhuma pendência 'AG' ou 'NA' encontrada. Verifique se essas siglas existem no arquivo.")
