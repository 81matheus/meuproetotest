import streamlit as st
import pandas as pd
import numpy as np
import io # Necessário para ler o buffer do arquivo carregado e da web
import re # Para extrair partes dos nomes das estratégias combinadas
import requests # Para buscar dados do GitHub

# --- Função para Carregar Dados do GITHUB ---
@st.cache_data(ttl=3600) # Cacheia os dados por 1 hora para evitar downloads repetidos
def load_data_from_github(url):
    """Busca e carrega um DataFrame de um arquivo Excel em uma URL raw do GitHub."""
    try:
        response = requests.get(url)
        response.raise_for_status() # Verifica se houve erro no request (4xx ou 5xx)

        # Usa io.BytesIO para ler o conteúdo binário da resposta no pandas
        df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        st.success("Base de dados histórica carregada com sucesso do GitHub!")
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar o arquivo do GitHub: {e}")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel do GitHub: {e}. Verifique a URL e o formato.")
        return None

# --- Função Auxiliar para Carregar Dados (Mantida para Upload Local) ---
def load_dataframe_local(uploaded_file):
    """Carrega um DataFrame de um arquivo XLSX ou CSV carregado via Streamlit."""
    if uploaded_file is None:
        return None
    try:
        file_content = uploaded_file.getvalue() # Ler o conteúdo uma vez
        # Verifica a extensão do nome do arquivo
        if uploaded_file.name.lower().endswith('.xlsx'):
            try:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            except Exception as e_xlsx:
                 st.error(f"Erro ao ler .xlsx: {e_xlsx}. Tente salvar como CSV ou 'Excel 97-2003 Workbook (*.xls)' se possível.")
                 return None
            return df
        elif uploaded_file.name.lower().endswith('.csv'):
            # Tenta detectar separador comum (vírgula ou ponto e vírgula)
            try:
                df = pd.read_csv(io.BytesIO(file_content), sep=',')
                if df.shape[1] <= 1: # Se só tem 1 coluna, tenta ;
                    df = pd.read_csv(io.BytesIO(file_content), sep=';')
            except Exception as e_csv:
                 st.warning(f"Não foi possível determinar o separador CSV automaticamente, tentando ';'. Erro: {e_csv}")
                 try:
                     df = pd.read_csv(io.BytesIO(file_content), sep=';')
                 except Exception as e_final:
                     st.error(f"Falha ao ler o arquivo CSV com separador ',' ou ';'. Verifique o formato. Erro: {e_final}")
                     return None

            if df.empty or df.shape[1] <= 1:
                 st.error("Falha ao ler o arquivo CSV corretamente. Verifique o separador (',' ou ';') e o formato.")
                 return None
            return df
        else:
            st.error("Formato de arquivo não suportado. Use .xlsx ou .csv")
            return None
    except Exception as e:
        st.error(f"Erro geral ao ler o arquivo '{uploaded_file.name}': {e}")
        return None
# --- Fim da Função Auxiliar ---

# --- INÍCIO: Definição das Ligas Aprovadas ---
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

# --- INÍCIO: Definição das Estratégias Correct Score Lay a Testar ---
cs_lay_strategies_to_test = [
    'Lay_0x0', 'Lay_0x1', 'Lay_1x0', 'Lay_1x1',
    'Lay_0x2', 'Lay_2x0', 'Lay_1x2', 'Lay_2x1', 'Lay_2x2',
    'Lay_0x3', 'Lay_3x0', 'Lay_1x3', 'Lay_3x1', 'Lay_2x3', 'Lay_3x2', 'Lay_3x3',
    'Lay_Goleada_H', 'Lay_Goleada_A'
]
# --- FIM: Definição das Estratégias Correct Score Lay a Testar ---

# --- Função para obter a condição de ocorrência do placar ---
# (Mantida como antes)
def get_score_condition(df, cs_lay_name):
    """Retorna a condição booleana do pandas para o placar da estratégia CS Lay ocorrer."""
    ocorrencias = pd.Series(False, index=df.index) # Default False
    try:
        if cs_lay_name == 'Lay_0x0':
            ocorrencias = (df['Goals_H'] == 0) & (df['Goals_A'] == 0)
        elif cs_lay_name == 'Lay_0x1':
            ocorrencias = (df['Goals_H'] == 0) & (df['Goals_A'] == 1)
        elif cs_lay_name == 'Lay_1x0':
            ocorrencias = (df['Goals_H'] == 1) & (df['Goals_A'] == 0)
        elif cs_lay_name == 'Lay_1x1':
            ocorrencias = (df['Goals_H'] == 1) & (df['Goals_A'] == 1)
        elif cs_lay_name == 'Lay_0x2':
            ocorrencias = (df['Goals_H'] == 0) & (df['Goals_A'] == 2)
        elif cs_lay_name == 'Lay_2x0':
            ocorrencias = (df['Goals_H'] == 2) & (df['Goals_A'] == 0)
        elif cs_lay_name == 'Lay_1x2':
            ocorrencias = (df['Goals_H'] == 1) & (df['Goals_A'] == 2)
        elif cs_lay_name == 'Lay_2x1':
            ocorrencias = (df['Goals_H'] == 2) & (df['Goals_A'] == 1)
        elif cs_lay_name == 'Lay_2x2':
            ocorrencias = (df['Goals_H'] == 2) & (df['Goals_A'] == 2)
        elif cs_lay_name == 'Lay_0x3':
            ocorrencias = (df['Goals_H'] == 0) & (df['Goals_A'] == 3)
        elif cs_lay_name == 'Lay_3x0':
            ocorrencias = (df['Goals_H'] == 3) & (df['Goals_A'] == 0)
        elif cs_lay_name == 'Lay_1x3':
            ocorrencias = (df['Goals_H'] == 1) & (df['Goals_A'] == 3)
        elif cs_lay_name == 'Lay_3x1':
            ocorrencias = (df['Goals_H'] == 3) & (df['Goals_A'] == 1)
        elif cs_lay_name == 'Lay_2x3':
            ocorrencias = (df['Goals_H'] == 2) & (df['Goals_A'] == 3)
        elif cs_lay_name == 'Lay_3x2':
            ocorrencias = (df['Goals_H'] == 3) & (df['Goals_A'] == 2)
        elif cs_lay_name == 'Lay_3x3':
            ocorrencias = (df['Goals_H'] == 3) & (df['Goals_A'] == 3)
        elif cs_lay_name == 'Lay_Goleada_H':
            ocorrencias = (df['Goals_H'] > df['Goals_A']) & ((df['Goals_H'] > 3) | (df['Goals_A'] > 3))
        elif cs_lay_name == 'Lay_Goleada_A':
            ocorrencias = (df['Goals_A'] > df['Goals_H']) & ((df['Goals_H'] > 3) | (df['Goals_A'] > 3))
        else:
            st.warning(f"Nome de estratégia CS Lay desconhecido: {cs_lay_name}")
            # Retorna False para todos se desconhecido
            ocorrencias = pd.Series(False, index=df.index)

    except KeyError as e:
        # Se faltar Goals_H ou Goals_A, não podemos calcular
        st.error(f"Erro em get_score_condition para {cs_lay_name}: Coluna '{e}' ausente.")
        return pd.Series(False, index=df.index) # Retorna False para todos

    # Garantir que o retorno seja sempre uma série booleana do mesmo tamanho que df
    if not isinstance(ocorrencias, pd.Series):
         ocorrencias = pd.Series(ocorrencias, index=df.index) # Converte se for um array numpy bool
    if ocorrencias.dtype != bool:
         ocorrencias = ocorrencias.fillna(False).astype(bool) # Trata NaNs e converte

    return ocorrencias

