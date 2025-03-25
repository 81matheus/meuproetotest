import streamlit as st
import pandas as pd
import numpy as np

# Título da aplicação
st.title("Estratégias Back Home")

# Função genérica de Backtest
def run_backtest(df, estrategia_func, estrategia_nome):
    df_filtrado = estrategia_func(df)
    df_filtrado['Profit'] = df_filtrado.apply(
        lambda row: (row['Odd_H_Back'] - 1) if row['Goals_H'] > row['Goals_A'] else -1,
        axis=1
    )
    total_jogos = len(df_filtrado)
    acertos = len(df_filtrado[df_filtrado['Goals_H'] > df_filtrado['Goals_A']])
    taxa_acerto = acertos / total_jogos if total_jogos > 0 else 0
    lucro_total = df_filtrado['Profit'].sum()
    
    return {
        "Estratégia": estrategia_nome,
        "Total de Jogos": total_jogos,
        "Taxa de Acerto": f"{taxa_acerto:.2%}",
        "Lucro Total": f"{lucro_total:.2f}",
        "Dataframe": df_filtrado
    }

# Análise das médias
def check_moving_averages(df_filtrado, estrategia_nome):
    df_filtrado['Acerto'] = (df_filtrado['Goals_H'] > df_filtrado['Goals_A']).astype(int)
    ultimos_8 = df_filtrado.tail(8) if len(df_filtrado) >= 8 else df_filtrado
    ultimos_40 = df_filtrado.tail(40) if len(df_filtrado) >= 40 else df_filtrado
    media_8 = ultimos_8['Acerto'].sum() / 8 if len(ultimos_8) == 8 else ultimos_8['Acerto'].mean()
    media_40 = ultimos_40['Acerto'].sum() / 40 if len(ultimos_40) == 40 else ultimos_40['Acerto'].mean()
    acima_das_medias = media_8 >= 0.5 and media_40 > 0.5
    
    return {
        "Estratégia": estrategia_nome,
        "Média 8": f"{media_8:.2f} ({ultimos_8['Acerto'].sum()} acertos em {len(ultimos_8)})",
        "Média 40": f"{media_40:.2f} ({ultimos_40['Acerto'].sum()} acertos em {len(ultimos_40)})",
        "Acima dos Limiares": acima_das_medias
    }

