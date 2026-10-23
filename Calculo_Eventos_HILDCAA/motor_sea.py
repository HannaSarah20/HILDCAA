# -*- coding: utf-8 -*-
"""
================================================================================
BLOCO 4: INTEGRAÇÃO COM O MÓDULO SEA_NORM (motor_sea.py)
================================================================================
Este módulo recebe a lista de eventos calculada pelo 'detector_hildcaa.py' e
conversa diretamente com a função 'sean' do módulo 'sea_norm.py', executando
a Análise de Sobreposição de Época (SEA) agrupada pelas 4 Fases do Ciclo Solar
e também para o Ciclo Solar Completo.

Metodologia do Intervalo Seguro [-2, +2] Dias:
  - t0 = t1 - 2 dias (-48h): Calmaria pré-evento
  - t1 = Início exato do evento HILDCAA* (Época Zero = 0.0)
  - t2 = t1 + 2 dias (+48h): Atividade HILDCAA* garantida (todos os eventos têm >= 48h)
  - Resolução de 1 hora (48 bins antes + 48 bins depois -> x_dimensions=[49, 49])
================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
from config_padrao import ORDER_FASES

# Compatibilidade retroativa NumPy >= 1.24
if not hasattr(np, 'int'):
    np.int = int
if not hasattr(np, 'float'):
    np.float = float

# Localiza e importa sea_norm.py automaticamente
_dir_atual = os.path.dirname(os.path.abspath(__file__))
_caminhos_sea = [
    _dir_atual,
    os.path.join(_dir_atual, '..', 'SEA_Code', 'sea_norm'),
    os.path.join(_dir_atual, '..', 'SEA_Code'),
    os.path.join(_dir_atual, '..', 'Ciclo solar 24'),
]
for _p in _caminhos_sea:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

import sea_norm


def construir_eixo_tempo_dias(n_bins_por_fase=48):
    """
    Constrói o vetor de tempo físico calibrado em Dias [-2.0 a +2.0 dias]
    para os 96 bins (48 bins pré-evento e 48 bins pós-evento).
    """
    dt_dias = 2.0 / n_bins_por_fase
    x_p1 = np.linspace(-2.0 + dt_dias / 2.0, -dt_dias / 2.0, n_bins_por_fase)
    x_p2 = np.linspace(dt_dias / 2.0, 2.0 - dt_dias / 2.0, n_bins_por_fase)
    return np.concatenate([x_p1, x_p2])


def executar_sea_por_ciclo(dados, df_eventos, nome_ciclo, usar_janela_segura=True, n_bins_fase=48):
    """
    Agrupa os eventos calculados pelas 4 Fases do Ciclo Solar (+ Ciclo Completo)
    e executa sea_norm.sean() para cada grupo.

    Retorna um dicionário:
      resultados_sea[fase] = {
          'seadat': DataFrame retornado pelo sea_norm (indexado em dias de -2 a +2),
          'meta': metadados do sea_norm,
          'qtd_eventos': int,
          'x_dias': array de tempo em dias [-2.0 a +2.0]
      }
    """
    resultados_sea = {}
    if len(df_eventos) == 0:
        print(f"[MOTOR SEA] Nenhum evento disponível para {nome_ciclo}.")
        return resultados_sea

    x_dims = [n_bins_fase + 1, n_bins_fase + 1]
    x_dias = construir_eixo_tempo_dias(n_bins_fase)

    # Monta os grupos: 4 Fases + Ciclo Completo
    grupos = {}
    for fase in ORDER_FASES:
        sub = df_eventos[df_eventos['Fase_Ciclo'] == fase]
        grupos[fase] = sub
    grupos['Ciclo Completo'] = df_eventos

    print(f"\n[MOTOR SEA] Iniciando Superposição de Época para {nome_ciclo}...")
    for nome_grupo, sub_df in grupos.items():
        qtd = len(sub_df)
        if qtd == 0:
            print(f"  -> [{nome_grupo}]: 0 eventos (pulando SEA)")
            continue

        serie_t1 = pd.Series(pd.to_datetime(sub_df['t1_Inicio'].values))
        serie_t0 = serie_t1 - pd.Timedelta(days=2)
        if usar_janela_segura:
            serie_t2 = serie_t1 + pd.Timedelta(days=2)
        else:
            serie_t2 = pd.Series(pd.to_datetime(sub_df['t2_Termino'].values))

        eventos_sea = [serie_t0, serie_t1, serie_t2]

        print(f"  -> Executando sea_norm.sean para [{nome_grupo}] ({qtd} eventos)...")
        seadat, meta = sea_norm.sean(
            data=dados,
            events=eventos_sea,
            x_dimensions=x_dims
        )

        # Adiciona coluna explícita de Tempo em Dias e Tempo em Horas
        seadat = seadat.copy()
        if len(seadat) == len(x_dias):
            seadat['Tempo_Dias'] = np.round(x_dias, 4)
            seadat['Tempo_Horas'] = np.round(x_dias * 24.0, 2)

        resultados_sea[nome_grupo] = {
            'seadat': seadat,
            'meta': meta,
            'qtd_eventos': qtd,
            'x_dias': x_dias if len(seadat) == len(x_dias) else seadat.index.values,
        }

    return resultados_sea
