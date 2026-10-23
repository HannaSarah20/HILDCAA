# -*- coding: utf-8 -*-
"""
================================================================================
IDENTIFICAÇÃO DE EVENTOS HILDCAA NO CICLO SOLAR 24 (2008 a 2019)
Arquivo: HILCAAA_24.py (e HILDCAA_24.py)
Metodologia Científica e Critérios Físicos:
  1. Tsurutani & Gonzalez (1987) - Critérios Clássicos de HILDCAA
  2. Prestes et al. (2017, Ann. Geophys. / Adv. Space Res.) - Critérios Alterados (HILDCAA*)
  3. Gonzalez et al. (1994) - Definição de Tempestades Magnéticas (Dst / Sym-H <= -50 nT)

CRITÉRIOS OBRIGATÓRIOS IMPLEMENTADOS:
  1. Intensidade Auroral (AE):
     - Pico do índice AE >= 1000 nT durante o evento.
  2. Atividade Auroral Contínua (AE):
     - O AE deve se manter predominantemente ativo (>= 200 nT).
     - Critério Alterado (HILDCAA*, Prestes et al., 2017): o AE não pode cair
       abaixo de 200 nT por mais de 4 horas consecutivas (240 minutos).
     - Critério Tradicional (HILDCAA, Tsurutani & Gonzalez, 1987): o AE não pode cair
       abaixo de 200 nT por mais de 2 horas consecutivas (120 minutos).
  3. Duração do Evento:
     - Duração total >= 2 dias (48 horas = 2880 minutos).
  4. Ocorrência Fora de Tempestades Magnéticas (Sym-H > -50 nT):
     - Os eventos HILDCAA NÃO podem ocorrer durante a fase principal de tempestades
       geomagnéticas. Portanto, Sym-H deve ser estritamente maior que -50 nT.
     - Períodos com Sym-H <= -50 nT caracterizam tempestades magnéticas e encerram
       ou impedem o intervalo HILDCAA.
================================================================================
"""

import os
import sys
import glob
import time
import numpy as np
import pandas as pd

# Ajustar saída para UTF-8 no terminal Windows para evitar erros de codificação
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def localizar_arquivos_ciclo24():
    """
    Localiza todos os arquivos 'dados*.txt' pertencentes ao Ciclo Solar 24.
    """
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorios_busca = [
        diretorio_script,
        os.path.join(diretorio_script, '..', 'Ciclo solar 24'),
        os.path.join(os.getcwd(), 'Ciclo solar 24'),
        os.getcwd()
    ]
    
    arquivos_encontrados = {}
    for d in diretorios_busca:
        if os.path.isdir(d):
            for caminho in glob.glob(os.path.join(d, 'dados*.txt')):
                nome = os.path.basename(caminho)
                # Selecionar arquivos entre 2008 e 2019
                for ano in range(2008, 2020):
                    if f"dados{ano}.txt" == nome and nome not in arquivos_encontrados:
                        arquivos_encontrados[nome] = os.path.abspath(caminho)
                        
    arquivos_ordenados = [arquivos_encontrados[k] for k in sorted(arquivos_encontrados.keys())]
    return arquivos_ordenados


