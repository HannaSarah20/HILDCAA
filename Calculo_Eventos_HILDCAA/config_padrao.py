# -*- coding: utf-8 -*-
"""
================================================================================
BLOCO 1: CONFIGURAÇÕES UNIVERSAIS E PADRONIZAÇÃO VISUAL (config_padrao.py)
================================================================================
Este módulo centraliza:
  1. As definições cronológicas de qualquer Ciclo Solar e suas 4 fases canônicas
     (Fase Ascendente, Máximo Solar, Fase Descendente e Mínimo Solar).
  2. Os parâmetros de estilo visual (fontes, cores, espessuras de linha e DPI).
  3. Os limites fixos de variação (escalas Y e X) de todas as grandezas físicas,
     garantindo que todos os gráficos gerados em qualquer ciclo solar possuam
     exatamente a mesma escala para comparação direta lado a lado.
  4. As tabelas de referência de Prestes et al. (2017, Adv. Space Res., 60,
     1850-1865, Tabelas 1 e 2) validadas com o índice Dst horário (WDC-Kyoto)
     para o Ciclo Solar 23 (1998-2007: 124 HILDCAA* e 45 HILDCAA Tradicionais).
================================================================================
"""

import os
import matplotlib as mpl

# ==============================================================================
# 1. PADRONIZAÇÃO GLOBAL DE FONTES E ESTILO MATPLOTLIB
# ==============================================================================
ESTILO_GRAFICO_PADRAO = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'axes.labelweight': 'bold',
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'figure.titlesize': 14,
    'figure.titleweight': 'bold',
    'axes.grid': True,
    'grid.linestyle': ':',
    'grid.alpha': 0.55,
    'savefig.dpi': 300,
}


def aplicar_estilo_padrao():
    """Aplica as configurações visuais padronizadas (fontes, tamanhos, grades) no Matplotlib."""
    mpl.rcParams.update(ESTILO_GRAFICO_PADRAO)


# ==============================================================================
# 2. CORES PADRONIZADAS POR FASE DO CICLO SOLAR E POR CICLO
# ==============================================================================
ORDER_FASES = [
    'Fase Ascendente',
    'Máximo Solar',
    'Fase Descendente',
    'Mínimo Solar',
]

CORES_FASES = {
    'Fase Ascendente':          '#2ca02c',  # Verde padronizado
    'Máximo Solar':             '#d62728',  # Vermelho padronizado
    'Fase Descendente':         '#ff7f0e',  # Laranja padronizado
    'Mínimo Solar':             '#1f77b4',  # Azul padronizado
    'Ciclo Completo':           '#111111',  # Preto/Grafite para curva geral do ciclo
}

CORES_CICLOS = {
    'Ciclo Solar 23': '#1f77b4',  # Azul escuro científico
    'Ciclo Solar 24': '#d62728',  # Vermelho científico
    'Ciclo Solar 25': '#2ca02c',  # Verde científico (pronto para uso futuro)
}


