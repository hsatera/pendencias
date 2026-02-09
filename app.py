import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

def process_data(file):
    try:
        # 1. Ler os cabeçalhos (Módulo e Atividade)
        file.seek(0)
        # Usamos latin1 para evitar erro de encoding com arquivos do Excel/Windows
        df_header = pd.read_csv(file, sep=';', nrows=2, header=None, encoding='latin1')
        
        # Preencher os nomes dos módulos para a direita (ffill)
        modules_row = df_header.iloc[0].ffill()
        activities_row = df_header.iloc[1]

        # 2. Carregar os dados reais
        file.seek(0)
        df = pd.read_csv(file, sep=';', skiprows=2, header=None, encoding='latin1')
        
        # Mapear as colunas: Lista de tuplas (Módulo, Atividade)
        columns_map = list(zip(modules_row, activities_row))
        
        pendencias = []

        # 3. Varredura de Pendências
        for _, row in df.iterrows():
            # Dados básicos do aluno (Colunas 0 a 3)
            aluno_info = {
                'Aluno': str(row[0]),
                'Equipe': str(row[1]),
                'Supervisor': str(row[2]),
                'Tutor': str(row[3])
            }
            
            # Percorrer as colunas de atividades (a partir da 5)
            for i in range(5, len(row)):
                if i >= len(columns_map): break
                
                modulo_nome = str(columns_map[i][0])
                atividade_nome = str(columns_map[i][1])
                valor = str(row[i]).strip().upper()

                # Ignorar colunas de Notas/Presença
                if any(x in atividade_nome.upper() for x in ["NOTA FINAL", "TOTAL DE", "SESSÕES", "PRESENÇA"]):
                    continue

                # Identificar AG ou NA
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
        st.error(f"Erro ao processar o arquivo: {e}")
        return pd.DataFrame()

# --- Interface Streamlit ---
st.title("📊 Monitoramento de Pendências")

file = st.file_uploader("Arraste o arquivo CSV (separado por ponto e vírgula) aqui", type=['csv'])

if file:
    df_pendencias = process_data(file)
    
    if not df_pendencias.empty:
        # --- Sidebar Filtros ---
        st.sidebar.header("Filtros Gerais")
        tutor_list = sorted(df_pendencias['Tutor'].unique().astype(str))
        tutor_sel = st.sidebar.multiselect("Filtrar por Tutor", options=tutor_list)
        
        dff = df_pendencias.copy()
        if tutor_sel:
            dff = dff[dff['Tutor'].isin(tutor_sel)]

        # --- Dashboard Inicial ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Pendências", len(dff))
        m2.metric("Status AG", len(dff[dff['Status'] == 'AG']))
        m3.metric("Status NA", len(dff[dff['Status'] == 'NA']))

        st.divider()

        # --- Gráfico de Ranking de Tutores (Decrescente) ---
        st.subheader("🏆 Ranking de Pendências por Tutor")
        
        # Agrupar e ordenar
        tutor_ranking = dff['Tutor'].value_counts().reset_index()
        tutor_ranking.columns = ['Tutor', 'Qtd Pendências']
        tutor_ranking = tutor_ranking.sort_values(by='Qtd Pendências', ascending=False)

        fig_rank = px.bar(
            tutor_ranking, 
            x='Tutor', 
            y='Qtd Pendências',
            text='Qtd Pendências',
            color='Qtd Pendências',
            color_continuous_scale='Reds'
        )
        fig_rank.update_traces(textposition='outside')
        fig_rank.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_rank, use_container_width=True)

        st.divider()

        # --- Pendências por Módulo ---
        st.subheader("📦 Pendências por Módulo")
        fig_mod = px.histogram(
            dff, x="Módulo", color="Status", barmode="group",
            color_discrete_map={'AG': '#FFA500', 'NA': '#EF553B'}
        )
        st.plotly_chart(fig_mod, use_container_width=True)

        # --- Tabela Detalhada ---
        st.subheader("📝 Lista Detalhada")
        st.dataframe(dff, use_container_width=True, hide_index=True)
        
        # Download
        csv_export = dff.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório CSV", csv_export, "pendencias.csv", "text/csv")

    else:
        st.info("Nenhuma pendência encontrada no arquivo.")
else:
    st.info("Aguardando upload do arquivo CSV para gerar os indicadores.")
