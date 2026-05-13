import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="Divisão de Disciplinas - Física 2026.2", layout="wide")
st.title("Alocação de Disciplinas - 2026.2")
st.subheader("Coordenação de Licenciatura em Física - IFPI Campus Parnaíba")

# 2. Carregamento e Tratamento dos Dados
@st.cache_data
def carregar_dados():
    # Lê as disciplinas da Aba Física (Ignora as 2 primeiras linhas que são cabeçalhos desconfigurados)
    df_sup = pd.read_csv("Divisão de disciplinas 2026.2.xlsx - Física - Superior.csv", header=1)
    df_sup = df_sup.dropna(subset=['Disciplina ', 'CH/semana'])
    df_sup = df_sup[df_sup['Disciplina '] != 'Disciplina '] # Remove cabeçalhos repetidos dos Módulos
    df_sup['CH/semana'] = pd.to_numeric(df_sup['CH/semana'], errors='coerce').fillna(0)
    df_sup['Tipo'] = 'Superior'
    df_sup = df_sup.rename(columns={'Disciplina ': 'Disciplina'})

    # Lê as disciplinas do Ensino Médio
    df_em = pd.read_csv("Divisão de disciplinas 2026.2.xlsx - Ensino médio.csv")
    df_em = df_em.dropna(subset=['Disciplina - Ensino médio', 'CH/semana'])
    df_em['CH/semana'] = pd.to_numeric(df_em['CH/semana'], errors='coerce').fillna(0)
    df_em['Tipo'] = 'Ensino Médio'
    df_em = df_em.rename(columns={'Disciplina - Ensino médio': 'Disciplina'})
    
    # Consolida a lista final
    df_todas = pd.concat([
        df_sup[['Disciplina', 'CH/semana', 'Tipo']],
        df_em[['Disciplina', 'CH/semana', 'Tipo']]
    ]).reset_index(drop=True)
    return df_todas

df_disciplinas = carregar_dados()

# 3. Criação do Banco de Dados Temporário (CSV) para salvar as respostas
ARQUIVO_RESPOSTAS = "respostas_professores.csv"
if not os.path.exists(ARQUIVO_RESPOSTAS):
    pd.DataFrame(columns=['Professor', 'Disciplina', 'CH_Semana', 'Tipo']).to_csv(ARQUIVO_RESPOSTAS, index=False)

df_respostas = pd.read_csv(ARQUIVO_RESPOSTAS)

# ==========================================
# ÁREA DO PROFESSOR (Formulário)
# ==========================================
st.divider()
st.write("### 📝 Área de Preenchimento do Docente")
nome_professor = st.text_input("Informe seu nome completo:")

disciplinas_selecionadas = st.multiselect(
    "Selecione as disciplinas que deseja ministrar (Superior e Ensino Médio):",
    df_disciplinas['Disciplina'].tolist()
)

if st.button("Enviar Solicitação de Carga Horária"):
    if not nome_professor:
        st.error("Por favor, insira seu nome.")
    else:
        selecoes_detalhes = df_disciplinas[df_disciplinas['Disciplina'].isin(disciplinas_selecionadas)]
        
        # Validação: Pelo menos 1 disciplina do Ensino Médio
        tem_ensino_medio = any(selecoes_detalhes['Tipo'] == 'Ensino Médio')
        
        if not tem_ensino_medio:
            st.error("⚠️ Atenção: É obrigatório selecionar no mínimo 1 (uma) disciplina do Ensino Médio.")
        else:
            # Salva os dados se passar nas regras
            novas_linhas = []
            for _, row in selecoes_detalhes.iterrows():
                novas_linhas.append({
                    'Professor': nome_professor,
                    'Disciplina': row['Disciplina'],
                    'CH_Semana': row['CH/semana'],
                    'Tipo': row['Tipo']
                })
            df_novas = pd.DataFrame(novas_linhas)
            
            # Atualiza evitando duplicatas do mesmo professor na mesma disciplina
            df_atualizado = pd.concat([df_respostas, df_novas]).drop_duplicates(subset=['Professor', 'Disciplina'])
            df_atualizado.to_csv(ARQUIVO_RESPOSTAS, index=False)
            
            st.success("✅ Seleção salva com sucesso!")
            df_respostas = df_atualizado # Recarrega a visualização

# ==========================================
# ÁREA DA COORDENAÇÃO (Dashboard)
# ==========================================
st.divider()
st.write("### 📊 Painel de Visualização da Coordenação")

if not df_respostas.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**1. Carga Horária Semanal por Docente:**")
        ch_por_professor = df_respostas.groupby('Professor')['CH_Semana'].sum().reset_index()
        ch_por_professor.rename(columns={'CH_Semana': 'Total CH/semana'}, inplace=True)
        st.dataframe(ch_por_professor, use_container_width=True)
    
    with col2:
        st.write("**2. Interessados por Disciplina:**")
        interessados = df_respostas.groupby('Disciplina')['Professor'].apply(lambda x: ' | '.join(x)).reset_index()
        interessados = interessados.merge(df_disciplinas[['Disciplina', 'CH/semana', 'Tipo']], on='Disciplina', how='left')
        st.dataframe(interessados, use_container_width=True)
else:
    st.info("Aguardando submissões dos professores.")