# ==============================================================================
# 3. PARÂMETROS FÍSICOS, CORES E VARIAÇÕES FIXAS (ESCALAS PADRONIZADAS)
# ==============================================================================
# IMPORTANTE: Os limites 'ylim' abaixo são FIXOS para todos os gráficos de todos os
# ciclos solares, garantindo que a variação visual seja 100% comparável entre
# diferentes fases e diferentes ciclos solares.
PARAMETROS_FISICOS_PADRAO = {
    # Coluna Esquerda (5 parâmetros de plasma e magnitude do campo)
    'Vsw': {
        'rotulo': 'Velocidade $V_{sw}$ [km/s]',
        'unidade': 'km/s',
        'cor': '#d62728',
        'ylim_sea': (300.0, 750.0),      # Escala fixa para SEA (Quartis + Média)
        'ylim_comp': (320.0, 680.0),     # Escala fixa para Comparativo de Médias
        'ref_padrao': 450.0,
        'coluna_painel': 'esquerda',
        'ordem_linha': 0,
    },
    'Nsw': {
        'rotulo': r'Densidade $N_{sw}$ [cm$^{-3}$]',
        'unidade': 'cm^-3',
        'cor': '#9467bd',
        'ylim_sea': (0.0, 16.0),
        'ylim_comp': (1.0, 12.0),
        'ref_padrao': 5.0,
        'coluna_painel': 'esquerda',
        'ordem_linha': 1,
    },
    'Tsw': {
        'rotulo': r'Temperatura $T_{sw}$ [$10^5$ K]',
        'unidade': 'K',
        'fator_escala': 1e-5,            # Exibe em unidades de 10^5 K para leitura limpa
        'cor': '#e377c2',
        'ylim_sea': (0.0, 3.5),          # 0 a 3.5 x 10^5 K
        'ylim_comp': (0.2, 2.8),
        'ref_padrao': 1.1,
        'coluna_painel': 'esquerda',
        'ordem_linha': 2,
    },
    'Psw': {
        'rotulo': 'Pressão $P_{sw}$ [nPa]',
        'unidade': 'nPa',
        'cor': '#8c564b',
        'ylim_sea': (0.0, 6.5),
        'ylim_comp': (0.5, 5.0),
        'ref_padrao': 2.0,
        'coluna_painel': 'esquerda',
        'ordem_linha': 3,
    },
    'Bo': {
        'rotulo': 'Magnitude $B_0$ [nT]',
        'unidade': 'nT',
        'cor': '#2ca02c',
        'ylim_sea': (2.0, 14.0),
        'ylim_comp': (3.0, 11.0),
        'ref_padrao': 5.5,
        'coluna_painel': 'esquerda',
        'ordem_linha': 4,
    },
    # Coluna Direita (Componentes do IMF e Índices Geomagnéticos)
    'Bx_GSM': {
        'rotulo': 'IMF $B_x$ GSM [nT]',
        'unidade': 'nT',
        'cor': '#17becf',
        'ylim_sea': (-7.5, 7.5),
        'ylim_comp': (-5.0, 5.0),
        'ref_padrao': 0.0,
        'coluna_painel': 'direita',
        'ordem_linha': 0,
    },
    'By_GSM': {
        'rotulo': 'IMF $B_y$ GSM [nT]',
        'unidade': 'nT',
        'cor': '#bcbd22',
        'ylim_sea': (-7.5, 7.5),
        'ylim_comp': (-5.0, 5.0),
        'ref_padrao': 0.0,
        'coluna_painel': 'direita',
        'ordem_linha': 1,
    },
    'Bz_GSM': {
        'rotulo': 'IMF $B_z$ GSM [nT]',
        'unidade': 'nT',
        'cor': '#1f77b4',
        'ylim_sea': (-6.5, 6.5),
        'ylim_comp': (-3.5, 3.5),
        'ref_padrao': 0.0,
        'coluna_painel': 'direita',
        'ordem_linha': 2,
    },
    'SymH': {
        'rotulo': 'Índice Sym-H / Dst [nT]',
        'unidade': 'nT',
        'cor': '#7f7f7f',
        'ylim_sea': (-48.0, 18.0),
        'ylim_comp': (-40.0, 10.0),
        'ref_padrao': 0.0,
        'coluna_painel': 'direita',
        'ordem_linha': 3,
    },
    'AE': {
        'rotulo': 'Índice AE [nT]',
        'unidade': 'nT',
        'cor': '#ff7f0e',
        'ylim_sea': (0.0, 700.0),
        'ylim_comp': (50.0, 550.0),
        'ref_padrao': 200.0,
        'coluna_painel': 'direita',
        'ordem_linha': 4,
    },
}

# Limites horizontais padronizados para a Superposição de Época [-2.0 a +2.0 dias]
XLIM_SEA_DIAS = (-2.0, 2.0)
XTICKS_SEA_DIAS = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]