def carregar_dados_ciclo24(arquivos):
    """
    Carrega e unifica os arquivos OMNIWeb em resolução de 1 minuto em um único DataFrame Pandas.
    Trata datas (Year, DOY, Hour, Minute) e remove valores nulos (fill values).
    """
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo 'dados*.txt' do Ciclo Solar 24 foi encontrado.")

    print(f"Carregando {len(arquivos)} arquivos do Ciclo Solar 24 (2008 a 2019)...")
    t0 = time.time()
    dfs = []
    
    for caminho in arquivos:
        nome = os.path.basename(caminho)
        # Nos arquivos do Ciclo 24 (18 colunas):
        # 0: Year, 1: DOY, 2: Hour, 3: Minute, 15: AE, 17: SymH
        df_ano = pd.read_csv(
            caminho,
            sep=r'\s+',
            header=None,
            usecols=[0, 1, 2, 3, 15, 17],
            names=['Year', 'DOY', 'Hour', 'Minute', 'AE', 'SymH'],
            dtype={
                'Year': np.int16,
                'DOY': np.int16,
                'Hour': np.int8,
                'Minute': np.int8,
                'AE': np.float32,
                'SymH': np.float32
            }
        )
        
        # Construção vetorizada rápida do DatetimeIndex
        base_ano = pd.to_datetime(df_ano['Year'].values.astype(str) + '-01-01')
        indice_dt = (
            base_ano +
            pd.to_timedelta(df_ano['DOY'] - 1, unit='D') +
            pd.to_timedelta(df_ano['Hour'], unit='h') +
            pd.to_timedelta(df_ano['Minute'], unit='m')
        )
        df_ano.index = indice_dt
        df_ano = df_ano[['AE', 'SymH']]
        dfs.append(df_ano)
        
    df_total = pd.concat(dfs)
    df_total.sort_index(inplace=True)
    # Remove eventuais duplicatas de timestamp na fronteira de anos
    df_total = df_total[~df_total.index.duplicated(keep='first')]
    
    # Tratamento dos fill values do OMNIWeb (99999, 9999 -> NaN)
    df_total['AE'] = df_total['AE'].replace([99999, 9999, 9999.0, 99999.0], np.nan)
    df_total['SymH'] = df_total['SymH'].replace([99999, 9999, 9999.0, 99999.0], np.nan)
    
    tempo_carga = time.time() - t0
    print(f"-> Dados carregados e tratados com sucesso em {tempo_carga:.1f}s!")
    print(f"-> Total de registros (minutos): {len(df_total):,}")
    print(f"-> Período: {df_total.index.min().strftime('%d/%m/%Y %H:%M')} até {df_total.index.max().strftime('%d/%m/%Y %H:%M')}\n")
    
    return df_total


