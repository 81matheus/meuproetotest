import streamlit as st
import pandas as pd
import numpy as np
import io # Necessário para ler o buffer do arquivo carregado

# --- Função Auxiliar para Carregar Dados ---
def load_dataframe(uploaded_file):
    """Carrega um DataFrame de um arquivo XLSX ou CSV carregado via Streamlit."""
    if uploaded_file is None:
        return None
    try:
        # Verifica a extensão do nome do arquivo
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.xlsx'):
            # Lê o arquivo Excel diretamente do buffer
            df = pd.read_excel(uploaded_file)
            return df
        elif file_name.endswith('.csv'):
            # Lê o arquivo CSV diretamente do buffer
            # Tenta detectar separador comum (vírgula ou ponto e vírgula)
            # Cria uma cópia do buffer para não consumir o original
            file_content = uploaded_file.getvalue()
            try:
                # Tenta com vírgula primeiro
                df = pd.read_csv(io.BytesIO(file_content), sep=',')
                 # Checa se a primeira linha foi lida corretamente (mais de uma coluna)
                if df.shape[1] <= 1:
                    # Se parece errado, tenta com ponto e vírgula
                    uploaded_file.seek(0) # Volta para o início do buffer
                    df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()), sep=';')
            except Exception as e_csv:
                 # Se ambos falharem, tenta com ponto e vírgula como fallback
                 st.warning(f"Não foi possível determinar o separador CSV automaticamente, tentando ';'. Erro: {e_csv}")
                 uploaded_file.seek(0) # Volta para o início do buffer
                 try:
                     df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()), sep=';')
                 except Exception as e_final_csv:
                      st.error(f"Falha ao ler o arquivo CSV mesmo com separador ';'. Verifique o formato. Erro: {e_final_csv}")
                      return None

            # Verificação final se a leitura do CSV foi bem sucedida
            if df.empty or df.shape[1] <= 1:
                 st.error("Falha ao ler o arquivo CSV corretamente. Verifique o separador (',' ou ';') e o formato.")
                 return None
            return df
        else:
            st.error("Formato de arquivo não suportado. Use .xlsx ou .csv")
            return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo '{uploaded_file.name}': {e}")
        return None
# --- Fim da Função Auxiliar ---

# --- INÍCIO: Definição das Ligas Aprovadas ---
# Use um set para busca eficiente
APPROVED_LEAGUES = set([
    "ARGENTINA 1", "ARGENTINA 2", "AUSTRALIA 1", "AUSTRIA 1", "AUSTRIA 2", "BELGIUM 1", "BELGIUM 2", "BOLIVIA 1", "BRAZIL 1", "BRAZIL 2",
    "BULGARIA 1", "CHILE 1", "CHINA 1", "CHINA 2", "COLOMBIA 1", "COLOMBIA 2", "CROATIA 1", "CZECH 1", "DENMARK 1", "DENMARK 2",
    "ECUADOR 1", "EGYPT 1", "ENGLAND 1", "ENGLAND 2", "ENGLAND 3", "ENGLAND 4", "ENGLAND 5", "ESTONIA 1", "EUROPA CHAMPIONS LEAGUE",
    "EUROPA CONFERENCE LEAGUE", "EUROPA LEAGUE", "FINLAND 1", "FRANCE 1", "GREECE 1", "HUNGARY 1", "IRELAND 1", "IRELAND 2", "ISRAEL 1",
    "ITALY 1", "ITALY 2", "JAPAN 1", "JAPAN 2", "MEXICO 1", "MEXICO 2",  "NETHERLANDS 1", "NETHERLANDS 2", "NORTHERN IRELAND 2", "NORWAY 1",
    "NORWAY 2", "PARAGUAY 1", "PERU 1", "POLAND 1", "POLAND 2", "PORTUGAL 1", "PORTUGAL 2", "ROMANIA 1", "ROMANIA 2", "SAUDI ARABIA 1",
    "SCOTLAND 1", "SCOTLAND 2", "SCOTLAND 3", "SCOTLAND 4", "SERBIA 1",  "SLOVAKIA 1", "SOUTH KOREA 1", "SOUTH KOREA 2", "SPAIN 1", "SPAIN 2",
    "SWEDEN 1", "SWEDEN 2", "SWITZERLAND 1", "SWITZERLAND 2", "TURKEY 1", "TURKEY 2", "UKRAINE 1", "URUGUAY 1", "USA 1", "VENEZUELA 1", "WALES 1"
])
# --- FIM: Definição das Ligas Aprovadas ---

