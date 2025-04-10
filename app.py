import streamlit as st

# Configuração geral
st.set_page_config(page_title="Aplicativo de Apostas", page_icon="🏆", layout="wide")

# Página inicial
st.title("Bem-vindo ao Aplicativo de Apostas")
st.write("""
    Este aplicativo permite analisar estratégias de apostas com base em dados históricos.
    Estatística quantitativa é um método que usa números para testar hipóteses e estabelecer relações entre variáveis.
    Com base em evidências, permite fazer previsões e tirar conclusões. 
    
    Use a barra lateral para navegar entre as páginas:
    - **Dashboard**: Visão geral dos dados.
    
    
""")


st.markdown("⚽ **Análise de Jogos**")
st.markdown("🥅 **Gols e Estatísticas**")
st.markdown("🏆 **Melhores Estratégias**")
st.markdown("📊 **Probabilidades e Odds**")
st.markdown("🎯 **Taxa de Acertos**")
st.markdown("💰 **Lucro das Estratégias**")
st.markdown("🟢 **Apostas Vencedoras**")
st.markdown("🔴 **Apostas Perdedoras**")
st.markdown("⏳ **Tempo de Jogo**")
st.markdown("🏟 **Estádios e Times**")
st.markdown("🎲 **Simulações de Jogos**")
st.markdown("📅 **Jogos do Dia**")
st.markdown("🔥 **Tendências do Mercado**")
st.markdown("📈 **Gráficos de Performance**")
st.markdown("🎥 **Replays e Análises**")
st.markdown("👕 **Uniformes e Escalações**")
st.markdown("🎉 **Comemorações de Gols**")
st.markdown("📝 **Relatórios e Estatísticas**")
st.markdown("🤖 **Automação de Apostas**")
st.markdown("🚀 **Testes de Estratégias**")

st.sidebar.title("Navegação")
st.sidebar.write("Escolha uma página nas opções acima.")
