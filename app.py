import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

def process_data(file):
    try:
        # 1. Ler os cabeçalhos usando latin1 para evitar erros de acentuação (ex: 'ó' em Módulo)
        # Lemos as primeiras 2 linhas
        file.seek(0)
        df_header = pd.read_csv(file, sep=';', nrows=2, header=None, encoding='latin1')
        
        # Preencher os nomes dos módulos (que vêm com células vazias à direita no CSV)
        # O ffill() faz o nome do módulo "correr" para a direita até encontrar o próximo
        modules_row = df_header.iloc[0].ffill()
        activities_row = df_header.iloc[1]

        # 2. Carregar os dados reais pulando as duas linhas de cabeçalho
        file.seek(0)
        df = pd.read_csv(file, sep=';', skiprows=2, header=None, encoding='latin1')
        
        # Mapear as colunas: Lista de tuplas (Módulo, Atividade)
        columns_map = list(zip(modules_row, activities_row))
        
        pendencias = []

        # 3. Varredura de Pendências (começando da coluna 5, onde terminam os dados do aluno)
        for _, row in df.iterrows():
            # Dados básicos do aluno (ajuste os índices se a estrutura mudar)
            aluno_info = {
                'Aluno': str(row[0]),
                'Equipe': str(row[1]),
                'Supervisor': str(row[2]),
                'Tutor': str(row[3])
            }
            
            # Percorre as colunas de atividades
            for i in range(5, len(row)):
                modulo_nome = str(columns_map[i][0])
                atividade_nome = str(columns_map[i][1])
                valor = str(row[i]).strip().upper()

                # Ignorar colunas de resumo ou notas que não são tarefas de entrega
                if any(x in atividade_nome.upper() for x in ["NOTA FINAL", "TOTAL DE", "SESSÕES"]):
                    continue

                # Filtro de pendências
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
st.markdown("Filtre e visualize atividades com status **AG** (Aguardando) ou **NA** (Não Atribuído).")

file = st.file_uploader("Arraste o arquivo CSV (ponto e vírgula) aqui", type=['csv'])

if file:
    df_pendencias = process_data(file)
    
    if not df_pendencias.empty:
        # --- Sidebar Filtros ---
        st.sidebar.header("Filtros")
        
        tutor_list = sorted(df_pendencias['Tutor'].unique().astype(str))
        tutor_sel = st.sidebar.multiselect("Filtrar por Tutor", options=tutor_list)
        
        mod_list = sorted(df_pendencias['Módulo'].unique().astype(str))
        mod_sel = st.sidebar.multiselect("Filtrar por Módulo", options=mod_list)

        # Aplicar Filtros
        dff = df_pendencias.copy()
        if tutor_sel:
            dff = dff[dff['Tutor'].isin(tutor_sel)]
        if mod_sel:
            dff = dff[dff['Módulo'].isin(mod_sel)]

        # --- Dashboard ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pendências", len(dff))
        col2.metric("Status AG", len(dff[dff['Status'] == 'AG']))
        col3.metric("Status NA", len(dff[dff['Status'] == 'NA']))

        # Gráfico
        st.subheader("Pendências por Módulo")
        if not dff.empty:
            fig = px.histogram(
                dff, 
                x="Módulo", 
                color="Status", 
                barmode="group",
                color_discrete_map={'AG': '#FFA500', 'NA': '#EF553B'} # Laranja e Vermelho
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabela
            st.subheader("Lista Detalhada")
            st.dataframe(dff, use_container_width=True, hide_index=True)
            
            # Download (usando utf-8-sig para que o Excel brasileiro abra corretamente)
            csv_export = dff.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Lista em CSV", csv_export, "relatorio_pendencias.csv", "text/csv")
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.info("Nenhuma pendência 'AG' ou 'NA' encontrada. Verifique o formato do arquivo.")
else:
    st.info("Aguardando upload do arquivo CSV.")