# --- Função Removida: run_backtest ---
# --- Função Removida: check_moving_averages ---

# Analisar jogos do dia
def analyze_daily_games(df_daily, estrategia_func):
    """Aplica uma função de estratégia a um DataFrame e retorna os jogos filtrados."""
    # Verifica se colunas necessárias existem antes de aplicar a estratégia
    required_cols = ['Odd_H_Back', 'Odd_D_Back', 'Odd_A_Back', 'Odd_Over25_FT_Back', 'Odd_Under25_FT_Back',
                     'Odd_BTTS_Yes_Back', 'Odd_BTTS_No_Back', 'Odd_CS_0x0_Lay', 'Odd_CS_0x1_Lay', 'Odd_CS_1x0_Lay']
    missing_cols = [col for col in required_cols if col not in df_daily.columns]
    if missing_cols:
        #st.warning(f"Colunas necessárias para as estratégias não encontradas no arquivo: {', '.join(missing_cols)}. Pulando análise.")
        # Retorna None ou DataFrame vazio para indicar falha
        return pd.DataFrame() # Retorna DataFrame vazio para consistência

    # Calcula as variáveis *apenas para os jogos do dia*
    try:
        vars_dict = pre_calculate_all_vars(df_daily)
        # Aplica a função da estratégia específica
        # A função estrategia_func agora opera diretamente sobre df_daily usando as vars_dict calculadas
        df_filtrado = estrategia_func(df_daily, vars_dict) # Passa vars_dict para a função
    except Exception as e:
        st.error(f"Erro ao calcular variáveis ou aplicar estratégia nos jogos do dia: {e}")
        return pd.DataFrame() # Retorna DataFrame vazio em caso de erro

    if df_filtrado is not None and not df_filtrado.empty:
        # Ajuste para incluir colunas relevantes se existirem
        cols_to_return = ['Time', 'League', 'Home', 'Away'] # Adiciona League por padrão
        # Garante que apenas colunas existentes sejam selecionadas
        cols_exist = [col for col in cols_to_return if col in df_filtrado.columns]
        if cols_exist:
             return df_filtrado[cols_exist].copy()
        else: # Se nenhuma das colunas básicas existir, retorna DF vazio
             # st.warning(f"Colunas essenciais ('Time', 'League', 'Home', 'Away') não encontradas no resultado da estratégia.")
             return pd.DataFrame()
    return pd.DataFrame() # Retorna DataFrame vazio se não houver jogos aprovados

# Pre-calcular variáveis (mantida como estava, pois é necessária para as estratégias)