def identificar_eventos(df, max_gap_hours=4.0, min_dur_days=2.0, peak_ae_min=1000.0, symh_thresh=-50.0):
    """
    Algoritmo em Duas Etapas (Figura 2 de Prestes et al., 2017) para identificação de eventos HILDCAA:
      - Etapa 1 (1 min): Continuidade do AE >= 200 nT (quedas < 200 nT por no máximo max_gap_hours),
        ajuste do ponto final (last_active_idx), comprimento >= 2880 pontos e pico AE >= 1000 nT.
      - Etapa 2 (1 hora): Teste de distúrbio geomagnético na média horária de Sym-H / Dst (1h),
        removendo fases principais de tempestades magnéticas (<= -50 nT) sem fragmentar
        fases de recuperação por flutuações rápidas de 1 minuto.
    """
    times = df.index
    ae_vals = df['AE'].values
    symh_vals = df['SymH'].values
    n = len(df)

    max_gap_mins = int(round(max_gap_hours * 60))
    min_pts = int(round(min_dur_days * 1440))

    # Etapa 1: Candidatos contínuos de AE (1 min)
    candidatos_ae = []
    in_ev = False
    s_idx = 0
    last_act = 0
    pk_ae = 0.0
    gap = 0

    for i in range(n):
        v = ae_vals[i]
        act = (not np.isnan(v)) and (v >= 200.0)
        if not in_ev:
            if act:
                in_ev = True
                s_idx = i
                last_act = i
                pk_ae = float(v)
                gap = 0
        else:
            if act:
                last_act = i
                gap = 0
                if v > pk_ae:
                    pk_ae = float(v)
            else:
                gap += 1
                if gap > max_gap_mins:
                    pts = int((times[last_act] - times[s_idx]).total_seconds() // 60) + 1
                    if pts >= min_pts and pk_ae >= peak_ae_min:
                        candidatos_ae.append((s_idx, last_act, f'AE < 200 nT por mais de {max_gap_hours} horas'))
                    in_ev = False

    if in_ev:
        pts = int((times[last_act] - times[s_idx]).total_seconds() // 60) + 1
        if pts >= min_pts and pk_ae >= peak_ae_min:
            candidatos_ae.append((s_idx, last_act, 'Fim da série temporal'))

    # Etapa 2: Teste de Distúrbio Geomagnético em resolução de 1 hora (Dst / Sym-H 1h)
    symh_1h = df['SymH'].resample('1h').mean()
    horas_tempestade = set(symh_1h[symh_1h <= symh_thresh].index)

    eventos = []
    for s_i, e_i, motivo_fim in candidatos_ae:
        h_ini = times[s_i].floor('1h')
        h_fim = times[e_i].floor('1h')
        horas_cand = pd.date_range(h_ini, h_fim, freq='1h')
        tem_tempestade = any(h in horas_tempestade for h in horas_cand)

        if not tem_tempestade:
            pts = int((times[e_i] - times[s_i]).total_seconds() // 60) + 1
            sub_ae = ae_vals[s_i:e_i + 1]
            sub_sh = symh_vals[s_i:e_i + 1]
            eventos.append({
                'inicio': times[s_i],
                'termino': times[e_i],
                'duracao_dias': pts / 1440.0,
                'duracao_horas': pts / 60.0,
                'pico_ae': float(np.nanmax(sub_ae)),
                'min_symh': float(np.nanmin(sub_sh)) if not np.all(np.isnan(sub_sh)) else 0.0,
                'motivo_fim': motivo_fim
            })
        else:
            in_sub = False
            sub_s = s_i
            for idx_pt in range(s_i, e_i + 1):
                ts = times[idx_pt]
                h_ts = ts.floor('1h')
                is_storm_hr = (h_ts in horas_tempestade)
                is_inicio_rec = (
                    is_storm_hr
                    and ts.minute == 59
                    and (h_ts + pd.Timedelta(hours=1)) not in horas_tempestade
                )
                if (not is_storm_hr) or is_inicio_rec:
                    if not in_sub:
                        if is_inicio_rec or (not np.isnan(ae_vals[idx_pt]) and ae_vals[idx_pt] >= 200.0):
                            in_sub = True
                            sub_s = idx_pt
                else:
                    if in_sub:
                        sub_e = idx_pt - 1
                        while sub_e > sub_s and (np.isnan(ae_vals[sub_e]) or ae_vals[sub_e] < 200.0):
                            sub_e -= 1
                        pts = int((times[sub_e] - times[sub_s]).total_seconds() // 60) + 1
                        sub_ae = ae_vals[sub_s:sub_e + 1]
                        pk = float(np.nanmax(sub_ae)) if len(sub_ae) > 0 else 0.0
                        if pts >= min_pts and pk >= peak_ae_min:
                            sub_sh = symh_vals[sub_s:sub_e + 1]
                            eventos.append({
                                'inicio': times[sub_s],
                                'termino': times[sub_e],
                                'duracao_dias': pts / 1440.0,
                                'duracao_horas': pts / 60.0,
                                'pico_ae': pk,
                                'min_symh': float(np.nanmin(sub_sh)) if not np.all(np.isnan(sub_sh)) else 0.0,
                                'motivo_fim': 'Remoção de Fase Principal de Tempestade (Dst/Sym-H 1h <= -50 nT)'
                            })
                        in_sub = False
            if in_sub:
                sub_e = e_i
                while sub_e > sub_s and (np.isnan(ae_vals[sub_e]) or ae_vals[sub_e] < 200.0):
                    sub_e -= 1
                pts = int((times[sub_e] - times[sub_s]).total_seconds() // 60) + 1
                sub_ae = ae_vals[sub_s:sub_e + 1]
                pk = float(np.nanmax(sub_ae)) if len(sub_ae) > 0 else 0.0
                if pts >= min_pts and pk >= peak_ae_min:
                    sub_sh = symh_vals[sub_s:sub_e + 1]
                    eventos.append({
                        'inicio': times[sub_s],
                        'termino': times[sub_e],
                        'duracao_dias': pts / 1440.0,
                        'duracao_horas': pts / 60.0,
                        'pico_ae': pk,
                        'min_symh': float(np.nanmin(sub_sh)) if not np.all(np.isnan(sub_sh)) else 0.0,
                        'motivo_fim': motivo_fim
                    })

    return eventos


def imprimir_tabela_eventos(eventos, titulo_criterio):
    """
    Imprime na tela a listagem completa com o formato exato solicitado pelo usuário:
    - Quantidade de eventos
    - Duração de cada evento
    - Dia, mês, ano e horário de início e término
    """
    print("=" * 115)
    print(f"RESULTADO: {titulo_criterio}")
    print(f"TOTAL DE EVENTOS ENCONTRADOS: {len(eventos)}")
    print("=" * 115)
    print(f"{'Nº':^4} | {'INÍCIO (Dia/Mês/Ano Hora:Min)':^30} | {'TÉRMINO (Dia/Mês/Ano Hora:Min)':^30} | {'DURAÇÃO':^22} | {'PICO AE':^9} | {'MÍN SYM-H':^10}")
    print("-" * 115)
    
    for i, ev in enumerate(eventos, start=1):
        str_inicio = ev['inicio'].strftime('%d/%m/%Y às %H:%M')
        str_termino = ev['termino'].strftime('%d/%m/%Y às %H:%M')
        dur_str = f"{ev['duracao_dias']:.2f} dias ({ev['duracao_horas']:.1f} h)"
        pico_ae_str = f"{ev['pico_ae']:.0f} nT"
        min_symh_str = f"{ev['min_symh']:.0f} nT"
        print(f"{i:02d}   | {str_inicio:^30} | {str_termino:^30} | {dur_str:^22} | {pico_ae_str:^9} | {min_symh_str:^10}")
        
    print("=" * 115 + "\n")


def salvar_tabela_csv(eventos, caminho_csv):
    """
    Exporta a lista de eventos para uma planilha CSV para facilitar o uso acadêmico.
    """
    linhas = []
    for i, ev in enumerate(eventos, start=1):
        linhas.append({
            'Evento': i,
            'Data_Inicio': ev['inicio'].strftime('%d/%m/%Y'),
            'Hora_Inicio': ev['inicio'].strftime('%H:%M'),
            'Data_Termino': ev['termino'].strftime('%d/%m/%Y'),
            'Hora_Termino': ev['termino'].strftime('%H:%M'),
            'Duracao_Dias': round(ev['duracao_dias'], 2),
            'Duracao_Horas': round(ev['duracao_horas'], 1),
            'Pico_AE_nT': round(ev['pico_ae'], 0),
            'Min_SymH_nT': round(ev['min_symh'], 0),
            'Motivo_Termino': ev['motivo_fim']
        })
    df_out = pd.DataFrame(linhas)
    df_out.to_csv(caminho_csv, index=False, sep=';', encoding='utf-8-sig')
    print(f"-> Tabela salva em CSV: {caminho_csv}")


def main():
    arquivos = localizar_arquivos_ciclo24()
    dados = carregar_dados_ciclo24(arquivos)
    
    # 1. CRITÉRIO ALTERADO (HILDCAA* - Prestes et al., 2017: AE < 200 nT por até 4 horas)
    eventos_hildcaa_star = identificar_eventos(
        dados,
        max_gap_hours=4.0,
        min_dur_days=2.0,
        peak_ae_min=1000.0,
        symh_thresh=-50.0
    )
    imprimir_tabela_eventos(
        eventos_hildcaa_star,
        "CRITÉRIO ALTERADO (HILDCAA* - Prestes et al., 2017) [Janela de Calmaria de AE até 4h]"
    )
    
    # Salvar em CSV no diretório do Ciclo Solar 24
    pasta_destino = os.path.dirname(arquivos[0])
    csv_hildcaa_star = os.path.join(pasta_destino, "eventos_HILDCAA_star_Ciclo24.csv")
    salvar_tabela_csv(eventos_hildcaa_star, csv_hildcaa_star)
    
    # 2. CRITÉRIO TRADICIONAL (HILDCAA Clássico - Tsurutani & Gonzalez, 1987: AE < 200 nT por até 2 horas)
    eventos_hildcaa_trad = identificar_eventos(
        dados,
        max_gap_hours=2.0,
        min_dur_days=2.0,
        peak_ae_min=1000.0,
        symh_thresh=-50.0
    )
    imprimir_tabela_eventos(
        eventos_hildcaa_trad,
        "CRITÉRIO TRADICIONAL (HILDCAA - Tsurutani & Gonzalez, 1987) [Janela de Calmaria de AE até 2h]"
    )
    csv_hildcaa_trad = os.path.join(pasta_destino, "eventos_HILDCAA_tradicional_Ciclo24.csv")
    salvar_tabela_csv(eventos_hildcaa_trad, csv_hildcaa_trad)


if __name__ == '__main__':
    main()
