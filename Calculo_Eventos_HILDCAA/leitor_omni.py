# -*- coding: utf-8 -*-
"""
================================================================================
BLOCO 2: LEITOR UNIVERSAL DE DADOS OMNIWEB (leitor_omni.py)
================================================================================
Este módulo carrega os arquivos 'dadosYYYY.txt' de qualquer Ciclo Solar:
  - Detecta automaticamente a estrutura de colunas do arquivo OMNIWeb (seja 17
    colunas como no Ciclo Solar 23, 18 colunas com B0 explícito como no Ciclo
    Solar 24, ou 12 colunas).
  - Constrói o índice temporal (DatetimeIndex) de forma vetorizada e rápida.
  - Trata rigorosamente todos os valores ausentes (fill values da NASA/OMNIWeb).
  - Padroniza os nomes das 10 variáveis físicas:
    ['Vsw', 'Nsw', 'Tsw', 'Psw', 'Bo', 'Bx_GSM', 'By_GSM', 'Bz_GSM', 'SymH', 'AE']
================================================================================
"""

import os
import glob
import time
import numpy as np
import pandas as pd


def localizar_arquivos_ciclo(anos_desejados, pastas_busca):
    """
    Procura os arquivos 'dadosYYYY.txt' referentes aos anos solicitados
    respeitando a ordem de prioridade das pastas informadas.
    """
    arquivos_encontrados = {}
    for pasta in pastas_busca:
        if not os.path.isdir(pasta):
            continue
        for ano in anos_desejados:
            nome_arq = f"dados{ano}.txt"
            caminho = os.path.join(pasta, nome_arq)
            if os.path.isfile(caminho) and ano not in arquivos_encontrados:
                arquivos_encontrados[ano] = os.path.abspath(caminho)

    return [arquivos_encontrados[ano] for ano in sorted(arquivos_encontrados.keys())]


def _detectar_esquema_colunas(caminho_arquivo):
    """
    Lê a primeira linha válida do arquivo OMNIWeb para detectar automaticamente
    o número de colunas (17 colunas sem Bo explícito, 18 colunas com Bo na col 4,
    ou 12 colunas).
    """
    with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
        for _ in range(5):
            linha = f.readline().strip()
            if not linha:
                continue
            partes = linha.split()
            # Verifica se a primeira coluna é um ano válido (ex: 1996..2030)
            if partes[0].isdigit() and 1950 <= int(partes[0]) <= 2050:
                return len(partes), 0
        # Se a primeira linha for cabeçalho textual, pula 1 linha
        f.seek(0)
        f.readline()
        segunda = f.readline().strip().split()
        return len(segunda), 1