# Pre-calcular variáveis
def pre_calculate_all_vars(df):
    probs = {
        'pH': 1 / df['Odd_H_Back'],
        'pD': 1 / df['Odd_D_Back'],
        'pA': 1 / df['Odd_A_Back'],
        'pOver': 1 / df['Odd_Over25_FT_Back'],
        'pUnder': 1 / df['Odd_Under25_FT_Back'],
        'pBTTS_Y': 1 / df['Odd_BTTS_Yes_Back'],
        'pBTTS_N': 1 / df['Odd_BTTS_No_Back'],
        'p0x0': 1 / df['Odd_CS_0x0_Lay'],
        'p0x1': 1 / df['Odd_CS_0x1_Lay'],
        'p1x0': 1 / df['Odd_CS_1x0_Lay']
    }
    
    vars_dict = {
        'VAR01': probs['pH'] / probs['pD'],
        'VAR02': probs['pH'] / probs['pA'],
        'VAR03': probs['pD'] / probs['pH'],
        'VAR04': probs['pD'] / probs['pA'],
        'VAR05': probs['pA'] / probs['pH'],
        'VAR06': probs['pA'] / probs['pD'],
        'VAR07': probs['pOver'] / probs['pUnder'],
        'VAR08': probs['pUnder'] / probs['pOver'],
        'VAR09': probs['pBTTS_Y'] / probs['pBTTS_N'],
        'VAR10': probs['pBTTS_N'] / probs['pBTTS_Y'],
        'VAR11': probs['pH'] / probs['pOver'],
        'VAR12': probs['pD'] / probs['pOver'],
        'VAR13': probs['pA'] / probs['pOver'],
        'VAR14': probs['pH'] / probs['pUnder'],
        'VAR15': probs['pD'] / probs['pUnder'],
        'VAR16': probs['pA'] / probs['pUnder'],
        'VAR17': probs['pH'] / probs['pBTTS_Y'],
        'VAR18': probs['pD'] / probs['pBTTS_Y'],
        'VAR19': probs['pA'] / probs['pBTTS_Y'],
        'VAR20': probs['pH'] / probs['pBTTS_N'],
        'VAR21': probs['pD'] / probs['pBTTS_N'],
        'VAR22': probs['pA'] / probs['pBTTS_N'],
        'VAR23': probs['p0x0'] / probs['pH'],
        'VAR24': probs['p0x0'] / probs['pD'],
        'VAR25': probs['p0x0'] / probs['pA'],
        'VAR26': probs['p0x0'] / probs['pOver'],
        'VAR27': probs['p0x0'] / probs['pUnder'],
        'VAR28': probs['p0x0'] / probs['pBTTS_Y'],
        'VAR29': probs['p0x0'] / probs['pBTTS_N'],
        'VAR30': probs['p0x1'] / probs['pH'],
        'VAR31': probs['p0x1'] / probs['pD'],
        'VAR32': probs['p0x1'] / probs['pA'],
        'VAR33': probs['p0x1'] / probs['pOver'],
        'VAR34': probs['p0x1'] / probs['pUnder'],
        'VAR35': probs['p0x1'] / probs['pBTTS_Y'],
        'VAR36': probs['p0x1'] / probs['pBTTS_N'],
        'VAR37': probs['p1x0'] / probs['pH'],
        'VAR38': probs['p1x0'] / probs['pD'],
        'VAR39': probs['p1x0'] / probs['pA'],
        'VAR40': probs['p1x0'] / probs['pOver'],
        'VAR41': probs['p1x0'] / probs['pUnder'],
        'VAR42': probs['p1x0'] / probs['pBTTS_Y'],
        'VAR43': probs['p1x0'] / probs['pBTTS_N'],
        'VAR44': probs['p0x0'] / probs['p0x1'],
        'VAR45': probs['p0x0'] / probs['p1x0'],
        'VAR46': probs['p0x1'] / probs['p0x0'],
        'VAR47': probs['p0x1'] / probs['p1x0'],
        'VAR48': probs['p1x0'] / probs['p0x0'],
        'VAR49': probs['p1x0'] / probs['p0x1'],
        'VAR50': (probs['pH'].to_frame().join(probs['pD'].to_frame()).join(probs['pA'].to_frame())).std(axis=1) /
                 (probs['pH'].to_frame().join(probs['pD'].to_frame()).join(probs['pA'].to_frame())).mean(axis=1),
        'VAR51': (probs['pOver'].to_frame().join(probs['pUnder'].to_frame())).std(axis=1) /
                 (probs['pOver'].to_frame().join(probs['pUnder'].to_frame())).mean(axis=1),
        'VAR52': (probs['pBTTS_Y'].to_frame().join(probs['pBTTS_N'].to_frame())).std(axis=1) /
                 (probs['pBTTS_Y'].to_frame().join(probs['pBTTS_N'].to_frame())).mean(axis=1),
        'VAR53': (probs['p0x0'].to_frame().join(probs['p0x1'].to_frame()).join(probs['p1x0'].to_frame())).std(axis=1) /
                 (probs['p0x0'].to_frame().join(probs['p0x1'].to_frame()).join(probs['p1x0'].to_frame())).mean(axis=1),
        'VAR54': abs(probs['pH'] - probs['pA']),
        'VAR55': abs(probs['pH'] - probs['pD']),
        'VAR56': abs(probs['pD'] - probs['pA']),
        'VAR57': abs(probs['pOver'] - probs['pUnder']),
        'VAR58': abs(probs['pBTTS_Y'] - probs['pBTTS_N']),
        'VAR59': abs(probs['p0x0'] - probs['p0x1']),
        'VAR60': abs(probs['p0x0'] - probs['p1x0']),
        'VAR61': abs(probs['p0x1'] - probs['p1x0']),
        'VAR62': np.arctan((probs['pA'] - probs['pH']) / 2) * 180 / np.pi,
        'VAR63': np.arctan((probs['pD'] - probs['pH']) / 2) * 180 / np.pi,
        'VAR64': np.arctan((probs['pA'] - probs['pD']) / 2) * 180 / np.pi,
        'VAR65': np.arctan((probs['pUnder'] - probs['pOver']) / 2) * 180 / np.pi,
        'VAR66': np.arctan((probs['pBTTS_N'] - probs['pBTTS_Y']) / 2) * 180 / np.pi,
        'VAR67': np.arctan((probs['p0x1'] - probs['p0x0']) / 2) * 180 / np.pi,
        'VAR68': np.arctan((probs['p1x0'] - probs['p0x0']) / 2) * 180 / np.pi,
        'VAR69': np.arctan((probs['p1x0'] - probs['p0x1']) / 2) * 180 / np.pi,
        'VAR70': abs(probs['pH'] - probs['pA']) / probs['pA'],
        'VAR71': abs(probs['pH'] - probs['pD']) / probs['pD'],
        'VAR72': abs(probs['pD'] - probs['pA']) / probs['pA'],
        'VAR73': abs(probs['pOver'] - probs['pUnder']) / probs['pUnder'],
        'VAR74': abs(probs['pBTTS_Y'] - probs['pBTTS_N']) / probs['pBTTS_N'],
        'VAR75': abs(probs['p0x0'] - probs['p0x1']) / probs['p0x1'],
        'VAR76': abs(probs['p0x0'] - probs['p1x0']) / probs['p1x0'],
        'VAR77': abs(probs['p0x1'] - probs['p1x0']) / probs['p1x0']
    }
    return vars_dict