# --- Função de Backtest para COMBINAÇÃO (Filtro VAR + CS Lay) ---
# (Mantida como antes)
def run_combined_backtest(df_filtered_by_var, cs_lay_name, combined_strategy_name, profit_win=0.10, profit_loss=-1.0):
    """Executa o backtest para uma estratégia Lay CS em um DataFrame JÁ FILTRADO por uma estratégia VAR."""
    df_copy = df_filtered_by_var.copy()
    total_jogos = len(df_copy)

    if total_jogos == 0:
        return {
            "Estratégia": combined_strategy_name, "Total de Jogos": 0,
            "Taxa de Acerto": "N/A", "Lucro Total": "0.00", "Dataframe": pd.DataFrame()
        }
    try:
        score_occurred = get_score_condition(df_copy, cs_lay_name)
        if score_occurred is None: # Erro dentro de get_score_condition
             raise ValueError("Falha ao obter condição de placar.")

        df_copy['Profit'] = np.where(score_occurred, profit_loss, profit_win)
        acertos = (~score_occurred).sum()
        taxa_acerto = acertos / total_jogos
        lucro_total = df_copy['Profit'].sum()

        return {
            "Estratégia": combined_strategy_name, "Total de Jogos": total_jogos,
            "Taxa de Acerto": f"{taxa_acerto:.2%}", "Lucro Total": f"{lucro_total:.2f}",
            "Dataframe": df_copy
        }

    except KeyError as e:
         st.error(f"Erro (KeyError) no backtest de {combined_strategy_name}: Coluna '{e}' ausente no subset filtrado.")
         return { "Estratégia": combined_strategy_name, "Total de Jogos": 0, "Taxa de Acerto": "Erro", "Lucro Total": "0.00", "Dataframe": pd.DataFrame()}
    except Exception as e:
         st.error(f"Erro inesperado no backtest de {combined_strategy_name}: {e}")
         return { "Estratégia": combined_strategy_name, "Total de Jogos": 0, "Taxa de Acerto": "Erro", "Lucro Total": "0.00", "Dataframe": pd.DataFrame()}


# --- Função de Análise de Médias Móveis para COMBINAÇÃO ---
# (Mantida como antes)
def check_combined_moving_averages(df_backtest_result, combined_strategy_name):
    """Analisa as médias móveis e lucros recentes para uma COMBINAÇÃO (Filtro VAR + CS Lay)."""

    if df_backtest_result is None or df_backtest_result.empty:
        return {
            "Estratégia": combined_strategy_name, "Média 8": "0.00% (0 acertos em 0)",
            "Média 40": "0.00% (0 acertos em 0)", "Lucro Últimos 8": "0.00 (em 0 jogos)",
            "Lucro Últimos 40": "0.00 (em 0 jogos)", "Acima dos Limiares": False
        }

    match = re.search(r'CS_(Lay_\w+)$', combined_strategy_name)
    if not match:
        st.error(f"Não foi possível extrair o nome CS Lay de: {combined_strategy_name}")
        return { "Estratégia": combined_strategy_name, "Média 8": "Erro", "Média 40": "Erro", "Lucro Últimos 8": "Erro", "Lucro Últimos 40": "Erro", "Acima dos Limiares": False }
    cs_lay_name = match.group(1)

    try:
        score_occurred = get_score_condition(df_backtest_result, cs_lay_name)
        if score_occurred is None: raise ValueError("Falha ao obter condição de placar.")
        df_backtest_result['Acerto'] = (~score_occurred).astype(int)

        if 'Profit' not in df_backtest_result.columns:
             st.error(f"Coluna 'Profit' não encontrada para {combined_strategy_name} ao calcular médias.")
             df_backtest_result['Profit'] = 0.0

        # AJUSTE: Usar os ultimos 8 e 40 jogos REAIS se houver menos que 80/170
        num_jogos = len(df_backtest_result)
        ultimos_8_n = min(num_jogos, 80)  # Pega até 80 jogos
        ultimos_40_n = min(num_jogos, 170) # Pega até 170 jogos

        ultimos_8 = df_backtest_result.tail(ultimos_8_n)
        ultimos_40 = df_backtest_result.tail(ultimos_40_n)

        media_8 = ultimos_8['Acerto'].mean() if not ultimos_8.empty else 0
        media_40 = ultimos_40['Acerto'].mean() if not ultimos_40.empty else 0
        lucro_8 = ultimos_8['Profit'].sum()
        lucro_40 = ultimos_40['Profit'].sum()

        # Critério de aprovação (AJUSTE CONFORME NECESSÁRIO)
        acima_limiares = media_8 > 0.95 and media_40 > 0.95

        return {
            "Estratégia": combined_strategy_name,
            "Média 8": f"{media_8:.2%} ({ultimos_8['Acerto'].sum()} acertos em {len(ultimos_8)})",
            "Média 40": f"{media_40:.2%} ({ultimos_40['Acerto'].sum()} acertos em {len(ultimos_40)})",
            "Lucro Últimos 8": f"{lucro_8:.2f} (em {len(ultimos_8)} jogos)",
            "Lucro Últimos 40": f"{lucro_40:.2f} (em {len(ultimos_40)} jogos)",
            "Acima dos Limiares": acima_limiares
        }

    except KeyError as e:
         st.error(f"Erro (KeyError) nas médias de {combined_strategy_name}: Coluna '{e}' ausente.")
         return { "Estratégia": combined_strategy_name, "Média 8": "Erro", "Média 40": "Erro", "Lucro Últimos 8": "Erro", "Lucro Últimos 40": "Erro", "Acima dos Limiares": False}
    except Exception as e:
         st.error(f"Erro inesperado nas médias de {combined_strategy_name}: {e}")
         return { "Estratégia": combined_strategy_name, "Média 8": "Erro", "Média 40": "Erro", "Lucro Últimos 8": "Erro", "Lucro Últimos 40": "Erro", "Acima dos Limiares": False}

