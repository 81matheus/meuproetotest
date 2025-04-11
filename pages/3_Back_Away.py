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
        if uploaded_file.name.lower().endswith('.xlsx'):
            # Lê o arquivo Excel diretamente do buffer
            df = pd.read_excel(uploaded_file)
            return df
        elif uploaded_file.name.lower().endswith('.csv'):
            # Lê o arquivo CSV diretamente do buffer
            # Tenta detectar separador comum (vírgula ou ponto e vírgula)
            # Cria uma cópia do buffer para não consumir o original
            file_content = uploaded_file.getvalue()
            try:
                # Tenta com vírgula primeiro
                df = pd.read_csv(io.BytesIO(file_content))
                 # Checa se a primeira linha foi lida corretamente (mais de uma coluna)
                if df.shape[1] <= 1:
                    # Se parece errado, tenta com ponto e vírgula
                    df = pd.read_csv(io.BytesIO(file_content), sep=';')
            except Exception as e_csv:
                 # Se ambos falharem, tenta com ponto e vírgula como fallback
                 st.warning(f"Não foi possível determinar o separador CSV automaticamente, tentando ';'. Erro: {e_csv}")
                 df = pd.read_csv(io.BytesIO(file_content), sep=';')

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

# Título da aplicação
st.title("Estratégias Back Away-Visitante")

# Função genérica de Backtest (mantida como no seu exemplo)
def run_backtest(df, estrategia_func, estrategia_nome):
     # Filtrar pela Odd_H_Back maior que 1.30
    df = df[df['Odd_A_Back'] >= 1.30]
     # Aplicar a estratégia
    df_filtrado = estrategia_func(df)
    
    # Verifica se o df_filtrado não está vazio antes de calcular o Profit
    if not df_filtrado.empty:
        df_filtrado['Profit'] = df_filtrado.apply(
            lambda row: (row['Odd_A_Back'] - 1) if row['Goals_H'] < row['Goals_A'] else -1,
            axis=1
        )
        total_jogos = len(df_filtrado)
        acertos = len(df_filtrado[df_filtrado['Goals_H'] < df_filtrado['Goals_A']])
        taxa_acerto = acertos / total_jogos if total_jogos > 0 else 0
        lucro_total = df_filtrado['Profit'].sum()
    else:
        # Define valores padrão se não houver jogos após o filtro da estratégia
        total_jogos = 0
        acertos = 0
        taxa_acerto = 0
        lucro_total = 0.0
        # Retorna um DataFrame vazio com as colunas esperadas se necessário, 
        # ou ajusta a lógica downstream para lidar com df_filtrado vazio.
        # Aqui, vamos garantir que df_filtrado tenha a coluna Profit se não estiver vazio
        # Se estiver vazio, o retorno abaixo lida com isso.

    return {
        "Estratégia": estrategia_nome,
        "Total de Jogos": total_jogos,
        "Taxa de Acerto": f"{taxa_acerto:.2%}",
        "Lucro Total": f"{lucro_total:.2f}",
        "Dataframe": df_filtrado # Pode ser um DataFrame vazio
    }

# Análise das médias E LUCROS RECENTES <--- MODIFICADA
def check_moving_averages(df_filtrado, estrategia_nome):
    # Garante que a coluna 'Profit' existe se o DataFrame não for vazio
    # Se df_filtrado veio de run_backtest e não estava vazio, 'Profit' deve existir.
    # Se df_filtrado estava vazio, as operações abaixo retornarão 0 ou médias 0.

    if df_filtrado.empty:
        # Retorna valores padrão se não houver dados para analisar
        return {
            "Estratégia": estrategia_nome,
            "Média 8": "0.00% (0 acertos em 0)",
            "Média 40": "0.00% (0 acertos em 0)",
            "Lucro Últimos 8": "0.00 (em 0 jogos)",
            "Lucro Últimos 40": "0.00 (em 0 jogos)",
            "Acima dos Limiares": False
        }
        
    # Calcula acerto (como antes)
    df_filtrado['Acerto'] = (df_filtrado['Goals_H'] < df_filtrado['Goals_A']).astype(int)
    
    # Seleciona os últimos jogos
    ultimos_8 = df_filtrado.tail(8) 
    ultimos_40 = df_filtrado.tail(40) 
    
    # Calcula a média de acertos (usando .mean() para robustez)
    media_8 = ultimos_8['Acerto'].mean() if not ultimos_8.empty else 0
    media_40 = ultimos_40['Acerto'].mean() if not ultimos_40.empty else 0
    
    # --- NOVO: Calcula o lucro dos últimos jogos ---
    lucro_8 = ultimos_8['Profit'].sum()
    lucro_40 = ultimos_40['Profit'].sum()
    # ---------------------------------------------
    
    # Verifica se as médias estão acima dos limiares (usando médias calculadas com .mean())
    # acima_das_medias = media_8 >= 0.70 and media_40 > 0.7 
    acima_das_medias = lucro_8 >= 0.1 and lucro_40 > 0.1 and media_8 >= 0.5 and media_40 > 0.5

    # Retorna o dicionário com as novas informações de lucro
    return {
        "Estratégia": estrategia_nome,
        # Formatando médias como porcentagem e incluindo contagem
        "Média 8": f"{media_8:.2%} ({ultimos_8['Acerto'].sum()} acertos em {len(ultimos_8)})", 
        "Média 40": f"{media_40:.2%} ({ultimos_40['Acerto'].sum()} acertos em {len(ultimos_40)})", 
        # --- NOVO: Incluindo os lucros formatados ---
        "Lucro Últimos 8": f"{lucro_8:.2f} (em {len(ultimos_8)} jogos)",
        "Lucro Últimos 40": f"{lucro_40:.2f} (em {len(ultimos_40)} jogos)",
        # ------------------------------------------
        "Acima dos Limiares": acima_das_medias
    }