# Definição das estratégias
# Modificado para aceitar df e vars_dict como argumentos
def define_strategies():
    """Retorna uma lista de tuplas (função_estrategia, nome_estrategia)."""
    #def estrategia_1(df, vars_dict): return df[(vars_dict['VAR24'] >= 0.274) & (vars_dict['VAR24'] <= 0.33) & (vars_dict['VAR39'] >= 0.84) & (vars_dict['VAR39'] <= 4.0)].copy()
    #def estrategia_2(df, vars_dict): return df[(vars_dict['VAR25'] >= 0.44) & (vars_dict['VAR25'] <= 0.60) & (vars_dict['VAR39'] >= 0.84) & (vars_dict['VAR39'] <= 4.0)].copy()
    def estrategia_3(df, vars_dict): return df[((vars_dict['VAR41'] >= 0.2335) & (vars_dict['VAR41'] <= 0.3310) | (vars_dict['VAR75'] >= 0.4838) & (vars_dict['VAR75'] <= 0.7777)) 
                                               & ((vars_dict['VAR68'] >= 1.891) & (vars_dict['VAR68'] <= 2.406) | (vars_dict['VAR14'] >= 0.954) & (vars_dict['VAR14'] <= 1.03) | (vars_dict['VAR60'] >= 0.0664) & (vars_dict['VAR60'] <= 0.084) | (vars_dict['VAR06'] >= 0.403) & (vars_dict['VAR06'] <= 0.53))].copy()
    def estrategia_4(df, vars_dict):
     return df[((vars_dict['VAR29'] >= 0.09) & (vars_dict['VAR29'] <= 0.10)) &
              ((vars_dict['VAR30'] >= 0.4333) & (vars_dict['VAR30'] <= 0.8636) |
               (vars_dict['VAR05'] >= 2.8571) & (vars_dict['VAR05'] <= 5.5944) |
               (vars_dict['VAR62'] >= 10.4432) & (vars_dict['VAR62'] <= 16.0214) |
               (vars_dict['VAR69'] >= -2.3481) & (vars_dict['VAR69'] <= -1.0145) |
               (vars_dict['VAR19'] >= 0.9826) & (vars_dict['VAR19'] <= 1.3819))].copy()
    
    def estrategia_5(df, vars_dict):
     return df[((vars_dict['VAR24'] >= 0.274) & (vars_dict['VAR24'] <= 0.33) | (vars_dict['VAR25'] >= 0.44) & (vars_dict['VAR25'] <= 0.60)) &
              ((vars_dict['VAR39'] >= 0.84) & (vars_dict['VAR39'] <= 4.0))].copy()
                                               


    return [
        #(estrategia_1, "Lay0x0_1(95%)"), (estrategia_2, "Lay0x0_2(95%)"),
        (estrategia_3, "Lay 0x0_(98%)"),(estrategia_4, "Lay 1x1(96%)"), (estrategia_5, "Over 0.5_(95%)")
        
   ]