# --- Pre-calcular variáveis ---
# (Função original fornecida pelo usuário, com validações adicionadas)
# (Mantida como antes)
def pre_calculate_all_vars(df):
    required_odds_cols = [
        'Odd_H_Back', 'Odd_D_Back', 'Odd_A_Back',
        'Odd_Over25_FT_Back', 'Odd_Under25_FT_Back',
        'Odd_BTTS_Yes_Back', 'Odd_BTTS_No_Back',
        'Odd_CS_0x0_Lay', 'Odd_CS_0x1_Lay', 'Odd_CS_1x0_Lay'
    ]
    missing_cols = [col for col in required_odds_cols if col not in df.columns]
    if missing_cols:
        st.error(f"As colunas de odds {', '.join(missing_cols)} são necessárias e não foram encontradas.")
        return None

    # Criar cópia para evitar modificar o original indiretamente
    df_copy = df.copy()

    # Verificar e tratar valores inválidos (NaN, Inf, <= 0) nas odds ANTES de calcular probs
    for col in required_odds_cols:
         # Verifica se a coluna é numérica antes de aplicar isnull/isinf/<=
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            invalid_mask = df_copy[col].isnull() | np.isinf(df_copy[col]) | (df_copy[col] <= 0)
            if invalid_mask.any():
                 #st.warning(f"Valores inválidos (NaN, Inf, <= 0) encontrados em '{col}'. Serão substituídos por um valor alto (1e12) para cálculo da probabilidade.")
                 # Substitui por um valor muito alto para gerar prob perto de 0
                 df_copy.loc[invalid_mask, col] = 1e12
        else:
            # Tenta converter para numérico, se falhar, a coluna é problemática
            try:
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                # Repete a checagem após conversão
                invalid_mask = df_copy[col].isnull() | np.isinf(df_copy[col]) | (df_copy[col] <= 0)
                if invalid_mask.any():
                    #st.warning(f"Valores inválidos (NaN, Inf, <= 0) encontrados em '{col}' após conversão. Serão substituídos por 1e12.")
                    df_copy.loc[invalid_mask, col] = 1e12
            except Exception as e_conv:
                 st.error(f"Não foi possível converter a coluna de odds '{col}' para numérica: {e_conv}. Cálculo das VARs pode falhar.")
                 return None # Não pode continuar se a coluna não for numérica

    probs = {}
    # Simplificando nomes das probabilidades (ex: pH, pD, pA, pOver, pUnder, pBTTS_Y, pBTTS_N, pCS_0x0, pCS_0x1, pCS_1x0)
    prob_name_map = {
        'Odd_H_Back': 'pH', 'Odd_D_Back': 'pD', 'Odd_A_Back': 'pA',
        'Odd_Over25_FT_Back': 'pOver', 'Odd_Under25_FT_Back': 'pUnder',
        'Odd_BTTS_Yes_Back': 'pBTTS_Y', 'Odd_BTTS_No_Back': 'pBTTS_N',
        'Odd_CS_0x0_Lay': 'pCS_0x0', 'Odd_CS_0x1_Lay': 'pCS_0x1', 'Odd_CS_1x0_Lay': 'pCS_1x0'
    }
    for col, prob_name in prob_name_map.items():
        if col in df_copy.columns: # Verifica se a coluna realmente existe
             # Garante divisão segura mesmo com 1e12
             probs[prob_name] = 1 / df_copy[col].replace(0, 1e-12) # Evita divisão por zero literal
        else: # Deve ter sido pego na validação inicial, mas por segurança
            st.error(f"Coluna {col} inesperadamente ausente durante cálculo de probabilidade.")
            return None

    try:
        # Usar um dicionário temporário para construir as VARs
        temp_vars = {}

        # --- Cálculos das VARs (usando os nomes simplificados das probs) ---
        temp_vars['VAR01'] = probs['pH'] / probs['pD']
        temp_vars['VAR02'] = probs['pH'] / probs['pA']
        temp_vars['VAR03'] = probs['pD'] / probs['pH']
        temp_vars['VAR04'] = probs['pD'] / probs['pA']
        temp_vars['VAR05'] = probs['pA'] / probs['pH']
        temp_vars['VAR06'] = probs['pA'] / probs['pD']
        temp_vars['VAR07'] = probs['pOver'] / probs['pUnder']
        temp_vars['VAR08'] = probs['pUnder'] / probs['pOver']
        temp_vars['VAR09'] = probs['pBTTS_Y'] / probs['pBTTS_N']
        temp_vars['VAR10'] = probs['pBTTS_N'] / probs['pBTTS_Y']
        temp_vars['VAR11'] = probs['pH'] / probs['pOver']
        temp_vars['VAR12'] = probs['pD'] / probs['pOver']
        temp_vars['VAR13'] = probs['pA'] / probs['pOver']
        temp_vars['VAR14'] = probs['pH'] / probs['pUnder']
        temp_vars['VAR15'] = probs['pD'] / probs['pUnder']
        temp_vars['VAR16'] = probs['pA'] / probs['pUnder']
        temp_vars['VAR17'] = probs['pH'] / probs['pBTTS_Y']
        temp_vars['VAR18'] = probs['pD'] / probs['pBTTS_Y']
        temp_vars['VAR19'] = probs['pA'] / probs['pBTTS_Y']
        temp_vars['VAR20'] = probs['pH'] / probs['pBTTS_N']
        temp_vars['VAR21'] = probs['pD'] / probs['pBTTS_N']
        temp_vars['VAR22'] = probs['pA'] / probs['pBTTS_N']
        temp_vars['VAR23'] = probs['pCS_0x0'] / probs['pH']
        temp_vars['VAR24'] = probs['pCS_0x0'] / probs['pD']
        temp_vars['VAR25'] = probs['pCS_0x0'] / probs['pA']
        temp_vars['VAR26'] = probs['pCS_0x0'] / probs['pOver']
        temp_vars['VAR27'] = probs['pCS_0x0'] / probs['pUnder']
        temp_vars['VAR28'] = probs['pCS_0x0'] / probs['pBTTS_Y']
        temp_vars['VAR29'] = probs['pCS_0x0'] / probs['pBTTS_N']
        temp_vars['VAR30'] = probs['pCS_0x1'] / probs['pH']
        temp_vars['VAR31'] = probs['pCS_0x1'] / probs['pD']
        temp_vars['VAR32'] = probs['pCS_0x1'] / probs['pA']
        temp_vars['VAR33'] = probs['pCS_0x1'] / probs['pOver']
        temp_vars['VAR34'] = probs['pCS_0x1'] / probs['pUnder']
        temp_vars['VAR35'] = probs['pCS_0x1'] / probs['pBTTS_Y']
        temp_vars['VAR36'] = probs['pCS_0x1'] / probs['pBTTS_N']
        temp_vars['VAR37'] = probs['pCS_1x0'] / probs['pH']
        temp_vars['VAR38'] = probs['pCS_1x0'] / probs['pD']
        temp_vars['VAR39'] = probs['pCS_1x0'] / probs['pA']
        temp_vars['VAR40'] = probs['pCS_1x0'] / probs['pOver']
        temp_vars['VAR41'] = probs['pCS_1x0'] / probs['pUnder']
        temp_vars['VAR42'] = probs['pCS_1x0'] / probs['pBTTS_Y']
        temp_vars['VAR43'] = probs['pCS_1x0'] / probs['pBTTS_N']
        temp_vars['VAR44'] = probs['pCS_0x0'] / probs['pCS_0x1']
        temp_vars['VAR45'] = probs['pCS_0x0'] / probs['pCS_1x0']
        temp_vars['VAR46'] = probs['pCS_0x1'] / probs['pCS_0x0']
        temp_vars['VAR47'] = probs['pCS_0x1'] / probs['pCS_1x0']
        temp_vars['VAR48'] = probs['pCS_1x0'] / probs['pCS_0x0']
        temp_vars['VAR49'] = probs['pCS_1x0'] / probs['pCS_0x1']
        # Cálculos com std/mean (usando concat para criar DFs temporários)
        df_HDA = pd.concat([probs['pH'], probs['pD'], probs['pA']], axis=1)
        temp_vars['VAR50'] = df_HDA.std(axis=1, skipna=True) / df_HDA.mean(axis=1, skipna=True).replace(0, 1e-12)
        df_OU = pd.concat([probs['pOver'], probs['pUnder']], axis=1)
        temp_vars['VAR51'] = df_OU.std(axis=1, skipna=True) / df_OU.mean(axis=1, skipna=True).replace(0, 1e-12)
        df_BTTS = pd.concat([probs['pBTTS_Y'], probs['pBTTS_N']], axis=1)
        temp_vars['VAR52'] = df_BTTS.std(axis=1, skipna=True) / df_BTTS.mean(axis=1, skipna=True).replace(0, 1e-12)
        df_CS = pd.concat([probs['pCS_0x0'], probs['pCS_0x1'], probs['pCS_1x0']], axis=1)
        temp_vars['VAR53'] = df_CS.std(axis=1, skipna=True) / df_CS.mean(axis=1, skipna=True).replace(0, 1e-12)
        # Cálculos com abs
        temp_vars['VAR54'] = abs(probs['pH'] - probs['pA'])
        temp_vars['VAR55'] = abs(probs['pH'] - probs['pD'])
        temp_vars['VAR56'] = abs(probs['pD'] - probs['pA'])
        temp_vars['VAR57'] = abs(probs['pOver'] - probs['pUnder'])
        temp_vars['VAR58'] = abs(probs['pBTTS_Y'] - probs['pBTTS_N'])
        temp_vars['VAR59'] = abs(probs['pCS_0x0'] - probs['pCS_0x1'])
        temp_vars['VAR60'] = abs(probs['pCS_0x0'] - probs['pCS_1x0'])
        temp_vars['VAR61'] = abs(probs['pCS_0x1'] - probs['pCS_1x0'])
        # Cálculos com arctan
        temp_vars['VAR62'] = np.arctan((probs['pA'] - probs['pH']) / 2) * 180 / np.pi
        temp_vars['VAR63'] = np.arctan((probs['pD'] - probs['pH']) / 2) * 180 / np.pi
        temp_vars['VAR64'] = np.arctan((probs['pA'] - probs['pD']) / 2) * 180 / np.pi
        temp_vars['VAR65'] = np.arctan((probs['pUnder'] - probs['pOver']) / 2) * 180 / np.pi
        temp_vars['VAR66'] = np.arctan((probs['pBTTS_N'] - probs['pBTTS_Y']) / 2) * 180 / np.pi
        temp_vars['VAR67'] = np.arctan((probs['pCS_0x1'] - probs['pCS_0x0']) / 2) * 180 / np.pi
        temp_vars['VAR68'] = np.arctan((probs['pCS_1x0'] - probs['pCS_0x0']) / 2) * 180 / np.pi
        temp_vars['VAR69'] = np.arctan((probs['pCS_1x0'] - probs['pCS_0x1']) / 2) * 180 / np.pi
        # Cálculos com divisão normalizada
        temp_vars['VAR70'] = abs(probs['pH'] - probs['pA']) / probs['pA'].replace(0, 1e-12)
        temp_vars['VAR71'] = abs(probs['pH'] - probs['pD']) / probs['pD'].replace(0, 1e-12)
        temp_vars['VAR72'] = abs(probs['pD'] - probs['pA']) / probs['pA'].replace(0, 1e-12)
        temp_vars['VAR73'] = abs(probs['pOver'] - probs['pUnder']) / probs['pUnder'].replace(0, 1e-12)
        temp_vars['VAR74'] = abs(probs['pBTTS_Y'] - probs['pBTTS_N']) / probs['pBTTS_N'].replace(0, 1e-12)
        temp_vars['VAR75'] = abs(probs['pCS_0x0'] - probs['pCS_0x1']) / probs['pCS_0x1'].replace(0, 1e-12)
        temp_vars['VAR76'] = abs(probs['pCS_0x0'] - probs['pCS_1x0']) / probs['pCS_1x0'].replace(0, 1e-12)
        temp_vars['VAR77'] = abs(probs['pCS_0x1'] - probs['pCS_1x0']) / probs['pCS_1x0'].replace(0, 1e-12)
        # --- Fim dos Cálculos ---

        # Tratar possíveis NaNs ou Infinitos resultantes das divisões/cálculos
        vars_dict = {}
        for key, series in temp_vars.items():
            # Substitui Inf por NaN e depois NaN por 0 (ou outra estratégia, se preferir)
            # É importante fazer isso pois as funções de estratégia não lidam bem com NaN/Inf
            vars_dict[key] = series.replace([np.inf, -np.inf], np.nan).fillna(0)

        return vars_dict
    except ZeroDivisionError as zde:
        st.error(f"Erro de divisão por zero durante o cálculo das VARs. Verifique se há odds inválidas ou zero no seu arquivo. Detalhe: {zde}")
        return None
    except KeyError as ke:
         st.error(f"Erro de chave durante cálculo das VARs: Probabilidade '{ke}' não encontrada. Verifique mapeamento 'prob_name_map'.")
         return None
    except Exception as e:
        st.error(f"Erro inesperado durante o cálculo das VARs: {e}")
        return None