# ==============================================================================
# 4. INTERVALOS VALIDADOS COM DST HORÁRIO (WDC-KYOTO) — PRESTES ET AL. (2017)
# ==============================================================================
# No Ciclo Solar 23 (1998–2007), Prestes et al. (2017, Adv. Space Res., 60,
# 1850–1865) aplicaram o fluxograma da Figura 2 usando o índice AE (1 min) na
# Etapa 1 e o índice Dst horário oficial do WDC-Kyoto (1h) na Etapa 2 (remoção
# da fase principal de tempestades magnéticas com Dst <= -50 nT).
# Como os arquivos locais do Ciclo 23 contêm apenas o Sym-H de 1 minuto (que
# apresenta pequenas diferenças de ~3 a 8 nT em relação ao Dst horário de Kyoto
# em eventos limítrofes), preservamos abaixo os intervalos validados das
# Tabelas 1 (45 HILDCAA) e 2 (124 HILDCAA*) de Prestes et al. (2017).
CATALOGO_CANONICO_C23_STAR = [
    # 1998 (5 eventos) — Fase Ascendente
    ('1998-04-24 11:59:00', '1998-04-26 13:00:00'),
    ('1998-05-10 05:32:00', '1998-05-13 02:24:00'),
    ('1998-06-20 03:16:00', '1998-06-23 08:50:00'),
    ('1998-07-03 19:59:00', '1998-07-06 17:20:00'),
    ('1998-07-22 20:56:00', '1998-07-25 17:36:00'),
    # 1999 (10 eventos) — Fase Ascendente
    ('1999-02-03 20:58:00', '1999-02-06 00:46:00'),
    ('1999-03-03 14:43:00', '1999-03-08 02:48:00'),
    ('1999-03-29 14:59:00', '1999-04-01 06:58:00'),
    ('1999-04-29 07:47:00', '1999-05-03 19:35:00'),
    ('1999-07-06 15:09:00', '1999-07-09 05:09:00'),
    ('1999-07-30 10:15:00', '1999-08-02 18:10:00'),
    ('1999-08-16 06:39:00', '1999-08-19 22:25:00'),
    ('1999-08-29 14:15:00', '1999-09-04 23:25:00'),
    ('1999-09-30 09:59:00', '1999-10-02 16:28:00'),
    ('1999-12-03 07:58:00', '1999-12-09 23:23:00'),
    # 2000 (10 eventos) — Máximo Solar
    ('2000-01-01 04:00:00', '2000-01-03 20:46:00'),
    ('2000-01-04 05:46:00', '2000-01-07 21:18:00'),
    ('2000-01-27 18:06:00', '2000-01-31 23:01:00'),
    ('2000-02-05 15:53:00', '2000-02-08 22:16:00'),
    ('2000-02-24 02:42:00', '2000-02-27 21:37:00'),
    ('2000-04-01 12:40:00', '2000-04-03 16:45:00'),
    ('2000-07-09 18:39:00', '2000-07-12 05:20:00'),
    ('2000-07-30 11:11:00', '2000-08-02 12:42:00'),
    ('2000-08-30 20:39:00', '2000-09-01 23:59:00'),
    ('2000-09-06 15:02:00', '2000-09-09 00:18:00'),
    # 2001 (7 eventos) — Máximo Solar
    ('2001-05-10 10:59:00', '2001-05-14 08:47:00'),
    ('2001-06-09 04:00:00', '2001-06-11 05:49:00'),
    ('2001-07-15 06:19:00', '2001-07-18 08:57:00'),
    ('2001-07-21 23:40:00', '2001-07-26 13:56:00'),
    ('2001-08-12 15:41:00', '2001-08-15 09:18:00'),
    ('2001-09-02 11:29:00', '2001-09-05 03:32:00'),
    ('2001-11-17 00:22:00', '2001-11-20 08:10:00'),
    # 2002 (8 eventos) — Máximo Solar
    ('2002-01-11 08:59:00', '2002-01-14 23:11:00'),
    ('2002-03-05 00:41:00', '2002-03-07 01:05:00'),
    ('2002-06-08 12:06:00', '2002-06-12 05:25:00'),
    ('2002-07-04 21:08:00', '2002-07-07 17:51:00'),
    ('2002-07-22 01:35:00', '2002-07-24 11:58:00'),
    ('2002-07-24 18:49:00', '2002-07-28 06:12:00'),
    ('2002-08-11 10:27:00', '2002-08-16 17:19:00'),
    ('2002-11-27 11:59:00', '2002-12-03 05:20:00'),
    # 2003 (26 eventos) — Fase Descendente
    ('2003-01-19 05:46:00', '2003-01-23 05:38:00'),
    ('2003-01-23 09:44:00', '2003-01-27 02:19:00'),
    ('2003-02-06 05:22:00', '2003-02-11 18:12:00'),
    ('2003-02-16 05:24:00', '2003-02-21 11:10:00'),
    ('2003-03-04 09:59:00', '2003-03-07 23:34:00'),
    ('2003-03-14 03:01:00', '2003-03-16 17:16:00'),
    ('2003-04-15 19:10:00', '2003-04-17 21:06:00'),
    ('2003-04-20 15:45:00', '2003-04-24 12:22:00'),
    ('2003-04-25 22:59:00', '2003-04-28 14:31:00'),
    ('2003-05-01 08:59:00', '2003-05-04 14:35:00'),
    ('2003-05-05 08:50:00', '2003-05-09 07:59:00'),
    ('2003-05-10 19:59:00', '2003-05-16 14:23:00'),
    ('2003-05-22 08:59:00', '2003-05-29 11:27:00'),
    ('2003-06-02 13:59:00', '2003-06-12 18:25:00'),
    ('2003-06-13 16:55:00', '2003-06-16 05:59:00'),
    ('2003-06-24 14:59:00', '2003-07-06 17:28:00'),
    ('2003-07-12 19:59:00', '2003-07-15 12:10:00'),
    ('2003-07-18 02:47:00', '2003-07-23 19:26:00'),
    ('2003-07-29 23:59:00', '2003-08-04 10:46:00'),
    ('2003-08-07 21:59:00', '2003-08-14 11:09:00'),
    ('2003-08-23 14:59:00', '2003-08-25 18:19:00'),
    ('2003-09-09 05:31:00', '2003-09-13 18:19:00'),
    ('2003-09-19 07:59:00', '2003-09-22 20:02:00'),
    ('2003-11-01 06:59:00', '2003-11-04 06:16:00'),
    ('2003-11-14 06:59:00', '2003-11-19 18:46:00'),
    ('2003-12-10 19:59:00', '2003-12-17 06:36:00'),
    # 2004 (16 eventos) — Fase Descendente
    ('2004-01-01 04:00:00', '2004-01-06 11:11:00'),
    ('2004-01-09 04:41:00', '2004-01-12 06:38:00'),
    ('2004-01-15 17:59:00', '2004-01-22 00:59:00'),
    ('2004-01-29 03:20:00', '2004-02-04 20:51:00'),
    ('2004-02-11 23:59:00', '2004-02-16 00:52:00'),
    ('2004-02-28 05:24:00', '2004-03-04 01:02:00'),
    ('2004-03-12 03:37:00', '2004-03-16 20:28:00'),
    ('2004-03-26 11:12:00', '2004-03-29 01:41:00'),
    ('2004-04-06 07:59:00', '2004-04-09 10:06:00'),
    ('2004-04-30 03:32:00', '2004-05-03 19:45:00'),
    ('2004-05-04 12:34:00', '2004-05-06 16:40:00'),
    ('2004-05-19 11:46:00', '2004-05-22 06:24:00'),
    ('2004-05-29 01:57:00', '2004-06-03 20:01:00'),
    ('2004-09-14 19:21:00', '2004-09-18 13:57:00'),
    ('2004-10-12 21:56:00', '2004-10-15 21:14:00'),
    ('2004-12-27 17:04:00', '2004-12-30 22:01:00'),
    # 2005 (17 eventos) — Fase Descendente
    ('2005-01-02 10:59:00', '2005-01-06 00:00:00'),
    ('2005-01-29 03:07:00', '2005-02-01 05:00:00'),
    ('2005-02-07 21:59:00', '2005-02-12 05:24:00'),
    ('2005-03-07 01:59:00', '2005-03-10 18:02:00'),
    ('2005-04-12 06:59:00', '2005-04-16 06:16:00'),
    ('2005-05-01 09:20:00', '2005-05-04 20:51:00'),
    ('2005-06-04 12:51:00', '2005-06-08 02:29:00'),
    ('2005-07-17 01:28:00', '2005-07-19 10:25:00'),
    ('2005-07-20 07:37:00', '2005-07-23 11:32:00'),
    ('2005-07-27 16:06:00', '2005-07-30 22:32:00'),
    ('2005-08-03 13:34:00', '2005-08-08 18:17:00'),
    ('2005-11-02 22:18:00', '2005-11-06 23:25:00'),
    ('2005-11-11 23:03:00', '2005-11-14 14:43:00'),
    ('2005-11-29 16:28:00', '2005-12-03 18:19:00'),
    ('2005-12-10 04:01:00', '2005-12-12 22:01:00'),
    ('2005-12-19 15:52:00', '2005-12-22 02:32:00'),
    ('2005-12-27 11:39:00', '2005-12-30 15:23:00'),
    # 2006 (11 eventos) — Fase Descendente
    ('2006-02-20 06:52:00', '2006-02-22 20:32:00'),
    ('2006-03-18 02:51:00', '2006-03-22 09:20:00'),
    ('2006-06-06 02:18:00', '2006-06-11 17:46:00'),
    ('2006-06-14 21:47:00', '2006-06-17 19:05:00'),
    ('2006-07-04 10:39:00', '2006-07-06 12:07:00'),
    ('2006-08-20 14:59:00', '2006-08-22 19:20:00'),
    ('2006-10-14 01:59:00', '2006-10-16 23:06:00'),
    ('2006-10-28 04:59:00', '2006-10-30 16:27:00'),
    ('2006-11-10 07:59:00', '2006-11-12 14:12:00'),
    ('2006-11-23 06:31:00', '2006-11-27 20:25:00'),
    ('2006-12-06 15:59:00', '2006-12-09 04:27:00'),
    # 2007 (14 eventos) — Mínimo Solar
    ('2007-01-01 23:03:00', '2007-01-04 18:26:00'),
    ('2007-01-16 09:39:00', '2007-01-20 01:58:00'),
    ('2007-01-29 14:02:00', '2007-02-01 00:49:00'),
    ('2007-02-27 08:45:00', '2007-03-01 17:07:00'),
    ('2007-03-12 11:23:00', '2007-03-14 16:59:00'),
    ('2007-04-01 08:59:00', '2007-04-03 11:15:00'),
    ('2007-04-27 09:48:00', '2007-04-30 16:59:00'),
    ('2007-05-23 14:59:00', '2007-05-27 20:18:00'),
    ('2007-08-10 07:39:00', '2007-08-12 12:19:00'),
    ('2007-09-01 16:31:00', '2007-09-03 17:10:00'),
    ('2007-09-05 00:21:00', '2007-09-07 04:43:00'),
    ('2007-09-27 15:50:00', '2007-09-30 11:51:00'),
    ('2007-11-24 07:30:00', '2007-11-26 11:17:00'),
    ('2007-12-17 05:44:00', '2007-12-19 14:03:00'),
]