# --- Interface Streamlit ---
st.title("Análise de Jogos do Dia por Estratégia")

st.header("Upload da Planilha dos Jogos do Dia")
uploaded_daily = st.file_uploader(
    "Faça upload da planilha com os jogos do dia (.xlsx ou .csv)",
    type=["xlsx", "csv"],
    key="daily_analyzer"
)

if uploaded_daily is not None:
    df_daily_original = load_dataframe(uploaded_daily)

    if df_daily_original is not None:
        # Filtro de Ligas (Jogos do Dia)
        df_daily = df_daily_original.copy() # Começa com todos os jogos
        if 'League' in df_daily_original.columns:
            # Garante que a coluna League seja string para comparação
            df_daily_original['League'] = df_daily_original['League'].astype(str).str.upper().str.strip()
            # Filtra pelas ligas aprovadas
            df_daily = df_daily_original[df_daily_original['League'].isin(APPROVED_LEAGUES)].copy()
            if df_daily.empty and not df_daily_original.empty:
                 st.warning("Nenhum jogo na planilha pertence às ligas aprovadas listadas.")
            elif not df_daily.empty:
                 st.success(f"{len(df_daily)} jogos encontrados nas ligas aprovadas.")
        else:
            st.warning("Coluna 'League' não encontrada no arquivo. Não foi possível filtrar por ligas aprovadas. Analisando todos os jogos.")
            # df_daily já é a cópia original neste caso

        if not df_daily.empty:
            # Define as estratégias
            estrategias = define_strategies()
            jogos_aprovados_por_estrategia = {}
            algum_jogo_aprovado = False

            st.header("Resultados da Análise")

            # Itera sobre cada estratégia definida
            for estrategia_func, estrategia_nome in estrategias:
                # Roda a análise para a estratégia atual nos jogos do dia filtrados
                # A função analyze_daily_games agora lida com o cálculo de VARs internamente
                jogos_aprovados = analyze_daily_games(df_daily.copy(), estrategia_func) # Passa a função diretamente

                # Verifica se a análise retornou algum jogo
                if jogos_aprovados is not None and not jogos_aprovados.empty:
                    st.subheader(f"✅ {estrategia_nome}")
                    st.dataframe(jogos_aprovados)
                    jogos_aprovados_por_estrategia[estrategia_nome] = jogos_aprovados
                    algum_jogo_aprovado = True
                # else:
                    # Opcional: Informar que a estratégia não teve jogos aprovados
                    # st.write(f"ℹ️ Nenhum jogo encontrado para: {estrategia_nome}")


            # Mensagem final se nenhum jogo foi aprovado em nenhuma estratégia
            if not algum_jogo_aprovado:
                st.info("Nenhum jogo na planilha (e nas ligas aprovadas, se aplicável) atendeu aos critérios de nenhuma das estratégias definidas.")

        else: # Se df_daily ficou vazio após filtro de ligas ou já era vazio
            if 'League' in df_daily_original.columns: # Só mostra essa msg se tentou filtrar
                 st.info("Não há jogos das ligas aprovadas na planilha para analisar.")
            # Se a coluna League não existia, a mensagem de warning já foi dada.

    # else: # df_daily_original is None (erro na leitura)
    #    A função load_dataframe já exibiu a mensagem de erro.
    #    pass

# else: # Nenhum arquivo carregado ainda
#    st.info("Aguardando o upload da planilha dos jogos do dia.")