import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configurações Iniciais
st.set_page_config(page_title="Monitoramento AG/NA", layout="wide")

st.title("📊 Painel de Atividades Faltantes")
st.markdown("Identificação automática de status **AG** (Aguardando) e **NA** (Não Realizado).")

# 2. Upload do Arquivo
uploaded_file = st.file_uploader("Arraste seu CSV aqui", type=['csv'])

def process_data(file):
    try:
        # Lógica para ler módulos (Linha 1 do CSV)
        file.seek(0)
        # Lendo apenas a primeira linha para mapear os módulos que estão acima das colunas
        df_header = pd.read_csv(file, nrows=0)
        raw_headers = df_header.columns.tolist()
        
        module_mapping = {}
        current_mod = "Geral"
        
        # Preenche os nomes dos módulos para as colunas vazias à direita
        for i, col in enumerate(raw_headers):
            if "Módulo" in str(col) and "Unnamed" not in str(col):
                current_mod = str(col).strip()
            module_mapping[i] = current_mod

        # Lógica para ler os dados (Pulando a linha 1 dos módulos)
        file.seek(0)
        df = pd.read_csv(file, skiprows=1)
        
        # Colunas que não são atividades
        info_cols = ['Aluno', 'Equipe', 'Supervisor', 'Tutor', 'Último acesso na plataforma']
        
        # Lista para converter o formato "Largo" (colunas) para "Longo" (linhas)
        pendencias = []
        
        # Varredura linha por linha
        for _, row in df.iterrows():
            aluno = row.get('Aluno', 'Desconhecido')
            tutor = row.get('Tutor', 'Sem Tutor')
            
            for i, col_name in enumerate(df.columns):
                # Ignorar colunas de cadastro e colunas vazias do pandas (Unnamed)
                if col_name not in info_cols and "Unnamed" not in str(col_name):
                    valor = str(row[col_name]).strip().upper()
                    
                    # Filtro de pendência
                    if valor in ['AG', 'NA', 'N/A', '', 'NAN']:
                        status_final = 'AG' if valor == 'AG' else 'NA'
                        pendencias.append({
                            'Aluno': aluno,
                            'Tutor': tutor,
                            'Módulo': module_mapping.get(i, "Geral"),
                            'Atividade': col_name,
                            'Status': status_final
                        })
        
        return pd.DataFrame(pendencias)
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return pd.DataFrame()

# 3. Execução e Visualização
if uploaded_file:
    with st.spinner('Processando...'):
        df_pendencias = process_data(uploaded_file)

    if not df_pendencias.empty:
        # Métricas no Topo
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Pendências", len(df_pendencias))
        m2.metric("Alunos com Faltas", df_pendencias['Aluno'].nunique())
        m3.metric("Módulos Afetados", df_pendencias['Módulo'].nunique())

        # Filtros na Lateral
        st.sidebar.header("Filtros")
        tutor_sel = st.sidebar.multiselect("Filtrar Tutor", options=sorted(df_pendencias['Tutor'].unique()))
        mod_sel = st.sidebar.multiselect("Filtrar Módulo", options=sorted(df_pendencias['Módulo'].unique()))

        # Aplicação dos Filtros
        dff = df_pendencias.copy()
        if tutor_sel: dff = dff[dff['Tutor'].isin(tutor_sel)]
        if mod_sel: dff = dff[dff['Módulo'].isin(mod_sel)]

        # Layout de Gráficos
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_tutor = px.bar(dff.groupby('Tutor').size().reset_index(name='Qtd'), 
                               x='Tutor', y='Qtd', title="Pendências por Tutor")
            st.plotly_chart(fig_tutor, use_container_width=True)
            
        with col_right:
            # Gráfico de Módulos (Top 10)
            mod_data = dff.groupby('Módulo').size().reset_index(name='Qtd').sort_values('Qtd', ascending=True)
            fig_mod = px.bar(mod_data.tail(10), y='Módulo', x='Qtd', orientation='h', title="Módulos mais Críticos")
            st.plotly_chart(fig_mod, use_container_width=True)

        # Tabela Detalhada
        st.subheader("📋 Lista para Cobrança")
        st.dataframe(dff, use_container_width=True, hide_index=True)

        # Botão de Exportação
        csv_data = dff.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Relatório de Cobrança", csv_data, "pendencias_atualizadas.csv", "text/csv")
    else:
        st.success("🎉 Nenhuma pendência encontrada no arquivo!")