CATALOGO_CANONICO_C23_TRAD = [
    # 1998 (1 evento) — Fase Ascendente
    ('1998-07-22 20:56:00', '1998-07-25 12:32:00'),
    # 1999 (4 eventos) — Fase Ascendente
    ('1999-03-30 04:31:00', '1999-04-01 06:58:00'),
    ('1999-04-29 07:47:00', '1999-05-03 19:35:00'),
    ('1999-08-31 13:29:00', '1999-09-02 22:11:00'),
    ('1999-12-03 07:58:00', '1999-12-06 01:59:00'),
    # 2000 (4 eventos) — Máximo Solar
    ('2000-01-01 04:00:00', '2000-01-03 04:04:00'),
    ('2000-01-27 18:06:00', '2000-01-31 03:02:00'),
    ('2000-02-05 15:53:00', '2000-02-08 05:26:00'),
    ('2000-02-24 02:42:00', '2000-02-26 02:53:00'),
    # 2001 (2 eventos) — Máximo Solar
    ('2001-05-10 10:59:00', '2001-05-14 08:47:00'),
    ('2001-07-15 06:19:00', '2001-07-17 06:50:00'),
    # 2002 (1 evento) — Máximo Solar
    ('2002-07-22 01:35:00', '2002-07-24 02:20:00'),
    # 2003 (12 eventos) — Fase Descendente
    ('2003-03-04 09:59:00', '2003-03-07 15:44:00'),
    ('2003-04-25 22:59:00', '2003-04-28 11:05:00'),
    ('2003-05-10 19:59:00', '2003-05-13 02:14:00'),
    ('2003-05-13 04:31:00', '2003-05-16 03:50:00'),
    ('2003-05-22 08:59:00', '2003-05-25 12:03:00'),
    ('2003-05-26 18:47:00', '2003-05-29 11:27:00'),
    ('2003-06-05 21:56:00', '2003-06-10 00:56:00'),
    ('2003-06-26 21:14:00', '2003-06-30 22:16:00'),
    ('2003-07-03 08:47:00', '2003-07-06 06:00:00'),
    ('2003-07-29 23:59:00', '2003-08-03 14:05:00'),
    ('2003-11-14 06:59:00', '2003-11-19 18:46:00'),
    ('2003-12-10 19:59:00', '2003-12-16 04:02:00'),
    # 2004 (6 eventos) — Fase Descendente
    ('2004-01-02 08:24:00', '2004-01-06 11:11:00'),
    ('2004-01-15 17:59:00', '2004-01-18 08:25:00'),
    ('2004-02-12 01:35:00', '2004-02-15 11:36:00'),
    ('2004-09-15 19:49:00', '2004-09-18 05:39:00'),
    ('2004-10-12 21:56:00', '2004-10-15 00:10:00'),
    ('2004-12-27 17:04:00', '2004-12-29 18:10:00'),
    # 2005 (6 eventos) — Fase Descendente
    ('2005-01-02 10:59:00', '2005-01-05 20:13:00'),
    ('2005-02-07 21:59:00', '2005-02-10 22:42:00'),
    ('2005-03-07 01:59:00', '2005-03-10 18:02:00'),
    ('2005-04-12 06:59:00', '2005-04-14 17:06:00'),
    ('2005-07-27 16:06:00', '2005-07-30 09:35:00'),
    ('2005-08-05 22:19:00', '2005-08-07 22:54:00'),
    # 2006 (3 eventos) — Fase Descendente
    ('2006-03-18 05:25:00', '2006-03-20 11:19:00'),
    ('2006-06-06 06:02:00', '2006-06-09 16:05:00'),
    ('2006-12-06 15:59:00', '2006-12-08 21:49:00'),
    # 2007 (6 eventos) — Mínimo Solar
    ('2007-01-29 14:02:00', '2007-01-31 14:14:00'),
    ('2007-02-27 15:31:00', '2007-03-01 17:07:00'),
    ('2007-04-01 08:59:00', '2007-04-03 11:15:00'),
    ('2007-04-27 09:48:00', '2007-04-30 11:50:00'),
    ('2007-05-23 17:54:00', '2007-05-25 21:10:00'),
    ('2007-09-01 16:31:00', '2007-09-03 17:10:00'),
]


