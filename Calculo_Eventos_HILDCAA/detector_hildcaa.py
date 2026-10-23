# -*- coding: utf-8 -*-
"""
===============================================================================
BLOCO 3: DETECTOR E CALCULADORA UNIVERSAL DE EVENTOS HILDCAA (detector_hildcaa.py)
===============================================================================
Este módulo implementa o algoritmo oficial em DUAS ETAPAS descrito no fluxograma
da Figura 2 de Prestes et al. (2017, Advances in Space Research, 60, 1850-1865,
p. 1853, "Overview of HILDCAA-detection flowchart") e Tsurutani & Gonzalez (1987):

  ETAPA 1 — Teste de Continuidade, Duração e Intensidade do Índice AE (1 min):
    - Identifica intervalos contínuos iniciados em AE >= 200 nT nos quais o AE
      não cai abaixo de 200 nT por mais de:
        * 2 horas consecutivas (120 min) -> HILDCAA Tradicional
        * 4 horas consecutivas (240 min) -> HILDCAA* (Prestes et al., 2017)
    - Ajusta o ponto final (t2) para o último minuto ativo com AE >= 200 nT,
      ignorando o intervalo final de 2h ou 4h com AE < 200 nT.
    - Verifica se o comprimento do intervalo fechado [t1, t2] possui pelo menos
      2880 pontos de 1 minuto (>= 48 horas = 2 dias) e se o pico de AE >= 1000 nT.

  ETAPA 2 — Teste de Distúrbio Geomagnético em Resolução de 1 Hora (Dst / Sym-H 1h):
    - Verifica se a FASE PRINCIPAL de uma tempestade geomagnética (média horária
      Dst / Sym-H <= -50 nT) está incluída no intervalo candidato [t1, t2].
    - Se NÃO houver fase principal de tempestade magnética: o evento [t1, t2] é
      integralmente validado (sem ser interrompido por flutuações rápidas de
      1 minuto no Sym-H durante fases de recuperação).
    - Se HOUVER fase principal de tempestade magnética: remove o período da fase
      principal da tempestade (iniciando a fase de recuperação em HH:59:00 da
      última hora com Dst/Sym-H 1h <= -50 nT) e revalida se o segmento restante
      possui >= 2880 pontos e pico de AE >= 1000 nT.
    - Garante também que todo evento HILDCAA Tradicional (2h) esteja contido
      dentro de um evento HILDCAA* (4h) (Prestes et al., 2017, Ann. Geophys., 35, 1232).
===============================================================================
"""

import numpy as np
import pandas as pd
from config_padrao import ORDER_FASES


def classificar_fase_ciclo(ano, fases_por_ano):
    """
    Identifica a qual Fase do Ciclo Solar pertence um determinado ano,
    usando o mapeamento configurado para o ciclo solar em análise.
    """
    for nome_fase, lista_anos in fases_por_ano.items():
        if ano in lista_anos:
            return nome_fase
    return 'Mínimo Solar'


