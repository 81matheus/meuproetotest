import streamlit as st

# Configuração geral
st.set_page_config(page_title="Aplicativo de Apostas", page_icon="🏆", layout="wide")

# Página inicial
st.title("Bem-vindo ao Aplicativo de Apostas Estatístico")
st.write("""
    Este aplicativo permite analisar estratégias de apostas com base em dados históricos.
    Estatística quantitativa é um método que usa números para testar hipóteses e estabelecer relações entre variáveis.
    Com base em evidências, permite fazer previsões e tirar conclusões. 

    
    * Newton buscava leis universais que descrevessem o movimento e as interações. Ele focava em:
    1. Forças e Equilíbrio: Identificar as "forças" em jogo (probabilidades implícitas) e procurar situações de desequilíbrio previsível ou de forte tendência para um estado específico.
    2. Causa e Efeito: Relacionar condições iniciais (odds e suas relações) com resultados prováveis.
    3. Leis Matemáticas: Expressar essas relações através de regras matemáticas claras e quantificáveis (nossas condições de filtro).
    4. Inércia: Um sistema tende a permanecer em seu estado (por exemplo, um jogo tende a ser de poucos gols se as "forças" apontarem nessa direção).          
    
  
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
