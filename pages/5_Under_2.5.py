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
st.title("Estratégias Under 2.5")

# Função genérica de Backtest (mantida como no seu exemplo)
def run_backtest(df, estrategia_func, estrategia_nome):
     # Filtrar pela Odd_H_Back maior que 1.30
    df = df[df['Odd_Under25_FT_Back'] >= 1.3]
     # Aplicar a estratégia
    df_filtrado = estrategia_func(df)
    df_filtrado['Total_Goals'] = df_filtrado['Goals_H'] + df_filtrado['Goals_A']
    
    # Verifica se o df_filtrado não está vazio antes de calcular o Profit
    if not df_filtrado.empty:
        df_filtrado['Profit'] = df_filtrado.apply(
            lambda row: (row['Odd_Under25_FT_Back'] - 1) if row['Total_Goals'] < 3 else -1,
            axis=1
        )
        total_jogos = len(df_filtrado)
        acertos = len(df_filtrado[df_filtrado['Total_Goals'] < 3])
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
    df_filtrado['Acerto'] = (df_filtrado['Total_Goals'] < 3).astype(int)
    
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
    
    def    estrategia_1(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR49'] >= 0.5159) & (vars_dict['VAR49'] <= 0.7959)].copy()   
    def    estrategia_2(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR47'] >= 1.2564) & (vars_dict['VAR47'] <= 1.9383)].copy()   
    def    estrategia_3(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR07'] >= 0.5068) & (vars_dict['VAR07'] <= 0.5718)].copy()   
    def    estrategia_4(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR08'] >= 1.749) & (vars_dict['VAR08'] <= 1.9732)].copy()   
    def    estrategia_5(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR22'] >= 0.4627) & (vars_dict['VAR22'] <= 0.546)].copy()   
    def    estrategia_6(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR56'] >= 0.1241) & (vars_dict['VAR56'] <= 0.251)].copy()   
    def    estrategia_7(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR65'] >= 7.9752) & (vars_dict['VAR65'] <= 9.5111)].copy()   
    def    estrategia_8(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR61'] >= 0.0476) & (vars_dict['VAR61'] <= 0.0545)].copy()   
    def    estrategia_9(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR11'] >= 1.1301) & (vars_dict['VAR11'] <= 1.165)].copy()   
    def    estrategia_10(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR12'] >= 0.8645) & (vars_dict['VAR12'] <= 0.9796)].copy()   
    def    estrategia_11(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR70'] >= 0.2225) & (vars_dict['VAR70'] <= 0.4284)].copy()   
    def    estrategia_12(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR39'] >= 0.123) & (vars_dict['VAR39'] <= 0.2396)].copy()   
    def    estrategia_13(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR69'] >= -1.5834) & (vars_dict['VAR69'] <= -0.6251)].copy()   
    def    estrategia_14(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR34'] >= 0.1522) & (vars_dict['VAR34'] <= 0.1819)].copy()   
    def    estrategia_15(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR40'] >= 0.2246) & (vars_dict['VAR40'] <= 0.2575)].copy()   
    def    estrategia_16(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR73'] >= 0.5598) & (vars_dict['VAR73'] <= 3.1803)].copy()   
    def    estrategia_17(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR41'] >= 0.1455) & (vars_dict['VAR41'] <= 0.18)].copy()   
    def    estrategia_18(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR37'] >= 0.317) & (vars_dict['VAR37'] <= 0.3471)].copy()   
    def    estrategia_19(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR38'] >= 0.2948) & (vars_dict['VAR38'] <= 0.3614)].copy()   
    def    estrategia_20(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR35'] >= 0.2628) & (vars_dict['VAR35'] <= 0.4129)].copy()   
    def    estrategia_21(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR06'] >= 1.3318) & (vars_dict['VAR06'] <= 1.906)].copy()   
    def    estrategia_22(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR04'] >= 0.5247) & (vars_dict['VAR04'] <= 0.7509)].copy()   
    def    estrategia_23(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR55'] >= 0.03) & (vars_dict['VAR55'] <= 0.0566)].copy()   
    def    estrategia_24(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR31'] >= 0.3063) & (vars_dict['VAR31'] <= 0.3669)].copy()   
    def    estrategia_25(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR26'] >= 0.1352) & (vars_dict['VAR26'] <= 0.168)].copy()   
    def    estrategia_26(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR23'] >= 0.1076) & (vars_dict['VAR23'] <= 0.142)].copy()   
    def    estrategia_27(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR58'] >= 0.0748) & (vars_dict['VAR58'] <= 0.0945)].copy()   
    def    estrategia_28(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR62'] >= 3.3474) & (vars_dict['VAR62'] <= 8.7806)].copy()   
    def    estrategia_29(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR54'] >= 0.1473) & (vars_dict['VAR54'] <= 0.2025)].copy()   
    def    estrategia_30(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR43'] >= 0.155) & (vars_dict['VAR43'] <= 0.1837)].copy()   
    def    estrategia_31(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR13'] >= 1.0608) & (vars_dict['VAR13'] <= 1.14)].copy()   
    def    estrategia_32(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR16'] >= 0.6569) & (vars_dict['VAR16'] <= 0.9379)].copy()   
    def    estrategia_33(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR19'] >= 0.8574) & (vars_dict['VAR19'] <= 1.0316)].copy()   
    def    estrategia_34(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR14'] >= 0.549) & (vars_dict['VAR14'] <= 0.6543)].copy()   
    def    estrategia_35(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR20'] >= 0.4826) & (vars_dict['VAR20'] <= 0.5923)].copy()   
    def    estrategia_36(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR63'] >= 0.7274) & (vars_dict['VAR63'] <= 1.763)].copy()   
    def    estrategia_37(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR45'] >= 0.563) & (vars_dict['VAR45'] <= 0.64)].copy()   
    def    estrategia_38(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR48'] >= 1.5625) & (vars_dict['VAR48'] <= 1.7763)].copy()   
    def    estrategia_39(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR66'] >= -13.769) & (vars_dict['VAR66'] <= -2.0474)].copy()   
    def    estrategia_40(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR64'] >= 2.9306) & (vars_dict['VAR64'] <= 7.1541)].copy()   
    def    estrategia_41(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR36'] >= 0.2258) & (vars_dict['VAR36'] <= 0.2647)].copy()   
    def    estrategia_42(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR25'] >= 0.1432) & (vars_dict['VAR25'] <= 0.2374)].copy()   
    def    estrategia_43(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR57'] >= 0.0652) & (vars_dict['VAR57'] <= 0.1026)].copy()   
    def    estrategia_44(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR67'] >= 1.122) & (vars_dict['VAR67'] <= 3.9434)].copy()   
    def    estrategia_45(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR30'] >= 0.3909) & (vars_dict['VAR30'] <= 0.55)].copy()   
    def    estrategia_46(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR74'] >= 0.1429) & (vars_dict['VAR74'] <= 0.1773)].copy()   
    def    estrategia_47(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR21'] >= 0.5411) & (vars_dict['VAR21'] <= 0.5524)].copy()   
    def    estrategia_48(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR01'] >= 0.77) & (vars_dict['VAR01'] <= 0.913)].copy()   
    def    estrategia_49(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR03'] >= 1.0952) & (vars_dict['VAR03'] <= 1.2987)].copy()   
    def    estrategia_50(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR46'] >= 1.0909) & (vars_dict['VAR46'] <= 1.5278)].copy()   
    def    estrategia_51(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR32'] >= 0.2444) & (vars_dict['VAR32'] <= 0.27)].copy()   
    def    estrategia_52(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR44'] >= 0.6545) & (vars_dict['VAR44'] <= 0.9167)].copy()   
    def    estrategia_53(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR76'] >= 0.3405) & (vars_dict['VAR76'] <= 0.4074)].copy()   
    def    estrategia_54(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR02'] >= 0.0969) & (vars_dict['VAR02'] <= 0.4195)].copy()   
    def    estrategia_55(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR05'] >= 2.3837) & (vars_dict['VAR05'] <= 10.3175)].copy()   
    def    estrategia_56(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR17'] >= 0.8718) & (vars_dict['VAR17'] <= 0.9722)].copy()   
    def    estrategia_57(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR68'] >= -3.8573) & (vars_dict['VAR68'] <= -0.6028)].copy()   
    def    estrategia_58(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR77'] >= 0.2174) & (vars_dict['VAR77'] <= 0.3391)].copy()   
    def    estrategia_59(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR24'] >= 0.3556) & (vars_dict['VAR24'] <= 0.3846)].copy()   
    def    estrategia_60(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR60'] >= 0.0278) & (vars_dict['VAR60'] <= 0.0368)].copy()   
    def    estrategia_61(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR33'] >= 0.1133) & (vars_dict['VAR33'] <= 0.1485)].copy()   
    def    estrategia_62(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR72'] >= 0.3062) & (vars_dict['VAR72'] <= 0.3603)].copy()   
    def    estrategia_63(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR10'] >= 0.4861) & (vars_dict['VAR10'] <= 0.8733)].copy()   
    def    estrategia_64(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR09'] >= 1.1451) & (vars_dict['VAR09'] <= 2.0571)].copy()   
    def    estrategia_65(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR71'] >= 0.0938) & (vars_dict['VAR71'] <= 0.1904)].copy()   
    def    estrategia_66(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR27'] >= 0.1142) & (vars_dict['VAR27'] <= 0.1284)].copy()   
    def    estrategia_67(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR42'] >= 0.2067) & (vars_dict['VAR42'] <= 0.2286)].copy()   
    def    estrategia_68(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR29'] >= 0.1288) & (vars_dict['VAR29'] <= 0.1474)].copy()   
    def    estrategia_69(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR18'] >= 0.5067) & (vars_dict['VAR18'] <= 0.5514)].copy()   
    def    estrategia_70(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR28'] >= 0.2828) & (vars_dict['VAR28'] <= 0.4355)].copy()   
    def    estrategia_71(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR59'] >= 0.0149) & (vars_dict['VAR59'] <= 0.0188)].copy()   
    def    estrategia_72(df): return df[(vars_dict['VAR15'] >= 0.4848) & (vars_dict['VAR15'] <= 0.5047) & (vars_dict['VAR75'] >= 0.4733) & (vars_dict['VAR75'] <= 0.6667)].copy() 
    def    estrategia_73(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR67'] >= -0.2456) & (vars_dict['VAR67'] <= -0.2046)].copy()   
    def    estrategia_74(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR36'] >= 0.0823) & (vars_dict['VAR36'] <= 0.0938)].copy()   
    def    estrategia_75(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR59'] >= 0.0074) & (vars_dict['VAR59'] <= 0.0089)].copy()   
    def    estrategia_76(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR69'] >= 1.3639) & (vars_dict['VAR69'] <= 1.4298)].copy()   
    def    estrategia_77(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR61'] >= 0.0476) & (vars_dict['VAR61'] <= 0.0499)].copy()   
    def    estrategia_78(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR18'] >= 0.4711) & (vars_dict['VAR18'] <= 0.5081)].copy()   
    def    estrategia_79(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR15'] >= 0.4933) & (vars_dict['VAR15'] <= 0.5033)].copy()   
    def    estrategia_80(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR04'] >= 1.0244) & (vars_dict['VAR04'] <= 1.1293)].copy()   
    def    estrategia_81(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR06'] >= 0.8855) & (vars_dict['VAR06'] <= 0.9762)].copy()   
    def    estrategia_82(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR72'] >= 0.0244) & (vars_dict['VAR72'] <= 0.1293)].copy()   
    def    estrategia_83(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR22'] >= 0.491) & (vars_dict['VAR22'] <= 0.5079)].copy()   
    def    estrategia_84(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR65'] >= 0.7858) & (vars_dict['VAR65'] <= 2.4897)].copy()   
    def    estrategia_85(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR12'] >= 0.5514) & (vars_dict['VAR12'] <= 0.6145)].copy()   
    def    estrategia_86(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR28'] >= 0.1078) & (vars_dict['VAR28'] <= 0.1255)].copy()   
    def    estrategia_87(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR25'] >= 0.2848) & (vars_dict['VAR25'] <= 0.3037)].copy()   
    def    estrategia_88(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR31'] >= 0.1638) & (vars_dict['VAR31'] <= 0.18)].copy()   
    def    estrategia_89(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR64'] >= -1.3762) & (vars_dict['VAR64'] <= -1.273)].copy()   
    def    estrategia_90(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR56'] >= 0.0444) & (vars_dict['VAR56'] <= 0.048)].copy()   
    def    estrategia_91(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR08'] >= 1.0538) & (vars_dict['VAR08'] <= 1.1803)].copy()   
    def    estrategia_92(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR07'] >= 0.8472) & (vars_dict['VAR07'] <= 0.949)].copy()   
    def    estrategia_93(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR19'] >= 0.4167) & (vars_dict['VAR19'] <= 0.4535)].copy()   
    def    estrategia_94(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR40'] >= 0.2149) & (vars_dict['VAR40'] <= 0.2375)].copy()   
    def    estrategia_95(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR68'] >= 0.3797) & (vars_dict['VAR68'] <= 0.6511)].copy()   
    def    estrategia_96(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR14'] >= 0.893) & (vars_dict['VAR14'] <= 0.9833)].copy()   
    def    estrategia_97(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR73'] >= 0.0) & (vars_dict['VAR73'] <= 0.0513)].copy()   
    def    estrategia_98(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR57'] >= 0.0533) & (vars_dict['VAR57'] <= 0.086)].copy()   
    def    estrategia_99(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR27'] >= 0.104) & (vars_dict['VAR27'] <= 0.1142)].copy()   
    def    estrategia_100(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR77'] >= 0.5217) & (vars_dict['VAR77'] <= 0.5625)].copy()   
    def    estrategia_101(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR47'] >= 0.4375) & (vars_dict['VAR47'] <= 0.4783)].copy()   
    def    estrategia_102(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR49'] >= 2.0909) & (vars_dict['VAR49'] <= 2.2857)].copy()   
    def    estrategia_103(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR38'] >= 0.1143) & (vars_dict['VAR38'] <= 0.35)].copy()   
    def    estrategia_104(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR10'] >= 0.9293) & (vars_dict['VAR10'] <= 0.984)].copy()   
    def    estrategia_105(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR09'] >= 1.0163) & (vars_dict['VAR09'] <= 1.0761)].copy()   
    def    estrategia_106(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR70'] >= 1.0909) & (vars_dict['VAR70'] <= 1.2872)].copy()   
    def    estrategia_107(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR05'] >= 0.4372) & (vars_dict['VAR05'] <= 0.4783)].copy()   
    def    estrategia_108(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR02'] >= 2.0909) & (vars_dict['VAR02'] <= 2.2872)].copy()   
    def    estrategia_109(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR30'] >= 0.0012) & (vars_dict['VAR30'] <= 0.0412)].copy()   
    def    estrategia_110(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR29'] >= 0.098) & (vars_dict['VAR29'] <= 0.1128)].copy()   
    def    estrategia_111(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR11'] >= 0.994) & (vars_dict['VAR11'] <= 1.0106)].copy()   
    def    estrategia_112(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR26'] >= 0.1144) & (vars_dict['VAR26'] <= 0.1366)].copy()   
    def    estrategia_113(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR21'] >= 0.5064) & (vars_dict['VAR21'] <= 0.5288)].copy()   
    def    estrategia_114(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR58'] >= 0.0945) & (vars_dict['VAR58'] <= 0.1127)].copy()   
    def    estrategia_115(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR32'] >= 0.2724) & (vars_dict['VAR32'] <= 0.2897)].copy()   
    def    estrategia_116(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR16'] >= 0.4286) & (vars_dict['VAR16'] <= 0.4381)].copy()   
    def    estrategia_117(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR35'] >= 0.001) & (vars_dict['VAR35'] <= 0.0451)].copy()   
    def    estrategia_118(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR66'] >= -2.6109) & (vars_dict['VAR66'] <= -1.7839)].copy()   
    def    estrategia_119(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR13'] >= 0.4545) & (vars_dict['VAR13'] <= 0.505)].copy()   
    def    estrategia_120(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR45'] >= 0.4549) & (vars_dict['VAR45'] <= 0.5208)].copy()   
    def    estrategia_121(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR48'] >= 1.92) & (vars_dict['VAR48'] <= 2.1981)].copy()   
    def    estrategia_122(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR17'] >= 1.0445) & (vars_dict['VAR17'] <= 1.0981)].copy()   
    def    estrategia_123(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR76'] >= 0.4792) & (vars_dict['VAR76'] <= 0.5455)].copy()   
    def    estrategia_124(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR54'] >= 0.4096) & (vars_dict['VAR54'] <= 0.4645)].copy()   
    def    estrategia_125(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR62'] >= -13.074) & (vars_dict['VAR62'] <= -11.5732)].copy()   
    def    estrategia_126(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR37'] >= 0.3053) & (vars_dict['VAR37'] <= 0.4688)].copy()   
    def    estrategia_127(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR24'] >= 0.3536) & (vars_dict['VAR24'] <= 0.4702)].copy()   
    def    estrategia_128(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR43'] >= 0.2122) & (vars_dict['VAR43'] <= 0.2188)].copy()   
    def    estrategia_129(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR60'] >= 0.0463) & (vars_dict['VAR60'] <= 0.1341)].copy()   
    def    estrategia_130(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR42'] >= 0.1827) & (vars_dict['VAR42'] <= 0.1967)].copy()   
    def    estrategia_131(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR23'] >= 0.0759) & (vars_dict['VAR23'] <= 0.0928)].copy()   
    def    estrategia_132(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR20'] >= 1.0359) & (vars_dict['VAR20'] <= 1.1135)].copy()   
    def    estrategia_133(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR34'] >= 0.0) & (vars_dict['VAR34'] <= 0.072)].copy()   
    def    estrategia_134(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR33'] >= 0.0) & (vars_dict['VAR33'] <= 0.0418)].copy()   
    def    estrategia_135(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR74'] >= 0.2301) & (vars_dict['VAR74'] <= 0.287)].copy()   
    def    estrategia_136(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR55'] >= 0.3176) & (vars_dict['VAR55'] <= 0.3607)].copy()   
    def    estrategia_137(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR63'] >= -10.2236) & (vars_dict['VAR63'] <= -9.0242)].copy()   
    def    estrategia_138(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR75'] >= 0.25) & (vars_dict['VAR75'] <= 0.2903)].copy()   
    def    estrategia_139(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR71'] >= 0.7257) & (vars_dict['VAR71'] <= 0.875)].copy()   
    def    estrategia_140(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR01'] >= 1.7257) & (vars_dict['VAR01'] <= 1.875)].copy()   
    def    estrategia_141(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR41'] >= 0.1818) & (vars_dict['VAR41'] <= 0.1904)].copy()   
    def    estrategia_142(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR03'] >= 0.5333) & (vars_dict['VAR03'] <= 0.5795)].copy()   
    def    estrategia_143(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR44'] >= 1.3704) & (vars_dict['VAR44'] <= 136.1111)].copy()   
    def    estrategia_144(df): return df[(vars_dict['VAR39'] >= 0.4146) & (vars_dict['VAR39'] <= 0.5408) & (vars_dict['VAR46'] >= 0.0073) & (vars_dict['VAR46'] <= 0.7297)].copy() 
    def    estrategia_145(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR40'] >= 0.0255) & (vars_dict['VAR40'] <= 0.1073)].copy()   
    def    estrategia_146(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR24'] >= 0.0058) & (vars_dict['VAR24'] <= 0.1928)].copy()   
    def    estrategia_147(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR37'] >= 0.0419) & (vars_dict['VAR37'] <= 0.1379)].copy()   
    def    estrategia_148(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR27'] >= 0.0027) & (vars_dict['VAR27'] <= 0.096)].copy()   
    def    estrategia_149(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR56'] >= 0.0561) & (vars_dict['VAR56'] <= 0.0665)].copy()   
    def    estrategia_150(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR23'] >= 0.3305) & (vars_dict['VAR23'] <= 0.6458)].copy()   
    def    estrategia_151(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR43'] >= 0.1149) & (vars_dict['VAR43'] <= 0.1486)].copy()   
    def    estrategia_152(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR69'] >= -3.7349) & (vars_dict['VAR69'] <= -1.3036)].copy()   
    def    estrategia_153(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR28'] >= 0.0022) & (vars_dict['VAR28'] <= 0.0779)].copy()   
    def    estrategia_154(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR42'] >= 0.0324) & (vars_dict['VAR42'] <= 0.1057)].copy()   
    def    estrategia_155(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR30'] >= 0.4392) & (vars_dict['VAR30'] <= 1.7222)].copy()   
    def    estrategia_156(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR07'] >= 1.412) & (vars_dict['VAR07'] <= 4.75)].copy()   
    def    estrategia_157(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR08'] >= 0.2105) & (vars_dict['VAR08'] <= 0.7082)].copy()   
    def    estrategia_158(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR16'] >= 0.3885) & (vars_dict['VAR16'] <= 0.4407)].copy()   
    def    estrategia_159(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR39'] >= 0.6448) & (vars_dict['VAR39'] <= 0.8509)].copy()   
    def    estrategia_160(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR76'] >= 0.4176) & (vars_dict['VAR76'] <= 0.52)].copy()   
    def    estrategia_161(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR26'] >= 0.0026) & (vars_dict['VAR26'] <= 0.0696)].copy()   
    def    estrategia_162(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR72'] >= 0.5676) & (vars_dict['VAR72'] <= 0.7215)].copy()   
    def    estrategia_163(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR65'] >= -20.307) & (vars_dict['VAR65'] <= -5.0026)].copy()   
    def    estrategia_164(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR36'] >= 0.2122) & (vars_dict['VAR36'] <= 0.2647)].copy()   
    def    estrategia_165(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR29'] >= 0.0021) & (vars_dict['VAR29'] <= 0.0817)].copy()   
    def    estrategia_166(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR25'] >= 0.0087) & (vars_dict['VAR25'] <= 0.1308)].copy()   
    def    estrategia_167(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR41'] >= 0.0425) & (vars_dict['VAR41'] <= 0.1122)].copy()   
    def    estrategia_168(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR48'] >= 0.8) & (vars_dict['VAR48'] <= 0.9618)].copy()   
    def    estrategia_169(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR45'] >= 1.0397) & (vars_dict['VAR45'] <= 1.25)].copy()   
    def    estrategia_170(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR73'] >= 0.461) & (vars_dict['VAR73'] <= 3.75)].copy()   
    def    estrategia_171(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR06'] >= 0.6008) & (vars_dict['VAR06'] <= 0.6765)].copy()   
    def    estrategia_172(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR04'] >= 1.4783) & (vars_dict['VAR04'] <= 1.6645)].copy()   
    def    estrategia_173(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR68'] >= 1.3629) & (vars_dict['VAR68'] <= 1.6443)].copy()   
    def    estrategia_174(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR35'] >= 0.2277) & (vars_dict['VAR35'] <= 0.3206)].copy()   
    def    estrategia_175(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR38'] >= 0.0774) & (vars_dict['VAR38'] <= 0.2127)].copy()   
    def    estrategia_176(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR18'] >= 0.1189) & (vars_dict['VAR18'] <= 0.3782)].copy()   
    def    estrategia_177(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR61'] >= 0.0508) & (vars_dict['VAR61'] <= 0.059)].copy()   
    def    estrategia_178(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR57'] >= 0.2775) & (vars_dict['VAR57'] <= 0.7401)].copy()   
    def    estrategia_179(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR54'] >= 0.3889) & (vars_dict['VAR54'] <= 0.4688)].copy()   
    def    estrategia_180(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR21'] >= 0.4573) & (vars_dict['VAR21'] <= 0.5014)].copy()   
    def    estrategia_181(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR32'] >= 0.2044) & (vars_dict['VAR32'] <= 0.221)].copy()   
    def    estrategia_182(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR47'] >= 1.2381) & (vars_dict['VAR47'] <= 1.8085)].copy()   
    def    estrategia_183(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR49'] >= 0.5529) & (vars_dict['VAR49'] <= 0.8077)].copy()   
    def    estrategia_184(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR31'] >= 0.381) & (vars_dict['VAR31'] <= 0.7632)].copy()   
    def    estrategia_185(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR14'] >= 0.4263) & (vars_dict['VAR14'] <= 0.537)].copy()   
    def    estrategia_186(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR33'] >= 0.2715) & (vars_dict['VAR33'] <= 0.4038)].copy()   
    def    estrategia_187(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR34'] >= 0.1713) & (vars_dict['VAR34'] <= 0.1975)].copy()   
    def    estrategia_188(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR66'] >= -2.3612) & (vars_dict['VAR66'] <= -2.2665)].copy()   
    def    estrategia_189(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR70'] >= 1.5752) & (vars_dict['VAR70'] <= 2.4483)].copy()   
    def    estrategia_190(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR02'] >= 2.5752) & (vars_dict['VAR02'] <= 3.4483)].copy()   
    def    estrategia_191(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR05'] >= 0.29) & (vars_dict['VAR05'] <= 0.3883)].copy()   
    def    estrategia_192(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR59'] >= 0.0321) & (vars_dict['VAR59'] <= 0.048)].copy()   
    def    estrategia_193(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR12'] >= 0.0) & (vars_dict['VAR12'] <= 0.3271)].copy()   
    def    estrategia_194(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR77'] >= 0.7612) & (vars_dict['VAR77'] <= 0.9912)].copy()   
    def    estrategia_195(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR64'] >= -2.0784) & (vars_dict['VAR64'] <= -1.6707)].copy()   
    def    estrategia_196(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR60'] >= 0.0011) & (vars_dict['VAR60'] <= 0.0064)].copy()   
    def    estrategia_197(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR17'] >= 1.1705) & (vars_dict['VAR17'] <= 1.3427)].copy()   
    def    estrategia_198(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR62'] >= -12.0948) & (vars_dict['VAR62'] <= -9.3826)].copy()   
    def    estrategia_199(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR75'] >= 0.0495) & (vars_dict['VAR75'] <= 0.1)].copy()   
    def    estrategia_200(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR22'] >= 0.2428) & (vars_dict['VAR22'] <= 0.3217)].copy()   
    def    estrategia_201(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR19'] >= 0.0558) & (vars_dict['VAR19'] <= 0.25)].copy()   
    def    estrategia_202(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR03'] >= 0.0606) & (vars_dict['VAR03'] <= 0.299)].copy()   
    def    estrategia_203(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR01'] >= 3.3445) & (vars_dict['VAR01'] <= 16.5138)].copy()   
    def    estrategia_204(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR71'] >= 2.3445) & (vars_dict['VAR71'] <= 15.5138)].copy()   
    def    estrategia_205(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR63'] >= -23.6879) & (vars_dict['VAR63'] <= -13.5031)].copy()   
    def    estrategia_206(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR55'] >= 0.4803) & (vars_dict['VAR55'] <= 0.8774)].copy()   
    def    estrategia_207(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR67'] >= 1.0281) & (vars_dict['VAR67'] <= 3.9434)].copy()   
    def    estrategia_208(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR15'] >= 0.445) & (vars_dict['VAR15'] <= 0.4764)].copy()   
    def    estrategia_209(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR11'] >= 1.0406) & (vars_dict['VAR11'] <= 1.094)].copy()   
    def    estrategia_210(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR44'] >= 0.0073) & (vars_dict['VAR44'] <= 0.6346)].copy()   
    def    estrategia_211(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR46'] >= 1.5758) & (vars_dict['VAR46'] <= 136.1111)].copy()   
    def    estrategia_212(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR58'] >= 0.0965) & (vars_dict['VAR58'] <= 0.1188)].copy()   
    def    estrategia_213(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR13'] >= 0.0) & (vars_dict['VAR13'] <= 0.2228)].copy()   
    def    estrategia_214(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR09'] >= 0.8204) & (vars_dict['VAR09'] <= 0.8318)].copy()   
    def    estrategia_215(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR10'] >= 1.2022) & (vars_dict['VAR10'] <= 1.2189)].copy()   
    def    estrategia_216(df): return df[(vars_dict['VAR74'] >= 0.132) & (vars_dict['VAR74'] <= 0.1797) & (vars_dict['VAR20'] >= 1.0482) & (vars_dict['VAR20'] <= 1.1605)].copy() 
    def    estrategia_217(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR14'] >= 0.8031) & (vars_dict['VAR14'] <= 0.8244)].copy()   
    def    estrategia_218(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR54'] >= 0.0) & (vars_dict['VAR54'] <= 0.0224)].copy()   
    def    estrategia_219(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR26'] >= 0.1263) & (vars_dict['VAR26'] <= 0.1504)].copy()   
    def    estrategia_220(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR70'] >= 0.0) & (vars_dict['VAR70'] <= 0.0598)].copy()   
    def    estrategia_221(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR22'] >= 0.9492) & (vars_dict['VAR22'] <= 2.0924)].copy()   
    def    estrategia_222(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR25'] >= 0.2) & (vars_dict['VAR25'] <= 0.2367)].copy()   
    def    estrategia_223(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR67'] >= 0.1194) & (vars_dict['VAR67'] <= 0.2456)].copy()   
    def    estrategia_224(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR18'] >= 0.39) & (vars_dict['VAR18'] <= 0.4349)].copy()   
    def    estrategia_225(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR13'] >= 0.6712) & (vars_dict['VAR13'] <= 0.6927)].copy()   
    def    estrategia_226(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR42'] >= 0.1667) & (vars_dict['VAR42'] <= 0.1917)].copy()   
    def    estrategia_227(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR17'] >= 0.7314) & (vars_dict['VAR17'] <= 0.7721)].copy()   
    def    estrategia_228(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR71'] >= 0.4783) & (vars_dict['VAR71'] <= 0.4955)].copy()   
    def    estrategia_229(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR03'] >= 0.6687) & (vars_dict['VAR03'] <= 0.6765)].copy()   
    def    estrategia_230(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR15'] >= 0.5415) & (vars_dict['VAR15'] <= 0.5538)].copy()   
    def    estrategia_231(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR44'] >= 0.8788) & (vars_dict['VAR44'] <= 0.9355)].copy()   
    def    estrategia_232(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR46'] >= 1.069) & (vars_dict['VAR46'] <= 1.1379)].copy()   
    def    estrategia_233(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR75'] >= 0.0714) & (vars_dict['VAR75'] <= 0.1071)].copy()   
    def    estrategia_234(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR43'] >= 0.1943) & (vars_dict['VAR43'] <= 0.2043)].copy()   
    def    estrategia_235(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR04'] >= 0.6822) & (vars_dict['VAR04'] <= 0.7616)].copy()   
    def    estrategia_236(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR06'] >= 1.313) & (vars_dict['VAR06'] <= 1.4659)].copy()   
    def    estrategia_237(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR09'] >= 1.0611) & (vars_dict['VAR09'] <= 1.1437)].copy()   
    def    estrategia_238(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR10'] >= 0.8744) & (vars_dict['VAR10'] <= 0.9424)].copy()   
    def    estrategia_239(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR38'] >= 0.2917) & (vars_dict['VAR38'] <= 0.3136)].copy()   
    def    estrategia_240(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR36'] >= 0.1555) & (vars_dict['VAR36'] <= 0.1608)].copy()   
    def    estrategia_241(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR55'] >= 0.1183) & (vars_dict['VAR55'] <= 0.1228)].copy()   
    def    estrategia_242(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR63'] >= -3.5143) & (vars_dict['VAR63'] <= -3.3854)].copy()   
    def    estrategia_243(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR20'] >= 0.7433) & (vars_dict['VAR20'] <= 0.7937)].copy()   
    def    estrategia_244(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR29'] >= 0.1416) & (vars_dict['VAR29'] <= 0.152)].copy()   
    def    estrategia_245(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR69'] >= 0.369) & (vars_dict['VAR69'] <= 0.5391)].copy()   
    def    estrategia_246(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR64'] >= 2.4828) & (vars_dict['VAR64'] <= 3.5576)].copy()   
    def    estrategia_247(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR73'] >= 0.5034) & (vars_dict['VAR73'] <= 2.68)].copy()   
    def    estrategia_248(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR66'] >= -2.0099) & (vars_dict['VAR66'] <= -0.9142)].copy()   
    def    estrategia_249(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR30'] >= 0.171) & (vars_dict['VAR30'] <= 0.1773)].copy()   
    def    estrategia_250(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR21'] >= 0.6719) & (vars_dict['VAR21'] <= 0.8452)].copy()   
    def    estrategia_251(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR32'] >= 0.1301) & (vars_dict['VAR32'] <= 0.1697)].copy()   
    def    estrategia_252(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR49'] >= 1.1818) & (vars_dict['VAR49'] <= 1.2609)].copy()   
    def    estrategia_253(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR47'] >= 0.7931) & (vars_dict['VAR47'] <= 0.8462)].copy()   
    def    estrategia_254(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR59'] >= 0.0051) & (vars_dict['VAR59'] <= 0.0078)].copy()   
    def    estrategia_255(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR72'] >= 0.2556) & (vars_dict['VAR72'] <= 0.3123)].copy()   
    def    estrategia_256(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR24'] >= 0.2276) & (vars_dict['VAR24'] <= 0.2482)].copy()   
    def    estrategia_257(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR39'] >= 0.1262) & (vars_dict['VAR39'] <= 0.1787)].copy()   
    def    estrategia_258(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR74'] >= 0.2048) & (vars_dict['VAR74'] <= 0.2599)].copy()   
    def    estrategia_259(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR57'] >= 0.2821) & (vars_dict['VAR57'] <= 0.5826)].copy()   
    def    estrategia_260(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR28'] >= 0.1116) & (vars_dict['VAR28'] <= 0.1311)].copy()   
    def    estrategia_261(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR08'] >= 1.6478) & (vars_dict['VAR08'] <= 2.6296)].copy()   
    def    estrategia_262(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR07'] >= 0.3803) & (vars_dict['VAR07'] <= 0.6069)].copy()   
    def    estrategia_263(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR16'] >= 0.5906) & (vars_dict['VAR16'] <= 0.6452)].copy()   
    def    estrategia_264(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR34'] >= 0.1348) & (vars_dict['VAR34'] <= 0.1408)].copy()   
    def    estrategia_265(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR61'] >= 0.014) & (vars_dict['VAR61'] <= 0.0208)].copy()   
    def    estrategia_266(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR56'] >= 0.1008) & (vars_dict['VAR56'] <= 0.1297)].copy()   
    def    estrategia_267(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR40'] >= 0.1911) & (vars_dict['VAR40'] <= 0.2229)].copy()   
    def    estrategia_268(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR27'] >= 0.1284) & (vars_dict['VAR27'] <= 0.1371)].copy()   
    def    estrategia_269(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR77'] >= 0.4167) & (vars_dict['VAR77'] <= 80.6667)].copy()   
    def    estrategia_270(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR31'] >= 0.0034) & (vars_dict['VAR31'] <= 0.1893)].copy()   
    def    estrategia_271(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR62'] >= -3.686) & (vars_dict['VAR62'] <= -2.9815)].copy()   
    def    estrategia_272(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR11'] >= 1.1678) & (vars_dict['VAR11'] <= 1.8269)].copy()   
    def    estrategia_273(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR58'] >= 0.2473) & (vars_dict['VAR58'] <= 0.5036)].copy()   
    def    estrategia_274(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR19'] >= 0.5723) & (vars_dict['VAR19'] <= 0.5836)].copy()   
    def    estrategia_275(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR41'] >= 0.1835) & (vars_dict['VAR41'] <= 0.1938)].copy()   
    def    estrategia_276(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR65'] >= -16.2411) & (vars_dict['VAR65'] <= -5.4202)].copy()   
    def    estrategia_277(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR12'] >= 0.8266) & (vars_dict['VAR12'] <= 1.2413)].copy()   
    def    estrategia_278(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR05'] >= 0.7533) & (vars_dict['VAR05'] <= 0.8066)].copy()   
    def    estrategia_279(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR02'] >= 1.2398) & (vars_dict['VAR02'] <= 1.3274)].copy()   
    def    estrategia_280(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR37'] >= 0.0025) & (vars_dict['VAR37'] <= 0.1381)].copy()   
    def    estrategia_281(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR33'] >= 0.1236) & (vars_dict['VAR33'] <= 0.1368)].copy()   
    def    estrategia_282(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR68'] >= 0.5013) & (vars_dict['VAR68'] <= 0.5449)].copy()   
    def    estrategia_283(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR23'] >= 0.1747) & (vars_dict['VAR23'] <= 0.1905)].copy()   
    def    estrategia_284(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR35'] >= 0.1117) & (vars_dict['VAR35'] <= 0.1221)].copy()   
    def    estrategia_285(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR60'] >= 0.0149) & (vars_dict['VAR60'] <= 0.0163)].copy()   
    def    estrategia_286(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR76'] >= 0.2188) & (vars_dict['VAR76'] <= 0.2414)].copy()   
    def    estrategia_287(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR45'] >= 0.0073) & (vars_dict['VAR45'] <= 0.6944)].copy()   
    def    estrategia_288(df): return df[(vars_dict['VAR01'] >= 1.3345) & (vars_dict['VAR01'] <= 1.4955) & (vars_dict['VAR48'] >= 1.44) & (vars_dict['VAR48'] <= 136.1111)].copy() 
    def    estrategia_289(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR71'] >= 0.4732) & (vars_dict['VAR71'] <= 0.5)].copy()   
    def    estrategia_290(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR32'] >= 0.1947) & (vars_dict['VAR32'] <= 0.2172)].copy()   
    def    estrategia_291(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR17'] >= 0.7353) & (vars_dict['VAR17'] <= 0.7747)].copy()   
    def    estrategia_292(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR22'] >= 0.9424) & (vars_dict['VAR22'] <= 2.0769)].copy()   
    def    estrategia_293(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR18'] >= 0.393) & (vars_dict['VAR18'] <= 0.4311)].copy()   
    def    estrategia_294(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR01'] >= 1.4732) & (vars_dict['VAR01'] <= 1.5)].copy()   
    def    estrategia_295(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR03'] >= 0.6667) & (vars_dict['VAR03'] <= 0.6788)].copy()   
    def    estrategia_296(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR07'] >= 1.4499) & (vars_dict['VAR07'] <= 2.5735)].copy()   
    def    estrategia_297(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR08'] >= 0.3886) & (vars_dict['VAR08'] <= 0.6897)].copy()   
    def    estrategia_298(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR30'] >= 0.1677) & (vars_dict['VAR30'] <= 0.1751)].copy()   
    def    estrategia_299(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR73'] >= 0.5069) & (vars_dict['VAR73'] <= 1.5735)].copy()   
    def    estrategia_300(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR66'] >= -2.0504) & (vars_dict['VAR66'] <= -0.8336)].copy()   
    def    estrategia_301(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR10'] >= 0.8725) & (vars_dict['VAR10'] <= 0.945)].copy()   
    def    estrategia_302(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR09'] >= 1.0582) & (vars_dict['VAR09'] <= 1.1461)].copy()   
    def    estrategia_303(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR69'] >= 0.382) & (vars_dict['VAR69'] <= 0.5565)].copy()   
    def    estrategia_304(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR38'] >= 0.2) & (vars_dict['VAR38'] <= 0.2419)].copy()   
    def    estrategia_305(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR40'] >= 0.1905) & (vars_dict['VAR40'] <= 0.2208)].copy()   
    def    estrategia_306(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR74'] >= 0.3372) & (vars_dict['VAR74'] <= 0.4304)].copy()   
    def    estrategia_307(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR43'] >= 0.1943) & (vars_dict['VAR43'] <= 0.2043)].copy()   
    def    estrategia_308(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR41'] >= 0.1274) & (vars_dict['VAR41'] <= 0.1461)].copy()   
    def    estrategia_309(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR14'] >= 0.7881) & (vars_dict['VAR14'] <= 0.8145)].copy()   
    def    estrategia_310(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR77'] >= 0.129) & (vars_dict['VAR77'] <= 0.1724)].copy()   
    def    estrategia_311(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR57'] >= 0.2761) & (vars_dict['VAR57'] <= 0.4668)].copy()   
    def    estrategia_312(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR20'] >= 0.7411) & (vars_dict['VAR20'] <= 0.7919)].copy()   
    def    estrategia_313(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR72'] >= 0.2853) & (vars_dict['VAR72'] <= 0.3597)].copy()   
    def    estrategia_314(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR42'] >= 0.1652) & (vars_dict['VAR42'] <= 0.19)].copy()   
    def    estrategia_315(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR75'] >= 0.0667) & (vars_dict['VAR75'] <= 0.0952)].copy()   
    def    estrategia_316(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR65'] >= -12.6689) & (vars_dict['VAR65'] <= -5.4921)].copy()   
    def    estrategia_317(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR13'] >= 0.6725) & (vars_dict['VAR13'] <= 0.6982)].copy()   
    def    estrategia_318(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR35'] >= 0.1314) & (vars_dict['VAR35'] <= 0.1423)].copy()   
    def    estrategia_319(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR64'] >= 0.1193) & (vars_dict['VAR64'] <= 0.6487)].copy()   
    def    estrategia_320(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR70'] >= 0.3242) & (vars_dict['VAR70'] <= 0.3989)].copy()   
    def    estrategia_321(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR60'] >= 0.0168) & (vars_dict['VAR60'] <= 0.0183)].copy()   
    def    estrategia_322(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR33'] >= 0.1494) & (vars_dict['VAR33'] <= 0.1646)].copy()   
    def    estrategia_323(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR15'] >= 0.5552) & (vars_dict['VAR15'] <= 0.5686)].copy()   
    def    estrategia_324(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR29'] >= 0.1406) & (vars_dict['VAR29'] <= 0.1517)].copy()   
    def    estrategia_325(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR36'] >= 0.1689) & (vars_dict['VAR36'] <= 0.1855)].copy()   
    def    estrategia_326(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR62'] >= -3.481) & (vars_dict['VAR62'] <= -2.9815)].copy()   
    def    estrategia_327(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR26'] >= 0.1252) & (vars_dict['VAR26'] <= 0.1496)].copy()   
    def    estrategia_328(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR24'] >= 0.2481) & (vars_dict['VAR24'] <= 0.2692)].copy()   
    def    estrategia_329(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR27'] >= 0.1282) & (vars_dict['VAR27'] <= 0.1368)].copy()   
    def    estrategia_330(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR25'] >= 0.2) & (vars_dict['VAR25'] <= 0.2357)].copy()   
    def    estrategia_331(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR19'] >= 0.5774) & (vars_dict['VAR19'] <= 0.5898)].copy()   
    def    estrategia_332(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR37'] >= 0.1367) & (vars_dict['VAR37'] <= 0.1657)].copy()   
    def    estrategia_333(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR56'] >= 0.051) & (vars_dict['VAR56'] <= 0.0638)].copy()   
    def    estrategia_334(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR06'] >= 1.0097) & (vars_dict['VAR06'] <= 1.0775)].copy()   
    def    estrategia_335(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR04'] >= 0.9281) & (vars_dict['VAR04'] <= 0.9904)].copy()   
    def    estrategia_336(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR61'] >= 0.0519) & (vars_dict['VAR61'] <= 0.1552)].copy()   
    def    estrategia_337(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR54'] >= 0.0667) & (vars_dict['VAR54'] <= 0.0858)].copy()   
    def    estrategia_338(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR47'] >= 0.7931) & (vars_dict['VAR47'] <= 0.84)].copy()   
    def    estrategia_339(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR49'] >= 1.1905) & (vars_dict['VAR49'] <= 1.2609)].copy()   
    def    estrategia_340(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR23'] >= 0.1738) & (vars_dict['VAR23'] <= 0.1917)].copy()   
    def    estrategia_341(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR39'] >= 0.1314) & (vars_dict['VAR39'] <= 0.1839)].copy()   
    def    estrategia_342(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR31'] >= 0.25) & (vars_dict['VAR31'] <= 0.26)].copy()   
    def    estrategia_343(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR58'] >= 0.2481) & (vars_dict['VAR58'] <= 0.495)].copy()   
    def    estrategia_344(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR34'] >= 0.1446) & (vars_dict['VAR34'] <= 0.1486)].copy()   
    def    estrategia_345(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR05'] >= 0.7152) & (vars_dict['VAR05'] <= 0.7556)].copy()   
    def    estrategia_346(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR02'] >= 1.3235) & (vars_dict['VAR02'] <= 1.3983)].copy()   
    def    estrategia_347(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR11'] >= 0.6875) & (vars_dict['VAR11'] <= 0.7404)].copy()   
    def    estrategia_348(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR55'] >= 0.1026) & (vars_dict['VAR55'] <= 0.106)].copy()   
    def    estrategia_349(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR68'] >= 0.4679) & (vars_dict['VAR68'] <= 0.514)].copy()   
    def    estrategia_350(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR21'] >= 0.5877) & (vars_dict['VAR21'] <= 0.6)].copy()   
    def    estrategia_351(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR67'] >= 0.1038) & (vars_dict['VAR67'] <= 0.228)].copy()   
    def    estrategia_352(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR16'] >= 0.9108) & (vars_dict['VAR16'] <= 1.9231)].copy()   
    def    estrategia_353(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR44'] >= 0.8857) & (vars_dict['VAR44'] <= 0.9565)].copy()   
    def    estrategia_354(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR46'] >= 1.0455) & (vars_dict['VAR46'] <= 1.129)].copy()   
    def    estrategia_355(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR45'] >= 0.8485) & (vars_dict['VAR45'] <= 0.8919)].copy()   
    def    estrategia_356(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR48'] >= 1.1212) & (vars_dict['VAR48'] <= 1.1786)].copy()   
    def    estrategia_357(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR12'] >= 0.4749) & (vars_dict['VAR12'] <= 0.5165)].copy()   
    def    estrategia_358(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR28'] >= 0.111) & (vars_dict['VAR28'] <= 0.1304)].copy()   
    def    estrategia_359(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR59'] >= 0.0048) & (vars_dict['VAR59'] <= 0.007)].copy()   
    def    estrategia_360(df): return df[(vars_dict['VAR63'] >= -4.2156) & (vars_dict['VAR63'] <= -2.9378) & (vars_dict['VAR76'] >= 0.1619) & (vars_dict['VAR76'] <= 0.1852)].copy() 
    def    estrategia_361(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR28'] >= 0.15) & (vars_dict['VAR28'] <= 0.1574)].copy()   
    def    estrategia_362(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR59'] >= 0.0287) & (vars_dict['VAR59'] <= 0.0406)].copy()   
    def    estrategia_363(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR37'] >= 0.27) & (vars_dict['VAR37'] <= 0.2795)].copy()   
    def    estrategia_364(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR36'] >= 0.109) & (vars_dict['VAR36'] <= 0.1307)].copy()   
    def    estrategia_365(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR40'] >= 0.2204) & (vars_dict['VAR40'] <= 0.2348)].copy()   
    def    estrategia_366(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR14'] >= 0.7964) & (vars_dict['VAR14'] <= 0.8435)].copy()   
    def    estrategia_367(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR34'] >= 0.1024) & (vars_dict['VAR34'] <= 0.12)].copy()   
    def    estrategia_368(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR67'] >= -0.217) & (vars_dict['VAR67'] <= -0.0955)].copy()   
    def    estrategia_369(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR30'] >= 0.1138) & (vars_dict['VAR30'] <= 0.14)].copy()   
    def    estrategia_370(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR46'] >= 0.9167) & (vars_dict['VAR46'] <= 0.96)].copy()   
    def    estrategia_371(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR44'] >= 1.0417) & (vars_dict['VAR44'] <= 1.0909)].copy()   
    def    estrategia_372(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR76'] >= 0.1833) & (vars_dict['VAR76'] <= 0.2174)].copy()   
    def    estrategia_373(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR21'] >= 0.5083) & (vars_dict['VAR21'] <= 0.5429)].copy()   
    def    estrategia_374(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR26'] >= 0.1717) & (vars_dict['VAR26'] <= 0.1783)].copy()   
    def    estrategia_375(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR43'] >= 0.2111) & (vars_dict['VAR43'] <= 0.2204)].copy()   
    def    estrategia_376(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR48'] >= 1.2381) & (vars_dict['VAR48'] <= 1.2857)].copy()   
    def    estrategia_377(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR45'] >= 0.7778) & (vars_dict['VAR45'] <= 0.8077)].copy()   
    def    estrategia_378(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR66'] >= 0.9557) & (vars_dict['VAR66'] <= 1.942)].copy()   
    def    estrategia_379(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR61'] >= 0.0596) & (vars_dict['VAR61'] <= 0.082)].copy()   
    def    estrategia_380(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR33'] >= 0.1632) & (vars_dict['VAR33'] <= 0.1732)].copy()   
    def    estrategia_381(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR60'] >= 0.0227) & (vars_dict['VAR60'] <= 0.0281)].copy()   
    def    estrategia_382(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR41'] >= 0.187) & (vars_dict['VAR41'] <= 0.1969)].copy()   
    def    estrategia_383(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR32'] >= 0.2319) & (vars_dict['VAR32'] <= 0.2457)].copy()   
    def    estrategia_384(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR17'] >= 0.5906) & (vars_dict['VAR17'] <= 0.6531)].copy()   
    def    estrategia_385(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR15'] >= 0.4754) & (vars_dict['VAR15'] <= 0.4969)].copy()   
    def    estrategia_386(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR58'] >= 0.0932) & (vars_dict['VAR58'] <= 0.1192)].copy()   
    def    estrategia_387(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR27'] >= 0.1492) & (vars_dict['VAR27'] <= 0.1512)].copy()   
    def    estrategia_388(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR09'] >= 0.4246) & (vars_dict['VAR09'] <= 0.8087)].copy()   
    def    estrategia_389(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR10'] >= 1.2366) & (vars_dict['VAR10'] <= 2.3551)].copy()   
    def    estrategia_390(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR39'] >= 0.205) & (vars_dict['VAR39'] <= 0.24)].copy()   
    def    estrategia_391(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR35'] >= 0.1285) & (vars_dict['VAR35'] <= 0.1371)].copy()   
    def    estrategia_392(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR04'] >= 0.9853) & (vars_dict['VAR04'] <= 1.0588)].copy()   
    def    estrategia_393(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR06'] >= 0.9444) & (vars_dict['VAR06'] <= 1.0149)].copy()   
    def    estrategia_394(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR24'] >= 0.3376) & (vars_dict['VAR24'] <= 0.4545)].copy()   
    def    estrategia_395(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR62'] >= -15.0769) & (vars_dict['VAR62'] <= -9.5321)].copy()   
    def    estrategia_396(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR55'] >= 0.0) & (vars_dict['VAR55'] <= 0.0161)].copy()   
    def    estrategia_397(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR20'] >= 0.9713) & (vars_dict['VAR20'] <= 1.0667)].copy()   
    def    estrategia_398(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR64'] >= -0.4818) & (vars_dict['VAR64'] <= 0.1258)].copy()   
    def    estrategia_399(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR25'] >= 0.2769) & (vars_dict['VAR25'] <= 0.3)].copy()   
    def    estrategia_400(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR05'] >= 0.1649) & (vars_dict['VAR05'] <= 0.3698)].copy()   
    def    estrategia_401(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR02'] >= 2.7044) & (vars_dict['VAR02'] <= 6.0645)].copy()   
    def    estrategia_402(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR70'] >= 1.7044) & (vars_dict['VAR70'] <= 5.0645)].copy()   
    def    estrategia_403(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR11'] >= 1.1156) & (vars_dict['VAR11'] <= 1.2663)].copy()   
    def    estrategia_404(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR71'] >= 0.0) & (vars_dict['VAR71'] <= 0.0533)].copy()   
    def    estrategia_405(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR31'] >= 0.2613) & (vars_dict['VAR31'] <= 0.272)].copy()   
    def    estrategia_406(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR77'] >= 0.363) & (vars_dict['VAR77'] <= 0.432)].copy()   
    def    estrategia_407(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR18'] >= 0.3885) & (vars_dict['VAR18'] <= 0.5275)].copy()   
    def    estrategia_408(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR12'] >= 0.5941) & (vars_dict['VAR12'] <= 0.6145)].copy()   
    def    estrategia_409(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR75'] >= 0.3333) & (vars_dict['VAR75'] <= 0.5625)].copy()   
    def    estrategia_410(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR16'] >= 0.0) & (vars_dict['VAR16'] <= 0.3255)].copy()   
    def    estrategia_411(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR01'] >= 1.8457) & (vars_dict['VAR01'] <= 2.5806)].copy()   
    def    estrategia_412(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR03'] >= 0.3875) & (vars_dict['VAR03'] <= 0.5418)].copy()   
    def    estrategia_413(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR49'] >= 1.7308) & (vars_dict['VAR49'] <= 2.2222)].copy()   
    def    estrategia_414(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR47'] >= 0.45) & (vars_dict['VAR47'] <= 0.5778)].copy()   
    def    estrategia_415(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR42'] >= 0.1888) & (vars_dict['VAR42'] <= 0.2021)].copy()   
    def    estrategia_416(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR22'] >= 0.1574) & (vars_dict['VAR22'] <= 0.3519)].copy()   
    def    estrategia_417(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR54'] >= 0.2777) & (vars_dict['VAR54'] <= 0.3466)].copy()   
    def    estrategia_418(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR13'] >= 0.0) & (vars_dict['VAR13'] <= 0.4632)].copy()   
    def    estrategia_419(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR38'] >= 0.4737) & (vars_dict['VAR38'] <= 0.7407)].copy()   
    def    estrategia_420(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR23'] >= 0.2139) & (vars_dict['VAR23'] <= 0.2291)].copy()   
    def    estrategia_421(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR19'] >= 0.2405) & (vars_dict['VAR19'] <= 0.4123)].copy()   
    def    estrategia_422(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR56'] >= 0.0) & (vars_dict['VAR56'] <= 0.0101)].copy()   
    def    estrategia_423(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR72'] >= 0.0) & (vars_dict['VAR72'] <= 0.0312)].copy()   
    def    estrategia_424(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR63'] >= -11.1766) & (vars_dict['VAR63'] <= -6.9609)].copy()   
    def    estrategia_425(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR57'] >= 0.0437) & (vars_dict['VAR57'] <= 0.0703)].copy()   
    def    estrategia_426(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR65'] >= 1.2507) & (vars_dict['VAR65'] <= 2.0144)].copy()   
    def    estrategia_427(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR68'] >= 0.5729) & (vars_dict['VAR68'] <= 0.7268)].copy()   
    def    estrategia_428(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR07'] >= 0.8692) & (vars_dict['VAR07'] <= 0.9175)].copy()   
    def    estrategia_429(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR08'] >= 1.0899) & (vars_dict['VAR08'] <= 1.1505)].copy()   
    def    estrategia_430(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR73'] >= 0.0825) & (vars_dict['VAR73'] <= 0.1308)].copy()   
    def    estrategia_431(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR69'] >= -0.9975) & (vars_dict['VAR69'] <= -0.4823)].copy()   
    def    estrategia_432(df): return df[(vars_dict['VAR29'] >= 0.16) & (vars_dict['VAR29'] <= 0.1822) & (vars_dict['VAR74'] >= 0.0745) & (vars_dict['VAR74'] <= 0.0968)].copy() 
    def    estrategia_433(df): return df[(vars_dict['VAR28'] >= 0.0343) & (vars_dict['VAR28'] <= 0.0394)].copy()   
    def    estrategia_434(df): return df[(vars_dict['VAR31'] >= 0.4167) & (vars_dict['VAR31'] <= 0.439)].copy()   
    def    estrategia_435(df): return df[(vars_dict['VAR08'] >= 1.1209) & (vars_dict['VAR08'] <= 1.1337)].copy()   
    def    estrategia_436(df): return df[(vars_dict['VAR07'] >= 0.8821) & (vars_dict['VAR07'] <= 0.8922)].copy()   
    def    estrategia_437(df): return df[(vars_dict['VAR69'] >= 1.3639) & (vars_dict['VAR69'] <= 1.4028)].copy()   
    def    estrategia_438(df): return df[(vars_dict['VAR61'] >= 0.0476) & (vars_dict['VAR61'] <= 0.0482)].copy()   
    def    estrategia_439(df): return df[(vars_dict['VAR34'] >= 0.1407) & (vars_dict['VAR34'] <= 0.1421)].copy()   
    def    estrategia_440(df): return df[(vars_dict['VAR14'] >= 0.8088) & (vars_dict['VAR14'] <= 0.8167)].copy()   
    def    estrategia_441(df): return df[(vars_dict['VAR43'] >= 0.1967) & (vars_dict['VAR43'] <= 0.1982)].copy()   
    def    estrategia_442(df): return df[(vars_dict['VAR26'] >= 0.1427) & (vars_dict['VAR26'] <= 0.1457)].copy()   
    def    estrategia_443(df): return df[(vars_dict['VAR37'] >= 0.1857) & (vars_dict['VAR37'] <= 0.1881)].copy()   
    def    estrategia_444(df): return df[(vars_dict['VAR38'] >= 0.4) & (vars_dict['VAR38'] <= 0.4074)].copy()   
    def    estrategia_445(df): return df[(vars_dict['VAR30'] >= 0.6714) & (vars_dict['VAR30'] <= 0.8252)].copy()   
    def    estrategia_446(df): return df[(vars_dict['VAR60'] >= 0.099) & (vars_dict['VAR60'] <= 0.1652)].copy()   
    def    estrategia_447(df): return df[(vars_dict['VAR17'] >= 0.5743) & (vars_dict['VAR17'] <= 0.5828)].copy()   
    def    estrategia_448(df): return df[(vars_dict['VAR02'] >= 0.8263) & (vars_dict['VAR02'] <= 0.8504)].copy()   
    def    estrategia_449(df): return df[(vars_dict['VAR05'] >= 1.1759) & (vars_dict['VAR05'] <= 1.2101)].copy()   
    def    estrategia_450(df): return df[(vars_dict['VAR63'] >= -17.4265) & (vars_dict['VAR63'] <= -16.4341)].copy()   
    def    estrategia_451(df): return df[(vars_dict['VAR21'] >= 0.5102) & (vars_dict['VAR21'] <= 0.515)].copy()   
    def    estrategia_452(df): return df[(vars_dict['VAR59'] >= 0.0069) & (vars_dict['VAR59'] <= 0.0072)].copy()   
    def    estrategia_453(df): return df[(vars_dict['VAR66'] >= 5.314) & (vars_dict['VAR66'] <= 5.8028)].copy()   
    def    estrategia_454(df): return df[(vars_dict['VAR40'] >= 0.22) & (vars_dict['VAR40'] <= 0.2239)].copy()   
    def    estrategia_455(df): return df[(vars_dict['VAR48'] >= 1.5909) & (vars_dict['VAR48'] <= 1.6146)].copy()   
    def    estrategia_456(df): return df[(vars_dict['VAR45'] >= 0.6194) & (vars_dict['VAR45'] <= 0.6286)].copy()   
    def    estrategia_457(df): return df[(vars_dict['VAR15'] >= 0.541) & (vars_dict['VAR15'] <= 0.5424)].copy()   
    def    estrategia_458(df): return df[(vars_dict['VAR23'] >= 0.2283) & (vars_dict['VAR23'] <= 0.2333)].copy()   
    def    estrategia_459(df): return df[(vars_dict['VAR32'] >= 0.3927) & (vars_dict['VAR32'] <= 0.4255)].copy()   
    def    estrategia_460(df): return df[(vars_dict['VAR55'] >= 0.1047) & (vars_dict['VAR55'] <= 0.1082)].copy()   
    def    estrategia_461(df): return df[(vars_dict['VAR58'] >= 0.2775) & (vars_dict['VAR58'] <= 0.2913)].copy()   
    def    estrategia_462(df): return df[(vars_dict['VAR36'] >= 0.0944) & (vars_dict['VAR36'] <= 0.0974)].copy()   
    def    estrategia_463(df): return df[(vars_dict['VAR64'] >= 9.9932) & (vars_dict['VAR64'] <= 11.0435)].copy()   
    def    estrategia_464(df): return df[(vars_dict['VAR29'] >= 0.2119) & (vars_dict['VAR29'] <= 0.2196)].copy()   
    def    estrategia_465(df): return df[(vars_dict['VAR18'] >= 0.4045) & (vars_dict['VAR18'] <= 0.4076)].copy()   
    def    estrategia_466(df): return df[(vars_dict['VAR20'] >= 0.2806) & (vars_dict['VAR20'] <= 0.3124)].copy()   
    def    estrategia_467(df): return df[(vars_dict['VAR06'] >= 0.7963) & (vars_dict['VAR06'] <= 0.8052)].copy()   
    def    estrategia_468(df): return df[(vars_dict['VAR04'] >= 1.2419) & (vars_dict['VAR04'] <= 1.2558)].copy()   
    def    estrategia_469(df): return df[(vars_dict['VAR16'] >= 1.0691) & (vars_dict['VAR16'] <= 1.1029)].copy()   
    def    estrategia_470(df): return df[(vars_dict['VAR41'] >= 0.2111) & (vars_dict['VAR41'] <= 0.2128)].copy()   
    def    estrategia_471(df): return df[(vars_dict['VAR19'] >= 0.6141) & (vars_dict['VAR19'] <= 0.6208)].copy()   
    def    estrategia_472(df): return df[(vars_dict['VAR24'] >= 0.3579) & (vars_dict['VAR24'] <= 0.3665)].copy()   
    def    estrategia_473(df): return df[(vars_dict['VAR70'] >= 2.1176) & (vars_dict['VAR70'] <= 2.2099)].copy()   
    def    estrategia_474(df): return df[(vars_dict['VAR25'] >= 0.561) & (vars_dict['VAR25'] <= 0.592)].copy()   
    def    estrategia_475(df): return df[(vars_dict['VAR10'] >= 0.9343) & (vars_dict['VAR10'] <= 0.94)].copy()   
    def    estrategia_476(df): return df[(vars_dict['VAR09'] >= 1.0638) & (vars_dict['VAR09'] <= 1.0703)].copy()   
    def    estrategia_477(df): return df[(vars_dict['VAR44'] >= 0.525) & (vars_dict['VAR44'] <= 0.5576)].copy()   
    def    estrategia_478(df): return df[(vars_dict['VAR46'] >= 1.7935) & (vars_dict['VAR46'] <= 1.9048)].copy()   
    def    estrategia_479(df): return df[(vars_dict['VAR49'] >= 1.175) & (vars_dict['VAR49'] <= 1.2)].copy()   
    def    estrategia_480(df): return df[(vars_dict['VAR13'] >= 0.6667) & (vars_dict['VAR13'] <= 0.675)].copy()   
    def    estrategia_481(df): return df[(vars_dict['VAR77'] >= 0.7828) & (vars_dict['VAR77'] <= 0.8095)].copy()   
    def    estrategia_482(df): return df[(vars_dict['VAR68'] >= 2.6971) & (vars_dict['VAR68'] <= 4.7224)].copy()   
    def    estrategia_483(df): return df[(vars_dict['VAR47'] >= 0.4583) & (vars_dict['VAR47'] <= 0.4711)].copy()   
    def    estrategia_484(df): return df[(vars_dict['VAR03'] >= 0.6687) & (vars_dict['VAR03'] <= 0.6765)].copy()   
    def    estrategia_485(df): return df[(vars_dict['VAR01'] >= 1.4783) & (vars_dict['VAR01'] <= 1.4955)].copy()   
    def    estrategia_486(df): return df[(vars_dict['VAR71'] >= 0.3587) & (vars_dict['VAR71'] <= 0.3717)].copy()   
    def    estrategia_487(df): return df[(vars_dict['VAR39'] >= 1.47) & (vars_dict['VAR39'] <= 1.9087)].copy()   
    def    estrategia_488(df): return df[(vars_dict['VAR62'] >= -11.6059) & (vars_dict['VAR62'] <= -11.3491)].copy()   
    def    estrategia_489(df): return df[(vars_dict['VAR42'] >= 0.1006) & (vars_dict['VAR42'] <= 0.1029)].copy()   
    def    estrategia_490(df): return df[(vars_dict['VAR65'] >= 11.2144) & (vars_dict['VAR65'] <= 16.7615)].copy()   
    def    estrategia_491(df): return df[(vars_dict['VAR56'] >= 0.0973) & (vars_dict['VAR56'] <= 0.0995)].copy()   
    def    estrategia_492(df): return df[(vars_dict['VAR57'] >= 0.3965) & (vars_dict['VAR57'] <= 0.4196)].copy()   
    def    estrategia_493(df): return df[(vars_dict['VAR33'] >= 0.0021) & (vars_dict['VAR33'] <= 0.0022)].copy()   
    def    estrategia_494(df): return df[(vars_dict['VAR72'] >= 0.3556) & (vars_dict['VAR72'] <= 0.3647)].copy()   
    def    estrategia_495(df): return df[(vars_dict['VAR67'] >= -0.2184) & (vars_dict['VAR67'] <= -0.2046)].copy()   
    def    estrategia_496(df): return df[(vars_dict['VAR54'] >= 0.383) & (vars_dict['VAR54'] <= 0.3896)].copy()   
    def    estrategia_497(df): return df[(vars_dict['VAR11'] >= 0.83) & (vars_dict['VAR11'] <= 0.8385)].copy()   
    def    estrategia_498(df): return df[(vars_dict['VAR27'] >= 0.1261) & (vars_dict['VAR27'] <= 0.1271)].copy()   
    def    estrategia_499(df): return df[(vars_dict['VAR35'] >= 0.2744) & (vars_dict['VAR35'] <= 0.3059)].copy()   
    def    estrategia_500(df): return df[(vars_dict['VAR12'] >= 0.3949) & (vars_dict['VAR12'] <= 0.4)].copy()   
    def    estrategia_501(df): return df[(vars_dict['VAR74'] >= 0.3099) & (vars_dict['VAR74'] <= 0.3179)].copy()   
    def    estrategia_502(df): return df[(vars_dict['VAR75'] >= 0.2) & (vars_dict['VAR75'] <= 0.2121)].copy()   
    def    estrategia_503(df): return df[(vars_dict['VAR76'] >= 0.9883) & (vars_dict['VAR76'] <= 0.9914)].copy()   
    def    estrategia_504(df): return df[(vars_dict['VAR22'] >= 0.4698) & (vars_dict['VAR22'] <= 0.4771)].copy()   
    def    estrategia_505(df): return df[(vars_dict['VAR73'] >= 0.4286) & (vars_dict['VAR73'] <= 0.438)].copy() 
    def    estrategia_506(df): return df[(vars_dict['VAR66'] >= -8.1671) & (vars_dict['VAR66'] <= -7.9435)].copy()   
    def    estrategia_507(df): return df[(vars_dict['VAR41'] >= 0.0028) & (vars_dict['VAR41'] <= 0.0033)].copy()   
    def    estrategia_508(df): return df[(vars_dict['VAR59'] >= 0.0202) & (vars_dict['VAR59'] <= 0.0207)].copy()   
    def    estrategia_509(df): return df[(vars_dict['VAR48'] >= 1.6) & (vars_dict['VAR48'] <= 1.6146)].copy()   
    def    estrategia_510(df): return df[(vars_dict['VAR14'] >= 2.314) & (vars_dict['VAR14'] <= 2.428)].copy()   
    def    estrategia_511(df): return df[(vars_dict['VAR32'] >= 0.1979) & (vars_dict['VAR32'] <= 0.2)].copy()   
    def    estrategia_512(df): return df[(vars_dict['VAR43'] >= 0.1556) & (vars_dict['VAR43'] <= 0.1564)].copy()   
    def    estrategia_513(df): return df[(vars_dict['VAR26'] >= 0.066) & (vars_dict['VAR26'] <= 0.0671)].copy()   
    def    estrategia_514(df): return df[(vars_dict['VAR58'] >= 0.2775) & (vars_dict['VAR58'] <= 0.2832)].copy()   
    def    estrategia_515(df): return df[(vars_dict['VAR33'] >= 0.0021) & (vars_dict['VAR33'] <= 0.0022)].copy()   
    def    estrategia_516(df): return df[(vars_dict['VAR57'] >= 0.1749) & (vars_dict['VAR57'] <= 0.1751)].copy()   
    def    estrategia_517(df): return df[(vars_dict['VAR38'] >= 0.2152) & (vars_dict['VAR38'] <= 0.2171)].copy()   
    def    estrategia_518(df): return df[(vars_dict['VAR22'] >= 0.6211) & (vars_dict['VAR22'] <= 0.6254)].copy()   
    def    estrategia_519(df): return df[(vars_dict['VAR37'] >= 0.2075) & (vars_dict['VAR37'] <= 0.2087)].copy()   
    def    estrategia_520(df): return df[(vars_dict['VAR69'] >= 1.7746) & (vars_dict['VAR69'] <= 1.8084)].copy()   
    def    estrategia_521(df): return df[(vars_dict['VAR28'] >= 0.0343) & (vars_dict['VAR28'] <= 0.0372)].copy()   
    def    estrategia_522(df): return df[(vars_dict['VAR61'] >= 0.0476) & (vars_dict['VAR61'] <= 0.0482)].copy()   
    def    estrategia_523(df): return df[(vars_dict['VAR36'] >= 0.0346) & (vars_dict['VAR36'] <= 0.0385)].copy()   
    def    estrategia_524(df): return df[(vars_dict['VAR76'] >= 0.375) & (vars_dict['VAR76'] <= 0.3806)].copy()   
    def    estrategia_525(df): return df[(vars_dict['VAR45'] >= 0.6194) & (vars_dict['VAR45'] <= 0.625)].copy()   
    def    estrategia_526(df): return df[(vars_dict['VAR56'] >= 0.0985) & (vars_dict['VAR56'] <= 0.0995)].copy()   
    def    estrategia_527(df): return df[(vars_dict['VAR12'] >= 0.3949) & (vars_dict['VAR12'] <= 0.3971)].copy()   
    def    estrategia_528(df): return df[(vars_dict['VAR08'] >= 1.1273) & (vars_dict['VAR08'] <= 1.1337)].copy()   
    def    estrategia_529(df): return df[(vars_dict['VAR07'] >= 0.8821) & (vars_dict['VAR07'] <= 0.8871)].copy()   
    def    estrategia_530(df): return df[(vars_dict['VAR34'] >= 0.1414) & (vars_dict['VAR34'] <= 0.1421)].copy()   
    def    estrategia_531(df): return df[(vars_dict['VAR49'] >= 5.1896) & (vars_dict['VAR49'] <= 5.764)].copy()   
    def    estrategia_532(df): return df[(vars_dict['VAR47'] >= 0.1735) & (vars_dict['VAR47'] <= 0.1927)].copy()   
    def    estrategia_533(df): return df[(vars_dict['VAR63'] >= -3.0415) & (vars_dict['VAR63'] <= -2.9771)].copy()   
    def    estrategia_534(df): return df[(vars_dict['VAR02'] >= 0.8263) & (vars_dict['VAR02'] <= 0.8393)].copy()   
    def    estrategia_535(df): return df[(vars_dict['VAR05'] >= 1.1914) & (vars_dict['VAR05'] <= 1.2101)].copy()   
    def    estrategia_536(df): return df[(vars_dict['VAR03'] >= 1.5) & (vars_dict['VAR03'] <= 1.5664)].copy()   
    def    estrategia_537(df): return df[(vars_dict['VAR21'] >= 0.5123) & (vars_dict['VAR21'] <= 0.515)].copy()   
    def    estrategia_538(df): return df[(vars_dict['VAR67'] >= 1.4436) & (vars_dict['VAR67'] <= 1.5343)].copy()   
    def    estrategia_539(df): return df[(vars_dict['VAR18'] >= 0.4053) & (vars_dict['VAR18'] <= 0.4076)].copy()   
    def    estrategia_540(df): return df[(vars_dict['VAR15'] >= 0.5115) & (vars_dict['VAR15'] <= 0.5125)].copy()   
    def    estrategia_541(df): return df[(vars_dict['VAR19'] >= 0.8292) & (vars_dict['VAR19'] <= 0.8374)].copy()   
    def    estrategia_542(df): return df[(vars_dict['VAR31'] >= 0.4278) & (vars_dict['VAR31'] <= 0.439)].copy()   
    def    estrategia_543(df): return df[(vars_dict['VAR24'] >= 0.2552) & (vars_dict['VAR24'] <= 0.256)].copy()   
    def    estrategia_544(df): return df[(vars_dict['VAR30'] >= 0.032) & (vars_dict['VAR30'] <= 0.0343)].copy()   
    def    estrategia_545(df): return df[(vars_dict['VAR01'] >= 0.6384) & (vars_dict['VAR01'] <= 0.6667)].copy()   
    def    estrategia_546(df): return df[(vars_dict['VAR77'] >= 0.5385) & (vars_dict['VAR77'] <= 0.5429)].copy()   
    def    estrategia_547(df): return df[(vars_dict['VAR17'] >= 0.5743) & (vars_dict['VAR17'] <= 0.5782)].copy()   
    def    estrategia_548(df): return df[(vars_dict['VAR71'] >= 0.3587) & (vars_dict['VAR71'] <= 0.3652)].copy()   
    def    estrategia_549(df): return df[(vars_dict['VAR29'] >= 0.1662) & (vars_dict['VAR29'] <= 0.167)].copy()   
    def    estrategia_550(df): return df[(vars_dict['VAR16'] >= 0.5791) & (vars_dict['VAR16'] <= 0.5829)].copy()   
    def    estrategia_551(df): return df[(vars_dict['VAR75'] >= 0.2) & (vars_dict['VAR75'] <= 0.2069)].copy()   
    def    estrategia_552(df): return df[(vars_dict['VAR74'] >= 0.0695) & (vars_dict['VAR74'] <= 0.0714)].copy()   
    def    estrategia_553(df): return df[(vars_dict['VAR20'] >= 1.0667) & (vars_dict['VAR20'] <= 1.0723)].copy()   
    def    estrategia_554(df): return df[(vars_dict['VAR40'] >= 0.22) & (vars_dict['VAR40'] <= 0.2218)].copy()   
    def    estrategia_555(df): return df[(vars_dict['VAR73'] >= 0.4601) & (vars_dict['VAR73'] <= 0.4643)].copy()   
    def    estrategia_556(df): return df[(vars_dict['VAR62'] >= -20.9055) & (vars_dict['VAR62'] <= -20.2991)].copy()   
    def    estrategia_557(df): return df[(vars_dict['VAR72'] >= 0.3294) & (vars_dict['VAR72'] <= 0.3333)].copy()   
    def    estrategia_558(df): return df[(vars_dict['VAR46'] >= 2.3247) & (vars_dict['VAR46'] <= 2.5546)].copy()   
    def    estrategia_559(df): return df[(vars_dict['VAR44'] >= 0.3914) & (vars_dict['VAR44'] <= 0.4302)].copy()   
    def    estrategia_560(df): return df[(vars_dict['VAR70'] >= 0.865) & (vars_dict['VAR70'] <= 0.8807)].copy()   
    def    estrategia_561(df): return df[(vars_dict['VAR55'] >= 0.2796) & (vars_dict['VAR55'] <= 0.2828)].copy()   
    def    estrategia_562(df): return df[(vars_dict['VAR39'] >= 0.1453) & (vars_dict['VAR39'] <= 0.1484)].copy()   
    def    estrategia_563(df): return df[(vars_dict['VAR25'] >= 0.0055) & (vars_dict['VAR25'] <= 0.0061)].copy()   
    def    estrategia_564(df): return df[(vars_dict['VAR04'] >= 2.05) & (vars_dict['VAR04'] <= 2.1186)].copy()   
    def    estrategia_565(df): return df[(vars_dict['VAR06'] >= 0.472) & (vars_dict['VAR06'] <= 0.4878)].copy()   
    def    estrategia_566(df): return df[(vars_dict['VAR35'] >= 0.0846) & (vars_dict['VAR35'] <= 0.0856)].copy()   
    def    estrategia_567(df): return df[(vars_dict['VAR54'] >= 0.733) & (vars_dict['VAR54'] <= 0.7524)].copy()   
    def    estrategia_568(df): return df[(vars_dict['VAR13'] >= 0.3436) & (vars_dict['VAR13'] <= 0.3488)].copy()   
    def    estrategia_569(df): return df[(vars_dict['VAR11'] >= 0.5937) & (vars_dict['VAR11'] <= 0.6)].copy()   
    def    estrategia_570(df): return df[(vars_dict['VAR64'] >= -1.8245) & (vars_dict['VAR64'] <= -1.7923)].copy()   
    def    estrategia_571(df): return df[(vars_dict['VAR42'] >= 0.1138) & (vars_dict['VAR42'] <= 0.1148)].copy()   
    def    estrategia_572(df): return df[(vars_dict['VAR09'] >= 0.9799) & (vars_dict['VAR09'] <= 0.9847)].copy()   
    def    estrategia_573(df): return df[(vars_dict['VAR10'] >= 1.0155) & (vars_dict['VAR10'] <= 1.0205)].copy()   
    def    estrategia_574(df): return df[(vars_dict['VAR60'] >= 0.0245) & (vars_dict['VAR60'] <= 0.025)].copy()   
    def    estrategia_575(df): return df[(vars_dict['VAR68'] >= 0.382) & (vars_dict['VAR68'] <= 0.3915)].copy()   
    def    estrategia_576(df): return df[(vars_dict['VAR65'] >= 1.7959) & (vars_dict['VAR65'] <= 1.8809)].copy()   
    def    estrategia_577(df): return df[(vars_dict['VAR23'] >= 0.2283) & (vars_dict['VAR23'] <= 0.2308)].copy()   
    def    estrategia_578(df): return df[(vars_dict['VAR27'] >= 0.1393) & (vars_dict['VAR27'] <= 0.14)].copy() 



   



    
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
        (estrategia_575, "Estratégia 575"), (estrategia_576, "Estratégia 576"), (estrategia_577, "Estratégia 577"), (estrategia_578, "Estratégia 578")
        
        
   ]

# Página teste
st.title("Under -2.5 gols")




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