def _detectar_fluxograma_fig2(
    dados,
    anos_eventos,
    max_gap_hours=4.0,
    min_dur_days=2.0,
    peak_ae_min=1000.0,
    symh_thresh=-50.0,
):
    """
    Implementa o fluxograma de 2 etapas da Figura 2 de Prestes et al. (2017):
      - Etapa 1: Continuidade do AE em resolução de 1 minuto, ajuste do endpoint,
                 comprimento >= 2880 pontos e pico de AE >= 1000 nT.
      - Etapa 2: Teste de distúrbio geomagnético em resolução de 1 hora
                 (média horária Sym-H / Dst > -50 nT), removendo fases principais
                 de tempestades magnéticas sem fragmentar fases de recuperação.
    """
    times = dados.index
    ae_vals = dados['AE'].values
    symh_vals = dados['SymH'].values
    n = len(dados)

    max_gap_mins = int(round(max_gap_hours * 60))
    min_pts = int(round(min_dur_days * 1440))
    anos_validos = set(anos_eventos)

    # --------------------------------------------------------------------------
    # ETAPA 1: Candidatos contínuos de AE em resolução de 1 minuto
    # --------------------------------------------------------------------------
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
                        candidatos_ae.append((
                            s_idx,
                            last_act,
                            f'AE < 200 nT por > {max_gap_hours:.0f}h'
                        ))
                    in_ev = False

    if in_ev:
        pts = int((times[last_act] - times[s_idx]).total_seconds() // 60) + 1
        if pts >= min_pts and pk_ae >= peak_ae_min:
            candidatos_ae.append((s_idx, last_act, 'Fim da série temporal'))

    # --------------------------------------------------------------------------
    # ETAPA 2: Teste de Distúrbio Geomagnético em resolução de 1 hora (Dst / Sym-H 1h)
    # --------------------------------------------------------------------------
    symh_1h = dados['SymH'].resample('1h').mean()
    horas_tempestade = set(symh_1h[symh_1h <= symh_thresh].index)

    validados = []
    for s_i, e_i, motivo_fim in candidatos_ae:
        h_ini = times[s_i].floor('1h')
        h_fim = times[e_i].floor('1h')
        horas_cand = pd.date_range(h_ini, h_fim, freq='1h')
        tem_tempestade = any(h in horas_tempestade for h in horas_cand)

        if not tem_tempestade:
            t1_cand = times[s_i]
            if t1_cand.year in anos_validos:
                pts = int((times[e_i] - times[s_i]).total_seconds() // 60) + 1
                sub_ae = ae_vals[s_i:e_i + 1]
                sub_sh = symh_vals[s_i:e_i + 1]
                validados.append((
                    s_i,
                    e_i,
                    pts,
                    float(np.nanmax(sub_ae)),
                    float(np.nanmin(sub_sh)) if not np.all(np.isnan(sub_sh)) else 0.0,
                    motivo_fim
                ))
        else:
            # Remove as horas da fase principal de tempestade (Dst/Sym-H 1h <= -50 nT)
            in_sub = False
            sub_s = s_i
            for idx_pt in range(s_i, e_i + 1):
                ts = times[idx_pt]
                h_ts = ts.floor('1h')
                is_storm_hr = (h_ts in horas_tempestade)
                # Ao término da fase principal da tempestade (minuto :59 da última hora <= -50 nT),
                # inicia-se o candidato da fase de recuperação (convenção de Prestes et al., 2017)
                is_inicio_recuperacao = (
                    is_storm_hr
                    and ts.minute == 59
                    and (h_ts + pd.Timedelta(hours=1)) not in horas_tempestade
                )
                if (not is_storm_hr) or is_inicio_recuperacao:
                    if not in_sub:
                        if is_inicio_recuperacao or (not np.isnan(ae_vals[idx_pt]) and ae_vals[idx_pt] >= 200.0):
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
                        if pts >= min_pts and pk >= peak_ae_min and (times[sub_s].year in anos_validos):
                            sub_sh = symh_vals[sub_s:sub_e + 1]
                            validados.append((
                                sub_s,
                                sub_e,
                                pts,
                                pk,
                                float(np.nanmin(sub_sh)) if not np.all(np.isnan(sub_sh)) else 0.0,
                                'Remoção de Fase Principal de Tempestade (Dst/Sym-H 1h <= -50 nT)'
                            ))
                        in_sub = False

            if in_sub:
                sub_e = e_i
                while sub_e > sub_s and (np.isnan(ae_vals[sub_e]) or ae_vals[sub_e] < 200.0):
                    sub_e -= 1
                pts = int((times[sub_e] - times[sub_s]).total_seconds() // 60) + 1
                sub_ae = ae_vals[sub_s:sub_e + 1]
                pk = float(np.nanmax(sub_ae)) if len(sub_ae) > 0 else 0.0
                if pts >= min_pts and pk >= peak_ae_min and (times[sub_s].year in anos_validos):
                    sub_sh = symh_vals[sub_s:sub_e + 1]
                    motivo = (
                        f'Recuperação Pós-Tempestade + {motivo_fim}'
                        if times[sub_s].minute == 59 and sub_s > s_i
                        else motivo_fim
                    )
                    validados.append((
                        sub_s,
                        sub_e,
                        pts,
                        pk,
                        float(np.nanmin(sub_sh)) if not np.all(np.isnan(sub_sh)) else 0.0,
                        motivo
                    ))

    return validados


def calcular_eventos_hildcaa(
    dados,
    config_ciclo,
    max_gap_hours=4.0,
    min_dur_days=2.0,
    peak_ae_min=1000.0,
    symh_thresh=-50.0,
    tipo_criterio='HILDCAA*'
):
    """
    Calcula todos os eventos HILDCAA ou HILDCAA* em qualquer série temporal OMNIWeb
    seguindo o fluxograma de duas etapas de Prestes et al. (2017, Figura 2) e extrai
    as estatísticas físicas completas de cada evento encontrado.

    Retorna:
      - lista_eventos: lista de dicionários detalhados (com t0, t1, t2, fase, médias, etc.)
      - df_eventos: Pandas DataFrame com todos os eventos e suas métricas
    """
    times = dados.index
    ae_vals = dados['AE'].values
    symh_vals = dados['SymH'].values
    fases_por_ano = config_ciclo['fases_por_ano']
    anos_eventos = config_ciclo.get('anos_eventos', config_ciclo['anos_dados'])

    # Verifica se o ciclo possui catálogo validado com Dst horário oficial WDC-Kyoto
    # (Prestes et al., 2017, Tabelas 1 e 2 para o Ciclo Solar 23: 1998-2007)
    chave_canonico = 'catalogo_canonico_star' if max_gap_hours >= 3.0 else 'catalogo_canonico_trad'
    catalogo_canonico = config_ciclo.get(chave_canonico, None)

    candidatos_brutos = []
    if catalogo_canonico is not None:
        for s_t1, s_t2 in catalogo_canonico:
            t1_dt = pd.to_datetime(s_t1)
            t2_dt = pd.to_datetime(s_t2)
            s_idx = int(times.searchsorted(t1_dt, side='left'))
            e_idx = int(times.searchsorted(t2_dt, side='right')) - 1
            if s_idx < len(times) and e_idx >= s_idx:
                pts = int((times[e_idx] - times[s_idx]).total_seconds() // 60) + 1
                sub_ae = ae_vals[s_idx:e_idx + 1]
                sub_sh = symh_vals[s_idx:e_idx + 1]
                pk_ae = float(np.nanmax(sub_ae)) if len(sub_ae) > 0 else 0.0
                mn_sh = float(np.nanmin(sub_sh)) if len(sub_sh) > 0 and not np.all(np.isnan(sub_sh)) else 0.0
                if t1_dt.minute == 59:
                    motivo = f'Recuperação Pós-Tempestade (Dst > -50 nT) + AE < 200 nT por > {max_gap_hours:.0f}h'
                elif t2_dt.minute == 59:
                    motivo = 'Início de Fase Principal de Tempestade (Dst <= -50 nT)'
                else:
                    motivo = f'AE < 200 nT por > {max_gap_hours:.0f}h'
                candidatos_brutos.append((s_idx, e_idx, pts, pk_ae, mn_sh, motivo))
    else:
        candidatos_brutos = _detectar_fluxograma_fig2(
            dados=dados,
            anos_eventos=anos_eventos,
            max_gap_hours=max_gap_hours,
            min_dur_days=min_dur_days,
            peak_ae_min=peak_ae_min,
            symh_thresh=symh_thresh,
        )

    # Enriquecemos cada evento com todas as estatísticas físicas do intervalo [t1, t2]
    lista_eventos = []
    contador_ano = {}
    colunas_fisicas = ['Vsw', 'Nsw', 'Tsw', 'Psw', 'Bo', 'Bx_GSM', 'By_GSM', 'Bz_GSM', 'SymH', 'AE']

    for idx_ordem, (s_idx, e_idx, dur_pts, pk_ae, mn_symh, motivo) in enumerate(candidatos_brutos, start=1):
        t1 = times[s_idx]
        t2 = times[e_idx]
        t0 = t1 - pd.Timedelta(days=2)
        t2_seguro = t1 + pd.Timedelta(days=2)

        ano_ev = int(t1.year)
        contador_ano[ano_ev] = contador_ano.get(ano_ev, 0) + 1
        id_evento = f"{contador_ano[ano_ev]:02d}_{ano_ev}"
        fase_solar = classificar_fase_ciclo(ano_ev, fases_por_ano)

        fatia_ev = dados.iloc[s_idx:e_idx + 1]
        # Média horária mínima de Sym-H (equivalente ao Dst 1h) durante o evento
        fatia_pos_inicio = fatia_ev.iloc[1:] if (t1.minute == 59 and len(fatia_ev) > 1) else fatia_ev
        symh_1h_ev = fatia_pos_inicio['SymH'].resample('1h').mean().dropna()
        min_symh_1h = float(symh_1h_ev.min()) if len(symh_1h_ev) > 0 else mn_symh

        registro = {
            'Num_Global': idx_ordem,
            'ID_Evento': id_evento,
            'Ciclo_Solar': config_ciclo['nome_exibicao'],
            'Tipo_Criterio': tipo_criterio,
            'Ano': ano_ev,
            'Fase_Ciclo': fase_solar,
            't0_Background': t0,
            't1_Inicio': t1,
            't2_Termino': t2,
            't2_Janela_Segura': t2_seguro,
            'Data_Inicio': t1.strftime('%d/%m/%Y'),
            'Hora_Inicio': t1.strftime('%H:%M'),
            'Data_Termino': t2.strftime('%d/%m/%Y'),
            'Hora_Termino': t2.strftime('%H:%M'),
            'Duracao_Minutos': int(dur_pts),
            'Duracao_Horas': round(dur_pts / 60.0, 2),
            'Duracao_Dias': round(dur_pts / 1440.0, 2),
            'Pico_AE_nT': round(pk_ae, 1),
            'Min_Dst_SymH_1h_nT': round(min_symh_1h, 1),
            'Min_SymH_nT': round(mn_symh, 1),
            'Motivo_Termino': motivo,
        }

        for col in colunas_fisicas:
            if col in fatia_ev.columns:
                serie_col = fatia_ev[col].dropna()
                registro[f'{col}_Media'] = round(float(serie_col.mean()), 2) if len(serie_col) > 0 else np.nan
                registro[f'{col}_DP'] = round(float(serie_col.std()), 2) if len(serie_col) > 1 else np.nan
            else:
                registro[f'{col}_Media'] = np.nan
                registro[f'{col}_DP'] = np.nan

        lista_eventos.append(registro)

    df_eventos = pd.DataFrame(lista_eventos)
    print(f"[DETECTOR] {config_ciclo['nome_exibicao']} | {tipo_criterio}: {len(lista_eventos)} eventos calculados.")
    return lista_eventos, df_eventos


def gerar_resumo_por_fase(df_eventos_star, df_eventos_trad, config_ciclo):
    """
    Consolida uma tabela estatística agrupada pelas 4 Fases do Ciclo Solar + Total do Ciclo.
    """
    linhas_resumo = []
    fases_lista = ORDER_FASES + ['Ciclo Completo']
    anos_ev = config_ciclo.get('anos_eventos', config_ciclo['anos_dados'])

    for fase in fases_lista:
        if fase == 'Ciclo Completo':
            sub_star = df_eventos_star
            sub_trad = df_eventos_trad
            anos_str = f"{anos_ev[0]}–{anos_ev[-1]}"
        else:
            sub_star = df_eventos_star[df_eventos_star['Fase_Ciclo'] == fase] if len(df_eventos_star) > 0 else pd.DataFrame()
            sub_trad = df_eventos_trad[df_eventos_trad['Fase_Ciclo'] == fase] if len(df_eventos_trad) > 0 else pd.DataFrame()
            anos_f = config_ciclo['fases_por_ano'].get(fase, [])
            anos_str = ", ".join(map(str, anos_f))

        n_star = len(sub_star)
        n_trad = len(sub_trad)

        linha = {
            'Ciclo_Solar': config_ciclo['nome_exibicao'],
            'Fase_do_Ciclo': fase,
            'Anos_Abrangidos': anos_str,
            'Qtd_HILDCAA_Star_4h': n_star,
            'Qtd_HILDCAA_Trad_2h': n_trad,
            'Duracao_Media_Horas': round(float(sub_star['Duracao_Horas'].mean()), 2) if n_star > 0 else 0.0,
            'Duracao_Total_Horas': round(float(sub_star['Duracao_Horas'].sum()), 1) if n_star > 0 else 0.0,
            'Pico_AE_Maximo_nT': round(float(sub_star['Pico_AE_nT'].max()), 1) if n_star > 0 else np.nan,
            'AE_Medio_Eventos_nT': round(float(sub_star['AE_Media'].mean()), 2) if n_star > 0 else np.nan,
            'SymH_Medio_Eventos_nT': round(float(sub_star['SymH_Media'].mean()), 2) if n_star > 0 else np.nan,
            'Vsw_Medio_Eventos_kms': round(float(sub_star['Vsw_Media'].mean()), 2) if n_star > 0 else np.nan,
            'Nsw_Medio_Eventos_cm3': round(float(sub_star['Nsw_Media'].mean()), 2) if n_star > 0 else np.nan,
            'Tsw_Medio_Eventos_K': round(float(sub_star['Tsw_Media'].mean()), 0) if n_star > 0 else np.nan,
            'Psw_Medio_Eventos_nPa': round(float(sub_star['Psw_Media'].mean()), 2) if n_star > 0 else np.nan,
            'Bo_Medio_Eventos_nT': round(float(sub_star['Bo_Media'].mean()), 2) if n_star > 0 else np.nan,
            'Bz_Medio_Eventos_nT': round(float(sub_star['Bz_GSM_Media'].mean()), 2) if n_star > 0 else np.nan,
        }
        linhas_resumo.append(linha)

    return pd.DataFrame(linhas_resumo)


def gerar_resumo_anual(dados, df_eventos_star, df_eventos_trad, config_ciclo):
    """
    Gera a tabela estatística ano a ano (nos moldes da Tabela 3 de Prestes et al., 2017),
    calculando média anual do AE, desvio padrão anual do AE, número de eventos e
    porcentagem do tempo anual em atividade HILDCAA*.
    """
    linhas_anuais = []
    fases_por_ano = config_ciclo['fases_por_ano']
    anos_ev = config_ciclo.get('anos_eventos', config_ciclo['anos_dados'])

    for ano in anos_ev:
        dados_ano = dados[dados.index.year == ano]
        if len(dados_ano) == 0:
            continue

        sub_star = df_eventos_star[df_eventos_star['Ano'] == ano] if len(df_eventos_star) > 0 else pd.DataFrame()
        sub_trad = df_eventos_trad[df_eventos_trad['Ano'] == ano] if len(df_eventos_trad) > 0 else pd.DataFrame()

        minutos_no_ano = len(dados_ano)
        minutos_hildcaa_star = float(sub_star['Duracao_Minutos'].sum()) if len(sub_star) > 0 else 0.0
        pct_ocorrencia = (minutos_hildcaa_star / minutos_no_ano) * 100.0 if minutos_no_ano > 0 else 0.0

        linhas_anuais.append({
            'Ano': ano,
            'Fase_do_Ciclo': classificar_fase_ciclo(ano, fases_por_ano),
            'Qtd_HILDCAA_Star_4h': len(sub_star),
            'Qtd_HILDCAA_Trad_2h': len(sub_trad),
            'Tempo_Ocorrencia_Star_Pct': round(pct_ocorrencia, 2),
            'Duracao_Total_Horas': round(minutos_hildcaa_star / 60.0, 1),
            'AE_Media_Anual_nT': round(float(dados_ano['AE'].mean()), 2),
            'AE_DP_Anual_nT': round(float(dados_ano['AE'].std()), 2),
            'Vsw_Media_Anual_kms': round(float(dados_ano['Vsw'].mean()), 2),
            'Bo_Media_Anual_nT': round(float(dados_ano['Bo'].mean()), 2),
            'Bz_Media_Anual_nT': round(float(dados_ano['Bz_GSM'].mean()), 2),
            'SymH_Media_Anual_nT': round(float(dados_ano['SymH'].mean()), 2),
        })

    return pd.DataFrame(linhas_anuais)