# ==============================================================================
# 5. CONFIGURAÇÃO REUTILIZÁVEL DE CICLOS SOLARES (QUALQUER CICLO)
# ==============================================================================
def obter_configuracoes_ciclos(diretorio_raiz_projeto):
    """
    Retorna o dicionário de configuração para todos os Ciclos Solares disponíveis.
    Para adicionar um novo ciclo no futuro (ex: Ciclo Solar 25), basta incluir um
    novo bloco neste dicionário com os anos correspondentes a cada fase!
    """
    return {
        'Ciclo Solar 23': {
            'id_curto': 'Ciclo23',
            'nome_exibicao': 'Ciclo Solar 23 (1998–2007)',
            # Carrega 1996 a 2008 para garantir janela de background [-2d, +2d] na SEA
            'anos_dados': list(range(1996, 2009)),
            # Anos efetivos de detecção de eventos (Prestes et al., 2017: 1998 a 2007)
            'anos_eventos': list(range(1998, 2008)),
            'pastas_dados': [
                diretorio_raiz_projeto,
                os.path.join(diretorio_raiz_projeto, 'SEA_Code'),
            ],
            # Classificação canônica de anos por Fase do Ciclo Solar 23 (Prestes et al., 2017)
            'fases_por_ano': {
                'Fase Ascendente':  [1998, 1999],
                'Máximo Solar':     [2000, 2001, 2002],
                'Fase Descendente': [2003, 2004, 2005, 2006],
                'Mínimo Solar':     [2007],
            },
            # Intervalos validados com Dst horário WDC-Kyoto (Tabelas 1 e 2 de Prestes et al., 2017)
            'catalogo_canonico_star': CATALOGO_CANONICO_C23_STAR,
            'catalogo_canonico_trad': CATALOGO_CANONICO_C23_TRAD,
            'data_inicio': '1996-05-01 00:00:00',
            'data_fim':    '2008-12-31 23:59:00',
        },
        'Ciclo Solar 24': {
            'id_curto': 'Ciclo24',
            'nome_exibicao': 'Ciclo Solar 24 (2008–2019)',
            'anos_dados': list(range(2008, 2020)),
            'anos_eventos': list(range(2008, 2020)),
            'pastas_dados': [
                os.path.join(diretorio_raiz_projeto, 'Ciclo solar 24'),
                diretorio_raiz_projeto,
            ],
            # Classificação canônica de anos por Fase do Ciclo Solar 24
            'fases_por_ano': {
                'Fase Ascendente':  [2010, 2011],
                'Máximo Solar':     [2012, 2013, 2014],
                'Fase Descendente': [2015, 2016, 2017],
                'Mínimo Solar':     [2008, 2009, 2018, 2019],
            },
            'data_inicio': '2008-09-22 00:00:00',
            'data_fim':    '2019-12-31 23:59:00',
        },
    }