def carregar_dados_ciclo(config_ciclo):
    """
    Carrega todos os arquivos anuais de um Ciclo Solar configurado em 'config_ciclo'
    e retorna um Pandas DataFrame padronizado com as 10 variáveis físicas.
    """
    nome_ciclo = config_ciclo['nome_exibicao']
    anos = config_ciclo['anos_dados']
    pastas = config_ciclo['pastas_dados']

    arquivos = localizar_arquivos_ciclo(anos, pastas)
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo 'dados*.txt' encontrado para {nome_ciclo} nas pastas: {pastas}"
        )

    print(f"\n[LEITOR OMNI] Carregando {len(arquivos)} arquivos para {nome_ciclo}...")
    t0 = time.time()
    dfs = []

    for caminho in arquivos:
        nome_arq = os.path.basename(caminho)
        n_cols, skip_rows = _detectar_esquema_colunas(caminho)

        if n_cols == 18:
            # Esquema de 18 colunas (ex: Ciclo Solar 24):
            # 0:Year, 1:DOY, 2:Hour, 3:Minute, 4:Bo, 5:Bx, 6:By, 7:Bz, 8:Vsw,
            # 9:Vx, 10:Vy, 11:Vz, 12:Nsw, 13:Tsw, 14:Psw, 15:AE, 16:AL, 17:SymH
            colunas = [
                'Year', 'DOY', 'Hour', 'Minute',
                'Bo', 'Bx_GSM', 'By_GSM', 'Bz_GSM',
                'Vsw', 'Vx_GSM', 'Vy_GSM', 'Vz_GSM',
                'Nsw', 'Tsw', 'Psw', 'AE', 'AL', 'SymH'
            ]
            use_cols = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15, 17]
            nomes_lidos = [
                'Year', 'DOY', 'Hour', 'Minute',
                'Bo', 'Bx_GSM', 'By_GSM', 'Bz_GSM',
                'Vsw', 'Nsw', 'Tsw', 'Psw', 'AE', 'SymH'
            ]
        elif n_cols == 17:
            # Esquema de 17 colunas (ex: Ciclo Solar 23):
            # 0:Year, 1:DOY, 2:Hour, 3:Minute, 4:Bx, 5:By, 6:Bz, 7:Vsw,
            # 8:Vx, 9:Vy, 10:Vz, 11:Nsw, 12:Tsw, 13:Psw, 14:AE, 15:AL, 16:SymH
            use_cols = [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 16]
            nomes_lidos = [
                'Year', 'DOY', 'Hour', 'Minute',
                'Bx_GSM', 'By_GSM', 'Bz_GSM',
                'Vsw', 'Nsw', 'Tsw', 'Psw', 'AE', 'SymH'
            ]
        elif n_cols == 12:
            # Esquema compacto de 12 colunas
            use_cols = [0, 1, 2, 3, 4, 5, 6, 7, 8, 11]
            nomes_lidos = [
                'Year', 'DOY', 'Hour', 'Minute',
                'Bo', 'Bz_GSM', 'Vsw', 'Nsw', 'AE', 'SymH'
            ]
        else:
            raise ValueError(f"Formato de arquivo não reconhecido ({n_cols} colunas) em {caminho}")

        dtypes = {col: np.float32 for col in nomes_lidos}
        dtypes.update({'Year': np.int16, 'DOY': np.int16, 'Hour': np.int8, 'Minute': np.int8})

        df_ano = pd.read_csv(
            caminho,
            sep=r'\s+',
            skiprows=skip_rows,
            header=None,
            usecols=use_cols,
            names=nomes_lidos,
            dtype=dtypes
        )

        # Construção vetorizada do DatetimeIndex
        base_ano = pd.to_datetime(df_ano['Year'].values.astype(str) + '-01-01')
        indice_dt = (
            base_ano +
            pd.to_timedelta(df_ano['DOY'] - 1, unit='D') +
            pd.to_timedelta(df_ano['Hour'], unit='h') +
            pd.to_timedelta(df_ano['Minute'], unit='m')
        )
        df_ano.index = indice_dt
        df_ano = df_ano.drop(columns=['Year', 'DOY', 'Hour', 'Minute'])
        dfs.append(df_ano)
        print(f"  -> {nome_arq} carregado ({len(df_ano):,} min | {n_cols} cols)")

    dados = pd.concat(dfs)
    dados.sort_index(inplace=True)
    dados = dados[~dados.index.duplicated(keep='first')]
    dados.index.name = 'Datetime'

    # Filtra intervalo de datas do ciclo se especificado
    if config_ciclo.get('data_inicio'):
        dados = dados[dados.index >= pd.to_datetime(config_ciclo['data_inicio'])]
    if config_ciclo.get('data_fim'):
        dados = dados[dados.index <= pd.to_datetime(config_ciclo['data_fim'])]

    # Tratamento rigoroso de Fill Values do OMNIWeb
    for col in ['Bo', 'Bx_GSM', 'By_GSM', 'Bz_GSM']:
        if col in dados.columns:
            dados[col] = dados[col].replace([9999.99, 999.99, 99.99], np.nan)
            dados.loc[dados[col].abs() > 500.0, col] = np.nan

    if 'Vsw' in dados.columns:
        dados['Vsw'] = dados['Vsw'].replace([99999.9, 9999.9, 9999.99], np.nan)
        dados.loc[(dados['Vsw'] <= 0.0) | (dados['Vsw'] > 3000.0), 'Vsw'] = np.nan

    if 'Nsw' in dados.columns:
        dados['Nsw'] = dados['Nsw'].replace([9999.99, 999.99, 99.99], np.nan)
        dados.loc[(dados['Nsw'] < 0.0) | (dados['Nsw'] > 500.0), 'Nsw'] = np.nan

    if 'Tsw' in dados.columns:
        dados['Tsw'] = dados['Tsw'].replace([9999999.0, 9999999, 999999.0], np.nan)
        dados.loc[(dados['Tsw'] <= 0.0) | (dados['Tsw'] >= 9000000.0), 'Tsw'] = np.nan

    if 'Psw' in dados.columns:
        dados['Psw'] = dados['Psw'].replace([99.99, 999.99, 9999.99], np.nan)
        dados.loc[(dados['Psw'] < 0.0) | (dados['Psw'] >= 99.0), 'Psw'] = np.nan

    if 'AE' in dados.columns:
        dados['AE'] = dados['AE'].replace([99999.0, 9999.0, 99999, 9999], np.nan)
        dados.loc[(dados['AE'] < 0.0) | (dados['AE'] > 8000.0), 'AE'] = np.nan

    if 'SymH' in dados.columns:
        dados['SymH'] = dados['SymH'].replace([99999.0, 9999.0, 99999, 9999], np.nan)
        dados.loc[(dados['SymH'] < -2000.0) | (dados['SymH'] > 1000.0), 'SymH'] = np.nan

    # Calcula Bo caso não exista na tabela original (ex: arquivos de 17 colunas do Ciclo 23)
    if 'Bo' not in dados.columns and {'Bx_GSM', 'By_GSM', 'Bz_GSM'}.issubset(dados.columns):
        dados['Bo'] = np.sqrt(
            dados['Bx_GSM']**2 + dados['By_GSM']**2 + dados['Bz_GSM']**2
        ).astype(np.float32)

    # Garante a ordem padronizada das 10 colunas
    colunas_padrao = ['Vsw', 'Nsw', 'Tsw', 'Psw', 'Bo', 'Bx_GSM', 'By_GSM', 'Bz_GSM', 'SymH', 'AE']
    colunas_presentes = [c for c in colunas_padrao if c in dados.columns]
    dados = dados[colunas_presentes]

    dt_load = time.time() - t0
    mem_mb = dados.memory_usage().sum() / (1024 * 1024)
    print(f"[LEITOR OMNI] {nome_ciclo} pronto em {dt_load:.1f}s | {len(dados):,} min | {mem_mb:.1f} MB RAM")
    print(f"              Período: {dados.index.min()} a {dados.index.max()}")

    return dados