# Analisar jogos do dia - Verifique se esta função já está como abaixo (incluindo 'League')
def analyze_daily_games(df_daily, estrategia_func, estrategia_nome):
    df_filtrado = estrategia_func(df_daily)
    if df_filtrado is not None and not df_filtrado.empty: # Adicionado check df_filtrado is not None
        # Ajuste para incluir 'League' se existir
        cols_to_return = ['Time', 'Home', 'Away']
        if 'League' in df_filtrado.columns:
            cols_to_return.insert(1, 'League')
        # Garante que apenas colunas existentes sejam selecionadas
        cols_exist = [col for col in cols_to_return if col in df_filtrado.columns]
        if cols_exist:
             return df_filtrado[cols_exist].copy()
        else: # Se nenhuma das colunas básicas existir, retorna None
             st.warning(f"Colunas essenciais ('Time', 'Home', 'Away') não encontradas no resultado da estratégia {estrategia_nome}")
             return None
    return None


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
def apply_strategies(df):
    vars_dict = pre_calculate_all_vars(df)
    
    def estrategia_1(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR55'] >= 0.0000) & (vars_dict['VAR55'] <= 0.1350)].copy()
    def estrategia_2(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR63'] >= -3.8604) & (vars_dict['VAR63'] <= 2.4499)].copy()
    def estrategia_3(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR68'] >= 1.0024) & (vars_dict['VAR68'] <= 1.1185)].copy()
    def estrategia_4(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR60'] >= 0.0350) & (vars_dict['VAR60'] <= 0.0390)].copy()
    def estrategia_5(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR43'] >= 0.2097) & (vars_dict['VAR43'] <= 0.2205)].copy()
    def estrategia_6(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR14'] >= 0.3571) & (vars_dict['VAR14'] <= 0.8289)].copy()
    def estrategia_7(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR38'] >= 0.3871) & (vars_dict['VAR38'] <= 0.4244)].copy()
    def estrategia_8(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR56'] >= 0.0480) & (vars_dict['VAR56'] <= 0.0595)].copy()
    def estrategia_9(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR16'] >= 0.7077) & (vars_dict['VAR16'] <= 0.8390)].copy()
    def estrategia_10(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR13'] >= 0.6041) & (vars_dict['VAR13'] <= 1.2478)].copy()
    def estrategia_11(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR29'] >= 0.1438) & (vars_dict['VAR29'] <= 0.1511)].copy()
    def estrategia_12(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR26'] >= 0.1393) & (vars_dict['VAR26'] <= 0.1571)].copy()
    def estrategia_13(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR41'] >= 0.1948) & (vars_dict['VAR41'] <= 0.2041)].copy()
    def estrategia_14(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR19'] >= 0.4627) & (vars_dict['VAR19'] <= 0.4800)].copy()
    def estrategia_15(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR09'] >= 1.0385) & (vars_dict['VAR09'] <= 1.1136)].copy()
    def estrategia_16(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR10'] >= 0.8980) & (vars_dict['VAR10'] <= 0.9630)].copy()
    def estrategia_17(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR39'] >= 0.4688) & (vars_dict['VAR39'] <= 0.5581)].copy()
    def estrategia_18(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR21'] >= 0.5908) & (vars_dict['VAR21'] <= 0.6058)].copy()
    def estrategia_19(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR58'] >= 0.0688) & (vars_dict['VAR58'] <= 0.0904)].copy()
    def estrategia_20(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR25'] >= 0.3214) & (vars_dict['VAR25'] <= 0.3777)].copy()
    def estrategia_21(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR71'] >= 0.0000) & (vars_dict['VAR71'] <= 0.4773)].copy()
    def estrategia_22(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR01'] >= 0.7450) & (vars_dict['VAR01'] <= 1.4773)].copy()
    def estrategia_23(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR03'] >= 0.6769) & (vars_dict['VAR03'] <= 1.3423)].copy()
    def estrategia_24(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR28'] >= 0.1270) & (vars_dict['VAR28'] <= 0.1431)].copy()
    def estrategia_25(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR22'] >= 0.4574) & (vars_dict['VAR22'] <= 0.5050)].copy()
    def estrategia_26(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR33'] >= 0.1247) & (vars_dict['VAR33'] <= 0.1322)].copy()
    def estrategia_27(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR24'] >= 0.2667) & (vars_dict['VAR24'] <= 0.2880)].copy()
    def estrategia_28(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR27'] >= 0.1333) & (vars_dict['VAR27'] <= 0.1400)].copy()
    def estrategia_29(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR12'] >= 0.4190) & (vars_dict['VAR12'] <= 0.4563)].copy()
    def estrategia_30(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR35'] >= 0.0947) & (vars_dict['VAR35'] <= 0.1005)].copy()
    def estrategia_31(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR40'] >= 0.2040) & (vars_dict['VAR40'] <= 0.2318)].copy()
    def estrategia_32(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR76'] >= 0.3409) & (vars_dict['VAR76'] <= 0.3481)].copy()
    def estrategia_33(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR45'] >= 0.6519) & (vars_dict['VAR45'] <= 0.6591)].copy()
    def estrategia_34(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR74'] >= 0.1339) & (vars_dict['VAR74'] <= 0.1803)].copy()
    def estrategia_35(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR66'] >= -1.6253) & (vars_dict['VAR66'] <= -0.5830)].copy()
    def estrategia_36(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR42'] >= 0.2078) & (vars_dict['VAR42'] <= 0.2373)].copy()
    def estrategia_37(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR67'] >= -0.3611) & (vars_dict['VAR67'] <= -0.2122)].copy()
    def estrategia_38(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR77'] >= 0.1246) & (vars_dict['VAR77'] <= 0.2059)].copy()
    def estrategia_39(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR30'] >= 0.1585) & (vars_dict['VAR30'] <= 0.5556)].copy()
    def estrategia_40(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR59'] >= 0.0102) & (vars_dict['VAR59'] <= 0.0126)].copy()
    def estrategia_41(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR32'] >= 0.2667) & (vars_dict['VAR32'] <= 0.2909)].copy()
    def estrategia_42(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR34'] >= 0.1294) & (vars_dict['VAR34'] <= 0.1345)].copy()
    def estrategia_43(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR54'] >= 0.0731) & (vars_dict['VAR54'] <= 0.1261)].copy()
    def estrategia_44(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR75'] >= 0.1316) & (vars_dict['VAR75'] <= 0.1757)].copy()
    def estrategia_45(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR20'] >= 0.9665) & (vars_dict['VAR20'] <= 0.9901)].copy()
    def estrategia_46(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR31'] >= 0.0031) & (vars_dict['VAR31'] <= 0.1800)].copy()
    def estrategia_47(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR06'] >= 1.1692) & (vars_dict['VAR06'] <= 1.3194)].copy()
    def estrategia_48(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR04'] >= 0.7579) & (vars_dict['VAR04'] <= 0.8553)].copy()
    def estrategia_49(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR44'] >= 1.3333) & (vars_dict['VAR44'] <= 1.5634)].copy()
    def estrategia_50(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR46'] >= 0.6396) & (vars_dict['VAR46'] <= 0.7500)].copy()
    def estrategia_51(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR23'] >= 0.1429) & (vars_dict['VAR23'] <= 0.1519)].copy()
    def estrategia_52(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR02'] >= 2.2073) & (vars_dict['VAR02'] <= 2.4510)].copy()
    def estrategia_53(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR05'] >= 0.4080) & (vars_dict['VAR05'] <= 0.4530)].copy()
    def estrategia_54(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR70'] >= 1.2073) & (vars_dict['VAR70'] <= 1.4510)].copy()
    def estrategia_55(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR17'] >= 0.8962) & (vars_dict['VAR17'] <= 0.9533)].copy()
    def estrategia_56(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR72'] >= 0.3699) & (vars_dict['VAR72'] <= 0.5165)].copy()
    def estrategia_57(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR37'] >= 0.2100) & (vars_dict['VAR37'] <= 0.2220)].copy()
    def estrategia_58(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR64'] >= 0.5266) & (vars_dict['VAR64'] <= 1.2864)].copy()
    def estrategia_59(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR47'] >= 0.5091) & (vars_dict['VAR47'] <= 0.5625)].copy()
    def estrategia_60(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR49'] >= 1.7778) & (vars_dict['VAR49'] <= 1.9643)].copy()
    def estrategia_61(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR65'] >= 1.9370) & (vars_dict['VAR65'] <= 3.3244)].copy()
    def estrategia_62(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR36'] >= 0.0988) & (vars_dict['VAR36'] <= 0.1113)].copy()
    def estrategia_63(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR11'] >= 0.6721) & (vars_dict['VAR11'] <= 0.7541)].copy()
    def estrategia_64(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR07'] >= 1.3064) & (vars_dict['VAR07'] <= 1.4943)].copy()
    def estrategia_65(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR08'] >= 0.6692) & (vars_dict['VAR08'] <= 0.7655)].copy()
    def estrategia_66(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR62'] >= -10.1447) & (vars_dict['VAR62'] <= -8.9100)].copy()
    def estrategia_67(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR15'] >= 0.5636) & (vars_dict['VAR15'] <= 0.5804)].copy()
    def estrategia_68(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR73'] >= 0.0000) & (vars_dict['VAR73'] <= 0.0316)].copy()
    def estrategia_69(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR18'] >= 0.4000) & (vars_dict['VAR18'] <= 0.4316)].copy()
    def estrategia_70(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR61'] >= 0.0481) & (vars_dict['VAR61'] <= 0.0592)].copy()
    def estrategia_71(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR69'] >= 0.4132) & (vars_dict['VAR69'] <= 0.6065)].copy()
    def estrategia_72(df): return df[(vars_dict['VAR48'] >= 1.3829) & (vars_dict['VAR48'] <= 1.5500) & (vars_dict['VAR57'] >= 0.0000) & (vars_dict['VAR57'] <= 0.0168)].copy()
    def estrategia_73(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR72'] >= 0.4525) & (vars_dict['VAR72'] <= 0.5795)].copy()
    def estrategia_74(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR07'] >= 0.9135) & (vars_dict['VAR07'] <= 0.9363)].copy()
    def estrategia_75(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR73'] >= 0.0637) & (vars_dict['VAR73'] <= 0.0865)].copy()
    def estrategia_76(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR08'] >= 1.0681) & (vars_dict['VAR08'] <= 1.0947)].copy()
    def estrategia_77(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR65'] >= 0.9557) & (vars_dict['VAR65'] <= 1.3046)].copy()
    def estrategia_78(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR57'] >= 0.0334) & (vars_dict['VAR57'] <= 0.0455)].copy()
    def estrategia_79(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR77'] >= 0.3587) & (vars_dict['VAR77'] <= 0.4375)].copy()
    def estrategia_80(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR20'] >= 0.9587) & (vars_dict['VAR20'] <= 1.0188)].copy()
    def estrategia_81(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR31'] >= 0.0000) & (vars_dict['VAR31'] <= 0.1778)].copy()
    def estrategia_82(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR10'] >= 1.0681) & (vars_dict['VAR10'] <= 1.1819)].copy()
    def estrategia_83(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR09'] >= 0.8461) & (vars_dict['VAR09'] <= 0.9363)].copy()
    def estrategia_84(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR21'] >= 0.4599) & (vars_dict['VAR21'] <= 0.5098)].copy()
    def estrategia_85(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR15'] >= 0.4658) & (vars_dict['VAR15'] <= 0.4916)].copy()
    def estrategia_86(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR24'] >= 0.2640) & (vars_dict['VAR24'] <= 0.2692)].copy()
    def estrategia_87(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR54'] >= 0.3534) & (vars_dict['VAR54'] <= 0.4320)].copy()
    def estrategia_88(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR33'] >= 0.1224) & (vars_dict['VAR33'] <= 0.1360)].copy()
    def estrategia_89(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR06'] >= 0.6467) & (vars_dict['VAR06'] <= 0.7447)].copy()
    def estrategia_90(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR04'] >= 1.3429) & (vars_dict['VAR04'] <= 1.5463)].copy()
    def estrategia_91(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR27'] >= 0.1362) & (vars_dict['VAR27'] <= 0.1400)].copy()
    def estrategia_92(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR40'] >= 0.2333) & (vars_dict['VAR40'] <= 0.2511)].copy()
    def estrategia_93(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR67'] >= 0.8011) & (vars_dict['VAR67'] <= 2.7889)].copy()
    def estrategia_94(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR60'] >= 0.0280) & (vars_dict['VAR60'] <= 0.0344)].copy()
    def estrategia_95(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR34'] >= 0.1943) & (vars_dict['VAR34'] <= 0.2859)].copy()
    def estrategia_96(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR37'] >= 0.2708) & (vars_dict['VAR37'] <= 0.3580)].copy()
    def estrategia_97(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR28'] >= 0.1439) & (vars_dict['VAR28'] <= 0.1472)].copy()
    def estrategia_98(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR58'] >= 0.0096) & (vars_dict['VAR58'] <= 0.0193)].copy()
    def estrategia_99(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR39'] >= 0.4432) & (vars_dict['VAR39'] <= 0.5581)].copy()
    def estrategia_100(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR18'] >= 0.5369) & (vars_dict['VAR18'] <= 0.5441)].copy()
    def estrategia_101(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR13'] >= 0.4460) & (vars_dict['VAR13'] <= 0.5182)].copy()
    def estrategia_102(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR61'] >= 0.0442) & (vars_dict['VAR61'] <= 0.0545)].copy()
    def estrategia_103(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR35'] >= 0.1989) & (vars_dict['VAR35'] <= 0.4290)].copy()
    def estrategia_104(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR01'] >= 0.8898) & (vars_dict['VAR01'] <= 1.0476)].copy()
    def estrategia_105(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR03'] >= 0.9545) & (vars_dict['VAR03'] <= 1.1238)].copy()
    def estrategia_106(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR66'] >= 0.9788) & (vars_dict['VAR66'] <= 2.4897)].copy()
    def estrategia_107(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR74'] >= 0.0169) & (vars_dict['VAR74'] <= 0.0370)].copy()
    def estrategia_108(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR48'] >= 0.8376) & (vars_dict['VAR48'] <= 1.0000)].copy()
    def estrategia_109(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR45'] >= 1.0000) & (vars_dict['VAR45'] <= 1.1938)].copy()
    def estrategia_110(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR68'] >= -0.3566) & (vars_dict['VAR68'] <= 0.0000)].copy()
    def estrategia_111(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR44'] >= 0.3765) & (vars_dict['VAR44'] <= 0.7355)].copy()
    def estrategia_112(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR46'] >= 1.3597) & (vars_dict['VAR46'] <= 2.6563)].copy()
    def estrategia_113(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR63'] >= -0.4153) & (vars_dict['VAR63'] <= 0.9078)].copy()
    def estrategia_114(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR59'] >= 0.0421) & (vars_dict['VAR59'] <= 0.0974)].copy()
    def estrategia_115(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR16'] >= 0.3094) & (vars_dict['VAR16'] <= 0.3748)].copy()
    def estrategia_116(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR02'] >= 0.5585) & (vars_dict['VAR02'] <= 0.7871)].copy()
    def estrategia_117(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR05'] >= 1.2705) & (vars_dict['VAR05'] <= 1.7905)].copy()
    def estrategia_118(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR76'] >= 0.4486) & (vars_dict['VAR76'] <= 89.9091)].copy()
    def estrategia_119(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR43'] >= 0.2060) & (vars_dict['VAR43'] <= 0.2174)].copy()
    def estrategia_120(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR36'] >= 0.2137) & (vars_dict['VAR36'] <= 0.2600)].copy()
    def estrategia_121(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR41'] >= 0.0014) & (vars_dict['VAR41'] <= 0.1151)].copy()
    def estrategia_122(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR56'] >= 0.0238) & (vars_dict['VAR56'] <= 0.0390)].copy()
    def estrategia_123(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR62'] >= 2.5023) & (vars_dict['VAR62'] <= 5.9030)].copy()
    def estrategia_124(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR17'] >= 1.0365) & (vars_dict['VAR17'] <= 1.1935)].copy()
    def estrategia_125(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR38'] >= 0.3238) & (vars_dict['VAR38'] <= 0.3486)].copy()
    def estrategia_126(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR69'] >= -4.4381) & (vars_dict['VAR69'] <= -1.1367)].copy()
    def estrategia_127(df):    return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5743)].copy()
    def estrategia_128(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR75'] >= 0.6800) & (vars_dict['VAR75'] <= 89.9091)].copy()
    def estrategia_129(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR42'] >= 0.2067) & (vars_dict['VAR42'] <= 0.2293)].copy()
    def estrategia_130(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR64'] >= -1.3613) & (vars_dict['VAR64'] <= -0.6115)].copy()
    def estrategia_131(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR55'] >= 0.0000) & (vars_dict['VAR55'] <= 0.0213)].copy()
    def estrategia_132(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR22'] >= 0.3899) & (vars_dict['VAR22'] <= 0.4752)].copy()
    def estrategia_133(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR29'] >= 0.1569) & (vars_dict['VAR29'] <= 0.1608)].copy()
    def estrategia_134(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR30'] >= 0.3967) & (vars_dict['VAR30'] <= 2.1094)].copy()
    def estrategia_135(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR11'] >= 1.1405) & (vars_dict['VAR11'] <= 1.2536)].copy()
    def estrategia_136(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR70'] >= 2.3921) & (vars_dict['VAR70'] <= 10.9403)].copy()
    def estrategia_137(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR32'] >= 0.2345) & (vars_dict['VAR32'] <= 0.2429)].copy()
    def estrategia_138(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR19'] >= 0.4043) & (vars_dict['VAR19'] <= 0.4602)].copy()
    def estrategia_139(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR23'] >= 0.0000) & (vars_dict['VAR23'] <= 0.1296)].copy()
    def estrategia_140(df):  return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR71'] >= 0.0000) & (vars_dict['VAR71'] <= 0.0700)].copy()
    def estrategia_141(df): return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) & (vars_dict['VAR25'] >= 0.0000) & (vars_dict['VAR25'] <= 0.1647)].copy()
    def estrategia_142(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR47'] >= 1.6284) & (vars_dict['VAR47'] <= 153.1250)].copy()
    def estrategia_143(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &  (vars_dict['VAR49'] >= 0.0065) & (vars_dict['VAR49'] <= 0.6140)].copy()
    def estrategia_144(df):   return df[(vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1833) &   (vars_dict['VAR12'] >= 0.5698) & (vars_dict['VAR12'] <= 0.5855)].copy()
    def estrategia_145(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR57'] >= 0.1012) & (vars_dict['VAR57'] <= 0.1288)].copy()
    def estrategia_146(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR26'] >= 0.1387) & (vars_dict['VAR26'] <= 0.1718)].copy()
    def estrategia_147(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR59'] >= 0.0357) & (vars_dict['VAR59'] <= 0.0386)].copy()
    def estrategia_148(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR62'] >= 6.4007) & (vars_dict['VAR62'] <= 7.8075)].copy()
    def estrategia_149(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR55'] >= 0.0377) & (vars_dict['VAR55'] <= 0.0470)].copy()
    def estrategia_150(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR73'] >= 0.2000) & (vars_dict['VAR73'] <= 0.2523)].copy()
    def estrategia_151(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR33'] >= 0.2370) & (vars_dict['VAR33'] <= 0.2826)].copy()
    def estrategia_152(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR11'] >= 0.4667) & (vars_dict['VAR11'] <= 0.5258)].copy()
    def estrategia_153(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR71'] >= 0.1490) & (vars_dict['VAR71'] <= 0.1923)].copy()
    def estrategia_154(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR24'] >= 0.0038) & (vars_dict['VAR24'] <= 0.1360)].copy()
    def estrategia_155(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR74'] >= 0.0309) & (vars_dict['VAR74'] <= 0.0663)].copy()
    def estrategia_156(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR58'] >= 0.0161) & (vars_dict['VAR58'] <= 0.0341)].copy()
    def estrategia_157(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR65'] >= 1.9876) & (vars_dict['VAR65'] <= 4.1926)].copy()
    def estrategia_158(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR02'] >= 0.4659) & (vars_dict['VAR02'] <= 0.5378)].copy()
    def estrategia_159(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR05'] >= 1.8594) & (vars_dict['VAR05'] <= 2.1466)].copy()
    def estrategia_160(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR18'] >= 0.4024) & (vars_dict['VAR18'] <= 0.4235)].copy()
    def estrategia_161(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR16'] >= 0.9816) & (vars_dict['VAR16'] <= 1.0659)].copy()
    def estrategia_162(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR21'] >= 0.5455) & (vars_dict['VAR21'] <= 0.5634)].copy()
    def estrategia_163(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR56'] >= 0.1997) & (vars_dict['VAR56'] <= 0.2374)].copy()
    def estrategia_164(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR64'] >= 5.7027) & (vars_dict['VAR64'] <= 6.7678)].copy()
    def estrategia_165(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR27'] >= 0.0021) & (vars_dict['VAR27'] <= 0.0714)].copy()
    def estrategia_166(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR54'] >= 0.2397) & (vars_dict['VAR54'] <= 0.2824)].copy()
    def estrategia_167(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR31'] >= 0.3667) & (vars_dict['VAR31'] <= 0.3909)].copy()
    def estrategia_168(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR12'] >= 0.3526) & (vars_dict['VAR12'] <= 0.3928)].copy()
    def estrategia_169(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR28'] >= 0.1313) & (vars_dict['VAR28'] <= 0.1592)].copy()
    def estrategia_170(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR23'] >= 0.0033) & (vars_dict['VAR23'] <= 0.1391)].copy()
    def estrategia_171(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR08'] >= 1.1459) & (vars_dict['VAR08'] <= 1.3294)].copy()
    def estrategia_172(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR07'] >= 0.7522) & (vars_dict['VAR07'] <= 0.8726)].copy()
    def estrategia_173(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR25'] >= 0.1279) & (vars_dict['VAR25'] <= 0.1541)].copy()
    def estrategia_174(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR34'] >= 0.2000) & (vars_dict['VAR34'] <= 0.2069)].copy()
    def estrategia_175(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR09'] >= 1.1257) & (vars_dict['VAR09'] <= 1.1868)].copy()
    def estrategia_176(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR10'] >= 0.8426) & (vars_dict['VAR10'] <= 0.8884)].copy()
    def estrategia_177(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR66'] >= -2.5417) & (vars_dict['VAR66'] <= -1.7597)].copy()
    def estrategia_178(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR70'] >= 0.3722) & (vars_dict['VAR70'] <= 0.4967)].copy()
    def estrategia_179(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR20'] >= 0.5122) & (vars_dict['VAR20'] <= 0.5759)].copy()
    def estrategia_180(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR40'] >= 0.0922) & (vars_dict['VAR40'] <= 0.1073)].copy()
    def estrategia_181(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR03'] >= 1.0226) & (vars_dict['VAR03'] <= 1.0976)].copy()
    def estrategia_182(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR01'] >= 0.9111) & (vars_dict['VAR01'] <= 0.9779)].copy()
    def estrategia_183(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR15'] >= 0.4933) & (vars_dict['VAR15'] <= 0.5060)].copy()
    def estrategia_184(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR76'] >= 0.3333) & (vars_dict['VAR76'] <= 0.4601)].copy()
    def estrategia_185(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR61'] >= 0.0652) & (vars_dict['VAR61'] <= 0.0744)].copy()
    def estrategia_186(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR22'] >= 0.9522) & (vars_dict['VAR22'] <= 1.0281)].copy()
    def estrategia_187(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR37'] >= 0.0121) & (vars_dict['VAR37'] <= 0.1687)].copy()
    def estrategia_188(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR42'] >= 0.1168) & (vars_dict['VAR42'] <= 0.1368)].copy()
    def estrategia_189(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR46'] >= 2.2917) & (vars_dict['VAR46'] <= 2.9673)].copy()
    def estrategia_190(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR44'] >= 0.3370) & (vars_dict['VAR44'] <= 0.4364)].copy()
    def estrategia_191(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR75'] >= 0.5636) & (vars_dict['VAR75'] <= 0.6630)].copy()
    def estrategia_192(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR29'] >= 0.1350) & (vars_dict['VAR29'] <= 0.1526)].copy()
    def estrategia_193(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR41'] >= 0.0788) & (vars_dict['VAR41'] <= 0.0885)].copy()
    def estrategia_194(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR63'] >= 0.1514) & (vars_dict['VAR63'] <= 0.6521)].copy()
    def estrategia_195(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR14'] >= 0.4267) & (vars_dict['VAR14'] <= 0.4599)].copy()
    def estrategia_196(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR17'] >= 0.4315) & (vars_dict['VAR17'] <= 0.4697)].copy()
    def estrategia_197(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR32'] >= 0.2036) & (vars_dict['VAR32'] <= 0.2216)].copy()
    def estrategia_198(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR36'] >= 0.1904) & (vars_dict['VAR36'] <= 0.1984)].copy()
    def estrategia_199(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR13'] >= 1.1261) & (vars_dict['VAR13'] <= 1.1900)].copy()
    def estrategia_200(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR30'] >= 0.3818) & (vars_dict['VAR30'] <= 0.4364)].copy()
    def estrategia_201(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR60'] >= 0.0184) & (vars_dict['VAR60'] <= 0.0264)].copy()
    def estrategia_202(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR72'] >= 0.5437) & (vars_dict['VAR72'] <= 0.5800)].copy()
    def estrategia_203(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR35'] >= 0.1877) & (vars_dict['VAR35'] <= 0.2067)].copy()
    def estrategia_204(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR04'] >= 0.5909) & (vars_dict['VAR04'] <= 0.7188)].copy()
    def estrategia_205(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR06'] >= 1.3911) & (vars_dict['VAR06'] <= 1.6923)].copy()
    def estrategia_206(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR43'] >= 0.1067) & (vars_dict['VAR43'] <= 0.1166)].copy()
    def estrategia_207(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR49'] >= 0.3556) & (vars_dict['VAR49'] <= 0.4182)].copy()
    def estrategia_208(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR77'] >= 1.3913) & (vars_dict['VAR77'] <= 1.8125)].copy()
    def estrategia_209(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR47'] >= 2.3913) & (vars_dict['VAR47'] <= 2.8125)].copy()
    def estrategia_210(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR69'] >= -1.1797) & (vars_dict['VAR69'] <= -1.0127)].copy()
    def estrategia_211(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR38'] >= 0.1973) & (vars_dict['VAR38'] <= 0.2106)].copy()
    def estrategia_212(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR39'] >= 0.1263) & (vars_dict['VAR39'] <= 0.1587)].copy()
    def estrategia_213(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR45'] >= 0.4479) & (vars_dict['VAR45'] <= 0.9630)].copy()
    def estrategia_214(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR48'] >= 1.0385) & (vars_dict['VAR48'] <= 2.2327)].copy()
    def estrategia_215(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR19'] >= 0.9041) & (vars_dict['VAR19'] <= 0.9616)].copy()
    def estrategia_216(df): return df[(vars_dict['VAR67'] >= 0.9014) & (vars_dict['VAR67'] <= 4.3032) & (vars_dict['VAR68'] >= -0.7427) & (vars_dict['VAR68'] <= -0.4985)].copy()
    def estrategia_217(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR18'] >= 0.3674) & (vars_dict['VAR18'] <= 0.3902)].copy()
    def estrategia_218(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR75'] >= 0.3845) & (vars_dict['VAR75'] <= 0.4103)].copy()
    def estrategia_219(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR01'] >= 1.0750) & (vars_dict['VAR01'] <= 2.3977)].copy()
    def estrategia_220(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR03'] >= 0.4171) & (vars_dict['VAR03'] <= 0.9302)].copy()
    def estrategia_221(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR63'] >= -9.6729) & (vars_dict['VAR63'] <= -0.5807)].copy()
    def estrategia_222(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR62'] >= -11.1028) & (vars_dict['VAR62'] <= 6.5526)].copy()
    def estrategia_223(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR55'] >= 0.0817) & (vars_dict['VAR55'] <= 0.0985)].copy()
    def estrategia_224(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR02'] >= 0.5441) & (vars_dict['VAR02'] <= 3.0409)].copy()
    def estrategia_225(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR05'] >= 0.3288) & (vars_dict['VAR05'] <= 1.8378)].copy()
    def estrategia_226(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR22'] >= 1.2346) & (vars_dict['VAR22'] <= 1.2868)].copy()
    def estrategia_227(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR37'] >= 0.1554) & (vars_dict['VAR37'] <= 0.1826)].copy()
    def estrategia_228(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR57'] >= 0.0966) & (vars_dict['VAR57'] <= 0.1258)].copy()
    def estrategia_229(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR54'] >= 0.0057) & (vars_dict['VAR54'] <= 0.2298)].copy()
    def estrategia_230(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR70'] >= 0.0153) & (vars_dict['VAR70'] <= 0.4593)].copy()
    def estrategia_231(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR77'] >= 0.0000) & (vars_dict['VAR77'] <= 0.4774)].copy()
    def estrategia_232(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR20'] >= 0.2581) & (vars_dict['VAR20'] <= 0.3056)].copy()
    def estrategia_233(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR27'] >= 0.1033) & (vars_dict['VAR27'] <= 0.1100)].copy()
    def estrategia_234(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR61'] >= 0.0000) & (vars_dict['VAR61'] <= 0.0204)].copy()
    def estrategia_235(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR41'] >= 0.1100) & (vars_dict['VAR41'] <= 0.1174)].copy()
    def estrategia_236(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR33'] >= 0.1046) & (vars_dict['VAR33'] <= 0.1232)].copy()
    def estrategia_237(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR14'] >= 0.6487) & (vars_dict['VAR14'] <= 1.3016)].copy()
    def estrategia_238(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR24'] >= 0.1552) & (vars_dict['VAR24'] <= 0.1750)].copy()
    def estrategia_239(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR28'] >= 0.0650) & (vars_dict['VAR28'] <= 0.0750)].copy()
    def estrategia_240(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR23'] >= 0.0874) & (vars_dict['VAR23'] <= 0.1614)].copy()
    def estrategia_241(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR17'] >= 0.4267) & (vars_dict['VAR17'] <= 1.0585)].copy()
    def estrategia_242(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR43'] >= 0.1108) & (vars_dict['VAR43'] <= 0.1211)].copy()
    def estrategia_243(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR47'] >= 1.0000) & (vars_dict['VAR47'] <= 1.4467)].copy()
    def estrategia_244(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR49'] >= 0.6912) & (vars_dict['VAR49'] <= 1.0000)].copy()
    def estrategia_245(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR10'] >= 0.3403) & (vars_dict['VAR10'] <= 0.6124)].copy()
    def estrategia_246(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR09'] >= 1.6329) & (vars_dict['VAR09'] <= 2.9389)].copy()
    def estrategia_247(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR74'] >= 0.6329) & (vars_dict['VAR74'] <= 1.9389)].copy()
    def estrategia_248(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR44'] >= 0.5939) & (vars_dict['VAR44'] <= 0.6222)].copy()
    def estrategia_249(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR46'] >= 1.6071) & (vars_dict['VAR46'] <= 1.6837)].copy()
    def estrategia_250(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR13'] >= 0.0000) & (vars_dict['VAR13'] <= 0.7688)].copy()
    def estrategia_251(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR65'] >= -4.0022) & (vars_dict['VAR65'] <= -3.0790)].copy()
    def estrategia_252(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR73'] >= 0.1153) & (vars_dict['VAR73'] <= 0.1823)].copy()
    def estrategia_253(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR40'] >= 0.0905) & (vars_dict['VAR40'] <= 0.1067)].copy()
    def estrategia_254(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR35'] >= 0.0804) & (vars_dict['VAR35'] <= 0.1097)].copy()
    def estrategia_255(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR66'] >= -14.9908) & (vars_dict['VAR66'] <= -7.0382)].copy()
    def estrategia_256(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR76'] >= 0.3333) & (vars_dict['VAR76'] <= 0.4806)].copy()
    def estrategia_257(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR71'] >= 0.3161) & (vars_dict['VAR71'] <= 0.3784)].copy()
    def estrategia_258(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR31'] >= 0.0040) & (vars_dict['VAR31'] <= 0.2341)].copy()
    def estrategia_259(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR56'] >= 0.0000) & (vars_dict['VAR56'] <= 0.2391)].copy()
    def estrategia_260(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR42'] >= 0.0553) & (vars_dict['VAR42'] <= 0.0638)].copy()
    def estrategia_261(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR69'] >= -0.5433) & (vars_dict['VAR69'] <= 0.0000)].copy()
    def estrategia_262(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR15'] >= 0.4585) & (vars_dict['VAR15'] <= 0.4844)].copy()
    def estrategia_263(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR06'] >= 2.3463) & (vars_dict['VAR06'] <= 2.5294)].copy()
    def estrategia_264(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR04'] >= 0.3953) & (vars_dict['VAR04'] <= 0.4262)].copy()
    def estrategia_265(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR32'] >= 0.0018) & (vars_dict['VAR32'] <= 0.0866)].copy()
    def estrategia_266(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR68'] >= -0.6969) & (vars_dict['VAR68'] <= -0.4653)].copy()
    def estrategia_267(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR29'] >= 0.0865) & (vars_dict['VAR29'] <= 0.0963)].copy()
    def estrategia_268(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR64'] >= -13.0557) & (vars_dict['VAR64'] <= 6.7543)].copy()
    def estrategia_269(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR12'] >= 0.3535) & (vars_dict['VAR12'] <= 0.3795)].copy()
    def estrategia_270(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR30'] >= 0.2138) & (vars_dict['VAR30'] <= 0.3071)].copy()
    def estrategia_271(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR08'] >= 0.5068) & (vars_dict['VAR08'] <= 0.5896)].copy()
    def estrategia_272(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR07'] >= 1.6962) & (vars_dict['VAR07'] <= 1.9733)].copy()
    def estrategia_273(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR25'] >= 0.0739) & (vars_dict['VAR25'] <= 0.0838)].copy()
    def estrategia_274(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR72'] >= 0.5472) & (vars_dict['VAR72'] <= 0.5745)].copy()
    def estrategia_275(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR60'] >= 0.0124) & (vars_dict['VAR60'] <= 0.0171)].copy()
    def estrategia_276(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR34'] >= 0.2000) & (vars_dict['VAR34'] <= 0.2094)].copy()
    def estrategia_277(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR21'] >= 0.5288) & (vars_dict['VAR21'] <= 0.5512)].copy()
    def estrategia_278(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR36'] >= 0.1614) & (vars_dict['VAR36'] <= 0.1750)].copy()
    def estrategia_279(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR45'] >= 1.3000) & (vars_dict['VAR45'] <= 1.4545)].copy()
    def estrategia_280(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR16'] >= 1.3722) & (vars_dict['VAR16'] <= 1.4860)].copy()
    def estrategia_281(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR39'] >= 0.0935) & (vars_dict['VAR39'] <= 0.1065)].copy()
    def estrategia_282(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR67'] >= 0.6860) & (vars_dict['VAR67'] <= 0.8867)].copy()
    def estrategia_283(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR48'] >= 0.6875) & (vars_dict['VAR48'] <= 0.7692)].copy()
    def estrategia_284(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR19'] >= 0.9626) & (vars_dict['VAR19'] <= 1.0172)].copy()
    def estrategia_285(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR58'] >= 0.2627) & (vars_dict['VAR58'] <= 0.5356)].copy()
    def estrategia_286(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR59'] >= 0.0476) & (vars_dict['VAR59'] <= 0.0536)].copy()
    def estrategia_287(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR38'] >= 0.1858) & (vars_dict['VAR38'] <= 0.2000)].copy()
    def estrategia_288(df): return df[(vars_dict['VAR11'] >= 0.0000) & (vars_dict['VAR11'] <= 0.4634) & (vars_dict['VAR26'] >= 0.0230) & (vars_dict['VAR26'] <= 0.0471)].copy()
    def estrategia_289(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR76'] >= 0.2917) & (vars_dict['VAR76'] <= 0.3542)].copy()
    def estrategia_290(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR75'] >= 0.2703) & (vars_dict['VAR75'] <= 0.3000)].copy()
    def estrategia_291(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR37'] >= 0.1829) & (vars_dict['VAR37'] <= 0.1970)].copy()
    def estrategia_292(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR11'] >= 0.7265) & (vars_dict['VAR11'] <= 0.7749)].copy()
    def estrategia_293(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR16'] >= 0.6986) & (vars_dict['VAR16'] <= 0.7439)].copy()
    def estrategia_294(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR39'] >= 0.2000) & (vars_dict['VAR39'] <= 0.2207)].copy()
    def estrategia_295(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR23'] >= 0.1276) & (vars_dict['VAR23'] <= 0.1503)].copy()
    def estrategia_296(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR34'] >= 0.1255) & (vars_dict['VAR34'] <= 0.1357)].copy()
    def estrategia_297(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR33'] >= 0.2170) & (vars_dict['VAR33'] <= 0.3917)].copy()
    def estrategia_298(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR69'] >= -3.8573) & (vars_dict['VAR69'] <= -1.3774)].copy()
    def estrategia_299(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR22'] >= 0.7111) & (vars_dict['VAR22'] <= 0.7808)].copy()
    def estrategia_300(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR21'] >= 0.0000) & (vars_dict['VAR21'] <= 0.5200)].copy()
    def estrategia_301(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR60'] >= 0.0228) & (vars_dict['VAR60'] <= 0.0268)].copy()
    def estrategia_302(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR03'] >= 0.7125) & (vars_dict['VAR03'] <= 0.7771)].copy()
    def estrategia_303(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR01'] >= 1.2868) & (vars_dict['VAR01'] <= 1.4035)].copy()
    def estrategia_304(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR29'] >= 0.1388) & (vars_dict['VAR29'] <= 0.1454)].copy()
    def estrategia_305(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR70'] >= 0.6509) & (vars_dict['VAR70'] <= 1.0202)].copy()
    def estrategia_306(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR31'] >= 0.3929) & (vars_dict['VAR31'] <= 0.6563)].copy()
    def estrategia_307(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR66'] >= -0.1504) & (vars_dict['VAR66'] <= 11.3613)].copy()
    def estrategia_308(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR09'] >= 0.5941) & (vars_dict['VAR09'] <= 1.0103)].copy()
    def estrategia_309(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR10'] >= 0.9898) & (vars_dict['VAR10'] <= 1.6832)].copy()
    def estrategia_310(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR30'] >= 0.4574) & (vars_dict['VAR30'] <= 1.3871)].copy()
    def estrategia_311(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR35'] >= 0.2000) & (vars_dict['VAR35'] <= 0.4000)].copy()
    def estrategia_312(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR40'] >= 0.1188) & (vars_dict['VAR40'] <= 0.1227)].copy()
    def estrategia_313(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR32'] >= 0.2133) & (vars_dict['VAR32'] <= 0.3375)].copy()
    def estrategia_314(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR57'] >= 0.2791) & (vars_dict['VAR57'] <= 0.6137)].copy()
    def estrategia_315(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR12'] >= 0.4507) & (vars_dict['VAR12'] <= 0.4730)].copy()
    def estrategia_316(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR71'] >= 0.3139) & (vars_dict['VAR71'] <= 0.4219)].copy()
    def estrategia_317(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR42'] >= 0.1071) & (vars_dict['VAR42'] <= 0.1103)].copy()
    def estrategia_318(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR67'] >= 0.0353) & (vars_dict['VAR67'] <= 0.1669)].copy()
    def estrategia_319(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR04'] >= 0.3619) & (vars_dict['VAR04'] <= 0.5324)].copy()
    def estrategia_320(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR06'] >= 1.8782) & (vars_dict['VAR06'] <= 2.7632)].copy()
    def estrategia_321(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR41'] >= 0.1766) & (vars_dict['VAR41'] <= 0.2296)].copy()
    def estrategia_322(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR14'] >= 0.0000) & (vars_dict['VAR14'] <= 0.4341)].copy()
    def estrategia_323(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR15'] >= 0.0000) & (vars_dict['VAR15'] <= 0.5105)].copy()
    def estrategia_324(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR63'] >= -3.1860) & (vars_dict['VAR63'] <= -2.3053)].copy()
    def estrategia_325(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR61'] >= 0.0530) & (vars_dict['VAR61'] <= 0.1348)].copy()
    def estrategia_326(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR44'] >= 0.8750) & (vars_dict['VAR44'] <= 0.9655)].copy()
    def estrategia_327(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR77'] >= 0.9271) & (vars_dict['VAR77'] <= 131.4324)].copy()
    def estrategia_328(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR47'] >= 1.8286) & (vars_dict['VAR47'] <= 132.4324)].copy()
    def estrategia_329(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR49'] >= 0.0076) & (vars_dict['VAR49'] <= 0.5469)].copy()
    def estrategia_330(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR72'] >= 0.1375) & (vars_dict['VAR72'] <= 0.1899)].copy()
    def estrategia_331(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR13'] >= 1.0428) & (vars_dict['VAR13'] <= 1.5570)].copy()
    def estrategia_332(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR07'] >= 1.7516) & (vars_dict['VAR07'] <= 3.8843)].copy()
    def estrategia_333(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR08'] >= 0.2574) & (vars_dict['VAR08'] <= 0.5709)].copy()
    def estrategia_334(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR73'] >= 0.7516) & (vars_dict['VAR73'] <= 2.8843)].copy()
    def estrategia_335(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR38'] >= 0.2536) & (vars_dict['VAR38'] <= 0.2630)].copy()
    def estrategia_336(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4488)].copy()
    def estrategia_337(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR19'] >= 0.9534) & (vars_dict['VAR19'] <= 1.6644)].copy()
    def estrategia_338(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR55'] >= 0.2015) & (vars_dict['VAR55'] <= 0.2827)].copy()
    def estrategia_339(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR43'] >= 0.1703) & (vars_dict['VAR43'] <= 0.1771)].copy()
    def estrategia_340(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR17'] >= 0.0000) & (vars_dict['VAR17'] <= 0.4205)].copy()
    def estrategia_341(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR65'] >= -17.0581) & (vars_dict['VAR65'] <= -7.8998)].copy()
    def estrategia_342(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR28'] >= 0.1314) & (vars_dict['VAR28'] <= 0.2157)].copy()
    def estrategia_343(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR36'] >= 0.2188) & (vars_dict['VAR36'] <= 0.2682)].copy()
    def estrategia_344(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR56'] >= 0.1608) & (vars_dict['VAR56'] <= 0.1920)].copy()
    def estrategia_345(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR45'] >= 0.7692) & (vars_dict['VAR45'] <= 0.8333)].copy()
    def estrategia_346(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR48'] >= 1.2000) & (vars_dict['VAR48'] <= 1.3000)].copy()
    def estrategia_347(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR02'] >= 0.1733) & (vars_dict['VAR02'] <= 0.4523)].copy()
    def estrategia_348(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR05'] >= 2.2111) & (vars_dict['VAR05'] <= 5.7718)].copy()
    def estrategia_349(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR46'] >= 1.0357) & (vars_dict['VAR46'] <= 1.1429)].copy()
    def estrategia_350(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR18'] >= 0.3634) & (vars_dict['VAR18'] <= 0.4000)].copy()
    def estrategia_351(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR64'] >= 4.5957) & (vars_dict['VAR64'] <= 5.4841)].copy()
    def estrategia_352(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR26'] >= 0.1440) & (vars_dict['VAR26'] <= 0.2091)].copy()
    def estrategia_353(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR24'] >= 0.2586) & (vars_dict['VAR24'] <= 0.3500)].copy()
    def estrategia_354(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR27'] >= 0.1046) & (vars_dict['VAR27'] <= 0.1103)].copy()
    def estrategia_355(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR74'] >= 0.7276) & (vars_dict['VAR74'] <= 1.4762)].copy()
    def estrategia_356(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR58'] >= 0.2103) & (vars_dict['VAR58'] <= 0.2384)].copy()
    def estrategia_357(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR59'] >= 0.0175) & (vars_dict['VAR59'] <= 0.0212)].copy()
    def estrategia_358(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR54'] >= 0.3534) & (vars_dict['VAR54'] <= 0.8466)].copy()
    def estrategia_359(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR62'] >= 8.0512) & (vars_dict['VAR62'] <= 15.5057)].copy()
    def estrategia_360(df): return df[(vars_dict['VAR25'] >= 0.1190) & (vars_dict['VAR25'] <= 0.1580) & (vars_dict['VAR68'] >= 0.5556) & (vars_dict['VAR68'] <= 0.7002)].copy()
    def estrategia_361(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR26'] >= 0.1382) & (vars_dict['VAR26'] <= 0.1780)].copy()
    def estrategia_362(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR44'] >= 0.5676) & (vars_dict['VAR44'] <= 0.6000)].copy()
    def estrategia_363(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR40'] >= 0.0908) & (vars_dict['VAR40'] <= 0.1084)].copy()
    def estrategia_364(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR46'] >= 1.6667) & (vars_dict['VAR46'] <= 1.7619)].copy()
    def estrategia_365(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR54'] >= 0.2314) & (vars_dict['VAR54'] <= 0.2727)].copy()
    def estrategia_366(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR62'] >= 6.6010) & (vars_dict['VAR62'] <= 7.7652)].copy()
    def estrategia_367(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR32'] >= 0.2070) & (vars_dict['VAR32'] <= 0.2331)].copy()
    def estrategia_368(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR60'] >= 0.0149) & (vars_dict['VAR60'] <= 0.0203)].copy()
    def estrategia_369(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR20'] >= 0.2567) & (vars_dict['VAR20'] <= 0.3031)].copy()
    def estrategia_370(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR14'] >= 0.4250) & (vars_dict['VAR14'] <= 0.4571)].copy()
    def estrategia_371(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR12'] >= 0.5644) & (vars_dict['VAR12'] <= 0.6590)].copy()
    def estrategia_372(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR72'] >= 0.4853) & (vars_dict['VAR72'] <= 0.5175)].copy()
    def estrategia_373(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR74'] >= 0.1333) & (vars_dict['VAR74'] <= 0.1739)].copy()
    def estrategia_374(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR08'] >= 1.1194) & (vars_dict['VAR08'] <= 1.3143)].copy()
    def estrategia_375(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR07'] >= 0.7609) & (vars_dict['VAR07'] <= 0.8933)].copy()
    def estrategia_376(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR63'] >= 2.3859) & (vars_dict['VAR63'] <= 2.8839)].copy()
    def estrategia_377(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR06'] >= 1.9415) & (vars_dict['VAR06'] <= 2.0718)].copy()
    def estrategia_378(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR04'] >= 0.4827) & (vars_dict['VAR04'] <= 0.5151)].copy()
    def estrategia_379(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR43'] >= 0.1038) & (vars_dict['VAR43'] <= 0.1141)].copy()
    def estrategia_380(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR55'] >= 0.0833) & (vars_dict['VAR55'] <= 0.1011)].copy()
    def estrategia_381(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR65'] >= 0.0000) & (vars_dict['VAR65'] <= 1.7246)].copy()
    def estrategia_382(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR75'] >= 0.3714) & (vars_dict['VAR75'] <= 0.4054)].copy()
    def estrategia_383(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR33'] >= 0.2326) & (vars_dict['VAR33'] <= 0.2836)].copy()
    def estrategia_384(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR41'] >= 0.1108) & (vars_dict['VAR41'] <= 0.1179)].copy()
    def estrategia_385(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR18'] >= 0.5239) & (vars_dict['VAR18'] <= 0.5865)].copy()
    def estrategia_386(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR42'] >= 0.0890) & (vars_dict['VAR42'] <= 0.1027)].copy()
    def estrategia_387(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR03'] >= 1.1777) & (vars_dict['VAR03'] <= 1.2381)].copy()
    def estrategia_388(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR01'] >= 0.8077) & (vars_dict['VAR01'] <= 0.8491)].copy()
    def estrategia_389(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR76'] >= 0.2727) & (vars_dict['VAR76'] <= 0.3714)].copy()
    def estrategia_390(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR31'] >= 0.3655) & (vars_dict['VAR31'] <= 0.3909)].copy()
    def estrategia_391(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR73'] >= 0.0994) & (vars_dict['VAR73'] <= 0.1620)].copy()
    def estrategia_392(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR34'] >= 0.1985) & (vars_dict['VAR34'] <= 0.2064)].copy()
    def estrategia_393(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR66'] >= 1.4696) & (vars_dict['VAR66'] <= 3.2512)].copy()
    def estrategia_394(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR11'] >= 0.3525) & (vars_dict['VAR11'] <= 0.3827)].copy()
    def estrategia_395(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR27'] >= 0.1155) & (vars_dict['VAR27'] <= 0.1233)].copy()
    def estrategia_396(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR36'] >= 0.1950) & (vars_dict['VAR36'] <= 0.2036)].copy()
    def estrategia_397(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR68'] >= -0.5571) & (vars_dict['VAR68'] <= -0.4102)].copy()
    def estrategia_398(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR58'] >= 0.0673) & (vars_dict['VAR58'] <= 0.0895)].copy()
    def estrategia_399(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR45'] >= 0.0143) & (vars_dict['VAR45'] <= 1.0000)].copy()
    def estrategia_400(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR48'] >= 1.0000) & (vars_dict['VAR48'] <= 70.0000)].copy()
    def estrategia_401(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR23'] >= 0.2360) & (vars_dict['VAR23'] <= 0.2701)].copy()
    def estrategia_402(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR59'] >= 0.0480) & (vars_dict['VAR59'] <= 0.0538)].copy()
    def estrategia_403(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR22'] >= 1.0055) & (vars_dict['VAR22'] <= 1.0723)].copy()
    def estrategia_404(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR16'] >= 0.8992) & (vars_dict['VAR16'] <= 1.0000)].copy()
    def estrategia_405(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR25'] >= 0.1070) & (vars_dict['VAR25'] <= 0.1247)].copy()
    def estrategia_406(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR61'] >= 0.0632) & (vars_dict['VAR61'] <= 0.0727)].copy()
    def estrategia_407(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR57'] >= 0.0852) & (vars_dict['VAR57'] <= 0.1145)].copy()
    def estrategia_408(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR56'] >= 0.0093) & (vars_dict['VAR56'] <= 0.2253)].copy()
    def estrategia_409(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR17'] >= 0.3185) & (vars_dict['VAR17'] <= 0.3463)].copy()
    def estrategia_410(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR37'] >= 0.1056) & (vars_dict['VAR37'] <= 0.1784)].copy()
    def estrategia_411(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR71'] >= 0.1522) & (vars_dict['VAR71'] <= 0.1951)].copy()
    def estrategia_412(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR64'] >= -10.6640) & (vars_dict['VAR64'] <= 6.3977)].copy()
    def estrategia_413(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR69'] >= -2.0815) & (vars_dict['VAR69'] <= -1.8111)].copy()
    def estrategia_414(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR67'] >= 1.3639) & (vars_dict['VAR67'] <= 1.5343)].copy()
    def estrategia_415(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR77'] >= 0.0000) & (vars_dict['VAR77'] <= 0.6667)].copy()
    def estrategia_416(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR28'] >= 0.0615) & (vars_dict['VAR28'] <= 0.0744)].copy()
    def estrategia_417(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR13'] >= 1.0298) & (vars_dict['VAR13'] <= 1.0699)].copy()
    def estrategia_418(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR49'] >= 0.3840) & (vars_dict['VAR49'] <= 0.4410)].copy()
    def estrategia_419(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR47'] >= 2.2674) & (vars_dict['VAR47'] <= 2.6042)].copy()
    def estrategia_420(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR09'] >= 0.8056) & (vars_dict['VAR09'] <= 0.9078)].copy()
    def estrategia_421(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR10'] >= 1.1016) & (vars_dict['VAR10'] <= 1.2414)].copy()
    def estrategia_422(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR38'] >= 0.0738) & (vars_dict['VAR38'] <= 0.1364)].copy()
    def estrategia_423(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR29'] >= 0.1347) & (vars_dict['VAR29'] <= 0.1533)].copy()
    def estrategia_424(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR15'] >= 0.5429) & (vars_dict['VAR15'] <= 0.5667)].copy()
    def estrategia_425(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR21'] >= 0.5455) & (vars_dict['VAR21'] <= 0.5622)].copy()
    def estrategia_426(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR30'] >= 0.5476) & (vars_dict['VAR30'] <= 0.6222)].copy()
    def estrategia_427(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR35'] >= 0.2043) & (vars_dict['VAR35'] <= 0.2310)].copy()
    def estrategia_428(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR05'] >= 1.9802) & (vars_dict['VAR05'] <= 2.1212)].copy()
    def estrategia_429(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR70'] >= 0.4950) & (vars_dict['VAR70'] <= 0.5286)].copy()
    def estrategia_430(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR39'] >= 0.0016) & (vars_dict['VAR39'] <= 0.0169)].copy()
    def estrategia_431(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR24'] >= 0.2472) & (vars_dict['VAR24'] <= 0.2684)].copy()
    def estrategia_432(df): return df[(vars_dict['VAR02'] >= 0.0225) & (vars_dict['VAR02'] <= 0.5050) & (vars_dict['VAR19'] >= 1.0412) & (vars_dict['VAR19'] <= 1.1012)].copy()
    def estrategia_432(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR57'] >= 0.0313) & (vars_dict['VAR57'] <= 0.0474)].copy()
    def estrategia_433(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR60'] >= 0.0203) & (vars_dict['VAR60'] <= 0.0251)].copy()
    def estrategia_434(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR33'] >= 0.1503) & (vars_dict['VAR33'] <= 0.1547)].copy()
    def estrategia_435(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR58'] >= 0.0414) & (vars_dict['VAR58'] <= 0.0644)].copy()
    def estrategia_436(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR20'] >= 0.8760) & (vars_dict['VAR20'] <= 0.9076)].copy()
    def estrategia_437(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR66'] >= -1.6450) & (vars_dict['VAR66'] <= -0.6756)].copy()
    def estrategia_438(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR09'] >= 1.0471) & (vars_dict['VAR09'] <= 1.1160)].copy()
    def estrategia_439(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR10'] >= 0.8960) & (vars_dict['VAR10'] <= 0.9550)].copy()
    def estrategia_440(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR43'] >= 0.2120) & (vars_dict['VAR43'] <= 0.2267)].copy()
    def estrategia_441(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR41'] >= 0.1928) & (vars_dict['VAR41'] <= 0.2078)].copy()
    def estrategia_442(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR37'] >= 0.2200) & (vars_dict['VAR37'] <= 0.2278)].copy()
    def estrategia_443(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR69'] >= 1.0675) & (vars_dict['VAR69'] <= 1.4210)].copy()
    def estrategia_444(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR56'] >= 0.0275) & (vars_dict['VAR56'] <= 0.0433)].copy()
    def estrategia_445(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR28'] >= 0.1326) & (vars_dict['VAR28'] <= 0.1446)].copy()
    def estrategia_446(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR23'] >= 0.1640) & (vars_dict['VAR23'] <= 0.1683)].copy()
    def estrategia_447(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR47'] >= 0.5677) & (vars_dict['VAR47'] <= 0.6571)].copy()
    def estrategia_448(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR49'] >= 1.5217) & (vars_dict['VAR49'] <= 1.7614)].copy()
    def estrategia_449(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR38'] >= 0.2500) & (vars_dict['VAR38'] <= 0.2731)].copy()
    def estrategia_450(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR21'] >= 0.6028) & (vars_dict['VAR21'] <= 0.6127)].copy()
    def estrategia_451(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR24'] >= 0.2118) & (vars_dict['VAR24'] <= 0.2250)].copy()
    def estrategia_452(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR25'] >= 0.2928) & (vars_dict['VAR25'] <= 0.3555)].copy()
    def estrategia_453(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR74'] >= 0.0787) & (vars_dict['VAR74'] <= 0.1257)].copy()
    def estrategia_454(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR68'] >= 0.6821) & (vars_dict['VAR68'] <= 0.8400)].copy()
    def estrategia_455(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR73'] >= 0.0625) & (vars_dict['VAR73'] <= 0.0913)].copy()
    def estrategia_456(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR39'] >= 0.3989) & (vars_dict['VAR39'] <= 0.5000)].copy()
    def estrategia_457(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR76'] >= 0.1957) & (vars_dict['VAR76'] <= 0.2258)].copy()
    def estrategia_458(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR45'] >= 0.7538) & (vars_dict['VAR45'] <= 0.7857)].copy()
    def estrategia_459(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR48'] >= 1.2727) & (vars_dict['VAR48'] <= 1.3265)].copy()
    def estrategia_460(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR03'] >= 0.7086) & (vars_dict['VAR03'] <= 0.7533)].copy()
    def estrategia_461(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR01'] >= 1.3274) & (vars_dict['VAR01'] <= 1.4113)].copy()
    def estrategia_462(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR36'] >= 0.1514) & (vars_dict['VAR36'] <= 0.1585)].copy()
    def estrategia_463(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR59'] >= 0.0093) & (vars_dict['VAR59'] <= 0.0124)].copy()
    def estrategia_464(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR32'] >= 0.2633) & (vars_dict['VAR32'] <= 0.2867)].copy()
    def estrategia_465(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR62'] >= -7.5954) & (vars_dict['VAR62'] <= -5.8964)].copy()
    def estrategia_466(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR18'] >= 0.5139) & (vars_dict['VAR18'] <= 0.5313)].copy()
    def estrategia_467(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR44'] >= 0.7941) & (vars_dict['VAR44'] <= 0.8710)].copy()
    def estrategia_468(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR46'] >= 1.1481) & (vars_dict['VAR46'] <= 1.2593)].copy()
    def estrategia_469(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR67'] >= 0.2738) & (vars_dict['VAR67'] <= 0.4436)].copy()
    def estrategia_470(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR19'] >= 0.5986) & (vars_dict['VAR19'] <= 0.6445)].copy()
    def estrategia_471(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR02'] >= 1.7847) & (vars_dict['VAR02'] <= 2.1471)].copy()
    def estrategia_472(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR05'] >= 0.4657) & (vars_dict['VAR05'] <= 0.5603)].copy()
    def estrategia_473(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR17'] >= 0.8714) & (vars_dict['VAR17'] <= 0.9702)].copy()
    def estrategia_474(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR27'] >= 0.1224) & (vars_dict['VAR27'] <= 0.1277)].copy()
    def estrategia_475(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR04'] >= 0.8449) & (vars_dict['VAR04'] <= 0.9286)].copy()
    def estrategia_476(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR06'] >= 1.0769) & (vars_dict['VAR06'] <= 1.1835)].copy()
    def estrategia_477(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR31'] >= 0.2414) & (vars_dict['VAR31'] <= 0.2500)].copy()
    def estrategia_478(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR12'] >= 0.5268) & (vars_dict['VAR12'] <= 0.5514)].copy()
    def estrategia_479(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR26'] >= 0.1366) & (vars_dict['VAR26'] <= 0.1496)].copy()
    def estrategia_480(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR77'] >= 0.0000) & (vars_dict['VAR77'] <= 0.0741)].copy()
    def estrategia_481(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR55'] >= 0.1242) & (vars_dict['VAR55'] <= 0.1484)].copy()
    def estrategia_482(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR34'] >= 0.1232) & (vars_dict['VAR34'] <= 0.1307)].copy()
    def estrategia_483(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR11'] >= 0.8389) & (vars_dict['VAR11'] <= 0.9106)].copy()
    def estrategia_484(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR65'] >= 1.5261) & (vars_dict['VAR65'] <= 2.5026)].copy()
    def estrategia_485(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR64'] >= -0.9699) & (vars_dict['VAR64'] <= -0.2287)].copy()
    def estrategia_486(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR63'] >= -4.2424) & (vars_dict['VAR63'] <= -3.5474)].copy()
    def estrategia_487(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR72'] >= 0.0901) & (vars_dict['VAR72'] <= 0.1449)].copy()
    def estrategia_488(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR75'] >= 0.1250) & (vars_dict['VAR75'] <= 0.1714)].copy()
    def estrategia_489(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR15'] >= 0.5408) & (vars_dict['VAR15'] <= 0.5515)].copy()
    def estrategia_490(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR08'] >= 1.1111) & (vars_dict['VAR08'] <= 1.1837)].copy()
    def estrategia_491(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR07'] >= 0.8448) & (vars_dict['VAR07'] <= 0.9000)].copy()
    def estrategia_492(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR42'] >= 0.1200) & (vars_dict['VAR42'] <= 0.1368)].copy()
    def estrategia_493(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR61'] >= 0.0000) & (vars_dict['VAR61'] <= 0.0051)].copy()
    def estrategia_494(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR16'] >= 0.5944) & (vars_dict['VAR16'] <= 0.6738)].copy()
    def estrategia_495(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR40'] >= 0.1338) & (vars_dict['VAR40'] <= 0.1542)].copy()
    def estrategia_496(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR54'] >= 0.0000) & (vars_dict['VAR54'] <= 0.0350)].copy()
    def estrategia_497(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR30'] >= 0.1736) & (vars_dict['VAR30'] <= 0.1896)].copy()
    def estrategia_498(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR70'] >= 0.8160) & (vars_dict['VAR70'] <= 1.1471)].copy()
    def estrategia_499(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR13'] >= 0.6331) & (vars_dict['VAR13'] <= 0.6747)].copy()
    def estrategia_500(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR71'] >= 0.3412) & (vars_dict['VAR71'] <= 0.4228)].copy()
    def estrategia_501(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR22'] >= 0.5915) & (vars_dict['VAR22'] <= 0.6577)].copy()
    def estrategia_502(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR14'] >= 0.9004) & (vars_dict['VAR14'] <= 0.9529)].copy()
    def estrategia_503(df): return df[(vars_dict['VAR35'] >= 0.1192) & (vars_dict['VAR35'] <= 0.1380) & (vars_dict['VAR29'] >= 0.1545) & (vars_dict['VAR29'] <= 0.1591)].copy()
    def estrategia_504(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR16'] >= 0.6985) & (vars_dict['VAR16'] <= 0.7836)].copy()
    def estrategia_505(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR22'] >= 0.7533) & (vars_dict['VAR22'] <= 0.8326)].copy()
    def estrategia_506(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR38'] >= 0.2462) & (vars_dict['VAR38'] <= 0.2704)].copy()
    def estrategia_507(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR37'] >= 0.1775) & (vars_dict['VAR37'] <= 0.2000)].copy()
    def estrategia_508(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR41'] >= 0.1432) & (vars_dict['VAR41'] <= 0.1537)].copy()
    def estrategia_509(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR19'] >= 0.6168) & (vars_dict['VAR19'] <= 0.6348)].copy()
    def estrategia_510(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR13'] >= 0.6412) & (vars_dict['VAR13'] <= 0.6642)].copy()
    def estrategia_511(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR39'] >= 0.1779) & (vars_dict['VAR39'] <= 0.2231)].copy()
    def estrategia_512(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR67'] >= 0.1980) & (vars_dict['VAR67'] <= 0.3581)].copy()
    def estrategia_513(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR24'] >= 0.2064) & (vars_dict['VAR24'] <= 0.2281)].copy()
    def estrategia_514(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR25'] >= 0.0971) & (vars_dict['VAR25'] <= 0.1286)].copy()
    def estrategia_515(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR29'] >= 0.1213) & (vars_dict['VAR29'] <= 0.1341)].copy()
    def estrategia_516(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR20'] >= 0.8731) & (vars_dict['VAR20'] <= 1.4915)].copy()
    def estrategia_517(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR54'] >= 0.0392) & (vars_dict['VAR54'] <= 0.0573)].copy()
    def estrategia_518(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR32'] >= 0.2024) & (vars_dict['VAR32'] <= 0.2246)].copy()
    def estrategia_519(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR74'] >= 0.2800) & (vars_dict['VAR74'] <= 0.3684)].copy()
    def estrategia_520(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR76'] >= 0.2381) & (vars_dict['VAR76'] <= 0.3193)].copy()
    def estrategia_521(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR75'] >= 0.1379) & (vars_dict['VAR75'] <= 0.1905)].copy()
    def estrategia_522(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR58'] >= 0.1104) & (vars_dict['VAR58'] <= 0.1374)].copy()
    def estrategia_523(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR11'] >= 0.6566) & (vars_dict['VAR11'] <= 0.7231)].copy()
    def estrategia_524(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR27'] >= 0.1054) & (vars_dict['VAR27'] <= 0.1168)].copy()
    def estrategia_525(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR40'] >= 0.1363) & (vars_dict['VAR40'] <= 0.1625)].copy()
    def estrategia_526(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR55'] >= 0.0843) & (vars_dict['VAR55'] <= 0.0876)].copy()
    def estrategia_527(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR42'] >= 0.1215) & (vars_dict['VAR42'] <= 0.1417)].copy()
    def estrategia_528(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR28'] >= 0.0928) & (vars_dict['VAR28'] <= 0.1103)].copy()
    def estrategia_529(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR61'] >= 0.0086) & (vars_dict['VAR61'] <= 0.0145)].copy()
    def estrategia_530(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR66'] >= -4.4866) & (vars_dict['VAR66'] <= -3.1981)].copy()
    def estrategia_531(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR36'] >= 0.1626) & (vars_dict['VAR36'] <= 0.1700)].copy()
    def estrategia_532(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR64'] >= 1.9269) & (vars_dict['VAR64'] <= 2.8872)].copy()
    def estrategia_533(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR23'] >= 0.1455) & (vars_dict['VAR23'] <= 0.1667)].copy()
    def estrategia_534(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR06'] >= 1.2234) & (vars_dict['VAR06'] <= 1.3447)].copy()
    def estrategia_535(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR04'] >= 0.7437) & (vars_dict['VAR04'] <= 0.8174)].copy()
    def estrategia_536(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR70'] >= 0.1042) & (vars_dict['VAR70'] <= 0.1578)].copy()
    def estrategia_537(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR59'] >= 0.0110) & (vars_dict['VAR59'] <= 0.0144)].copy()
    def estrategia_538(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR15'] >= 0.5552) & (vars_dict['VAR15'] <= 0.5714)].copy()
    def estrategia_539(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR63'] >= -2.5422) & (vars_dict['VAR63'] <= -2.4036)].copy()
    def estrategia_540(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR49'] >= 0.9118) & (vars_dict['VAR49'] <= 1.0000)].copy()
    def estrategia_541(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR47'] >= 1.0000) & (vars_dict['VAR47'] <= 1.0968)].copy()
    def estrategia_542(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR30'] >= 0.2015) & (vars_dict['VAR30'] <= 0.2109)].copy()
    def estrategia_543(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR31'] >= 0.2500) & (vars_dict['VAR31'] <= 0.2654)].copy()
    def estrategia_544(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR65'] >= -2.0555) & (vars_dict['VAR65'] <= -0.4683)].copy()
    def estrategia_545(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR69'] >= 0.0000) & (vars_dict['VAR69'] <= 0.1132)].copy()
    def estrategia_546(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR12'] >= 0.4987) & (vars_dict['VAR12'] <= 0.5434)].copy()
    def estrategia_547(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR43'] >= 0.1305) & (vars_dict['VAR43'] <= 0.1543)].copy()
    def estrategia_548(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR10'] >= 0.7368) & (vars_dict['VAR10'] <= 0.8056)].copy()
    def estrategia_549(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR09'] >= 1.2414) & (vars_dict['VAR09'] <= 1.3571)].copy()
    def estrategia_550(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR48'] >= 1.3182) & (vars_dict['VAR48'] <= 140.0000)].copy()
    def estrategia_551(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR45'] >= 0.0071) & (vars_dict['VAR45'] <= 0.7586)].copy()
    def estrategia_552(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR62'] >= -1.4688) & (vars_dict['VAR62'] <= -0.5976)].copy()
    def estrategia_553(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR60'] >= 0.0171) & (vars_dict['VAR60'] <= 0.0202)].copy()
    def estrategia_554(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR35'] >= 0.1103) & (vars_dict['VAR35'] <= 0.1243)].copy()
    def estrategia_555(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR05'] >= 0.9478) & (vars_dict['VAR05'] <= 1.0466)].copy()
    def estrategia_556(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR02'] >= 0.9555) & (vars_dict['VAR02'] <= 1.0551)].copy()
    def estrategia_557(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR14'] >= 0.7447) & (vars_dict['VAR14'] <= 0.7734)].copy()
    def estrategia_558(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR68'] >= 0.3125) & (vars_dict['VAR68'] <= 0.3611)].copy()
    def estrategia_559(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR03'] >= 0.7710) & (vars_dict['VAR03'] <= 0.7806)].copy()
    def estrategia_560(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR01'] >= 1.2810) & (vars_dict['VAR01'] <= 1.2970)].copy()
    def estrategia_561(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR07'] >= 1.0307) & (vars_dict['VAR07'] <= 1.1397)].copy()
    def estrategia_562(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR08'] >= 0.8774) & (vars_dict['VAR08'] <= 0.9702)].copy()
    def estrategia_563(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR46'] >= 1.5294) & (vars_dict['VAR46'] <= 1.9886)].copy()
    def estrategia_564(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR44'] >= 0.5029) & (vars_dict['VAR44'] <= 0.6538)].copy()
    def estrategia_565(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR33'] >= 0.1179) & (vars_dict['VAR33'] <= 0.1365)].copy()
    def estrategia_566(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR77'] >= 0.0000) & (vars_dict['VAR77'] <= 0.0327)].copy()
    def estrategia_567(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR72'] >= 0.1905) & (vars_dict['VAR72'] <= 0.2451)].copy()
    def estrategia_568(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR56'] >= 0.2434) & (vars_dict['VAR56'] <= 0.4024)].copy()
    def estrategia_569(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR26'] >= 0.0994) & (vars_dict['VAR26'] <= 0.1213)].copy()
    def estrategia_570(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR34'] >= 0.1542) & (vars_dict['VAR34'] <= 0.1615)].copy()
    def estrategia_571(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR18'] >= 0.4857) & (vars_dict['VAR18'] <= 0.5176)].copy()
    def estrategia_572(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR73'] >= 0.4301) & (vars_dict['VAR73'] <= 0.5600)].copy()
    def estrategia_573(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR57'] >= 0.0494) & (vars_dict['VAR57'] <= 0.0778)].copy()
    def estrategia_574(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR17'] >= 0.7292) & (vars_dict['VAR17'] <= 0.7921)].copy()
    def estrategia_575(df): return df[(vars_dict['VAR71'] >= 0.2598) & (vars_dict['VAR71'] <= 0.3716) & (vars_dict['VAR21'] >= 0.5537) & (vars_dict['VAR21'] <= 0.5833)].copy()
    def estrategia_576(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR38'] >= 0.2467) & (vars_dict['VAR38'] <= 0.2704)].copy()
    def estrategia_577(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR24'] >= 0.2097) & (vars_dict['VAR24'] <= 0.2321)].copy()
    def estrategia_578(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR37'] >= 0.1970) & (vars_dict['VAR37'] <= 0.2167)].copy()
    def estrategia_579(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR71'] >= 0.3600) & (vars_dict['VAR71'] <= 0.3898)].copy()
    def estrategia_580(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR25'] >= 0.1000) & (vars_dict['VAR25'] <= 0.1300)].copy()
    def estrategia_581(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR70'] >= 0.6412) & (vars_dict['VAR70'] <= 0.7768)].copy()
    def estrategia_582(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR32'] >= 0.2015) & (vars_dict['VAR32'] <= 0.2241)].copy()
    def estrategia_583(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR29'] >= 0.1200) & (vars_dict['VAR29'] <= 0.1344)].copy()
    def estrategia_584(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR12'] >= 0.5021) & (vars_dict['VAR12'] <= 0.5478)].copy()
    def estrategia_585(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR39'] >= 0.1828) & (vars_dict['VAR39'] <= 0.2208)].copy()
    def estrategia_586(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR30'] >= 0.1733) & (vars_dict['VAR30'] <= 0.1883)].copy()
    def estrategia_587(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR44'] >= 0.7660) & (vars_dict['VAR44'] <= 0.8387)].copy()
    def estrategia_588(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR46'] >= 1.1923) & (vars_dict['VAR46'] <= 1.3056)].copy()
    def estrategia_589(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR35'] >= 0.1222) & (vars_dict['VAR35'] <= 0.1360)].copy()
    def estrategia_590(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR60'] >= 0.0181) & (vars_dict['VAR60'] <= 0.0216)].copy()
    def estrategia_591(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR64'] >= 2.0004) & (vars_dict['VAR64'] <= 2.7626)].copy()
    def estrategia_592(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR27'] >= 0.1162) & (vars_dict['VAR27'] <= 0.1257)].copy()
    def estrategia_593(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR22'] >= 1.0088) & (vars_dict['VAR22'] <= 1.1795)].copy()
    def estrategia_594(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR76'] >= 0.2500) & (vars_dict['VAR76'] <= 0.3846)].copy()
    def estrategia_595(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR11'] >= 0.6692) & (vars_dict['VAR11'] <= 0.7262)].copy()
    def estrategia_596(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR58'] >= 0.1141) & (vars_dict['VAR58'] <= 0.1435)].copy()
    def estrategia_597(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR04'] >= 0.7536) & (vars_dict['VAR04'] <= 0.8153)].copy()
    def estrategia_598(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR06'] >= 1.2265) & (vars_dict['VAR06'] <= 1.3269)].copy()
    def estrategia_599(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR54'] >= 0.0000) & (vars_dict['VAR54'] <= 0.0145)].copy()
    def estrategia_600(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR42'] >= 0.1009) & (vars_dict['VAR42'] <= 0.1222)].copy()
    def estrategia_601(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR66'] >= -4.5869) & (vars_dict['VAR66'] <= -3.1694)].copy()
    def estrategia_602(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR41'] >= 0.1440) & (vars_dict['VAR41'] <= 0.1531)].copy()
    def estrategia_603(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR43'] >= 0.1554) & (vars_dict['VAR43'] <= 0.1691)].copy()
    def estrategia_604(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR33'] >= 0.1145) & (vars_dict['VAR33'] <= 0.1360)].copy()
    def estrategia_605(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR03'] >= 0.6837) & (vars_dict['VAR03'] <= 0.7353)].copy()
    def estrategia_606(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR01'] >= 1.3600) & (vars_dict['VAR01'] <= 1.4626)].copy()
    def estrategia_607(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR19'] >= 0.6301) & (vars_dict['VAR19'] <= 0.6506)].copy()
    def estrategia_608(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR13'] >= 0.6399) & (vars_dict['VAR13'] <= 0.6625)].copy()
    def estrategia_609(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR28'] >= 0.0975) & (vars_dict['VAR28'] <= 0.1125)].copy()
    def estrategia_610(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR07'] >= 1.0256) & (vars_dict['VAR07'] <= 1.1195)].copy()
    def estrategia_611(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR08'] >= 0.8933) & (vars_dict['VAR08'] <= 0.9750)].copy()
    def estrategia_612(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR23'] >= 0.1034) & (vars_dict['VAR23'] <= 0.1410)].copy()
    def estrategia_613(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR36'] >= 0.1624) & (vars_dict['VAR36'] <= 0.1696)].copy()
    def estrategia_614(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR40'] >= 0.1354) & (vars_dict['VAR40'] <= 0.1608)].copy()
    def estrategia_615(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR16'] >= 0.7031) & (vars_dict['VAR16'] <= 0.7789)].copy()
    def estrategia_616(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR31'] >= 0.2607) & (vars_dict['VAR31'] <= 0.2731)].copy()
    def estrategia_617(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR15'] >= 0.5972) & (vars_dict['VAR15'] <= 0.6367)].copy()
    def estrategia_618(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR67'] >= 0.4775) & (vars_dict['VAR67'] <= 0.6548)].copy()
    def estrategia_619(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR10'] >= 0.7328) & (vars_dict['VAR10'] <= 0.8084)].copy()
    def estrategia_620(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR09'] >= 1.2370) & (vars_dict['VAR09'] <= 1.3647)].copy()
    def estrategia_621(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR69'] >= 0.0000) & (vars_dict['VAR69'] <= 0.1038)].copy()
    def estrategia_622(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR65'] >= -1.7473) & (vars_dict['VAR65'] <= -0.3826)].copy()
    def estrategia_623(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR62'] >= -2.9319) & (vars_dict['VAR62'] <= -2.0366)].copy()
    def estrategia_624(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR17'] >= 0.5327) & (vars_dict['VAR17'] <= 0.5919)].copy()
    def estrategia_625(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR59'] >= 0.0064) & (vars_dict['VAR59'] <= 0.0100)].copy()
    def estrategia_626(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR61'] >= 0.0000) & (vars_dict['VAR61'] <= 0.0039)].copy()
    def estrategia_627(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR45'] >= 0.8276) & (vars_dict['VAR45'] <= 0.8485)].copy()
    def estrategia_628(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR48'] >= 1.1786) & (vars_dict['VAR48'] <= 1.2083)].copy()
    def estrategia_629(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR72'] >= 0.1818) & (vars_dict['VAR72'] <= 0.2329)].copy()
    def estrategia_630(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR20'] >= 0.2886) & (vars_dict['VAR20'] <= 0.3975)].copy()
    def estrategia_631(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR68'] >= 0.3125) & (vars_dict['VAR68'] <= 0.3581)].copy()
    def estrategia_632(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR26'] >= 0.1011) & (vars_dict['VAR26'] <= 0.1222)].copy()
    def estrategia_633(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR74'] >= 0.2832) & (vars_dict['VAR74'] <= 0.3772)].copy()
    def estrategia_634(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR21'] >= 0.5014) & (vars_dict['VAR21'] <= 0.5637)].copy()
    def estrategia_635(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR02'] >= 0.2613) & (vars_dict['VAR02'] <= 0.5650)].copy()
    def estrategia_636(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR05'] >= 1.7699) & (vars_dict['VAR05'] <= 3.8275)].copy()
    def estrategia_637(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR77'] >= 0.0606) & (vars_dict['VAR77'] <= 0.1000)].copy()
    def estrategia_638(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR75'] >= 0.2381) & (vars_dict['VAR75'] <= 0.3043)].copy()
    def estrategia_639(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR57'] >= 0.1500) & (vars_dict['VAR57'] <= 0.1822)].copy()
    def estrategia_640(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR63'] >= -2.5028) & (vars_dict['VAR63'] <= -2.3813)].copy()
    def estrategia_641(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR18'] >= 0.4593) & (vars_dict['VAR18'] <= 0.4873)].copy()
    def estrategia_642(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR47'] >= 0.9565) & (vars_dict['VAR47'] <= 1.0000)].copy()
    def estrategia_643(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR49'] >= 1.0000) & (vars_dict['VAR49'] <= 1.0455)].copy()
    def estrategia_644(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR14'] >= 0.7538) & (vars_dict['VAR14'] <= 0.7847)].copy()
    def estrategia_645(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR34'] >= 0.1592) & (vars_dict['VAR34'] <= 0.1670)].copy()
    def estrategia_646(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR56'] >= 0.0806) & (vars_dict['VAR56'] <= 0.1039)].copy()
    def estrategia_647(df): return df[(vars_dict['VAR55'] >= 0.0763) & (vars_dict['VAR55'] <= 0.1082) & (vars_dict['VAR73'] >= 0.4084) & (vars_dict['VAR73'] <= 0.5100)].copy()
    def estrategia_648(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR55'] >= 0.0000) & (vars_dict['VAR55'] <= 0.1350)].copy()
    def estrategia_649(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR63'] >= -3.8604) & (vars_dict['VAR63'] <= 2.4499)].copy()
    def estrategia_650(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR68'] >= 1.0024) & (vars_dict['VAR68'] <= 1.1185)].copy()
    def estrategia_651(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR60'] >= 0.0350) & (vars_dict['VAR60'] <= 0.0390)].copy()
    def estrategia_652(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR43'] >= 0.2097) & (vars_dict['VAR43'] <= 0.2205)].copy()
    def estrategia_653(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR14'] >= 0.3571) & (vars_dict['VAR14'] <= 0.8289)].copy()
    def estrategia_654(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR38'] >= 0.3871) & (vars_dict['VAR38'] <= 0.4244)].copy()
    def estrategia_655(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR56'] >= 0.0480) & (vars_dict['VAR56'] <= 0.0595)].copy()
    def estrategia_656(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR16'] >= 0.7077) & (vars_dict['VAR16'] <= 0.8390)].copy()
    def estrategia_657(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR13'] >= 0.6041) & (vars_dict['VAR13'] <= 1.2478)].copy()
    def estrategia_658(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR29'] >= 0.1438) & (vars_dict['VAR29'] <= 0.1511)].copy()
    def estrategia_659(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR26'] >= 0.1393) & (vars_dict['VAR26'] <= 0.1571)].copy()
    def estrategia_660(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR41'] >= 0.1948) & (vars_dict['VAR41'] <= 0.2041)].copy()
    def estrategia_661(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR19'] >= 0.4627) & (vars_dict['VAR19'] <= 0.4800)].copy()
    def estrategia_662(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR09'] >= 1.0385) & (vars_dict['VAR09'] <= 1.1136)].copy()
    def estrategia_663(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR10'] >= 0.8980) & (vars_dict['VAR10'] <= 0.9630)].copy()
    def estrategia_664(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR39'] >= 0.4688) & (vars_dict['VAR39'] <= 0.5581)].copy()
    def estrategia_665(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR21'] >= 0.5908) & (vars_dict['VAR21'] <= 0.6058)].copy()
    def estrategia_666(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR58'] >= 0.0688) & (vars_dict['VAR58'] <= 0.0904)].copy()
    def estrategia_667(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR25'] >= 0.3214) & (vars_dict['VAR25'] <= 0.3777)].copy()
    def estrategia_668(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR71'] >= 0.0000) & (vars_dict['VAR71'] <= 0.4773)].copy()
    def estrategia_669(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR01'] >= 0.7450) & (vars_dict['VAR01'] <= 1.4773)].copy()
    def estrategia_670(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR03'] >= 0.6769) & (vars_dict['VAR03'] <= 1.3423)].copy()
    def estrategia_671(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR28'] >= 0.1270) & (vars_dict['VAR28'] <= 0.1431)].copy()
    def estrategia_672(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR22'] >= 0.4574) & (vars_dict['VAR22'] <= 0.5050)].copy()
    def estrategia_673(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR33'] >= 0.1247) & (vars_dict['VAR33'] <= 0.1322)].copy()
    def estrategia_674(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR24'] >= 0.2667) & (vars_dict['VAR24'] <= 0.2880)].copy()
    def estrategia_675(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR27'] >= 0.1333) & (vars_dict['VAR27'] <= 0.1400)].copy()
    def estrategia_676(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR12'] >= 0.4190) & (vars_dict['VAR12'] <= 0.4563)].copy()
    def estrategia_677(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR35'] >= 0.0947) & (vars_dict['VAR35'] <= 0.1005)].copy()
    def estrategia_678(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR40'] >= 0.2040) & (vars_dict['VAR40'] <= 0.2318)].copy()
    def estrategia_679(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR76'] >= 0.3409) & (vars_dict['VAR76'] <= 0.3481)].copy()
    def estrategia_680(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR48'] >= 1.5172) & (vars_dict['VAR48'] <= 1.5341)].copy()
    def estrategia_681(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR74'] >= 0.1339) & (vars_dict['VAR74'] <= 0.1803)].copy()
    def estrategia_682(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR66'] >= -1.6253) & (vars_dict['VAR66'] <= -0.5830)].copy()
    def estrategia_683(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR42'] >= 0.2078) & (vars_dict['VAR42'] <= 0.2373)].copy()
    def estrategia_684(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR67'] >= -0.3611) & (vars_dict['VAR67'] <= -0.2122)].copy()
    def estrategia_685(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR77'] >= 0.1246) & (vars_dict['VAR77'] <= 0.2059)].copy()
    def estrategia_686(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR30'] >= 0.1585) & (vars_dict['VAR30'] <= 0.5556)].copy()
    def estrategia_687(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR59'] >= 0.0102) & (vars_dict['VAR59'] <= 0.0126)].copy()
    def estrategia_688(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR32'] >= 0.2667) & (vars_dict['VAR32'] <= 0.2909)].copy()
    def estrategia_689(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR34'] >= 0.1294) & (vars_dict['VAR34'] <= 0.1345)].copy()
    def estrategia_690(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR54'] >= 0.0731) & (vars_dict['VAR54'] <= 0.1261)].copy()
    def estrategia_691(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR75'] >= 0.1316) & (vars_dict['VAR75'] <= 0.1757)].copy()
    def estrategia_692(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR20'] >= 0.9665) & (vars_dict['VAR20'] <= 0.9901)].copy()
    def estrategia_693(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR31'] >= 0.0031) & (vars_dict['VAR31'] <= 0.1800)].copy()
    def estrategia_694(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR06'] >= 1.1692) & (vars_dict['VAR06'] <= 1.3194)].copy()
    def estrategia_695(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR04'] >= 0.7579) & (vars_dict['VAR04'] <= 0.8553)].copy()
    def estrategia_696(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR44'] >= 1.3333) & (vars_dict['VAR44'] <= 1.5634)].copy()
    def estrategia_697(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR46'] >= 0.6396) & (vars_dict['VAR46'] <= 0.7500)].copy()
    def estrategia_698(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR23'] >= 0.1429) & (vars_dict['VAR23'] <= 0.1519)].copy()
    def estrategia_699(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR02'] >= 2.2073) & (vars_dict['VAR02'] <= 2.4510)].copy()
    def estrategia_700(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR05'] >= 0.4080) & (vars_dict['VAR05'] <= 0.4530)].copy()
    def estrategia_701(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR70'] >= 1.2073) & (vars_dict['VAR70'] <= 1.4510)].copy()
    def estrategia_702(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR17'] >= 0.8962) & (vars_dict['VAR17'] <= 0.9533)].copy()
    def estrategia_703(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR72'] >= 0.3699) & (vars_dict['VAR72'] <= 0.5165)].copy()
    def estrategia_704(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR37'] >= 0.2100) & (vars_dict['VAR37'] <= 0.2220)].copy()
    def estrategia_705(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR64'] >= 0.5266) & (vars_dict['VAR64'] <= 1.2864)].copy()
    def estrategia_706(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR47'] >= 0.5091) & (vars_dict['VAR47'] <= 0.5625)].copy()
    def estrategia_707(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR49'] >= 1.7778) & (vars_dict['VAR49'] <= 1.9643)].copy()
    def estrategia_708(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR65'] >= 1.9370) & (vars_dict['VAR65'] <= 3.3244)].copy()
    def estrategia_709(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR36'] >= 0.0988) & (vars_dict['VAR36'] <= 0.1113)].copy()
    def estrategia_710(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR11'] >= 0.6721) & (vars_dict['VAR11'] <= 0.7541)].copy()
    def estrategia_711(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR07'] >= 1.3064) & (vars_dict['VAR07'] <= 1.4943)].copy()
    def estrategia_712(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR08'] >= 0.6692) & (vars_dict['VAR08'] <= 0.7655)].copy()
    def estrategia_713(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR62'] >= -10.1447) & (vars_dict['VAR62'] <= -8.9100)].copy()
    def estrategia_714(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR15'] >= 0.5636) & (vars_dict['VAR15'] <= 0.5804)].copy()
    def estrategia_715(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR73'] >= 0.0000) & (vars_dict['VAR73'] <= 0.0316)].copy()
    def estrategia_716(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR18'] >= 0.4000) & (vars_dict['VAR18'] <= 0.4316)].copy()
    def estrategia_717(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR61'] >= 0.0481) & (vars_dict['VAR61'] <= 0.0592)].copy()
    def estrategia_718(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR69'] >= 0.4132) & (vars_dict['VAR69'] <= 0.6065)].copy()
    def estrategia_719(df): return df[(vars_dict['VAR45'] >= 0.6452) & (vars_dict['VAR45'] <= 0.7230) & (vars_dict['VAR57'] >= 0.0000) & (vars_dict['VAR57'] <= 0.0168)].copy()
    def estrategia_720(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR36'] >= 0.0000) & (vars_dict['VAR36'] <= 0.0880)].copy()
    def estrategia_721(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR32'] >= 0.2421) & (vars_dict['VAR32'] <= 0.2649)].copy()
    def estrategia_722(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR35'] >= 0.0982) & (vars_dict['VAR35'] <= 0.1044)].copy()
    def estrategia_723(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR19'] >= 0.0000) & (vars_dict['VAR19'] <= 0.3563)].copy()
    def estrategia_724(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR25'] >= 0.2777) & (vars_dict['VAR25'] <= 0.3240)].copy()
    def estrategia_725(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR34'] >= 0.0015) & (vars_dict['VAR34'] <= 0.0884)].copy()
    def estrategia_726(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR39'] >= 0.4359) & (vars_dict['VAR39'] <= 0.5000)].copy()
    def estrategia_727(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR30'] >= 0.0012) & (vars_dict['VAR30'] <= 0.0833)].copy()
    def estrategia_728(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR41'] >= 0.2000) & (vars_dict['VAR41'] <= 0.2099)].copy()
    def estrategia_729(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR64'] >= -1.5438) & (vars_dict['VAR64'] <= -1.1406)].copy()
    def estrategia_730(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR61'] >= 0.0426) & (vars_dict['VAR61'] <= 0.0487)].copy()
    def estrategia_731(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR15'] >= 0.5211) & (vars_dict['VAR15'] <= 0.5368)].copy()
    def estrategia_732(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR37'] >= 0.1895) & (vars_dict['VAR37'] <= 0.2035)].copy()
    def estrategia_733(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR60'] >= 0.0364) & (vars_dict['VAR60'] <= 0.0394)].copy()
    def estrategia_734(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR56'] >= 0.0325) & (vars_dict['VAR56'] <= 0.0436)].copy()
    def estrategia_735(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR43'] >= 0.1984) & (vars_dict['VAR43'] <= 0.2076)].copy()
    def estrategia_736(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR69'] >= 1.2730) & (vars_dict['VAR69'] <= 1.4988)].copy()
    def estrategia_737(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR68'] >= 1.0378) & (vars_dict['VAR68'] <= 1.1273)].copy()
    def estrategia_738(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR62'] >= -20.5119) & (vars_dict['VAR62'] <= -11.2036)].copy()
    def estrategia_739(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR55'] >= 0.3112) & (vars_dict['VAR55'] <= 0.6726)].copy()
    def estrategia_740(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR63'] >= -18.5881) & (vars_dict['VAR63'] <= -8.8436)].copy()
    def estrategia_741(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR65'] >= 1.3871) & (vars_dict['VAR65'] <= 2.8119)].copy()
    def estrategia_742(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR57'] >= 0.1113) & (vars_dict['VAR57'] <= 0.1384)].copy()
    def estrategia_743(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR77'] >= 0.6917) & (vars_dict['VAR77'] <= 4.7143)].copy()
    def estrategia_744(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR59'] >= 0.0419) & (vars_dict['VAR59'] <= 0.1153)].copy()
    def estrategia_745(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR67'] >= -0.3780) & (vars_dict['VAR67'] <= -0.2395)].copy()
    def estrategia_746(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR13'] >= 0.1136) & (vars_dict['VAR13'] <= 0.3745)].copy()
    def estrategia_747(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR33'] >= 0.0015) & (vars_dict['VAR33'] <= 0.0714)].copy()
    def estrategia_748(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR75'] >= 0.6190) & (vars_dict['VAR75'] <= 112.9535)].copy()
    def estrategia_749(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR47'] >= 0.0055) & (vars_dict['VAR47'] <= 0.3987)].copy()
    def estrategia_750(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR49'] >= 2.5085) & (vars_dict['VAR49'] <= 181.4815)].copy()
    def estrategia_751(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR58'] >= 0.0405) & (vars_dict['VAR58'] <= 0.0632)].copy()
    def estrategia_752(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR08'] >= 1.1001) & (vars_dict['VAR08'] <= 1.2123)].copy()
    def estrategia_753(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR07'] >= 0.8249) & (vars_dict['VAR07'] <= 0.9090)].copy()
    def estrategia_754(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR38'] >= 0.3698) & (vars_dict['VAR38'] <= 0.4010)].copy()
    def estrategia_755(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR71'] >= 1.1926) & (vars_dict['VAR71'] <= 4.5738)].copy()
    def estrategia_756(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR03'] >= 0.1794) & (vars_dict['VAR03'] <= 0.4561)].copy()
    def estrategia_757(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR01'] >= 2.1926) & (vars_dict['VAR01'] <= 5.5738)].copy()
    def estrategia_758(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR45'] >= 0.6167) & (vars_dict['VAR45'] <= 0.6250)].copy()
    def estrategia_759(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR27'] >= 0.1243) & (vars_dict['VAR27'] <= 0.1297)].copy()
    def estrategia_760(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR24'] >= 0.2281) & (vars_dict['VAR24'] <= 0.2452)].copy()
    def estrategia_761(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR46'] >= 0.0088) & (vars_dict['VAR46'] <= 0.6216)].copy()
    def estrategia_762(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR44'] >= 1.6087) & (vars_dict['VAR44'] <= 113.9535)].copy()
    def estrategia_763(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR31'] >= 0.0031) & (vars_dict['VAR31'] <= 0.1700)].copy()
    def estrategia_764(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR22'] >= 0.3701) & (vars_dict['VAR22'] <= 0.4206)].copy()
    def estrategia_765(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR26'] >= 0.1481) & (vars_dict['VAR26'] <= 0.1728)].copy()
    def estrategia_766(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR72'] >= 0.1250) & (vars_dict['VAR72'] <= 0.1709)].copy()
    def estrategia_767(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR74'] >= 0.2874) & (vars_dict['VAR74'] <= 0.3665)].copy()
    def estrategia_768(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR48'] >= 1.6000) & (vars_dict['VAR48'] <= 1.6216)].copy()
    def estrategia_769(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR73'] >= 0.1306) & (vars_dict['VAR73'] <= 0.1713)].copy()
    def estrategia_770(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR04'] >= 1.2537) & (vars_dict['VAR04'] <= 1.3846)].copy()
    def estrategia_771(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR06'] >= 0.7222) & (vars_dict['VAR06'] <= 0.7976)].copy()
    def estrategia_772(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR66'] >= 1.0797) & (vars_dict['VAR66'] <= 2.9448)].copy()
    def estrategia_773(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR42'] >= 0.1800) & (vars_dict['VAR42'] <= 0.2035)].copy()
    def estrategia_774(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR29'] >= 0.0000) & (vars_dict['VAR29'] <= 0.0945)].copy()
    def estrategia_775(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR12'] >= 0.6000) & (vars_dict['VAR12'] <= 0.6609)].copy()
    def estrategia_776(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR05'] >= 0.0871) & (vars_dict['VAR05'] <= 0.3084)].copy()
    def estrategia_777(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR02'] >= 3.2421) & (vars_dict['VAR02'] <= 11.4754)].copy()
    def estrategia_778(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR70'] >= 2.2420) & (vars_dict['VAR70'] <= 10.4754)].copy()
    def estrategia_779(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR23'] >= 0.1127) & (vars_dict['VAR23'] <= 0.1211)].copy()
    def estrategia_780(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR28'] >= 0.1059) & (vars_dict['VAR28'] <= 0.1200)].copy()
    def estrategia_781(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR21'] >= 0.0000) & (vars_dict['VAR21'] <= 0.4639)].copy()
    def estrategia_782(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR54'] >= 0.4202) & (vars_dict['VAR54'] <= 0.7667)].copy()
    def estrategia_783(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR16'] >= 0.3606) & (vars_dict['VAR16'] <= 0.4122)].copy()
    def estrategia_784(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR40'] >= 0.1937) & (vars_dict['VAR40'] <= 0.2213)].copy()
    def estrategia_785(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR17'] >= 0.9948) & (vars_dict['VAR17'] <= 1.0756)].copy()
    def estrategia_786(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR11'] >= 1.0000) & (vars_dict['VAR11'] <= 1.0664)].copy()
    def estrategia_787(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR18'] >= 0.5211) & (vars_dict['VAR18'] <= 0.5493)].copy()
    def estrategia_788(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR10'] >= 1.0734) & (vars_dict['VAR10'] <= 1.2145)].copy()
    def estrategia_789(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR09'] >= 0.8234) & (vars_dict['VAR09'] <= 0.9316)].copy()
    def estrategia_790(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR14'] >= 1.0209) & (vars_dict['VAR14'] <= 1.0549)].copy()
    def estrategia_791(df): return df[(vars_dict['VAR76'] >= 0.3265) & (vars_dict['VAR76'] <= 0.3999) & (vars_dict['VAR20'] >= 1.1300) & (vars_dict['VAR20'] <= 1.1694)].copy()
    def estrategia_792(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR57'] >= 0.1185) & (vars_dict['VAR57'] <= 0.1443)].copy()
    def estrategia_793(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR42'] >= 0.1267) & (vars_dict['VAR42'] <= 0.1471)].copy()
    def estrategia_794(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR27'] >= 0.1255) & (vars_dict['VAR27'] <= 0.1360)].copy()
    def estrategia_795(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR48'] >= 0.0076) & (vars_dict['VAR48'] <= 0.8727)].copy()
    def estrategia_796(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR45'] >= 1.1458) & (vars_dict['VAR45'] <= 131.5789)].copy()
    def estrategia_797(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR13'] >= 0.9149) & (vars_dict['VAR13'] <= 0.9307)].copy()
    def estrategia_798(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR59'] >= 0.0245) & (vars_dict['VAR59'] <= 0.0303)].copy()
    def estrategia_799(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR25'] >= 0.1671) & (vars_dict['VAR25'] <= 0.2000)].copy()
    def estrategia_800(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR68'] >= -3.7355) & (vars_dict['VAR68'] <= -0.3691)].copy()
    def estrategia_801(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR40'] >= 0.1457) & (vars_dict['VAR40'] <= 0.1744)].copy()
    def estrategia_802(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR63'] >= 0.6521) & (vars_dict['VAR63'] <= 0.8919)].copy()
    def estrategia_803(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR10'] >= 0.8649) & (vars_dict['VAR10'] <= 0.9147)].copy()
    def estrategia_804(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR09'] >= 1.0932) & (vars_dict['VAR09'] <= 1.1563)].copy()
    def estrategia_805(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR26'] >= 0.1526) & (vars_dict['VAR26'] <= 0.1833)].copy()
    def estrategia_806(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR39'] >= 0.1600) & (vars_dict['VAR39'] <= 0.1908)].copy()
    def estrategia_807(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR60'] >= 0.0155) & (vars_dict['VAR60'] <= 0.1341)].copy()
    def estrategia_808(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR65'] >= -0.2344) & (vars_dict['VAR65'] <= 1.4127)].copy()
    def estrategia_809(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR07'] >= 0.9095) & (vars_dict['VAR07'] <= 1.0155)].copy()
    def estrategia_810(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR08'] >= 0.9848) & (vars_dict['VAR08'] <= 1.0994)].copy()
    def estrategia_811(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR77'] >= 0.2755) & (vars_dict['VAR77'] <= 0.3478)].copy()
    def estrategia_812(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR31'] >= 0.3348) & (vars_dict['VAR31'] <= 0.3457)].copy()
    def estrategia_813(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR74'] >= 0.2934) & (vars_dict['VAR74'] <= 0.3762)].copy()
    def estrategia_814(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR21'] >= 0.4978) & (vars_dict['VAR21'] <= 0.5543)].copy()
    def estrategia_815(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR71'] >= 0.0714) & (vars_dict['VAR71'] <= 0.0867)].copy()
    def estrategia_816(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR44'] >= 1.2000) & (vars_dict['VAR44'] <= 163.3333)].copy()
    def estrategia_817(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR46'] >= 0.0061) & (vars_dict['VAR46'] <= 0.8333)].copy()
    def estrategia_818(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR55'] >= 0.0213) & (vars_dict['VAR55'] <= 0.0259)].copy()
    def estrategia_819(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR73'] >= 0.5246) & (vars_dict['VAR73'] <= 2.3594)].copy()
    def estrategia_820(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR05'] >= 1.0205) & (vars_dict['VAR05'] <= 1.1654)].copy()
    def estrategia_821(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR02'] >= 0.8581) & (vars_dict['VAR02'] <= 0.9799)].copy()
    def estrategia_822(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR36'] >= 0.2178) & (vars_dict['VAR36'] <= 0.2388)].copy()
    def estrategia_823(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR20'] >= 0.5425) & (vars_dict['VAR20'] <= 0.5600)].copy()
    def estrategia_824(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR03'] >= 1.0889) & (vars_dict['VAR03'] <= 1.1268)].copy()
    def estrategia_825(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR01'] >= 0.8875) & (vars_dict['VAR01'] <= 0.9184)].copy()
    def estrategia_826(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR24'] >= 0.3281) & (vars_dict['VAR24'] <= 0.3641)].copy()
    def estrategia_827(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR12'] >= 0.6485) & (vars_dict['VAR12'] <= 0.7015)].copy()
    def estrategia_828(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR66'] >= -2.1441) & (vars_dict['VAR66'] <= -1.3530)].copy()
    def estrategia_829(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR34'] >= 0.1933) & (vars_dict['VAR34'] <= 0.2011)].copy()
    def estrategia_830(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR61'] >= 0.0111) & (vars_dict['VAR61'] <= 0.0169)].copy()
    def estrategia_831(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR19'] >= 0.7851) & (vars_dict['VAR19'] <= 0.8114)].copy()
    def estrategia_832(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR37'] >= 0.2440) & (vars_dict['VAR37'] <= 0.2640)].copy()
    def estrategia_833(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR15'] >= 0.5082) & (vars_dict['VAR15'] <= 0.5200)].copy()
    def estrategia_834(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR32'] >= 0.2404) & (vars_dict['VAR32'] <= 0.2636)].copy()
    def estrategia_835(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR23'] >= 0.2773) & (vars_dict['VAR23'] <= 0.2978)].copy()
    def estrategia_836(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR69'] >= -0.8185) & (vars_dict['VAR69'] <= -0.6821)].copy()
    def estrategia_837(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR75'] >= 0.2069) & (vars_dict['VAR75'] <= 0.2637)].copy()
    def estrategia_838(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR70'] >= 0.5865) & (vars_dict['VAR70'] <= 0.9912)].copy()
    def estrategia_839(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR67'] >= 0.5890) & (vars_dict['VAR67'] <= 0.7427)].copy()
    def estrategia_840(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR54'] >= 0.1607) & (vars_dict['VAR54'] <= 0.2020)].copy()
    def estrategia_841(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR72'] >= 0.3455) & (vars_dict['VAR72'] <= 0.4056)].copy()
    def estrategia_842(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR62'] >= 0.1975) & (vars_dict['VAR62'] <= 1.5412)].copy()
    def estrategia_843(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR76'] >= 0.1176) & (vars_dict['VAR76'] <= 0.1799)].copy()
    def estrategia_844(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR29'] >= 0.1333) & (vars_dict['VAR29'] <= 0.1481)].copy()
    def estrategia_845(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR33'] >= 0.1488) & (vars_dict['VAR33'] <= 0.1733)].copy()
    def estrategia_846(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR43'] >= 0.1282) & (vars_dict['VAR43'] <= 0.1422)].copy()
    def estrategia_847(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR04'] >= 0.6687) & (vars_dict['VAR04'] <= 0.7250)].copy()
    def estrategia_848(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR06'] >= 1.3793) & (vars_dict['VAR06'] <= 1.4955)].copy()
    def estrategia_849(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR56'] >= 0.1515) & (vars_dict['VAR56'] <= 0.1906)].copy()
    def estrategia_850(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR11'] >= 0.4590) & (vars_dict['VAR11'] <= 0.5243)].copy()
    def estrategia_851(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR30'] >= 0.3043) & (vars_dict['VAR30'] <= 0.3200)].copy()
    def estrategia_852(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR41'] >= 0.1600) & (vars_dict['VAR41'] <= 0.1786)].copy()
    def estrategia_853(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR64'] >= 4.2424) & (vars_dict['VAR64'] <= 5.4130)].copy()
    def estrategia_854(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR58'] >= 0.0183) & (vars_dict['VAR58'] <= 0.0348)].copy()
    def estrategia_855(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR22'] >= 1.2165) & (vars_dict['VAR22'] <= 2.0444)].copy()
    def estrategia_856(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR28'] >= 0.1326) & (vars_dict['VAR28'] <= 0.1542)].copy()
    def estrategia_857(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR16'] >= 0.9029) & (vars_dict['VAR16'] <= 1.0202)].copy()
    def estrategia_858(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR38'] >= 0.2393) & (vars_dict['VAR38'] <= 0.2600)].copy()
    def estrategia_859(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR35'] >= 0.1887) & (vars_dict['VAR35'] <= 0.2021)].copy()
    def estrategia_860(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR47'] >= 1.8591) & (vars_dict['VAR47'] <= 106.5217)].copy()
    def estrategia_861(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR49'] >= 0.0094) & (vars_dict['VAR49'] <= 0.5379)].copy()
    def estrategia_862(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR18'] >= 0.6230) & (vars_dict['VAR18'] <= 0.6774)].copy()
    def estrategia_863(df): return df[(vars_dict['VAR14'] >= 0.4684) & (vars_dict['VAR14'] <= 0.5813) & (vars_dict['VAR17'] >= 0.4972) & (vars_dict['VAR17'] <= 0.5385)].copy()
    def estrategia_864(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR18'] >= 0.2693) & (vars_dict['VAR18'] <= 0.3088)].copy()
    def estrategia_865(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR58'] >= 0.0988) & (vars_dict['VAR58'] <= 0.1271)].copy()
    def estrategia_866(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR66'] >= 2.4486) & (vars_dict['VAR66'] <= 4.0630)].copy()
    def estrategia_867(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR28'] >= 0.1155) & (vars_dict['VAR28'] <= 0.1429)].copy()
    def estrategia_868(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR26'] >= 0.1345) & (vars_dict['VAR26'] <= 0.1800)].copy()
    def estrategia_869(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR61'] >= 0.0640) & (vars_dict['VAR61'] <= 0.0731)].copy()
    def estrategia_870(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR55'] >= 0.0852) & (vars_dict['VAR55'] <= 0.0984)].copy()
    def estrategia_871(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR60'] >= 0.0183) & (vars_dict['VAR60'] <= 0.0245)].copy()
    def estrategia_872(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR10'] >= 1.1776) & (vars_dict['VAR10'] <= 1.3103)].copy()
    def estrategia_873(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR09'] >= 0.7632) & (vars_dict['VAR09'] <= 0.8492)].copy()
    def estrategia_874(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR40'] >= 0.0994) & (vars_dict['VAR40'] <= 0.1349)].copy()
    def estrategia_875(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR37'] >= 0.3043) & (vars_dict['VAR37'] <= 0.3565)].copy()
    def estrategia_876(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR62'] >= 3.9717) & (vars_dict['VAR62'] <= 7.2310)].copy()
    def estrategia_877(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR25'] >= 0.1207) & (vars_dict['VAR25'] <= 0.1591)].copy()
    def estrategia_878(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR39'] >= 0.0896) & (vars_dict['VAR39'] <= 0.1213)].copy()
    def estrategia_879(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR11'] >= 0.3342) & (vars_dict['VAR11'] <= 0.3840)].copy()
    def estrategia_880(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR69'] >= -2.0899) & (vars_dict['VAR69'] <= -1.8236)].copy()
    def estrategia_881(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR72'] >= 0.2915) & (vars_dict['VAR72'] <= 0.3972)].copy()
    def estrategia_882(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR59'] >= 0.0656) & (vars_dict['VAR59'] <= 0.1656)].copy()
    def estrategia_883(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR43'] >= 0.0748) & (vars_dict['VAR43'] <= 0.0880)].copy()
    def estrategia_884(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR23'] >= 0.0047) & (vars_dict['VAR23'] <= 0.1563)].copy()
    def estrategia_885(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR44'] >= 0.3740) & (vars_dict['VAR44'] <= 0.4527)].copy()
    def estrategia_886(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR46'] >= 2.2088) & (vars_dict['VAR46'] <= 2.6736)].copy()
    def estrategia_887(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR65'] >= -4.0795) & (vars_dict['VAR65'] <= -2.6585)].copy()
    def estrategia_888(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR68'] >= -0.6735) & (vars_dict['VAR68'] <= -0.4911)].copy()
    def estrategia_889(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR17'] >= 0.3017) & (vars_dict['VAR17'] <= 0.3275)].copy()
    def estrategia_890(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR27'] >= 0.1150) & (vars_dict['VAR27'] <= 0.1271)].copy()
    def estrategia_891(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR34'] >= 0.1892) & (vars_dict['VAR34'] <= 0.2079)].copy()
    def estrategia_892(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR71'] >= 0.3584) & (vars_dict['VAR71'] <= 0.4118)].copy()
    def estrategia_893(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR06'] >= 1.8763) & (vars_dict['VAR06'] <= 2.1512)].copy()
    def estrategia_894(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR04'] >= 0.4649) & (vars_dict['VAR04'] <= 0.5329)].copy()
    def estrategia_895(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR32'] >= 0.1719) & (vars_dict['VAR32'] <= 0.1989)].copy()
    def estrategia_896(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR74'] >= 0.1400) & (vars_dict['VAR74'] <= 0.1891)].copy()
    def estrategia_897(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR24'] >= 0.1829) & (vars_dict['VAR24'] <= 0.2143)].copy()
    def estrategia_898(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR56'] >= 0.1279) & (vars_dict['VAR56'] <= 0.1983)].copy()
    def estrategia_899(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR36'] >= 0.1794) & (vars_dict['VAR36'] <= 0.1981)].copy()
    def estrategia_900(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR64'] >= 3.3525) & (vars_dict['VAR64'] <= 5.4922)].copy()
    def estrategia_901(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR54'] >= 0.3791) & (vars_dict['VAR54'] <= 0.4267)].copy()
    def estrategia_902(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR30'] >= 0.5250) & (vars_dict['VAR30'] <= 0.5857)].copy()
    def estrategia_903(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR76'] >= 0.3227) & (vars_dict['VAR76'] <= 0.4205)].copy()
    def estrategia_904(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR47'] >= 2.2893) & (vars_dict['VAR47'] <= 2.6250)].copy()
    def estrategia_905(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR77'] >= 1.2893) & (vars_dict['VAR77'] <= 1.6250)].copy()
    def estrategia_906(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR49'] >= 0.3809) & (vars_dict['VAR49'] <= 0.4368)].copy()
    def estrategia_907(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR67'] >= 1.3713) & (vars_dict['VAR67'] <= 1.5343)].copy()
    def estrategia_908(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR70'] >= 0.3938) & (vars_dict['VAR70'] <= 0.5302)].copy()
    def estrategia_909(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR41'] >= 0.0767) & (vars_dict['VAR41'] <= 0.0877)].copy()
    def estrategia_910(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR33'] >= 0.2256) & (vars_dict['VAR33'] <= 0.2732)].copy()
    def estrategia_911(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR16'] >= 0.7384) & (vars_dict['VAR16'] <= 0.8492)].copy()
    def estrategia_912(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR03'] >= 1.2000) & (vars_dict['VAR03'] <= 1.2653)].copy()
    def estrategia_913(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR01'] >= 0.7903) & (vars_dict['VAR01'] <= 0.8333)].copy()
    def estrategia_914(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR13'] >= 1.1319) & (vars_dict['VAR13'] <= 1.1790)].copy()
    def estrategia_915(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR35'] >= 0.2438) & (vars_dict['VAR35'] <= 0.2889)].copy()
    def estrategia_916(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR31'] >= 0.0031) & (vars_dict['VAR31'] <= 0.0038)].copy()
    def estrategia_917(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR21'] >= 0.2608) & (vars_dict['VAR21'] <= 0.3062)].copy()
    def estrategia_918(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR14'] >= 0.2977) & (vars_dict['VAR14'] <= 0.3344)].copy()
    def estrategia_919(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR38'] >= 0.0037) & (vars_dict['VAR38'] <= 0.0081)].copy()
    def estrategia_920(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR75'] >= 0.3188) & (vars_dict['VAR75'] <= 0.4000)].copy()
    def estrategia_921(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR05'] >= 1.9846) & (vars_dict['VAR05'] <= 2.4353)].copy()
    def estrategia_922(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR02'] >= 0.4106) & (vars_dict['VAR02'] <= 0.5039)].copy()
    def estrategia_923(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR73'] >= 0.3983) & (vars_dict['VAR73'] <= 0.5125)].copy()
    def estrategia_924(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR63'] >= 2.5323) & (vars_dict['VAR63'] <= 3.0067)].copy()
    def estrategia_925(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR29'] >= 0.1340) & (vars_dict['VAR29'] <= 0.1618)].copy()
    def estrategia_926(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR22'] >= 1.2388) & (vars_dict['VAR22'] <= 1.3352)].copy()
    def estrategia_927(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR42'] >= 0.1355) & (vars_dict['VAR42'] <= 0.3375)].copy()
    def estrategia_928(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR07'] >= 1.4495) & (vars_dict['VAR07'] <= 1.7392)].copy()
    def estrategia_929(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR08'] >= 0.5750) & (vars_dict['VAR08'] <= 0.6899)].copy()
    def estrategia_930(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR45'] >= 1.3043) & (vars_dict['VAR45'] <= 1.3936)].copy()
    def estrategia_931(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR48'] >= 0.7176) & (vars_dict['VAR48'] <= 0.7667)].copy()
    def estrategia_932(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR12'] >= 0.3840) & (vars_dict['VAR12'] <= 0.4295)].copy()
    def estrategia_933(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR57'] >= 0.0870) & (vars_dict['VAR57'] <= 0.1188)].copy()
    def estrategia_934(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR19'] >= 1.4488) & (vars_dict['VAR19'] <= 2.6293)].copy()
    def estrategia_935(df): return df[(vars_dict['VAR20'] >= 0.0000) & (vars_dict['VAR20'] <= 0.4520) & (vars_dict['VAR15'] >= 0.4887) & (vars_dict['VAR15'] <= 0.5000)].copy()
    def estrategia_935(df): return df[  (vars_dict['VAR76'] >= 0.326923) & (vars_dict['VAR76'] <= 0.400000) &   (vars_dict['VAR36'] >= 0.001010) & (vars_dict['VAR36'] <= 0.088048) ].copy()
    def estrategia_936(df):  return df[  (vars_dict['VAR35'] >= 0.119259) & (vars_dict['VAR35'] <= 0.138065) &  (vars_dict['VAR52'] >= 0.039548) & (vars_dict['VAR52'] <= 0.061268)  ].copy()
    def estrategia_937(df):   return df[   (vars_dict['VAR23'] >= 0.129655) & (vars_dict['VAR23'] <= 0.157333) &   (vars_dict['VAR35'] >= 0.095000) & (vars_dict['VAR35'] <= 0.103333)  ].copy()
    def estrategia_938(df):    return df[ (vars_dict['VAR48'] >= 1.382979) & (vars_dict['VAR48'] <= 1.551724) &  (vars_dict['VAR63'] >= -3.860938) & (vars_dict['VAR63'] <= 2.449919)   ].copy()
    def estrategia_939(df):  return df[   (vars_dict['VAR29'] >= 0.131765) & (vars_dict['VAR29'] <= 0.145333) & (vars_dict['VAR12'] >= 0.430769) & (vars_dict['VAR12'] <= 0.467333)  ].copy()
    def estrategia_940(df):   return df[  (vars_dict['VAR26'] >= 0.147407) & (vars_dict['VAR26'] <= 0.180870) &   (vars_dict['VAR13'] >= 0.443478) & (vars_dict['VAR13'] <= 0.517073)  ].copy()
    def estrategia_941(df):   return df[  (vars_dict['VAR47'] >= 0.692308) & (vars_dict['VAR47'] <= 0.833333) &   (vars_dict['VAR68'] >= 0.654780) & (vars_dict['VAR68'] <= 0.700247)  ].copy()
    def estrategia_942(df):  return df[  (vars_dict['VAR67'] >= 0.901433) & (vars_dict['VAR67'] <= 4.303247) &   (vars_dict['VAR51'] >= 0.097257) & (vars_dict['VAR51'] <= 0.124689)  ].copy()
    def estrategia_943(df):  return df[  (vars_dict['VAR34'] >= 0.189362) & (vars_dict['VAR34'] <= 0.297368) &   (vars_dict['VAR35'] >= 0.238066) & (vars_dict['VAR35'] <= 0.261538)  ].copy()
    def estrategia_944(df):   return df[   (vars_dict['VAR11'] >= 0.025250) & (vars_dict['VAR11'] <= 0.463291) &    (vars_dict['VAR63'] >= -4.823201) & (vars_dict['VAR63'] <= -0.516723)  ].copy()
    def estrategia_945(df):  return df[  (vars_dict['VAR05'] >= 1.980769) & (vars_dict['VAR05'] <= 44.444444) &   (vars_dict['VAR26'] >= 0.137931) & (vars_dict['VAR26'] <= 0.177194) ].copy()
    def estrategia_946(df):   return df[   (vars_dict['VAR02'] >= 0.022500) & (vars_dict['VAR02'] <= 0.504854) &   (vars_dict['VAR26'] >= 0.137931) & (vars_dict['VAR26'] <= 0.177194) ].copy()





    return [
        
        (estrategia_1, "Estratégia 1"), (estrategia_2, "Estratégia 2"), (estrategia_3, "Estratégia 3"), (estrategia_4, "Estratégia 4"), (estrategia_5, "Estratégia 5"), (estrategia_6, "Estratégia 6"), (estrategia_7, "Estratégia 7"), 
        (estrategia_8, "Estratégia 8"), (estrategia_9, "Estratégia 9"), (estrategia_10, "Estratégia 10"), (estrategia_11, "Estratégia 11"), (estrategia_12, "Estratégia 12"), (estrategia_13, "Estratégia 13"), (estrategia_14, "Estratégia 14"), 
        (estrategia_15, "Estratégia 15"), (estrategia_16, "Estratégia 16"), (estrategia_17, "Estratégia 17"), (estrategia_18, "Estratégia 18"), (estrategia_19, "Estratégia 19"), (estrategia_20, "Estratégia 20"), (estrategia_21, "Estratégia 21"), 
        (estrategia_22, "Estratégia 22"), (estrategia_23, "Estratégia 23"), (estrategia_24, "Estratégia 24"), (estrategia_25, "Estratégia 25"), (estrategia_26, "Estratégia 26"), (estrategia_27, "Estratégia 27"), (estrategia_28, "Estratégia 28"), 
        (estrategia_29, "Estratégia 29"), (estrategia_30, "Estratégia 30"), (estrategia_31, "Estratégia 31"), (estrategia_32, "Estratégia 32"), (estrategia_33, "Estratégia 33"), (estrategia_34, "Estratégia 34"), (estrategia_35, "Estratégia 35"), 
        (estrategia_36, "Estratégia 36"), (estrategia_37, "Estratégia 37"), (estrategia_38, "Estratégia 38"), (estrategia_39, "Estratégia 39"), (estrategia_40, "Estratégia 40"), (estrategia_41, "Estratégia 41"), (estrategia_42, "Estratégia 42"), 
        (estrategia_43, "Estratégia 43"), (estrategia_44, "Estratégia 44"), (estrategia_45, "Estratégia 45"), (estrategia_46, "Estratégia 46"), (estrategia_47, "Estratégia 47"), (estrategia_48, "Estratégia 48"), (estrategia_49, "Estratégia 49"), 
        (estrategia_50, "Estratégia 50"), (estrategia_51, "Estratégia 51"), (estrategia_52, "Estratégia 52"), (estrategia_53, "Estratégia 53"), (estrategia_54, "Estratégia 54"), (estrategia_55, "Estratégia 55"), (estrategia_56, "Estratégia 56"), 
        (estrategia_57, "Estratégia 57"), (estrategia_58, "Estratégia 58"), (estrategia_59, "Estratégia 59"), (estrategia_60, "Estratégia 60"), (estrategia_61, "Estratégia 61"), (estrategia_62, "Estratégia 62"), (estrategia_63, "Estratégia 63"), 
        (estrategia_64, "Estratégia 64"), (estrategia_65, "Estratégia 65"), (estrategia_66, "Estratégia 66"), (estrategia_67, "Estratégia 67"), (estrategia_68, "Estratégia 68"), (estrategia_69, "Estratégia 69"), (estrategia_70, "Estratégia 70"), 
        (estrategia_71, "Estratégia 71"), (estrategia_72, "Estratégia 72"), (estrategia_73, "Estratégia 73"), (estrategia_74, "Estratégia 74"), (estrategia_75, "Estratégia 75"), (estrategia_76, "Estratégia 76"), (estrategia_77, "Estratégia 77"), (estrategia_78, "Estratégia 78"), (estrategia_79, "Estratégia 79"), 
        (estrategia_80, "Estratégia 80"), (estrategia_81, "Estratégia 81"), (estrategia_82, "Estratégia 82"), (estrategia_83, "Estratégia 83"), (estrategia_84, "Estratégia 84"), (estrategia_85, "Estratégia 85"), (estrategia_86, "Estratégia 86"), 
        (estrategia_87, "Estratégia 87"), (estrategia_88, "Estratégia 88"), (estrategia_89, "Estratégia 89"), (estrategia_90, "Estratégia 90"), (estrategia_91, "Estratégia 91"), (estrategia_92, "Estratégia 92"), (estrategia_93, "Estratégia 93"), 
        (estrategia_94, "Estratégia 94"), (estrategia_95, "Estratégia 95"), (estrategia_96, "Estratégia 96"), (estrategia_97, "Estratégia 97"), (estrategia_98, "Estratégia 98"), (estrategia_99, "Estratégia 99"), (estrategia_100, "Estratégia 100"), 
        (estrategia_101, "Estratégia 101"), (estrategia_102, "Estratégia 102"), (estrategia_103, "Estratégia 103"), (estrategia_104, "Estratégia 104"), (estrategia_105, "Estratégia 105"), (estrategia_106, "Estratégia 106"), (estrategia_107, "Estratégia 107"), 
        (estrategia_108, "Estratégia 108"), (estrategia_109, "Estratégia 109"), (estrategia_110, "Estratégia 110"), (estrategia_111, "Estratégia 111"), (estrategia_112, "Estratégia 112"), (estrategia_113, "Estratégia 113"), (estrategia_114, "Estratégia 114"), 
        (estrategia_115, "Estratégia 115"), (estrategia_116, "Estratégia 116"), (estrategia_117, "Estratégia 117"), (estrategia_118, "Estratégia 118"), (estrategia_119, "Estratégia 119"), (estrategia_120, "Estratégia 120"), (estrategia_121, "Estratégia 121"), 
        (estrategia_122, "Estratégia 122"), (estrategia_123, "Estratégia 123"), (estrategia_124, "Estratégia 124"), (estrategia_125, "Estratégia 125"), (estrategia_126, "Estratégia 126"), (estrategia_127, "Estratégia 127"), (estrategia_128, "Estratégia 128"), 
        (estrategia_129, "Estratégia 129"), (estrategia_130, "Estratégia 130"), (estrategia_131, "Estratégia 131"), (estrategia_132, "Estratégia 132"), (estrategia_133, "Estratégia 133"), (estrategia_134, "Estratégia 134"), (estrategia_135, "Estratégia 135"), 
        (estrategia_136, "Estratégia 136"), (estrategia_137, "Estratégia 137"), (estrategia_138, "Estratégia 138"), (estrategia_139, "Estratégia 139"), (estrategia_140, "Estratégia 140"), (estrategia_141, "Estratégia 141"), (estrategia_142, "Estratégia 142"), 
        (estrategia_143, "Estratégia 143"), (estrategia_144, "Estratégia 144"),        (estrategia_145, "Estratégia 145"), (estrategia_146, "Estratégia 146"), (estrategia_147, "Estratégia 147"), (estrategia_148, "Estratégia 148"), (estrategia_149, "Estratégia 149"), (estrategia_150, "Estratégia 150"), (estrategia_151, "Estratégia 151"), 
        (estrategia_152, "Estratégia 152"), (estrategia_153, "Estratégia 153"), (estrategia_154, "Estratégia 154"), (estrategia_155, "Estratégia 155"), (estrategia_156, "Estratégia 156"), (estrategia_157, "Estratégia 157"), (estrategia_158, "Estratégia 158"), 
        (estrategia_159, "Estratégia 159"), (estrategia_160, "Estratégia 160"), (estrategia_161, "Estratégia 161"), (estrategia_162, "Estratégia 162"), (estrategia_163, "Estratégia 163"), (estrategia_164, "Estratégia 164"), (estrategia_165, "Estratégia 165"), 
        (estrategia_166, "Estratégia 166"), (estrategia_167, "Estratégia 167"), (estrategia_168, "Estratégia 168"), (estrategia_169, "Estratégia 169"), (estrategia_170, "Estratégia 170"), (estrategia_171, "Estratégia 171"), (estrategia_172, "Estratégia 172"), 
        (estrategia_173, "Estratégia 173"), (estrategia_174, "Estratégia 174"), (estrategia_175, "Estratégia 175"), (estrategia_176, "Estratégia 176"), (estrategia_177, "Estratégia 177"), (estrategia_178, "Estratégia 178"), (estrategia_179, "Estratégia 179"), 
        (estrategia_180, "Estratégia 180"), (estrategia_181, "Estratégia 181"), (estrategia_182, "Estratégia 182"), (estrategia_183, "Estratégia 183"), (estrategia_184, "Estratégia 184"), (estrategia_185, "Estratégia 185"), (estrategia_186, "Estratégia 186"), 
        (estrategia_187, "Estratégia 187"), (estrategia_188, "Estratégia 188"), (estrategia_189, "Estratégia 189"), (estrategia_190, "Estratégia 190"), (estrategia_191, "Estratégia 191"), (estrategia_192, "Estratégia 192"), (estrategia_193, "Estratégia 193"), 
        (estrategia_194, "Estratégia 194"), (estrategia_195, "Estratégia 195"), (estrategia_196, "Estratégia 196"), (estrategia_197, "Estratégia 197"), (estrategia_198, "Estratégia 198"), (estrategia_199, "Estratégia 199"), (estrategia_200, "Estratégia 200"), 
        (estrategia_201, "Estratégia 201"), (estrategia_202, "Estratégia 202"), (estrategia_203, "Estratégia 203"), (estrategia_204, "Estratégia 204"), (estrategia_205, "Estratégia 205"), (estrategia_206, "Estratégia 206"), (estrategia_207, "Estratégia 207"), 
        (estrategia_208, "Estratégia 208"), (estrategia_209, "Estratégia 209"), (estrategia_210, "Estratégia 210"), (estrategia_211, "Estratégia 211"), (estrategia_212, "Estratégia 212"), (estrategia_213, "Estratégia 213"), (estrategia_214, "Estratégia 214"), 
        (estrategia_215, "Estratégia 215"), (estrategia_216, "Estratégia 216"),         (estrategia_217, "Estratégia 217"), (estrategia_218, "Estratégia 218"), (estrategia_219, "Estratégia 219"), (estrategia_220, "Estratégia 220"), 
        (estrategia_221, "Estratégia 221"), (estrategia_222, "Estratégia 222"), (estrategia_223, "Estratégia 223"), (estrategia_224, "Estratégia 224"), 
        (estrategia_225, "Estratégia 225"), (estrategia_226, "Estratégia 226"), (estrategia_227, "Estratégia 227"), (estrategia_228, "Estratégia 228"), 
        (estrategia_229, "Estratégia 229"), (estrategia_230, "Estratégia 230"), (estrategia_231, "Estratégia 231"), (estrategia_232, "Estratégia 232"), 
        (estrategia_233, "Estratégia 233"), (estrategia_234, "Estratégia 234"), (estrategia_235, "Estratégia 235"), (estrategia_236, "Estratégia 236"), 
        (estrategia_237, "Estratégia 237"), (estrategia_238, "Estratégia 238"), (estrategia_239, "Estratégia 239"), (estrategia_240, "Estratégia 240"), 
        (estrategia_241, "Estratégia 241"), (estrategia_242, "Estratégia 242"), (estrategia_243, "Estratégia 243"), (estrategia_244, "Estratégia 244"), 
        (estrategia_245, "Estratégia 245"), (estrategia_246, "Estratégia 246"), (estrategia_247, "Estratégia 247"), (estrategia_248, "Estratégia 248"), 
        (estrategia_249, "Estratégia 249"), (estrategia_250, "Estratégia 250"), (estrategia_251, "Estratégia 251"), (estrategia_252, "Estratégia 252"), 
        (estrategia_253, "Estratégia 253"), (estrategia_254, "Estratégia 254"), (estrategia_255, "Estratégia 255"), (estrategia_256, "Estratégia 256"), 
        (estrategia_257, "Estratégia 257"), (estrategia_258, "Estratégia 258"), (estrategia_259, "Estratégia 259"), (estrategia_260, "Estratégia 260"), 
        (estrategia_261, "Estratégia 261"), (estrategia_262, "Estratégia 262"),         (estrategia_263, "Estratégia 263"), (estrategia_264, "Estratégia 264"), (estrategia_265, "Estratégia 265"), (estrategia_266, "Estratégia 266"), 
        (estrategia_267, "Estratégia 267"), (estrategia_268, "Estratégia 268"), (estrategia_269, "Estratégia 269"), (estrategia_270, "Estratégia 270"), 
        (estrategia_271, "Estratégia 271"), (estrategia_272, "Estratégia 272"), (estrategia_273, "Estratégia 273"), (estrategia_274, "Estratégia 274"), 
        (estrategia_275, "Estratégia 275"), (estrategia_276, "Estratégia 276"), (estrategia_277, "Estratégia 277"), (estrategia_278, "Estratégia 278"), 
        (estrategia_279, "Estratégia 279"), (estrategia_280, "Estratégia 280"), (estrategia_281, "Estratégia 281"), (estrategia_282, "Estratégia 282"), 
        (estrategia_283, "Estratégia 283"), (estrategia_284, "Estratégia 284"), (estrategia_285, "Estratégia 285"), (estrategia_286, "Estratégia 286"), 
        (estrategia_287, "Estratégia 287"), (estrategia_288, "Estratégia 288"), (estrategia_289, "Estratégia 289"), (estrategia_290, "Estratégia 290"), 
        (estrategia_291, "Estratégia 291"), (estrategia_292, "Estratégia 292"), (estrategia_293, "Estratégia 293"), (estrategia_294, "Estratégia 294"), 
        (estrategia_295, "Estratégia 295"), (estrategia_296, "Estratégia 296"), (estrategia_297, "Estratégia 297"), (estrategia_298, "Estratégia 298"), 
        (estrategia_299, "Estratégia 299"), (estrategia_300, "Estratégia 300"), (estrategia_301, "Estratégia 301"), (estrategia_302, "Estratégia 302"), 
        (estrategia_303, "Estratégia 303"), (estrategia_304, "Estratégia 304"), (estrategia_305, "Estratégia 305"), (estrategia_306, "Estratégia 306"), 
        (estrategia_307, "Estratégia 307"), (estrategia_308, "Estratégia 308"), (estrategia_309, "Estratégia 309"), (estrategia_310, "Estratégia 310"), 
        (estrategia_311, "Estratégia 311"), (estrategia_312, "Estratégia 312"), (estrategia_313, "Estratégia 313"), (estrategia_314, "Estratégia 314"), 
        (estrategia_315, "Estratégia 315"), (estrategia_316, "Estratégia 316"), (estrategia_317, "Estratégia 317"), (estrategia_318, "Estratégia 318"), 
        (estrategia_319, "Estratégia 319"), (estrategia_320, "Estratégia 320"), (estrategia_321, "Estratégia 321"), (estrategia_322, "Estratégia 322"), 
        (estrategia_323, "Estratégia 323"), (estrategia_324, "Estratégia 324"), (estrategia_325, "Estratégia 325"), (estrategia_326, "Estratégia 326"), 
        (estrategia_327, "Estratégia 327"), (estrategia_328, "Estratégia 328"), (estrategia_329, "Estratégia 329"), (estrategia_330, "Estratégia 330"), 
        (estrategia_331, "Estratégia 331"), (estrategia_332, "Estratégia 332"), (estrategia_333, "Estratégia 333"), (estrategia_334, "Estratégia 334"),        (estrategia_335, "Estratégia 335"), (estrategia_336, "Estratégia 336"), (estrategia_337, "Estratégia 337"), (estrategia_338, "Estratégia 338"), 
        (estrategia_339, "Estratégia 339"), (estrategia_340, "Estratégia 340"), (estrategia_341, "Estratégia 341"), (estrategia_342, "Estratégia 342"), 
        (estrategia_343, "Estratégia 343"), (estrategia_344, "Estratégia 344"), (estrategia_345, "Estratégia 345"), (estrategia_346, "Estratégia 346"), 
        (estrategia_347, "Estratégia 347"), (estrategia_348, "Estratégia 348"), (estrategia_349, "Estratégia 349"), (estrategia_350, "Estratégia 350"), 
        (estrategia_351, "Estratégia 351"), (estrategia_352, "Estratégia 352"), (estrategia_353, "Estratégia 353"), (estrategia_354, "Estratégia 354"), 
        (estrategia_355, "Estratégia 355"), (estrategia_356, "Estratégia 356"), (estrategia_357, "Estratégia 357"), (estrategia_358, "Estratégia 358"), 
        (estrategia_359, "Estratégia 359"), (estrategia_360, "Estratégia 360"), (estrategia_361, "Estratégia 361"), (estrategia_362, "Estratégia 362"), 
        (estrategia_363, "Estratégia 363"), (estrategia_364, "Estratégia 364"), (estrategia_365, "Estratégia 365"), (estrategia_366, "Estratégia 366"), 
        (estrategia_367, "Estratégia 367"), (estrategia_368, "Estratégia 368"), (estrategia_369, "Estratégia 369"), (estrategia_370, "Estratégia 370"), 
        (estrategia_371, "Estratégia 371"), (estrategia_372, "Estratégia 372"), (estrategia_373, "Estratégia 373"), (estrategia_374, "Estratégia 374"), 
        (estrategia_375, "Estratégia 375"), (estrategia_376, "Estratégia 376"), (estrategia_377, "Estratégia 377"), (estrategia_378, "Estratégia 378"), 
        (estrategia_379, "Estratégia 379"), (estrategia_380, "Estratégia 380"), (estrategia_381, "Estratégia 381"), (estrategia_382, "Estratégia 382"), 
        (estrategia_383, "Estratégia 383"), (estrategia_384, "Estratégia 384"), (estrategia_385, "Estratégia 385"), (estrategia_386, "Estratégia 386"), 
        (estrategia_387, "Estratégia 387"), (estrategia_388, "Estratégia 388"), (estrategia_389, "Estratégia 389"), (estrategia_390, "Estratégia 390"), 
        (estrategia_391, "Estratégia 391"), (estrategia_392, "Estratégia 392"), (estrategia_393, "Estratégia 393"), (estrategia_394, "Estratégia 394"), 
        (estrategia_395, "Estratégia 395"), (estrategia_396, "Estratégia 396"), (estrategia_397, "Estratégia 397"), (estrategia_398, "Estratégia 398"), 
        (estrategia_399, "Estratégia 399"), (estrategia_400, "Estratégia 400"), (estrategia_401, "Estratégia 401"), (estrategia_402, "Estratégia 402"), 
        (estrategia_403, "Estratégia 403"), (estrategia_404, "Estratégia 404"), (estrategia_405, "Estratégia 405"), (estrategia_406, "Estratégia 406"),        (estrategia_407, "Estratégia 407"), (estrategia_408, "Estratégia 408"), (estrategia_409, "Estratégia 409"), (estrategia_410, "Estratégia 410"), 
        (estrategia_411, "Estratégia 411"), (estrategia_412, "Estratégia 412"), (estrategia_413, "Estratégia 413"), (estrategia_414, "Estratégia 414"), 
        (estrategia_415, "Estratégia 415"), (estrategia_416, "Estratégia 416"), (estrategia_417, "Estratégia 417"), (estrategia_418, "Estratégia 418"), 
        (estrategia_419, "Estratégia 419"), (estrategia_420, "Estratégia 420"), (estrategia_421, "Estratégia 421"), (estrategia_422, "Estratégia 422"), 
        (estrategia_423, "Estratégia 423"), (estrategia_424, "Estratégia 424"), (estrategia_425, "Estratégia 425"), (estrategia_426, "Estratégia 426"), 
        (estrategia_427, "Estratégia 427"), (estrategia_428, "Estratégia 428"), (estrategia_429, "Estratégia 429"), (estrategia_430, "Estratégia 430"), 
        (estrategia_431, "Estratégia 431"), (estrategia_432, "Estratégia 432"), (estrategia_433, "Estratégia 433"), (estrategia_434, "Estratégia 434"), 
        (estrategia_435, "Estratégia 435"), (estrategia_436, "Estratégia 436"), (estrategia_437, "Estratégia 437"), (estrategia_438, "Estratégia 438"), 
        (estrategia_439, "Estratégia 439"), (estrategia_440, "Estratégia 440"), (estrategia_441, "Estratégia 441"), (estrategia_442, "Estratégia 442"), 
        (estrategia_443, "Estratégia 443"), (estrategia_444, "Estratégia 444"), (estrategia_445, "Estratégia 445"), (estrategia_446, "Estratégia 446"), 
        (estrategia_447, "Estratégia 447"), (estrategia_448, "Estratégia 448"), (estrategia_449, "Estratégia 449"), (estrategia_450, "Estratégia 450"), 
        (estrategia_451, "Estratégia 451"), (estrategia_452, "Estratégia 452"), (estrategia_453, "Estratégia 453"), (estrategia_454, "Estratégia 454"), 
        (estrategia_455, "Estratégia 455"), (estrategia_456, "Estratégia 456"), (estrategia_457, "Estratégia 457"), (estrategia_458, "Estratégia 458"), 
        (estrategia_459, "Estratégia 459"), (estrategia_460, "Estratégia 460"), (estrategia_461, "Estratégia 461"), (estrategia_462, "Estratégia 462"), 
        (estrategia_463, "Estratégia 463"), (estrategia_464, "Estratégia 464"), (estrategia_465, "Estratégia 465"), (estrategia_466, "Estratégia 466"), 
        (estrategia_467, "Estratégia 467"), (estrategia_468, "Estratégia 468"), (estrategia_469, "Estratégia 469"), (estrategia_470, "Estratégia 470"), 
        (estrategia_471, "Estratégia 471"), (estrategia_472, "Estratégia 472"), (estrategia_473, "Estratégia 473"), (estrategia_474, "Estratégia 474"), 
        (estrategia_475, "Estratégia 475"), (estrategia_476, "Estratégia 476"), (estrategia_477, "Estratégia 477"), (estrategia_478, "Estratégia 478"),        (estrategia_479, "Estratégia 479"), (estrategia_480, "Estratégia 480"), (estrategia_481, "Estratégia 481"), (estrategia_482, "Estratégia 482"), 
        (estrategia_483, "Estratégia 483"), (estrategia_484, "Estratégia 484"), (estrategia_485, "Estratégia 485"), (estrategia_486, "Estratégia 486"), 
        (estrategia_487, "Estratégia 487"), (estrategia_488, "Estratégia 488"), (estrategia_489, "Estratégia 489"), (estrategia_490, "Estratégia 490"), 
        (estrategia_491, "Estratégia 491"), (estrategia_492, "Estratégia 492"), (estrategia_493, "Estratégia 493"), (estrategia_494, "Estratégia 494"), 
        (estrategia_495, "Estratégia 495"), (estrategia_496, "Estratégia 496"), (estrategia_497, "Estratégia 497"), (estrategia_498, "Estratégia 498"), 
        (estrategia_499, "Estratégia 499"), (estrategia_500, "Estratégia 500"), (estrategia_501, "Estratégia 501"), (estrategia_502, "Estratégia 502"), 
        (estrategia_503, "Estratégia 503"), (estrategia_504, "Estratégia 504"), (estrategia_505, "Estratégia 505"), (estrategia_506, "Estratégia 506"), 
        (estrategia_507, "Estratégia 507"), (estrategia_508, "Estratégia 508"), (estrategia_509, "Estratégia 509"), (estrategia_510, "Estratégia 510"), 
        (estrategia_511, "Estratégia 511"), (estrategia_512, "Estratégia 512"), (estrategia_513, "Estratégia 513"), (estrategia_514, "Estratégia 514"), 
        (estrategia_515, "Estratégia 515"), (estrategia_516, "Estratégia 516"), (estrategia_517, "Estratégia 517"), (estrategia_518, "Estratégia 518"), 
        (estrategia_519, "Estratégia 519"), (estrategia_520, "Estratégia 520"), (estrategia_521, "Estratégia 521"), (estrategia_522, "Estratégia 522"), 
        (estrategia_523, "Estratégia 523"), (estrategia_524, "Estratégia 524"), (estrategia_525, "Estratégia 525"), (estrategia_526, "Estratégia 526"), 
        (estrategia_527, "Estratégia 527"), (estrategia_528, "Estratégia 528"), (estrategia_529, "Estratégia 529"), (estrategia_530, "Estratégia 530"), 
        (estrategia_531, "Estratégia 531"), (estrategia_532, "Estratégia 532"), (estrategia_533, "Estratégia 533"), (estrategia_534, "Estratégia 534"), 
        (estrategia_535, "Estratégia 535"), (estrategia_536, "Estratégia 536"), (estrategia_537, "Estratégia 537"), (estrategia_538, "Estratégia 538"), 
        (estrategia_539, "Estratégia 539"), (estrategia_540, "Estratégia 540"), (estrategia_541, "Estratégia 541"), (estrategia_542, "Estratégia 542"), 
        (estrategia_543, "Estratégia 543"), (estrategia_544, "Estratégia 544"), (estrategia_545, "Estratégia 545"), (estrategia_546, "Estratégia 546"), 
        (estrategia_547, "Estratégia 547"), (estrategia_548, "Estratégia 548"), (estrategia_549, "Estratégia 549"), (estrategia_550, "Estratégia 550"),         (estrategia_551, "Estratégia 551"), (estrategia_552, "Estratégia 552"), (estrategia_553, "Estratégia 553"), (estrategia_554, "Estratégia 554"), 
        (estrategia_555, "Estratégia 555"), (estrategia_556, "Estratégia 556"), (estrategia_557, "Estratégia 557"), (estrategia_558, "Estratégia 558"), 
        (estrategia_559, "Estratégia 559"), (estrategia_560, "Estratégia 560"), (estrategia_561, "Estratégia 561"), (estrategia_562, "Estratégia 562"), 
        (estrategia_563, "Estratégia 563"), (estrategia_564, "Estratégia 564"), (estrategia_565, "Estratégia 565"), (estrategia_566, "Estratégia 566"), 
        (estrategia_567, "Estratégia 567"), (estrategia_568, "Estratégia 568"), (estrategia_569, "Estratégia 569"), (estrategia_570, "Estratégia 570"), 
        (estrategia_571, "Estratégia 571"), (estrategia_572, "Estratégia 572"), (estrategia_573, "Estratégia 573"), (estrategia_574, "Estratégia 574"), 
        (estrategia_575, "Estratégia 575"), (estrategia_576, "Estratégia 576"), (estrategia_577, "Estratégia 577"), (estrategia_578, "Estratégia 578"), 
        (estrategia_579, "Estratégia 579"), (estrategia_580, "Estratégia 580"), (estrategia_581, "Estratégia 581"), (estrategia_582, "Estratégia 582"), 
        (estrategia_583, "Estratégia 583"), (estrategia_584, "Estratégia 584"), (estrategia_585, "Estratégia 585"), (estrategia_586, "Estratégia 586"), 
        (estrategia_587, "Estratégia 587"), (estrategia_588, "Estratégia 588"), (estrategia_589, "Estratégia 589"), (estrategia_590, "Estratégia 590"), 
        (estrategia_591, "Estratégia 591"), (estrategia_592, "Estratégia 592"), (estrategia_593, "Estratégia 593"), (estrategia_594, "Estratégia 594"), 
        (estrategia_595, "Estratégia 595"), (estrategia_596, "Estratégia 596"), (estrategia_597, "Estratégia 597"), (estrategia_598, "Estratégia 598"), 
        (estrategia_599, "Estratégia 599"), (estrategia_600, "Estratégia 600"), (estrategia_601, "Estratégia 601"), (estrategia_602, "Estratégia 602"), 
        (estrategia_603, "Estratégia 603"), (estrategia_604, "Estratégia 604"), (estrategia_605, "Estratégia 605"), (estrategia_606, "Estratégia 606"), 
        (estrategia_607, "Estratégia 607"), (estrategia_608, "Estratégia 608"), (estrategia_609, "Estratégia 609"), (estrategia_610, "Estratégia 610"), 
        (estrategia_611, "Estratégia 611"), (estrategia_612, "Estratégia 612"), (estrategia_613, "Estratégia 613"), (estrategia_614, "Estratégia 614"), 
        (estrategia_615, "Estratégia 615"), (estrategia_616, "Estratégia 616"), (estrategia_617, "Estratégia 617"), (estrategia_618, "Estratégia 618"), 
        (estrategia_619, "Estratégia 619"), (estrategia_620, "Estratégia 620"), (estrategia_621, "Estratégia 621"), (estrategia_622, "Estratégia 622"),         (estrategia_623, "Estratégia 623"), (estrategia_624, "Estratégia 624"), (estrategia_625, "Estratégia 625"), (estrategia_626, "Estratégia 626"), 
        (estrategia_627, "Estratégia 627"), (estrategia_628, "Estratégia 628"), (estrategia_629, "Estratégia 629"), (estrategia_630, "Estratégia 630"), 
        (estrategia_631, "Estratégia 631"), (estrategia_632, "Estratégia 632"), (estrategia_633, "Estratégia 633"), (estrategia_634, "Estratégia 634"), 
        (estrategia_635, "Estratégia 635"), (estrategia_636, "Estratégia 636"), (estrategia_637, "Estratégia 637"), (estrategia_638, "Estratégia 638"), 
        (estrategia_639, "Estratégia 639"), (estrategia_640, "Estratégia 640"), (estrategia_641, "Estratégia 641"), (estrategia_642, "Estratégia 642"), 
        (estrategia_643, "Estratégia 643"), (estrategia_644, "Estratégia 644"), (estrategia_645, "Estratégia 645"), (estrategia_646, "Estratégia 646"), 
        (estrategia_647, "Estratégia 647"), (estrategia_648, "Estratégia 648"), (estrategia_649, "Estratégia 649"), (estrategia_650, "Estratégia 650"), 
        (estrategia_651, "Estratégia 651"), (estrategia_652, "Estratégia 652"), (estrategia_653, "Estratégia 653"), (estrategia_654, "Estratégia 654"), 
        (estrategia_655, "Estratégia 655"), (estrategia_656, "Estratégia 656"), (estrategia_657, "Estratégia 657"), (estrategia_658, "Estratégia 658"), 
        (estrategia_659, "Estratégia 659"), (estrategia_660, "Estratégia 660"), (estrategia_661, "Estratégia 661"), (estrategia_662, "Estratégia 662"), 
        (estrategia_663, "Estratégia 663"), (estrategia_664, "Estratégia 664"), (estrategia_665, "Estratégia 665"), (estrategia_666, "Estratégia 666"), 
        (estrategia_667, "Estratégia 667"), (estrategia_668, "Estratégia 668"), (estrategia_669, "Estratégia 669"), (estrategia_670, "Estratégia 670"), 
        (estrategia_671, "Estratégia 671"), (estrategia_672, "Estratégia 672"), (estrategia_673, "Estratégia 673"), (estrategia_674, "Estratégia 674"), 
        (estrategia_675, "Estratégia 675"), (estrategia_676, "Estratégia 676"), (estrategia_677, "Estratégia 677"), (estrategia_678, "Estratégia 678"), 
        (estrategia_679, "Estratégia 679"), (estrategia_680, "Estratégia 680"), (estrategia_681, "Estratégia 681"), (estrategia_682, "Estratégia 682"), 
        (estrategia_683, "Estratégia 683"), (estrategia_684, "Estratégia 684"), (estrategia_685, "Estratégia 685"), (estrategia_686, "Estratégia 686"), 
        (estrategia_687, "Estratégia 687"), (estrategia_688, "Estratégia 688"), (estrategia_689, "Estratégia 689"), (estrategia_690, "Estratégia 690"), 
        (estrategia_691, "Estratégia 691"), (estrategia_692, "Estratégia 692"), (estrategia_693, "Estratégia 693"), (estrategia_694, "Estratégia 694"), (estrategia_695, "Estratégia 695"), (estrategia_696, "Estratégia 696"), (estrategia_697, "Estratégia 697"), (estrategia_698, "Estratégia 698"), 
        (estrategia_699, "Estratégia 699"), (estrategia_700, "Estratégia 700"), (estrategia_701, "Estratégia 701"), (estrategia_702, "Estratégia 702"), 
        (estrategia_703, "Estratégia 703"), (estrategia_704, "Estratégia 704"), (estrategia_705, "Estratégia 705"), (estrategia_706, "Estratégia 706"), 
        (estrategia_707, "Estratégia 707"), (estrategia_708, "Estratégia 708"), (estrategia_709, "Estratégia 709"), (estrategia_710, "Estratégia 710"), 
        (estrategia_711, "Estratégia 711"), (estrategia_712, "Estratégia 712"), (estrategia_713, "Estratégia 713"), (estrategia_714, "Estratégia 714"), 
        (estrategia_715, "Estratégia 715"), (estrategia_716, "Estratégia 716"), (estrategia_717, "Estratégia 717"), (estrategia_718, "Estratégia 718"), 
        (estrategia_719, "Estratégia 719"), (estrategia_720, "Estratégia 720"), (estrategia_721, "Estratégia 721"), (estrategia_722, "Estratégia 722"), 
        (estrategia_723, "Estratégia 723"), (estrategia_724, "Estratégia 724"), (estrategia_725, "Estratégia 725"), (estrategia_726, "Estratégia 726"), 
        (estrategia_727, "Estratégia 727"), (estrategia_728, "Estratégia 728"), (estrategia_729, "Estratégia 729"), (estrategia_730, "Estratégia 730"), 
        (estrategia_731, "Estratégia 731"), (estrategia_732, "Estratégia 732"), (estrategia_733, "Estratégia 733"), (estrategia_734, "Estratégia 734"), 
        (estrategia_735, "Estratégia 735"), (estrategia_736, "Estratégia 736"), (estrategia_737, "Estratégia 737"), (estrategia_738, "Estratégia 738"), 
        (estrategia_739, "Estratégia 739"), (estrategia_740, "Estratégia 740"), (estrategia_741, "Estratégia 741"), (estrategia_742, "Estratégia 742"), 
        (estrategia_743, "Estratégia 743"), (estrategia_744, "Estratégia 744"), (estrategia_745, "Estratégia 745"), (estrategia_746, "Estratégia 746"), 
        (estrategia_747, "Estratégia 747"), (estrategia_748, "Estratégia 748"), (estrategia_749, "Estratégia 749"), (estrategia_750, "Estratégia 750"), 
        (estrategia_751, "Estratégia 751"), (estrategia_752, "Estratégia 752"), (estrategia_753, "Estratégia 753"), (estrategia_754, "Estratégia 754"), 
        (estrategia_755, "Estratégia 755"), (estrategia_756, "Estratégia 756"), (estrategia_757, "Estratégia 757"), (estrategia_758, "Estratégia 758"), 
        (estrategia_759, "Estratégia 759"), (estrategia_760, "Estratégia 760"), (estrategia_761, "Estratégia 761"), (estrategia_762, "Estratégia 762"), 
        (estrategia_763, "Estratégia 763"), (estrategia_764, "Estratégia 764"), (estrategia_765, "Estratégia 765"), (estrategia_766, "Estratégia 766"), (estrategia_767, "Estratégia 767"), (estrategia_768, "Estratégia 768"), (estrategia_769, "Estratégia 769"), (estrategia_770, "Estratégia 770"), 
        (estrategia_771, "Estratégia 771"), (estrategia_772, "Estratégia 772"), (estrategia_773, "Estratégia 773"), (estrategia_774, "Estratégia 774"), 
        (estrategia_775, "Estratégia 775"), (estrategia_776, "Estratégia 776"), (estrategia_777, "Estratégia 777"), (estrategia_778, "Estratégia 778"), 
        (estrategia_779, "Estratégia 779"), (estrategia_780, "Estratégia 780"), (estrategia_781, "Estratégia 781"), (estrategia_782, "Estratégia 782"), 
        (estrategia_783, "Estratégia 783"), (estrategia_784, "Estratégia 784"), (estrategia_785, "Estratégia 785"), (estrategia_786, "Estratégia 786"), 
        (estrategia_787, "Estratégia 787"), (estrategia_788, "Estratégia 788"), (estrategia_789, "Estratégia 789"), (estrategia_790, "Estratégia 790"), 
        (estrategia_791, "Estratégia 791"), (estrategia_792, "Estratégia 792"), (estrategia_793, "Estratégia 793"), (estrategia_794, "Estratégia 794"), 
        (estrategia_795, "Estratégia 795"), (estrategia_796, "Estratégia 796"), (estrategia_797, "Estratégia 797"), (estrategia_798, "Estratégia 798"), 
        (estrategia_799, "Estratégia 799"), (estrategia_800, "Estratégia 800"), (estrategia_801, "Estratégia 801"), (estrategia_802, "Estratégia 802"), 
        (estrategia_803, "Estratégia 803"), (estrategia_804, "Estratégia 804"), (estrategia_805, "Estratégia 805"), (estrategia_806, "Estratégia 806"), 
        (estrategia_807, "Estratégia 807"), (estrategia_808, "Estratégia 808"), (estrategia_809, "Estratégia 809"), (estrategia_810, "Estratégia 810"), 
        (estrategia_811, "Estratégia 811"), (estrategia_812, "Estratégia 812"), (estrategia_813, "Estratégia 813"), (estrategia_814, "Estratégia 814"), 
        (estrategia_815, "Estratégia 815"), (estrategia_816, "Estratégia 816"), (estrategia_817, "Estratégia 817"), (estrategia_818, "Estratégia 818"), 
        (estrategia_819, "Estratégia 819"), (estrategia_820, "Estratégia 820"), (estrategia_821, "Estratégia 821"), (estrategia_822, "Estratégia 822"), 
        (estrategia_823, "Estratégia 823"), (estrategia_824, "Estratégia 824"), (estrategia_825, "Estratégia 825"), (estrategia_826, "Estratégia 826"), 
        (estrategia_827, "Estratégia 827"), (estrategia_828, "Estratégia 828"), (estrategia_829, "Estratégia 829"), (estrategia_830, "Estratégia 830"), 
        (estrategia_831, "Estratégia 831"), (estrategia_832, "Estratégia 832"), (estrategia_833, "Estratégia 833"), (estrategia_834, "Estratégia 834"), 
        (estrategia_835, "Estratégia 835"), (estrategia_836, "Estratégia 836"), (estrategia_837, "Estratégia 837"), (estrategia_838, "Estratégia 838"),         (estrategia_839, "Estratégia 839"), (estrategia_840, "Estratégia 840"), (estrategia_841, "Estratégia 841"), (estrategia_842, "Estratégia 842"),
        (estrategia_843, "Estratégia 843"), (estrategia_844, "Estratégia 844"), (estrategia_845, "Estratégia 845"), (estrategia_846, "Estratégia 846"),
        (estrategia_847, "Estratégia 847"), (estrategia_848, "Estratégia 848"), (estrategia_849, "Estratégia 849"), (estrategia_850, "Estratégia 850"),
        (estrategia_851, "Estratégia 851"), (estrategia_852, "Estratégia 852"), (estrategia_853, "Estratégia 853"), (estrategia_854, "Estratégia 854"),
        (estrategia_855, "Estratégia 855"), (estrategia_856, "Estratégia 856"), (estrategia_857, "Estratégia 857"), (estrategia_858, "Estratégia 858"),
        (estrategia_859, "Estratégia 859"), (estrategia_860, "Estratégia 860"), (estrategia_861, "Estratégia 861"), (estrategia_862, "Estratégia 862"),
        (estrategia_863, "Estratégia 863"), (estrategia_864, "Estratégia 864"), (estrategia_865, "Estratégia 865"), (estrategia_866, "Estratégia 866"),
        (estrategia_867, "Estratégia 867"), (estrategia_868, "Estratégia 868"), (estrategia_869, "Estratégia 869"), (estrategia_870, "Estratégia 870"),
        (estrategia_871, "Estratégia 871"), (estrategia_872, "Estratégia 872"), (estrategia_873, "Estratégia 873"), (estrategia_874, "Estratégia 874"),
        (estrategia_875, "Estratégia 875"), (estrategia_876, "Estratégia 876"), (estrategia_877, "Estratégia 877"), (estrategia_878, "Estratégia 878"),
        (estrategia_879, "Estratégia 879"), (estrategia_880, "Estratégia 880"), (estrategia_881, "Estratégia 881"), (estrategia_882, "Estratégia 882"),
        (estrategia_883, "Estratégia 883"), (estrategia_884, "Estratégia 884"), (estrategia_885, "Estratégia 885"), (estrategia_886, "Estratégia 886"),
        (estrategia_887, "Estratégia 887"), (estrategia_888, "Estratégia 888"), (estrategia_889, "Estratégia 889"), (estrategia_890, "Estratégia 890"),
        (estrategia_891, "Estratégia 891"), (estrategia_892, "Estratégia 892"), (estrategia_893, "Estratégia 893"), (estrategia_894, "Estratégia 894"),
        (estrategia_895, "Estratégia 895"), (estrategia_896, "Estratégia 896"), (estrategia_897, "Estratégia 897"), (estrategia_898, "Estratégia 898"),
        (estrategia_899, "Estratégia 899"), (estrategia_900, "Estratégia 900"), (estrategia_901, "Estratégia 901"), (estrategia_902, "Estratégia 902"),
        (estrategia_903, "Estratégia 903"), (estrategia_904, "Estratégia 904"), (estrategia_905, "Estratégia 905"), (estrategia_906, "Estratégia 906"),
        (estrategia_907, "Estratégia 907"), (estrategia_908, "Estratégia 908"), (estrategia_909, "Estratégia 909"), (estrategia_910, "Estratégia 910"),
        (estrategia_911, "Estratégia 911"), (estrategia_912, "Estratégia 912"), (estrategia_913, "Estratégia 913"), (estrategia_914, "Estratégia 914"),
        (estrategia_915, "Estratégia 915"), (estrategia_916, "Estratégia 916"), (estrategia_917, "Estratégia 917"), (estrategia_918, "Estratégia 918"),
        (estrategia_919, "Estratégia 919"), (estrategia_920, "Estratégia 920"), (estrategia_921, "Estratégia 921"), (estrategia_922, "Estratégia 922"),
        (estrategia_923, "Estratégia 923"), (estrategia_924, "Estratégia 924"), (estrategia_925, "Estratégia 925"), (estrategia_926, "Estratégia 926"),
        (estrategia_927, "Estratégia 927"), (estrategia_928, "Estratégia 928"), (estrategia_929, "Estratégia 929"), (estrategia_930, "Estratégia 930"),
        (estrategia_931, "Estratégia 931"), (estrategia_932, "Estratégia 932"), (estrategia_933, "Estratégia 933"), (estrategia_934, "Estratégia 934"),
        (estrategia_935, "Estratégia 935"), (estrategia_936, "Estratégia 936"), (estrategia_937, "Estratégia 937"), (estrategia_938, "Estratégia 938"),
        (estrategia_939, "Estratégia 939"), (estrategia_940, "Estratégia 940"), (estrategia_941, "Estratégia 941"), (estrategia_942, "Estratégia 942"),
        (estrategia_943, "Estratégia 943"), (estrategia_944, "Estratégia 944"), (estrategia_945, "Estratégia 945"), (estrategia_946, "Estratégia 946")






    ]

# Página teste
st.title("Back Away")

# --- Interface Streamlit ---
st.header("Upload da Planilha Histórica")
# --- MODIFICAÇÃO 1: Permitir XLSX e CSV no upload histórico ---
uploaded_historical = st.file_uploader(
    "Faça upload da planilha histórica (.xlsx ou .csv)",
    type=["xlsx", "csv"], # Permitir ambos os tipos
    key="hist_simple_csv"
)

if uploaded_historical is not None:
    # --- MODIFICAÇÃO 2: Usar a função load_dataframe ---
    df_historico_original = load_dataframe(uploaded_historical)
    # --- Fim da Modificação 2 ---

    if df_historico_original is not None:
        # Filtro Simples de Ligas (Histórico) - Mantém como estava
        if 'League' in df_historico_original.columns:
            df_historico = df_historico_original[df_historico_original['League'].isin(APPROVED_LEAGUES)].copy()
            if df_historico.empty and not df_historico_original.empty:
                 st.warning("Nenhum jogo do histórico pertence às ligas aprovadas.")
        else:
            st.warning("Coluna 'League' não encontrada no arquivo histórico. Filtro de ligas não aplicado.")
            df_historico = df_historico_original.copy()

        if not df_historico.empty:
            # Restante do código do backtest (mantém como estava)
            try:
                estrategias = apply_strategies(df_historico.copy())
            except Exception as e:
                st.error(f"Erro ao pré-calcular variáveis ou aplicar estratégias no histórico: {e}")
                estrategias = []

            if estrategias:
                st.header("Resultados do Backtest (Ligas Filtradas)")
                backtest_results = []
                medias_results = []
                resultados = {}

                for estrategia_func, estrategia_nome in estrategias:
                    backtest_result = run_backtest(df_historico.copy(), estrategia_func, estrategia_nome)
                    if backtest_result["Dataframe"] is not None and not backtest_result["Dataframe"].empty:
                         medias_result = check_moving_averages(backtest_result["Dataframe"].copy(), estrategia_nome)
                    else:
                         medias_result = {
                            "Estratégia": estrategia_nome, "Média 8": "N/A", "Média 40": "N/A", "Acima dos Limiares": False
                        }
                    backtest_results.append(backtest_result)
                    medias_results.append(medias_result)
                    resultados[estrategia_nome] = (backtest_result["Dataframe"], medias_result["Acima dos Limiares"])

                # Exibir resultados (mantém como estava)
                with st.expander("📊 Resultados do Backtest"):
                     st.subheader("Resumo do Backtest")
                     df_summary = pd.DataFrame([r for r in backtest_results if r["Total de Jogos"] > 0]).drop(columns=["Dataframe"], errors='ignore') # Added errors='ignore'
                     if not df_summary.empty:
                         st.dataframe(df_summary)
                     else:
                         st.write("Nenhum jogo encontrado para as estratégias após filtros.")

                #with st.expander("📈 Análise das Médias"):
                    #st.subheader("Detalhes das Médias")
                    #st.dataframe(pd.DataFrame(medias_results))
                   # Exibir análise das médias (o DataFrame resultante já terá as novas colunas)
                with st.expander("📈 Análise das Médias e Lucros Recentes"): # Nome atualizado
                 st.subheader("Detalhes das Médias e Lucros Recentes")
                # Cria o DataFrame a partir dos resultados, incluindo as novas chaves
                 df_medias = pd.DataFrame(medias_results) 
                 st.dataframe(df_medias) # O dataframe exibido agora incluirá as colunas de lucro    

                # Upload dos jogos do dia
                estrategias_aprovadas = [nome for nome, (_, acima) in resultados.items() if acima]
                if estrategias_aprovadas:
                    st.header("Upload dos Jogos do Dia")
                    # --- MODIFICAÇÃO 3: Permitir XLSX e CSV no upload diário ---
                    uploaded_daily = st.file_uploader(
                        "Faça upload da planilha com os jogos do dia (.xlsx ou .csv)",
                        type=["xlsx", "csv"], # Permitir ambos os tipos
                        key="daily_simple_csv"
                    )

                    if uploaded_daily is not None:
                        # --- MODIFICAÇÃO 4: Usar a função load_dataframe ---
                        df_daily_original = load_dataframe(uploaded_daily)
                        # --- Fim da Modificação 4 ---

                        if df_daily_original is not None:
                            # Filtro Simples de Ligas (Jogos do Dia) - Mantém como estava
                            if 'League' in df_daily_original.columns:
                                df_daily = df_daily_original[df_daily_original['League'].isin(APPROVED_LEAGUES)].copy()
                                if df_daily.empty and not df_daily_original.empty:
                                     st.warning("Nenhum jogo do dia pertence às ligas aprovadas.")
                            else:
                                st.warning("Coluna 'League' não encontrada no arquivo de jogos do dia. Filtro de ligas não aplicado.")
                                df_daily = df_daily_original.copy()

                            if not df_daily.empty:
                                # Restante da análise diária (mantém como estava)
                                st.header("Jogos Aprovados para Hoje (Ligas Filtradas)")
                                jogos_aprovados_total = []
                                mapa_estrategias_diarias = {} # Reset map

                                try:
                                    estrategias_diarias_funcs = apply_strategies(df_daily.copy())
                                    mapa_estrategias_diarias = {nome: func for func, nome in estrategias_diarias_funcs}
                                except Exception as e:
                                    st.error(f"Erro ao pré-calcular variáveis ou aplicar estratégias nos jogos do dia: {e}")
                                    # Keep mapa_estrategias_diarias as empty

                                if mapa_estrategias_diarias:
                                    for estrategia_nome in estrategias_aprovadas:
                                         if estrategia_nome in mapa_estrategias_diarias:
                                             estrategia_func_diaria = mapa_estrategias_diarias[estrategia_nome]
                                             jogos_aprovados = analyze_daily_games(df_daily.copy(), estrategia_func_diaria, estrategia_nome)
                                             if jogos_aprovados is not None and not jogos_aprovados.empty:
                                                 # st.subheader(f"{estrategia_nome}")
                                                 # st.dataframe(jogos_aprovados)
                                                 jogos_aprovados_total.extend(jogos_aprovados.to_dict('records'))
                                         else:
                                             st.info(f"Estratégia '{estrategia_nome}' não aplicável aos dados do dia.")


                                    if jogos_aprovados_total:
                                        df_jogos_aprovados_final = pd.DataFrame(jogos_aprovados_total)
                                        cols_to_check_duplicates = ['Time', 'Home', 'Away']
                                        if 'League' in df_jogos_aprovados_final.columns:
                                            cols_to_check_duplicates.insert(1, 'League')
                                        # Remove duplicates based on existing columns only
                                        cols_exist_check = [col for col in cols_to_check_duplicates if col in df_jogos_aprovados_final.columns]
                                        if cols_exist_check:
                                            df_jogos_aprovados_final = df_jogos_aprovados_final.drop_duplicates(subset=cols_exist_check)

                                        st.header("🏆 Lista Unificada de Jogos Aprovados")
                                        st.dataframe(df_jogos_aprovados_final)
                                    elif estrategias_aprovadas:
                                        st.write("Nenhum jogo do dia (nas ligas aprovadas) atende aos critérios das estratégias aprovadas.")
                                else: # Se o mapa não foi criado devido a erro em apply_strategies
                                     st.warning("Não foi possível aplicar estratégias aos jogos do dia devido a erro anterior.")


                            else: # Se df_daily vazio após filtro
                                st.info("Não há jogos do dia nas ligas aprovadas para analisar.")
                        # else: # df_daily_original is None (erro na leitura) - Mensagem já dada por load_dataframe
                        #    pass
                else: # Se não há estratégias aprovadas
                     st.info("Nenhuma estratégia foi aprovada na análise de médias.")
            else: # Se apply_strategies retornou vazio ou deu erro
                st.info("Não foi possível processar o backtest devido a erro nas estratégias/variáveis.")

        else: # Se df_historico vazio após filtro
            st.info("Não há dados históricos nas ligas aprovadas para realizar o backtest.")
    # else: # df_historico_original is None (erro na leitura) - Mensagem já dada por load_dataframe
    #    pass