# Analisar jogos do dia
def analyze_daily_games(df_daily, estrategia_func, estrategia_nome):
    df_filtrado = estrategia_func(df_daily)
    if not df_filtrado.empty:
        return df_filtrado[['Time', 'Home', 'Away']]
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
    
    def estrategia_1(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR60'] >= 0.0047) & (vars_dict['VAR60'] <= 0.0110)].copy()

    def estrategia_2(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR76'] >= 0.050) & (vars_dict['VAR76'] <= 0.125)].copy()

    def estrategia_3(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR45'] >= 0.8333) & (vars_dict['VAR45'] <= 0.9166)].copy()

    def estrategia_4(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR32'] >= 0.2500) & (vars_dict['VAR32'] <= 0.2750)].copy()

    def estrategia_5(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR24'] >= 0.2248) & (vars_dict['VAR24'] <= 0.2413)].copy()

    def estrategia_6(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR65'] >= 2.9288) & (vars_dict['VAR65'] <= 4.965)].copy()

    def estrategia_7(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR15'] >= 0.5292) & (vars_dict['VAR15'] <= 0.5424)].copy()

    def estrategia_8(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR61'] >= 0.0036) & (vars_dict['VAR61'] <= 0.0075)].copy()

    def estrategia_9(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR37'] >= 0.2174) & (vars_dict['VAR37'] <= 0.2433)].copy()

    def estrategia_10(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR20'] >= 0.7299) & (vars_dict['VAR20'] <= 0.8085)].copy()

    def estrategia_11(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR48'] >= 1.0909) & (vars_dict['VAR48'] <= 1.20)].copy()

    def estrategia_12(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR21'] >= 0.6053) & (vars_dict['VAR21'] <= 0.6181)].copy()

    def estrategia_13(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR77'] >= 0.0434) & (vars_dict['VAR77'] <= 0.0937)].copy()

    def estrategia_14(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR74'] >= 0.0) & (vars_dict['VAR74'] <= 0.040)].copy()

    def estrategia_15(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR38'] >= 0.2913) & (vars_dict['VAR38'] <= 0.30)].copy()

    def estrategia_16(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR07'] >= 0.7124) & (vars_dict['VAR07'] <= 0.8207)].copy()

    def estrategia_17(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR08'] >= 1.2183) & (vars_dict['VAR08'] <= 1.4036)].copy()

    def estrategia_18(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR14'] >= 0.6471) & (vars_dict['VAR14'] <= 0.7238)].copy()

    def estrategia_19(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR34'] >= 0.1772) & (vars_dict['VAR34'] <= 0.2288)].copy()

    def estrategia_20(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR66'] >= -0.1538) & (vars_dict['VAR66'] <= 1.1857)].copy()

    def estrategia_21(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR27'] >= 0.1321) & (vars_dict['VAR27'] <= 0.1424)].copy()

    def estrategia_22(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR10'] >= 0.9896) & (vars_dict['VAR10'] <= 1.0822)].copy()

    def estrategia_23(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR58'] >= 0.00) & (vars_dict['VAR58'] <= 0.0208)].copy()

    def estrategia_24(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR09'] >= 0.9240) & (vars_dict['VAR09'] <= 1.0104)].copy()

    def estrategia_25(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR29'] >= 0.1469) & (vars_dict['VAR29'] <= 0.16)].copy()

    def estrategia_26(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR54'] >= 0.0485) & (vars_dict['VAR54'] <= 0.0742)].copy()

    def estrategia_27(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR68'] >= 0.2170) & (vars_dict['VAR68'] <= 0.3841)].copy()

    def estrategia_28(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR23'] >= 0.180) & (vars_dict['VAR23'] <= 0.2191)].copy()

    def estrategia_29(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR26'] >= 0.1712) & (vars_dict['VAR26'] <= 0.2155)].copy()

    def estrategia_30(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR41'] >= 0.1553) & (vars_dict['VAR41'] <= 0.1583)].copy()
      # adicional-------------------------------------------------------------
    def estrategia_31(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR33'] >= 0.1536) & (vars_dict['VAR33'] <= 0.1812)].copy()

    def estrategia_32(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR35'] >= 0.1354) & (vars_dict['VAR35'] <= 0.1565)].copy()

    def estrategia_33(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR18'] >= 0.5253) & (vars_dict['VAR18'] <= 0.5655)].copy()

    def estrategia_34(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR30'] >= 0.2400) & (vars_dict['VAR30'] <= .3150)].copy()

    def estrategia_35(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR25'] >= 0.2207) & (vars_dict['VAR25'] <= 0.2423)].copy()

    def estrategia_36(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR28'] >= 0.1062) & (vars_dict['VAR28'] <= 0.1241)].copy()

    def estrategia_37(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR42'] >= 0.1533) & (vars_dict['VAR42'] <= 0.1634)].copy()

    def estrategia_38(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR01'] >= 1.1807) & (vars_dict['VAR01'] <= 1.2804)].copy()

    def estrategia_39(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR03'] >= 0.7809) & (vars_dict['VAR03'] <= 0.8468)].copy()

    def estrategia_40(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR12'] >= 0.6564) & (vars_dict['VAR12'] <= 0.7434)].copy()

    def estrategia_41(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR22'] >= 0.5408) & (vars_dict['VAR22'] <= 0.6123)].copy()

    def estrategia_42(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR70'] >= 0.1347) & (vars_dict['VAR70'] <= 0.2064)].copy()

    def estrategia_43(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR63'] >= -2.3843) & (vars_dict['VAR63'] <= -1.5319)].copy()

    def estrategia_44(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR71'] >= 0.1860) & (vars_dict['VAR71'] <= 0.2804)].copy()

    def estrategia_45(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR59'] >= 0.0155) & (vars_dict['VAR59'] <= 0.0208)].copy()

    def estrategia_46(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR11'] >= 0.7028) & (vars_dict['VAR11'] <= 0.7363)].copy()

    def estrategia_47(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR75'] >= 0.1428) & (vars_dict['VAR75'] <= 0.1747)].copy()

    def estrategia_48(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR40'] >= 0.1927) & (vars_dict['VAR40'] <= 0.2171)].copy()

    def estrategia_49(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR39'] >= 0.23) & (vars_dict['VAR39'] <= 0.2472)].copy()

    def estrategia_50(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR72'] >= 0.250) & (vars_dict['VAR72'] <= 0.2869)].copy()

    def estrategia_51(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR57'] >= 0.1361) & (vars_dict['VAR57'] <= 0.1750)].copy()

    def estrategia_52(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR46'] >= 1.0) & (vars_dict['VAR46'] <= 1.0597)].copy()

    def estrategia_53(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR44'] >= 0.9436) & (vars_dict['VAR44'] <= 1.000)].copy()

    def estrategia_54(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR67'] >= 0.4822) & (vars_dict['VAR67'] <= 2.2614)].copy()

    def estrategia_55(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR31'] >= 0.3285) & (vars_dict['VAR31'] <= 0.4949)].copy()

    def estrategia_56(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR36'] >= 0.2019) & (vars_dict['VAR36'] <= 0.2576)].copy()

    def estrategia_57(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR69'] >= -1.5240) & (vars_dict['VAR69'] <= -0.3797)].copy()

    def estrategia_58(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR49'] >= 0.680) & (vars_dict['VAR49'] <= 0.8727)].copy()

    def estrategia_59(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR47'] >= 1.1458) & (vars_dict['VAR47'] <= 1.4705)].copy()

    def estrategia_60(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR73'] >= 0.00) & (vars_dict['VAR73'] <= 0.0515)].copy()
    # adicional-------------------------------------------------------------
    def estrategia_61(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR13'] >= 0.6978) & (vars_dict['VAR13'] <= 0.7639)].copy()

    def estrategia_62(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR19'] >= 0.6635) & (vars_dict['VAR19'] <= 0.7417)].copy()

    def estrategia_63(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR62'] >= 0.5185) & (vars_dict['VAR62'] <= 2.0514)].copy()

    def estrategia_64(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR55'] >= 0.0845) & (vars_dict['VAR55'] <= 0.1209)].copy()

    def estrategia_65(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR02'] >= 0.8194) & (vars_dict['VAR02'] <= 0.9509)].copy()

    def estrategia_66(df):
       return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR05'] >= 1.0516) & (vars_dict['VAR05'] <= 1.2203)].copy()

    def estrategia_67(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR56'] >= 0.0630) & (vars_dict['VAR56'] <= 0.0729)].copy()

    def estrategia_68(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR16'] >= 0.5129) & (vars_dict['VAR16'] <= 0.5721)].copy()

    def estrategia_69(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR17'] >= 0.5967) & (vars_dict['VAR17'] <= 0.6268)].copy()

    def estrategia_70(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR64'] >= 2.8089) & (vars_dict['VAR64'] <= 4.2769)].copy()

    def estrategia_71(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR06'] >= 1.2131) & (vars_dict['VAR06'] <= 1.2792)].copy()

    def estrategia_72(df):
        return df[(vars_dict['VAR43'] >= 0.1688) & (vars_dict['VAR43'] <= 0.1830) &
                 (vars_dict['VAR04'] >= 0.7817) & (vars_dict['VAR04'] <= 0.8243)].copy()
    
    return [
        (estrategia_1, "Estratégia 1"),
        (estrategia_2, "Estratégia 2"),
        (estrategia_3, "Estratégia 3"),
        (estrategia_4, "Estratégia 4"),
        (estrategia_5, "Estratégia 5"),
        (estrategia_6, "Estratégia 6"),
        (estrategia_7, "Estratégia 7"),
        (estrategia_8, "Estratégia 8"),
        (estrategia_9, "Estratégia 9"),
        (estrategia_10, "Estratégia 10"),
        (estrategia_11, "Estratégia 11"),
        (estrategia_12, "Estratégia 12"),
        (estrategia_13, "Estratégia 13"),
        (estrategia_14, "Estratégia 14"),
        (estrategia_15, "Estratégia 15"),
        (estrategia_16, "Estratégia 16"),
        (estrategia_17, "Estratégia 17"),
        (estrategia_18, "Estratégia 18"),
        (estrategia_19, "Estratégia 19"),
        (estrategia_20, "Estratégia 20"),
        (estrategia_21, "Estratégia 21"),
        (estrategia_22, "Estratégia 22"),
        (estrategia_23, "Estratégia 23"),
        (estrategia_24, "Estratégia 24"),
        (estrategia_25, "Estratégia 25"),
        (estrategia_26, "Estratégia 26"),
        (estrategia_27, "Estratégia 27"),
        (estrategia_28, "Estratégia 28"),
        (estrategia_29, "Estratégia 29"),
        (estrategia_30, "Estratégia 30"),
        (estrategia_31, "Estratégia 31"),
        (estrategia_32, "Estratégia 32"),
        (estrategia_33, "Estratégia 33"),
        (estrategia_34, "Estratégia 34"),
        (estrategia_35, "Estratégia 35"),
        (estrategia_36, "Estratégia 36"),
        (estrategia_37, "Estratégia 37"),
        (estrategia_38, "Estratégia 38"),
        (estrategia_39, "Estratégia 39"),
        (estrategia_40, "Estratégia 40"),
        (estrategia_41, "Estratégia 41"),
        (estrategia_42, "Estratégia 42"),
        (estrategia_43, "Estratégia 43"),
        (estrategia_44, "Estratégia 44"),
        (estrategia_45, "Estratégia 45"),
        (estrategia_46, "Estratégia 46"),
        (estrategia_47, "Estratégia 47"),
        (estrategia_48, "Estratégia 48"),
        (estrategia_49, "Estratégia 49"),
        (estrategia_50, "Estratégia 50"),
        (estrategia_51, "Estratégia 51"),
        (estrategia_52, "Estratégia 52"),
        (estrategia_53, "Estratégia 53"),
        (estrategia_54, "Estratégia 54"),
        (estrategia_55, "Estratégia 55"),
        (estrategia_56, "Estratégia 56"),
        (estrategia_57, "Estratégia 57"),
        (estrategia_58, "Estratégia 58"),
        (estrategia_59, "Estratégia 59"),
        (estrategia_60, "Estratégia 60"),
        (estrategia_61, "Estratégia 61"),
        (estrategia_62, "Estratégia 62"),
        (estrategia_63, "Estratégia 63"),
        (estrategia_64, "Estratégia 64"),
        (estrategia_65, "Estratégia 65"),
        (estrategia_66, "Estratégia 66"),
        (estrategia_67, "Estratégia 67"),
        (estrategia_68, "Estratégia 68"),
        (estrategia_69, "Estratégia 69"),
        (estrategia_70, "Estratégia 70"),
        (estrategia_71, "Estratégia 71"),
        (estrategia_72, "Estratégia 72")
    ]

# Página teste
st.title("Back Home")

# Interface Streamlit
st.header("Upload da Planilha Histórica")
uploaded_historical = st.file_uploader("Faça upload da planilha histórica (xlsx)", type=["xlsx"])

if uploaded_historical is not None:
    df_historico = pd.read_excel(uploaded_historical)
    estrategias = apply_strategies(df_historico)
    
    # Executar backtest
    st.header("Resultados do Backtest")
    backtest_results = []
    medias_results = []
    resultados = {}
    
    for estrategia_func, estrategia_nome in estrategias:
        backtest_result = run_backtest(df_historico, estrategia_func, estrategia_nome)
        medias_result = check_moving_averages(backtest_result["Dataframe"], estrategia_nome)
        backtest_results.append(backtest_result)
        medias_results.append(medias_result)
        resultados[estrategia_nome] = (backtest_result["Dataframe"], medias_result["Acima dos Limiares"])
    
    # Exibir resultados do backtest
    # st.subheader("Resumo do Backtest")
    # st.dataframe(pd.DataFrame([r for r in backtest_results if r["Total de Jogos"] > 0]).drop(columns=["Dataframe"]))
    with st.expander("📊 Resultados do Backtest"):
        st.subheader("Resumo do Backtest")
        st.dataframe(pd.DataFrame([r for r in backtest_results if r["Total de Jogos"] > 0]).drop(columns=["Dataframe"]))
    
    # Exibir análise das médias
    # st.subheader("Análise das Médias")
    # st.dataframe(pd.DataFrame(medias_results))
    with st.expander("📈 Análise das Médias"):
        st.subheader("Detalhes das Médias")
        st.dataframe(pd.DataFrame(medias_results))
    
    # Upload dos jogos do dia para estratégias aprovadas
    estrategias_aprovadas = [nome for nome, (_, acima) in resultados.items() if acima]
    if estrategias_aprovadas:
        st.header("Upload dos Jogos do Dia")
        uploaded_daily = st.file_uploader("Faça upload da planilha com os jogos do dia (xlsx)", type=["xlsx"])
        
        if uploaded_daily is not None:
            df_daily = pd.read_excel(uploaded_daily)
            st.header("Jogos Aprovados para Hoje")
            
            # Lista unificada de jogos aprovados
            jogos_aprovados_total = []
            
            for estrategia_nome in estrategias_aprovadas:
                estrategia_func = next(func for func, nome in estrategias if nome == estrategia_nome)
                jogos_aprovados = analyze_daily_games(df_daily, estrategia_func, estrategia_nome)
                if jogos_aprovados is not None:
                    # st.subheader(f"{estrategia_nome}")
                    # st.dataframe(jogos_aprovados)
                    # jogos_aprovados_total.extend(jogos_aprovados.to_dict('records'))
                 # with st.expander(f"🏆 {estrategia_nome}"):
                  #  st.dataframe(jogos_aprovados)
                    jogos_aprovados_total.extend(jogos_aprovados.to_dict('records'))
            
            # Remover jogos repetidos
            if jogos_aprovados_total:
                # Usar drop_duplicates para remover linhas duplicadas
                df_jogos_aprovados = pd.DataFrame(jogos_aprovados_total).drop_duplicates()
                
                st.header("🏆 Lista Unificada de Jogos Aprovados")
                st.dataframe(df_jogos_aprovados)
            else:
                st.write("Nenhum jogo do dia atende aos critérios das estratégias.")



       