# --- Fim Pre-calcular variáveis ---

# --- Definição das estratégias VAR ---
# (Função original mantida, apenas recebe vars_dict)
def define_var_strategies(vars_dict):
    """Define as funções de filtro VAR com base no dicionário de VARs pré-calculadas."""
    if vars_dict is None:
        return [], {} # Retorna listas vazias se vars_dict for None

    # Define as funções lambda usando o vars_dict pré-calculado
    # (As 152 definições de estratégia como no original)
    # --- Cole aqui as 152 definições de estrategia_X ---
    # Exemplo das primeiras:
    def estrategia_1(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR30'] >= 0.0441) & (vars_dict['VAR30'] <= 0.0497)].copy()
    def estrategia_2(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR45'] >= 0.4375) & (vars_dict['VAR45'] <= 0.46)].copy()
    def estrategia_3(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR48'] >= 1.0) & (vars_dict['VAR48'] <= 2.0455)].copy()
    def estrategia_4(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR47'] >= 0.0063) & (vars_dict['VAR47'] <= 0.0146)].copy()
    def estrategia_5(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR49'] >= 68.2759) & (vars_dict['VAR49'] <= 158.0645)].copy()
    def estrategia_6(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR29'] >= 0.09) & (vars_dict['VAR29'] <= 0.1021)].copy()
    def estrategia_7(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR75'] >= 0.25) & (vars_dict['VAR75'] <= 0.36)].copy()
    def estrategia_8(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR76'] >= 0.5412) & (vars_dict['VAR76'] <= 0.5625)].copy()
    def estrategia_9(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR20'] >= 1.1485) & (vars_dict['VAR20'] <= 1.2481)].copy()
    def estrategia_10(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR77'] >= 0.9862) & (vars_dict['VAR77'] <= 32.7931)].copy()
    def estrategia_11(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR53'] >= 0.5022) & (vars_dict['VAR53'] <= 0.5313)].copy()
    def estrategia_12(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR33'] >= 0.0018) & (vars_dict['VAR33'] <= 0.0158)].copy()
    def estrategia_13(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR74'] >= 0.1298) & (vars_dict['VAR74'] <= 0.1667)].copy()
    def estrategia_14(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR58'] >= 0.0437) & (vars_dict['VAR58'] <= 0.0673)].copy()
    def estrategia_15(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR17'] >= 1.268) & (vars_dict['VAR17'] <= 1.3472)].copy()
    def estrategia_16(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR39'] >= 0.6261) & (vars_dict['VAR39'] <= 0.736)].copy()
    def estrategia_17(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR54'] >= 0.5556) & (vars_dict['VAR54'] <= 0.5766)].copy()
    def estrategia_18(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR63'] >= -13.9652) & (vars_dict['VAR63'] <= -13.4641)].copy()
    def estrategia_19(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR71'] >= 2.0951) & (vars_dict['VAR71'] <= 2.2903)].copy()
    def estrategia_20(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR01'] >= 3.0951) & (vars_dict['VAR01'] <= 3.2903)].copy()
    def estrategia_21(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR36'] >= 0.0611) & (vars_dict['VAR36'] <= 0.0672)].copy()
    def estrategia_22(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR09'] >= 1.1057) & (vars_dict['VAR09'] <= 1.2067)].copy()
    def estrategia_23(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR35'] >= 0.0023) & (vars_dict['VAR35'] <= 0.0216)].copy()
    def estrategia_24(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR19'] >= 0.2196) & (vars_dict['VAR19'] <= 0.2333)].copy()
    def estrategia_25(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR03'] >= 0.3039) & (vars_dict['VAR03'] <= 0.3231)].copy()
    def estrategia_26(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR10'] >= 0.8287) & (vars_dict['VAR10'] <= 0.9044)].copy()
    def estrategia_27(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR08'] >= 0.8238) & (vars_dict['VAR08'] <= 0.951)].copy()
    def estrategia_28(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR41'] >= 0.2294) & (vars_dict['VAR41'] <= 0.237)].copy()
    def estrategia_29(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR66'] >= -2.7619) & (vars_dict['VAR66'] <= -1.5147)].copy()
    def estrategia_30(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR44'] >= 1.2143) & (vars_dict['VAR44'] <= 1.3333)].copy()
    def estrategia_31(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR55'] >= 0.4788) & (vars_dict['VAR55'] <= 0.4974)].copy()
    def estrategia_32(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR12'] >= 0.3075) & (vars_dict['VAR12'] <= 0.3297)].copy()
    def estrategia_33(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR24'] >= 0.2562) & (vars_dict['VAR24'] <= 0.2899)].copy()
    def estrategia_34(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR43'] >= 0.2038) & (vars_dict['VAR43'] <= 0.2192)].copy()
    def estrategia_35(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR15'] >= 0.5083) & (vars_dict['VAR15'] <= 0.5545)].copy()
    def estrategia_36(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR62'] >= -16.0814) & (vars_dict['VAR62'] <= -15.5241)].copy()
    def estrategia_37(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR21'] >= 0.3888) & (vars_dict['VAR21'] <= 0.4111)].copy()
    def estrategia_38(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR34'] >= 0.0737) & (vars_dict['VAR34'] <= 0.0793)].copy()
    def estrategia_39(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR65'] >= -3.0083) & (vars_dict['VAR65'] <= -0.8472)].copy()
    def estrategia_40(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR38'] >= 0.469) & (vars_dict['VAR38'] <= 0.5035)].copy()
    def estrategia_41(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR25'] >= 0.4211) & (vars_dict['VAR25'] <= 0.5)].copy()
    def estrategia_42(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR26'] >= 0.0589) & (vars_dict['VAR26'] <= 0.0688)].copy()
    def estrategia_43(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR31'] >= 0.001) & (vars_dict['VAR31'] <= 0.0052)].copy()
    def estrategia_44(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR67'] >= -2.6977) & (vars_dict['VAR67'] <= -0.8662)].copy()
    def estrategia_45(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR11'] >= 1.056) & (vars_dict['VAR11'] <= 1.1024)].copy()
    def estrategia_46(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR07'] >= 1.0515) & (vars_dict['VAR07'] <= 1.2139)].copy()
    def estrategia_47(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR23'] >= 0.067) & (vars_dict['VAR23'] <= 0.0803)].copy()
    def estrategia_48(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR46'] >= 0.5818) & (vars_dict['VAR46'] <= 0.6364)].copy()
    def estrategia_49(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR22'] >= 0.2732) & (vars_dict['VAR22'] <= 0.3174)].copy()
    def estrategia_50(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR27'] >= 0.1017) & (vars_dict['VAR27'] <= 0.1091)].copy()
    def estrategia_51(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR64'] >= -2.3859) & (vars_dict['VAR64'] <= -2.1693)].copy()
    def estrategia_52(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR05'] >= 0.1468) & (vars_dict['VAR05'] <= 0.1614)].copy()
    def estrategia_53(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR02'] >= 6.1972) & (vars_dict['VAR02'] <= 6.8116)].copy()
    def estrategia_54(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR70'] >= 5.1972) & (vars_dict['VAR70'] <= 5.8116)].copy()
    def estrategia_55(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR32'] >= 0.25) & (vars_dict['VAR32'] <= 0.2759)].copy()
    def estrategia_56(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR16'] >= 0.2021) & (vars_dict['VAR16'] <= 0.2269)].copy()
    def estrategia_57(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR56'] >= 0.0758) & (vars_dict['VAR56'] <= 0.0833)].copy()
    def estrategia_58(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR42'] >= 0.1259) & (vars_dict['VAR42'] <= 0.1446)].copy()
    def estrategia_59(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR06'] >= 0.5408) & (vars_dict['VAR06'] <= 0.5745)].copy()
    def estrategia_60(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR28'] >= 0.0607) & (vars_dict['VAR28'] <= 0.0704)].copy()
    def estrategia_61(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR04'] >= 1.7407) & (vars_dict['VAR04'] <= 1.8491)].copy()
    def estrategia_62(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR72'] >= 0.7407) & (vars_dict['VAR72'] <= 0.8491)].copy()
    def estrategia_63(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR52'] >= 0.0424) & (vars_dict['VAR52'] <= 0.0653)].copy()
    def estrategia_64(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR59'] >= 0.0305) & (vars_dict['VAR59'] <= 0.0942)].copy()
    def estrategia_65(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR73'] >= 0.1202) & (vars_dict['VAR73'] <= 0.2222)].copy()
    def estrategia_66(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR68'] >= 1.2685) & (vars_dict['VAR68'] <= 1.389)].copy()
    def estrategia_67(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR37'] >= 0.0925) & (vars_dict['VAR37'] <= 0.105)].copy()
    def estrategia_68(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR57'] >= 0.0) & (vars_dict['VAR57'] <= 0.061)].copy()
    def estrategia_69(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR51'] >= 0.0) & (vars_dict['VAR51'] <= 0.0579)].copy()
    def estrategia_70(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR40'] >= 0.1325) & (vars_dict['VAR40'] <= 0.1473)].copy()
    def estrategia_71(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR18'] >= 0.3571) & (vars_dict['VAR18'] <= 0.3809)].copy()
    def estrategia_72(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR60'] >= 0.0565) & (vars_dict['VAR60'] <= 0.0613)].copy()
    def estrategia_73(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR69'] >= 2.9523) & (vars_dict['VAR69'] <= 4.5816)].copy()
    def estrategia_74(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR61'] >= 0.1031) & (vars_dict['VAR61'] <= 0.1603)].copy()
    def estrategia_75(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR14'] >= 1.3671) & (vars_dict['VAR14'] <= 1.5102)].copy()
    def estrategia_76(df): return df[(vars_dict['VAR13'] >= 0.023) & (vars_dict['VAR13'] <= 0.25) & (vars_dict['VAR50'] >= 0.8531) & (vars_dict['VAR50'] <= 0.9052)].copy()
    def estrategia_77(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR01'] >= 1.07) & (vars_dict['VAR01'] <= 1.6667)].copy()
    def estrategia_78(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR03'] >= 0.6) & (vars_dict['VAR03'] <= 0.9345)].copy()
    def estrategia_79(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR77'] >= 0.0) & (vars_dict['VAR77'] <= 0.4783)].copy()
    def estrategia_80(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR18'] >= 0.3675) & (vars_dict['VAR18'] <= 0.3902)].copy()
    def estrategia_81(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR63'] >= -4.8232) & (vars_dict['VAR63'] <= -0.5167)].copy()
    def estrategia_82(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR54'] >= 0.0057) & (vars_dict['VAR54'] <= 0.2316)].copy()
    def estrategia_83(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR62'] >= -3.898) & (vars_dict['VAR62'] <= 6.6068)].copy()
    def estrategia_84(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR02'] >= 0.5405) & (vars_dict['VAR02'] <= 1.4565)].copy()
    def estrategia_85(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR37'] >= 0.1546) & (vars_dict['VAR37'] <= 0.182)].copy()
    def estrategia_86(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR70'] >= 0.0153) & (vars_dict['VAR70'] <= 0.4595)].copy()
    def estrategia_87(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR05'] >= 0.6866) & (vars_dict['VAR05'] <= 1.85)].copy()
    def estrategia_88(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR75'] >= 0.3846) & (vars_dict['VAR75'] <= 0.4118)].copy()
    def estrategia_89(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR50'] >= 0.492) & (vars_dict['VAR50'] <= 0.5441)].copy()
    def estrategia_90(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR55'] >= 0.0817) & (vars_dict['VAR55'] <= 0.0981)].copy()
    def estrategia_91(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR13'] >= 0.3015) & (vars_dict['VAR13'] <= 0.7716)].copy()
    def estrategia_92(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR57'] >= 0.0967) & (vars_dict['VAR57'] <= 0.1257)].copy()
    def estrategia_93(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR23'] >= 0.0853) & (vars_dict['VAR23'] <= 0.1604)].copy()
    def estrategia_94(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR20'] >= 0.2592) & (vars_dict['VAR20'] <= 0.3061)].copy()
    def estrategia_95(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR49'] >= 0.6893) & (vars_dict['VAR49'] <= 1.0)].copy()
    def estrategia_96(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR27'] >= 0.1032) & (vars_dict['VAR27'] <= 0.11)].copy()
    def estrategia_97(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR61'] >= 0.0) & (vars_dict['VAR61'] <= 0.0202)].copy()
    def estrategia_98(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR17'] >= 0.4256) & (vars_dict['VAR17'] <= 0.7155)].copy()
    def estrategia_99(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR22'] >= 1.2365) & (vars_dict['VAR22'] <= 1.2884)].copy()
    def estrategia_100(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR44'] >= 0.5938) & (vars_dict['VAR44'] <= 0.6216)].copy()
    def estrategia_101(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR33'] >= 0.1047) & (vars_dict['VAR33'] <= 0.1232)].copy()
    def estrategia_102(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR24'] >= 0.155) & (vars_dict['VAR24'] <= 0.174)].copy()
    def estrategia_103(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR14'] >= 0.6491) & (vars_dict['VAR14'] <= 1.3016)].copy()
    def estrategia_104(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR56'] >= 0.0) & (vars_dict['VAR56'] <= 0.2403)].copy()
    def estrategia_105(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR46'] >= 1.6087) & (vars_dict['VAR46'] <= 1.6842)].copy()
    def estrategia_106(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR35'] >= 0.0794) & (vars_dict['VAR35'] <= 0.1097)].copy()
    def estrategia_107(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR26'] >= 0.1402) & (vars_dict['VAR26'] <= 0.3463)].copy()
    def estrategia_108(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR47'] >= 1.0) & (vars_dict['VAR47'] <= 1.4508)].copy()
    def estrategia_109(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR65'] >= -4.0022) & (vars_dict['VAR65'] <= -3.0924)].copy()
    def estrategia_110(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR41'] >= 0.11) & (vars_dict['VAR41'] <= 0.1174)].copy()
    def estrategia_111(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR31'] >= 0.004) & (vars_dict['VAR31'] <= 0.2333)].copy()
    def estrategia_112(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR28'] >= 0.0646) & (vars_dict['VAR28'] <= 0.0748)].copy()
    def estrategia_113(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR71'] >= 0.3158) & (vars_dict['VAR71'] <= 0.3773)].copy()
    def estrategia_114(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR73'] >= 0.1154) & (vars_dict['VAR73'] <= 0.1824)].copy()
    def estrategia_115(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR09'] >= 1.6332) & (vars_dict['VAR09'] <= 2.9389)].copy()
    def estrategia_116(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR74'] >= 0.6332) & (vars_dict['VAR74'] <= 1.9389)].copy()
    def estrategia_117(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR10'] >= 0.3403) & (vars_dict['VAR10'] <= 0.6123)].copy()
    def estrategia_118(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR68'] >= 0.1061) & (vars_dict['VAR68'] <= 1.7607)].copy()
    def estrategia_119(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR64'] >= -13.0557) & (vars_dict['VAR64'] <= 6.8043)].copy()
    def estrategia_120(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR29'] >= 0.1046) & (vars_dict['VAR29'] <= 0.1135)].copy()
    def estrategia_121(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR19'] >= 0.3015) & (vars_dict['VAR19'] <= 0.7358)].copy()
    def estrategia_122(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR43'] >= 0.1108) & (vars_dict['VAR43'] <= 0.121)].copy()
    def estrategia_123(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR66'] >= -14.9908) & (vars_dict['VAR66'] <= -7.0667)].copy()
    def estrategia_124(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR53'] >= 0.341) & (vars_dict['VAR53'] <= 0.3837)].copy()
    def estrategia_125(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR32'] >= 0.0018) & (vars_dict['VAR32'] <= 0.0863)].copy()
    def estrategia_126(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR59'] >= 0.0476) & (vars_dict['VAR59'] <= 0.0536)].copy()
    def estrategia_127(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR30'] >= 0.2137) & (vars_dict['VAR30'] <= 0.3071)].copy()
    def estrategia_128(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR36'] >= 0.1867) & (vars_dict['VAR36'] <= 0.1964)].copy()
    def estrategia_129(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR76'] >= 0.3333) & (vars_dict['VAR76'] <= 0.4809)].copy()
    def estrategia_130(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR42'] >= 0.0552) & (vars_dict['VAR42'] <= 0.0637)].copy()
    def estrategia_131(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR16'] >= 1.3735) & (vars_dict['VAR16'] <= 1.4882)].copy()
    def estrategia_132(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR39'] >= 0.0931) & (vars_dict['VAR39'] <= 0.1056)].copy()
    def estrategia_133(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR15'] >= 0.4597) & (vars_dict['VAR15'] <= 0.485)].copy()
    def estrategia_134(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR40'] >= 0.0903) & (vars_dict['VAR40'] <= 0.1061)].copy()
    def estrategia_135(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR08'] >= 0.5068) & (vars_dict['VAR08'] <= 0.5896)].copy()
    def estrategia_136(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR69'] >= -0.5433) & (vars_dict['VAR69'] <= 0.0)].copy()
    def estrategia_137(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR12'] >= 0.3535) & (vars_dict['VAR12'] <= 0.3803)].copy()
    def estrategia_138(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR67'] >= 0.6886) & (vars_dict['VAR67'] <= 0.889)].copy()
    def estrategia_139(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR06'] >= 2.3464) & (vars_dict['VAR06'] <= 2.5294)].copy()
    def estrategia_140(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR21'] >= 0.5288) & (vars_dict['VAR21'] <= 0.5512)].copy()
    def estrategia_141(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR60'] >= 0.0124) & (vars_dict['VAR60'] <= 0.0171)].copy()
    def estrategia_142(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR04'] >= 0.4262) & (vars_dict['VAR04'] <= 0.4532)].copy()
    def estrategia_143(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR38'] >= 0.1975) & (vars_dict['VAR38'] <= 0.2135)].copy()
    def estrategia_144(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR07'] >= 1.6962) & (vars_dict['VAR07'] <= 1.9733)].copy()
    def estrategia_145(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR25'] >= 0.0737) & (vars_dict['VAR25'] <= 0.0835)].copy()
    def estrategia_146(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR72'] >= 0.5486) & (vars_dict['VAR72'] <= 0.5755)].copy()
    def estrategia_147(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR51'] >= 0.2592) & (vars_dict['VAR51'] <= 0.3274)].copy()
    def estrategia_148(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR45'] >= 0.0163) & (vars_dict['VAR45'] <= 0.913)].copy()
    def estrategia_149(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR52'] >= 0.2503) & (vars_dict['VAR52'] <= 0.4922)].copy()
    def estrategia_150(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR48'] >= 1.0) & (vars_dict['VAR48'] <= 1.0952)].copy()
    def estrategia_151(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR34'] >= 0.2) & (vars_dict['VAR34'] <= 0.2093)].copy()
    def estrategia_152(df): return df[(vars_dict['VAR11'] >= 0.0253) & (vars_dict['VAR11'] <= 0.4633) & (vars_dict['VAR58'] >= 0.2631) & (vars_dict['VAR58'] <= 0.5356)].copy()

    # --- Lista de estratégias ---
    strategy_list = [
        (estrategia_1, "Estrategia_1"), (estrategia_2, "Estrategia_2"), (estrategia_3, "Estrategia_3"),
        (estrategia_4, "Estrategia_4"), (estrategia_5, "Estrategia_5"), (estrategia_6, "Estrategia_6"),
        (estrategia_7, "Estrategia_7"), (estrategia_8, "Estrategia_8"), (estrategia_9, "Estrategia_9"),
        (estrategia_10, "Estrategia_10"), (estrategia_11, "Estrategia_11"), (estrategia_12, "Estrategia_12"),
        (estrategia_13, "Estrategia_13"), (estrategia_14, "Estrategia_14"), (estrategia_15, "Estrategia_15"),
        (estrategia_16, "Estrategia_16"), (estrategia_17, "Estrategia_17"), (estrategia_18, "Estrategia_18"),
        (estrategia_19, "Estrategia_19"), (estrategia_20, "Estrategia_20"), (estrategia_21, "Estrategia_21"),
        (estrategia_22, "Estrategia_22"), (estrategia_23, "Estrategia_23"), (estrategia_24, "Estrategia_24"),
        (estrategia_25, "Estrategia_25"), (estrategia_26, "Estrategia_26"), (estrategia_27, "Estrategia_27"),
        (estrategia_28, "Estrategia_28"), (estrategia_29, "Estrategia_29"), (estrategia_30, "Estrategia_30"),
        (estrategia_31, "Estrategia_31"), (estrategia_32, "Estrategia_32"), (estrategia_33, "Estrategia_33"),
        (estrategia_34, "Estrategia_34"), (estrategia_35, "Estrategia_35"), (estrategia_36, "Estrategia_36"),
        (estrategia_37, "Estrategia_37"), (estrategia_38, "Estrategia_38"), (estrategia_39, "Estrategia_39"),
        (estrategia_40, "Estrategia_40"), (estrategia_41, "Estrategia_41"), (estrategia_42, "Estrategia_42"),
        (estrategia_43, "Estrategia_43"), (estrategia_44, "Estrategia_44"), (estrategia_45, "Estrategia_45"),
        (estrategia_46, "Estrategia_46"), (estrategia_47, "Estrategia_47"), (estrategia_48, "Estrategia_48"),
        (estrategia_49, "Estrategia_49"), (estrategia_50, "Estrategia_50"), (estrategia_51, "Estrategia_51"),
        (estrategia_52, "Estrategia_52"), (estrategia_53, "Estrategia_53"), (estrategia_54, "Estrategia_54"),
        (estrategia_55, "Estrategia_55"), (estrategia_56, "Estrategia_56"), (estrategia_57, "Estrategia_57"),
        (estrategia_58, "Estrategia_58"), (estrategia_59, "Estrategia_59"), (estrategia_60, "Estrategia_60"),
        (estrategia_61, "Estrategia_61"), (estrategia_62, "Estrategia_62"), (estrategia_63, "Estrategia_63"),
        (estrategia_64, "Estrategia_64"), (estrategia_65, "Estrategia_65"), (estrategia_66, "Estrategia_66"),
        (estrategia_67, "Estrategia_67"), (estrategia_68, "Estrategia_68"), (estrategia_69, "Estrategia_69"),
        (estrategia_70, "Estrategia_70"), (estrategia_71, "Estrategia_71"), (estrategia_72, "Estrategia_72"),
        (estrategia_73, "Estrategia_73"), (estrategia_74, "Estrategia_74"), (estrategia_75, "Estrategia_75"),
        (estrategia_76, "Estrategia_76"),   (estrategia_77, "Estrategia_77"), (estrategia_78, "Estrategia_78"), (estrategia_79, "Estrategia_79"),
        (estrategia_80, "Estrategia_80"), (estrategia_81, "Estrategia_81"), (estrategia_82, "Estrategia_82"), (estrategia_83, "Estrategia_83"), (estrategia_84, "Estrategia_84"), (estrategia_85, "Estrategia_85"), (estrategia_86, "Estrategia_86"),
        (estrategia_87, "Estrategia_87"), (estrategia_88, "Estrategia_88"), (estrategia_89, "Estrategia_89"), (estrategia_90, "Estrategia_90"), (estrategia_91, "Estrategia_91"), (estrategia_92, "Estrategia_92"), (estrategia_93, "Estrategia_93"),
        (estrategia_94, "Estrategia_94"), (estrategia_95, "Estrategia_95"), (estrategia_96, "Estrategia_96"), (estrategia_97, "Estrategia_97"), (estrategia_98, "Estrategia_98"), (estrategia_99, "Estrategia_99"), (estrategia_100, "Estrategia_100"),
        (estrategia_101, "Estrategia_101"), (estrategia_102, "Estrategia_102"), (estrategia_103, "Estrategia_103"), (estrategia_104, "Estrategia_104"), (estrategia_105, "Estrategia_105"), (estrategia_106, "Estrategia_106"), (estrategia_107, "Estrategia_107"),
        (estrategia_108, "Estrategia_108"), (estrategia_109, "Estrategia_109"), (estrategia_110, "Estrategia_110"), (estrategia_111, "Estrategia_111"), (estrategia_112, "Estrategia_112"), (estrategia_113, "Estrategia_113"), (estrategia_114, "Estrategia_114"),
        (estrategia_115, "Estrategia_115"), (estrategia_116, "Estrategia_116"), (estrategia_117, "Estrategia_117"), (estrategia_118, "Estrategia_118"), (estrategia_119, "Estrategia_119"), (estrategia_120, "Estrategia_120"), (estrategia_121, "Estrategia_121"),
        (estrategia_122, "Estrategia_122"), (estrategia_123, "Estrategia_123"), (estrategia_124, "Estrategia_124"), (estrategia_125, "Estrategia_125"), (estrategia_126, "Estrategia_126"), (estrategia_127, "Estrategia_127"), (estrategia_128, "Estrategia_128"),
        (estrategia_129, "Estrategia_129"), (estrategia_130, "Estrategia_130"), (estrategia_131, "Estrategia_131"), (estrategia_132, "Estrategia_132"), (estrategia_133, "Estrategia_133"), (estrategia_134, "Estrategia_134"), (estrategia_135, "Estrategia_135"),
        (estrategia_136, "Estrategia_136"), (estrategia_137, "Estrategia_137"), (estrategia_138, "Estrategia_138"), (estrategia_139, "Estrategia_139"), (estrategia_140, "Estrategia_140"), (estrategia_141, "Estrategia_141"), (estrategia_142, "Estrategia_142"),
        (estrategia_143, "Estrategia_143"), (estrategia_144, "Estrategia_144"), (estrategia_145, "Estrategia_145"), (estrategia_146, "Estrategia_146"), (estrategia_147, "Estrategia_147"), (estrategia_148, "Estrategia_148"),
        (estrategia_149, "Estrategia_149"), (estrategia_150, "Estrategia_150"), (estrategia_151, "Estrategia_151"), (estrategia_152, "Estrategia_152")
    ]
    strategy_map = {name: func for func, name in strategy_list}
    return strategy_list, strategy_map
# --- Fim Definição das estratégias VAR ---

# --- Título ---
st.title("Estratégia Lay Correct Score 95% >>")

# --- Carregar Histórico do GitHub ---
st.header("Carregamento da Base Histórica")
github_raw_url = "https://raw.githubusercontent.com/81matheus/BasedeDadosBet365/main/pagesbet365/Base_de_Dados_Betfair_Exchange2024.xlsx"
with st.spinner("Buscando e carregando dados históricos do GitHub..."):
    df_historico_original = load_data_from_github(github_raw_url)

# --- Processamento ---
if df_historico_original is not None:
    st.info(f"Base histórica carregada com {len(df_historico_original)} linhas.")

    # --- Validação de Colunas Essenciais e Filtro de Ligas ---
    required_base_cols = ['League', 'Goals_H', 'Goals_A'] # Inclui League aqui
    required_odds_cols = [ # Colunas necessárias para VARs
        'Odd_H_Back', 'Odd_D_Back', 'Odd_A_Back',
        'Odd_Over25_FT_Back', 'Odd_Under25_FT_Back',
        'Odd_BTTS_Yes_Back', 'Odd_BTTS_No_Back',
        'Odd_CS_0x0_Lay', 'Odd_CS_0x1_Lay', 'Odd_CS_1x0_Lay'
    ]
    all_required_cols = required_base_cols + required_odds_cols
    missing_cols = [col for col in all_required_cols if col not in df_historico_original.columns]

    if missing_cols:
        st.error(f"Colunas essenciais ausentes na base histórica: {', '.join(missing_cols)}. Não é possível continuar.")
        df_historico = None # Impede a execução do resto
    else:
        # Filtro de Ligas APROVADAS
        df_historico = df_historico_original[df_historico_original['League'].isin(APPROVED_LEAGUES)].copy()
        if df_historico.empty:
            st.warning("Nenhum jogo da base histórica pertence às ligas aprovadas. O backtest será vazio.")
        else:
            st.info(f"Histórico filtrado para {len(df_historico)} jogos nas ligas aprovadas.")

    # --- Backtest Combinado (só executa se df_historico for válido e não vazio) ---
    if df_historico is not None and not df_historico.empty:
        #st.info("Iniciando pré-cálculo das variáveis VAR para o histórico...")
        vars_dict_historico = pre_calculate_all_vars(df_historico)

        if vars_dict_historico is None:
            st.error("Falha ao pré-calcular variáveis VAR do histórico. Verifique os dados e mensagens acima.")
        else:
            #st.success("Variáveis VAR do histórico calculadas.")
            #st.info("Definindo estratégias VAR e iniciando backtest combinado...")
            var_strategy_list, var_strategy_map = define_var_strategies(vars_dict_historico)

            if not var_strategy_list:
                 st.warning("Nenhuma estratégia VAR foi definida.")
            else:
                combined_backtest_results_list = []
                combined_medias_results_list = []
                approved_combined_strategies = [] # Lista para guardar nomes das combinações aprovadas

                total_combinations = len(var_strategy_list) * len(cs_lay_strategies_to_test)
                st.write(f"Executando backtest para {total_combinations} combinações (Estratégias VAR x Lay CS)...")
                progress_bar = st.progress(0)
                processed_count = 0

                for var_strategy_func, var_strategy_name in var_strategy_list:
                    try:
                        # Aplica filtro VAR ao DF já filtrado por liga
                        df_filtered_by_var = var_strategy_func(df_historico)
                    except Exception as e_filter:
                        st.error(f"Erro ao aplicar filtro {var_strategy_name} no histórico: {e_filter}")
                        df_filtered_by_var = pd.DataFrame() # Cria DF vazio para pular o loop CS

                    # Loop CS Lay apenas se o filtro VAR retornou algo
                    if not df_filtered_by_var.empty:
                         for cs_lay_name in cs_lay_strategies_to_test:
                            combined_name = f"VAR_{var_strategy_name}_CS_{cs_lay_name}"
                            backtest_result = run_combined_backtest(df_filtered_by_var.copy(), cs_lay_name, combined_name)
                            combined_backtest_results_list.append(backtest_result)

                            if backtest_result["Total de Jogos"] > 0:
                                medias_result = check_combined_moving_averages(backtest_result["Dataframe"], combined_name)
                                combined_medias_results_list.append(medias_result)
                                if medias_result["Acima dos Limiares"]:
                                    # Guarda o nome da COMBINAÇÃO aprovada
                                    approved_combined_strategies.append(combined_name)
                            else:
                                # Adiciona entrada mesmo para 0 jogos para consistência na tabela de médias
                                combined_medias_results_list.append({
                                    "Estratégia": combined_name, "Média 8": "N/A (0 jogos)", "Média 40": "N/A (0 jogos)",
                                    "Lucro Últimos 8": "N/A (0 jogos)", "Lucro Últimos 40": "N/A (0 jogos)",
                                    "Acima dos Limiares": False
                                })
                            processed_count += 1
                            progress_bar.progress(min(1.0, processed_count / total_combinations)) # Garante que não passa de 1.0
                    else:
                        # Pula as combinações CS Lay para este filtro VAR vazio, atualiza progresso
                        processed_count += len(cs_lay_strategies_to_test)
                        progress_bar.progress(min(1.0, processed_count / total_combinations))

                progress_bar.empty() # Limpa a barra de progresso
                st.success("Backtest combinado concluído.")

                # --- Exibição dos Resultados do Backtest ---
                with st.expander("📊 Resultados Detalhados do Backtest Combinado"):
                    st.subheader("📊 Resumo do Backtest por Combinação")
                    # Filtra resultados onde houve jogos para mostrar no resumo
                    df_summary_combined = pd.DataFrame([r for r in combined_backtest_results_list if r['Total de Jogos'] > 0])
                    if not df_summary_combined.empty:
                        st.dataframe(df_summary_combined.drop(columns=["Dataframe"], errors='ignore').set_index("Estratégia"))
                    else:
                        st.write("Nenhuma combinação de estratégia resultou em jogos no backtest.")

                with st.expander ("📈 Análise das Médias e Lucros Recentes por Combinação"):
                    st.subheader("📈 Análise das Médias e Lucros Recentes (Combinado)")
                    df_medias_combined = pd.DataFrame(combined_medias_results_list)
                    if not df_medias_combined.empty:
                        # Ordena para ver as aprovadas primeiro (opcional)
                        df_medias_combined = df_medias_combined.sort_values(by="Acima dos Limiares", ascending=False)
                        st.dataframe(df_medias_combined.set_index("Estratégia"))
                    else:
                        st.write("Nenhuma análise de médias gerada.")

                # --- Seção de Jogos do Dia ---
                st.divider() # Linha divisória
                st.header("🔍 Análise dos Jogos do Dia")

                if not approved_combined_strategies:
                     st.info("Nenhuma estratégia combinada foi aprovada no backtest histórico. Não há recomendações para os jogos do dia.")
                else:
                    st.success(f"{len(approved_combined_strategies)} combinações foram aprovadas no histórico!")
                    st.write("Faça o upload da planilha com os jogos do dia para verificar recomendações:")

                    uploaded_daily = st.file_uploader(
                        "Upload da planilha com os jogos do dia (.xlsx ou .csv)",
                        type=["xlsx", "csv"],
                        key="daily_combined_v2"
                    )

                    if uploaded_daily is not None:
                        # Usa a função de carregamento LOCAL para o arquivo do dia
                        df_daily_original = load_dataframe_local(uploaded_daily)

                        if df_daily_original is not None:
                            st.success(f"Arquivo de jogos do dia '{uploaded_daily.name}' carregado ({len(df_daily_original)} linhas).")

                            # Validação de colunas de Odds para aplicar filtros VAR nos jogos do dia
                            missing_daily_cols = [col for col in required_odds_cols if col not in df_daily_original.columns]
                            # Verifica também a coluna League
                            if 'League' not in df_daily_original.columns:
                                missing_daily_cols.append('League')

                            if missing_daily_cols:
                                 st.error(f"Colunas necessárias ({', '.join(missing_daily_cols)}) não encontradas nos jogos do dia. Não é possível gerar recomendações.")
                                 df_daily = None
                            else:
                                # Filtro de Ligas diário
                                df_daily = df_daily_original[df_daily_original['League'].isin(APPROVED_LEAGUES)].copy()
                                if df_daily.empty and not df_daily_original.empty:
                                    st.warning("Nenhum jogo do dia pertence às ligas aprovadas.")
                                elif not df_daily.empty:
                                    st.info(f"Encontrados {len(df_daily)} jogos do dia nas ligas aprovadas para análise.")
                                else: # df_daily_original já estava vazio ou só tinha ligas não aprovadas
                                    st.info("Não há jogos do dia nas ligas aprovadas para analisar.")


                            # --- Aplica Filtros Aprovados aos Jogos do Dia ---
                            if df_daily is not None and not df_daily.empty:
                                st.subheader("📋 Recomendações para os Jogos do Dia")
                                #st.info("Calculando variáveis VAR para os jogos do dia...")
                                with st.spinner("Calculando variáveis VAR e aplicando filtros aprovados..."):
                                    vars_dict_daily = pre_calculate_all_vars(df_daily.copy()) # Usa cópia

                                    if vars_dict_daily is None:
                                        st.error("Falha ao calcular VARs para os jogos do dia. Não é possível gerar recomendações.")
                                    else:
                                        #st.success("Variáveis VAR dos jogos do dia calculadas.")
                                        #st.info("Aplicando filtros VAR das estratégias aprovadas...")
                                        _, daily_var_strategy_map = define_var_strategies(vars_dict_daily) # Gera mapa para dados do dia

                                        daily_recommendations_list = []
                                        # Colunas básicas para mostrar, se existirem
                                        cols_to_display_base = ['Time', 'League', 'Home', 'Away']
                                        cols_exist_daily = [col for col in cols_to_display_base if col in df_daily.columns]

                                        # Loop pelas COMBINAÇÕES APROVADAS no histórico
                                        for combined_name in approved_combined_strategies:
                                            # Extrai o nome da Estrategia_VAR e do Lay_CS
                                            match_var = re.search(r'VAR_(Estrategia_\d+)_CS_(Lay_\w+)$', combined_name)
                                            if match_var:
                                                var_name = match_var.group(1)
                                                cs_lay_name_approved = match_var.group(2) # Nome do Lay CS aprovado

                                                if var_name in daily_var_strategy_map:
                                                    var_func = daily_var_strategy_map[var_name]
                                                    try:
                                                        # Aplica o filtro VAR ao DF diário COMPLETO (já filtrado por liga)
                                                        df_daily_filtered = var_func(df_daily)

                                                        if not df_daily_filtered.empty:
                                                            # Para cada jogo que passou no filtro, adiciona a recomendação
                                                            for idx, row in df_daily_filtered.iterrows():
                                                                rec = row[cols_exist_daily].to_dict()
                                                                # Adiciona a recomendação específica (Lay CS)
                                                                rec['Recomendação'] = cs_lay_name_approved
                                                                rec['Filtro_VAR'] = var_name # Qual filtro VAR ativou
                                                                # Adiciona o nome da combinação original para referência, se útil
                                                                # rec['Estrategia_Combinada'] = combined_name
                                                                daily_recommendations_list.append(rec)
                                                    except Exception as e_apply_daily:
                                                        st.warning(f"Erro ao aplicar filtro {var_name} (de {combined_name}) aos jogos do dia: {e_apply_daily}. Pulando este filtro.")
                                                else:
                                                    # Isso não deveria acontecer se define_var_strategies for consistente
                                                    st.warning(f"Filtro VAR '{var_name}' (de {combined_name}) não encontrado no mapa diário.")
                                            else:
                                                 st.warning(f"Não foi possível extrair nome VAR e CS Lay de: {combined_name}")


                                        if daily_recommendations_list:
                                            df_final_recommendations = pd.DataFrame(daily_recommendations_list)

                                            # Agrupar por jogo para mostrar todas as recomendações juntas
                                            if cols_exist_daily: # Garante que há colunas para agrupar
                                                group_cols = cols_exist_daily
                                                # Agrupa por jogo e junta as recomendações e filtros VAR
                                                df_grouped_recs = df_final_recommendations.groupby(group_cols).agg(
                                                    Recomendações=('Recomendação', lambda x: ', '.join(sorted(list(set(x))))), # Lista única e ordenada de Lays
                                                    Filtros_VAR=('Filtro_VAR', lambda x: ', '.join(sorted(list(set(x))))) # Lista única e ordenada de VARs
                                                ).reset_index()
                                                st.dataframe(df_grouped_recs)
                                            else: # Se faltar colunas básicas, mostra a lista desagrupada
                                                 st.dataframe(df_final_recommendations)

                                        else:
                                            st.info("Nenhum jogo do dia (nas ligas aprovadas) correspondeu aos filtros VAR das estratégias combinadas aprovadas no histórico.")
                            elif df_daily is not None and df_daily.empty:
                                pass # Mensagem de "nenhum jogo nas ligas aprovadas" já foi mostrada
                            # else: df_daily é None devido a erro de coluna ou leitura, erro já mostrado
                        # else: Erro ao carregar df_daily_original, erro já mostrado por load_dataframe_local
                    # else: Nenhum arquivo diário foi carregado
        # else: Falha ao calcular vars_dict_historico, erro já mostrado
    elif df_historico is None:
         pass # Erro de coluna na base histórica já tratado
    # else: df_historico vazio (nenhum jogo nas ligas aprovadas), aviso já dado

# else: Erro ao carregar df_historico_original do GitHub, erro já mostrado
