# -*- coding: utf-8 -*-
"""
================================================================================
BLOCO 6: GERADOR DE GRÁFICOS PADRONIZADOS (gerador_graficos.py)
================================================================================
Este módulo gera todos os gráficos científicos do projeto obedecendo a uma
padronização rigorosa:
  1. Mesmas cores e mesmas fontes (definidas em config_padrao.py).
  2. MESMAS VARIAÇÕES (escalas Y e X fixas) em todos os painéis e entre todos os
     Ciclos Solares, permitindo colocar qualquer gráfico lado a lado e comparar
     visualmente as intensidades sem distorção de escala.
  3. Gera:
     - Painéis SEA 2x5 (10 variáveis) para cada Fase e para o Ciclo Completo.
     - Painel SEA Comparativo das 4 Fases dentro do mesmo Ciclo Solar.
     - Gráfico de Distribuição por Fase e por Ano (padronizado).
     - Painel Comparativo Direto entre Ciclos Solares (ex: Ciclo 23 vs Ciclo 24).
================================================================================
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config_padrao import (
    aplicar_estilo_padrao,
    ORDER_FASES,
    CORES_FASES,
    CORES_CICLOS,
    PARAMETROS_FISICOS_PADRAO,
    XLIM_SEA_DIAS,
    XTICKS_SEA_DIAS,
)


def _ordenar_colunas_painel():
    """Retorna as listas de variáveis da coluna esquerda e direita na ordem 0..4."""
    esq = [
        (k, v) for k, v in PARAMETROS_FISICOS_PADRAO.items()
        if v['coluna_painel'] == 'esquerda'
    ]
    dir_ = [
        (k, v) for k, v in PARAMETROS_FISICOS_PADRAO.items()
        if v['coluna_painel'] == 'direita'
    ]
    esq.sort(key=lambda item: item[1]['ordem_linha'])
    dir_.sort(key=lambda item: item[1]['ordem_linha'])
    return esq, dir_


def gerar_paineis_sea_padronizados_ciclo(config_ciclo, resultados_sea, pasta_graficos):
    """
    Gera os gráficos de Superposição de Época (SEA) padronizados (painel 2x5 com
    mesmas cores, fontes e mesmas variações de eixo Y e X) para cada Fase e para
    o Ciclo Completo, além do comparativo entre fases.
    """
    aplicar_estilo_padrao()
    os.makedirs(pasta_graficos, exist_ok=True)

    nome_ciclo = config_ciclo['nome_exibicao']
    id_curto = config_ciclo['id_curto']
    col_esquerda, col_direita = _ordenar_colunas_painel()
    arquivos_gerados = []

    # --------------------------------------------------------------------------
    # 1. PAINÉIS INDIVIDUAIS 2x5 (Média + Mediana + Quartis 25%-75%) COM ESCALA FIXA
    # --------------------------------------------------------------------------
    for nome_grupo, res in resultados_sea.items():
        seadat = res['seadat']
        qtd_ev = res['qtd_eventos']
        x_dias = res['x_dias']

        fig, axes = plt.subplots(nrows=5, ncols=2, sharex=True, figsize=(14, 15))
        fig.suptitle(
            f"Análise de Sobreposição de Época (SEA Padronizada) — Eventos HILDCAA*\n"
            f"{nome_ciclo} | {nome_grupo} (N = {qtd_ev} eventos)\n",
            fontsize=13,
            fontweight='bold',
            y=0.985
        )

        for row in range(5):
            for col_idx, lista_vars in enumerate([col_esquerda, col_direita]):
                var_nome, cfg_var = lista_vars[row]
                ax = axes[row, col_idx]

                cor = cfg_var['cor']
                rotulo = cfg_var['rotulo']
                ylim_fixo = cfg_var['ylim_sea']
                fator = cfg_var.get('fator_escala', 1.0)
                ref_val = cfg_var['ref_padrao']

                c_mean = f"{var_nome}_mean"
                c_med = f"{var_nome}_median"
                c_low = f"{var_nome}_lowq"
                c_up = f"{var_nome}_upq"

                if c_mean in seadat.columns and c_med in seadat.columns:
                    media = seadat[c_mean].values * fator
                    mediana = seadat[c_med].values * fator
                    q_inf = seadat[c_low].values * fator if c_low in seadat.columns else media
                    q_sup = seadat[c_up].values * fator if c_up in seadat.columns else media

                    ax.fill_between(x_dias, q_inf, q_sup, color=cor, alpha=0.22, label='Quartis (25%–75%)')
                    ax.plot(x_dias, mediana, color='#222222', linestyle='--', linewidth=1.4, label='Mediana')
                    ax.plot(x_dias, media, color=cor, linestyle='-', linewidth=2.1, label='Média')

                # Linhas de referência física e época zero (t1 = 0)
                ax.axhline(ref_val, color='#666666', linestyle=':', linewidth=1.0, alpha=0.8)
                ax.axvline(0.0, color='#d62728', linestyle='--', linewidth=1.5, alpha=0.9)

                # APLICAÇÃO DA MESMA VARIAÇÃO (ESCALA FIXA PADRONIZADA)
                ax.set_ylim(ylim_fixo)
                ax.set_xlim(XLIM_SEA_DIAS)
                ax.set_xticks(XTICKS_SEA_DIAS)
                ax.set_ylabel(rotulo, fontsize=10, fontweight='bold')

                if row == 0:
                    ax.legend(loc='upper right', fontsize=8, framealpha=0.92)
                    y_min, y_max = ylim_fixo
                    y_pos = y_min + 0.86 * (y_max - y_min)
                    ax.text(-1.05, y_pos, 'Calmaria Pré-Evento\n($-2$ a $0$ dias)',
                            ha='center', va='center', fontsize=8, style='italic', color='#1b365d')
                    ax.text(1.05, y_pos, 'HILDCAA* Ativo\n($0$ a $+2$ dias)',
                            ha='center', va='center', fontsize=8, style='italic', color='#800000')

        axes[-1, 0].set_xlabel('Tempo Relativo ao Início [Dias] (Época Zero $t_1 = 0$)', fontsize=10.5, fontweight='bold')
        axes[-1, 1].set_xlabel('Tempo Relativo ao Início [Dias] (Época Zero $t_1 = 0$)', fontsize=10.5, fontweight='bold')

        plt.tight_layout(rect=[0, 0, 1, 0.955])
        sufixo = nome_grupo.replace(' ', '_').replace('á', 'a').replace('í', 'i')
        caminho_fig = os.path.join(pasta_graficos, f"SEA_Padronizado_{id_curto}_{sufixo}.png")
        plt.savefig(caminho_fig, dpi=300, bbox_inches='tight')
        plt.close(fig)
        arquivos_gerados.append(caminho_fig)
        print(f"  [GRÁFICO SALVO] {caminho_fig}")

    # --------------------------------------------------------------------------
    # 2. PAINEL COMPARATIVO DAS 4 FASES DENTRO DO MESMO CICLO SOLAR
    # --------------------------------------------------------------------------
    fig_comp, axes_comp = plt.subplots(nrows=5, ncols=2, sharex=True, figsize=(15, 16))
    fig_comp.suptitle(
        f"Comparativo Padronizado entre as 4 Fases — {nome_ciclo}\n"
        f"Curvas Médias da Superposição de Época (SEA) na Mesma Escala de Variação",
        fontsize=13.5,
        fontweight='bold',
        y=0.985
    )

    for row in range(5):
        for col_idx, lista_vars in enumerate([col_esquerda, col_direita]):
            var_nome, cfg_var = lista_vars[row]
            ax = axes_comp[row, col_idx]

            rotulo = cfg_var['rotulo']
            ylim_comp = cfg_var['ylim_comp']
            fator = cfg_var.get('fator_escala', 1.0)
            ref_val = cfg_var['ref_padrao']
            c_mean = f"{var_nome}_mean"

            for fase in ORDER_FASES:
                if fase in resultados_sea:
                    sdat = resultados_sea[fase]['seadat']
                    x_d = resultados_sea[fase]['x_dias']
                    qtd_f = resultados_sea[fase]['qtd_eventos']
                    if c_mean in sdat.columns:
                        ax.plot(
                            x_d,
                            sdat[c_mean].values * fator,
                            label=f"{fase} (N={qtd_f})",
                            color=CORES_FASES[fase],
                            linewidth=2.0
                        )

            ax.axhline(ref_val, color='#666666', linestyle=':', linewidth=1.0, alpha=0.7)
            ax.axvline(0.0, color='#d62728', linestyle='--', linewidth=1.4, alpha=0.9)
            ax.set_ylim(ylim_comp)
            ax.set_xlim(XLIM_SEA_DIAS)
            ax.set_xticks(XTICKS_SEA_DIAS)
            ax.set_ylabel(rotulo, fontsize=10, fontweight='bold')

            if row == 0:
                ax.legend(loc='upper right', fontsize=8, framealpha=0.92)

    axes_comp[-1, 0].set_xlabel('Tempo Relativo ao Início [Dias] (Época Zero $t_1 = 0$)', fontsize=10.5, fontweight='bold')
    axes_comp[-1, 1].set_xlabel('Tempo Relativo ao Início [Dias] (Época Zero $t_1 = 0$)', fontsize=10.5, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    caminho_comp = os.path.join(pasta_graficos, f"SEA_Comparativo_Fases_{id_curto}.png")
    plt.savefig(caminho_comp, dpi=300, bbox_inches='tight')
    plt.close(fig_comp)
    arquivos_gerados.append(caminho_comp)
    print(f"  [GRÁFICO SALVO] {caminho_comp}")

    return arquivos_gerados


def gerar_grafico_distribuicao_ciclo(config_ciclo, df_resumo_fases, df_resumo_anual, pasta_graficos):
    """
    Gera um painel estatístico padronizado (com escalas fixas) mostrando:
      - Esquerda: Quantidade de eventos HILDCAA* (4h) e HILDCAA Tradicional (2h) por Fase do Ciclo.
      - Direita: Evolução anual do número de eventos e da média anual do índice AE.
    """
    aplicar_estilo_padrao()
    os.makedirs(pasta_graficos, exist_ok=True)
    id_curto = config_ciclo['id_curto']
    nome_ciclo = config_ciclo['nome_exibicao']

    fig, (ax_fases, ax_anos) = plt.subplots(nrows=1, ncols=2, figsize=(14, 5.5))
    fig.suptitle(
        f"Distribuição Estatística Padronizada de Eventos HILDCAA* e HILDCAA — {nome_ciclo}",
        fontsize=13,
        fontweight='bold',
        y=1.02
    )

    # Subplot 1: Eventos por Fase (Escala Y fixa em 0..80 para comparação direta entre ciclos)
    df_f = df_resumo_fases[df_resumo_fases['Fase_do_Ciclo'].isin(ORDER_FASES)].copy()
    x_pos = np.arange(len(df_f))
    larg = 0.36

    b1 = ax_fases.bar(
        x_pos - larg / 2,
        df_f['Qtd_HILDCAA_Star_4h'],
        width=larg,
        color='#ff7f0e',
        edgecolor='black',
        label='HILDCAA* (Tolerância 4h)'
    )
    b2 = ax_fases.bar(
        x_pos + larg / 2,
        df_f['Qtd_HILDCAA_Trad_2h'],
        width=larg,
        color='#1f77b4',
        edgecolor='black',
        label='HILDCAA Tradicional (Tolerância 2h)'
    )

    for barra in b1:
        h = barra.get_height()
        ax_fases.text(barra.get_x() + barra.get_width() / 2, h + 1.2, f"{int(h)}",
                      ha='center', va='bottom', fontsize=9, fontweight='bold')
    for barra in b2:
        h = barra.get_height()
        ax_fases.text(barra.get_x() + barra.get_width() / 2, h + 1.2, f"{int(h)}",
                      ha='center', va='bottom', fontsize=9)

    ax_fases.set_xticks(x_pos)
    ax_fases.set_xticklabels(df_f['Fase_do_Ciclo'], rotation=12, fontweight='bold')
    ax_fases.set_ylim(0, 80)  # Escala padronizada fixa (0 a 80 eventos)
    ax_fases.set_ylabel('Número de Eventos Identificados', fontweight='bold')
    ax_fases.set_title('Ocorrência por Fase do Ciclo Solar', fontweight='bold')
    ax_fases.legend(loc='upper left')

    # Subplot 2: Evolução Anual (Escala Y fixa em 0..35 eventos por ano)
    anos = df_resumo_anual['Ano'].astype(str).values
    x_a = np.arange(len(anos))
    cores_barras_ano = [CORES_FASES.get(f, '#7f7f7f') for f in df_resumo_anual['Fase_do_Ciclo']]

    barras_ano = ax_anos.bar(
        x_a,
        df_resumo_anual['Qtd_HILDCAA_Star_4h'],
        color=cores_barras_ano,
        edgecolor='black',
        alpha=0.85,
        label='Eventos HILDCAA* no Ano'
    )
    for barra in barras_ano:
        h = barra.get_height()
        if h > 0:
            ax_anos.text(barra.get_x() + barra.get_width() / 2, h + 0.5, f"{int(h)}",
                         ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    ax_anos.set_xticks(x_a)
    ax_anos.set_xticklabels(anos, rotation=30, fontweight='bold')
    ax_anos.set_ylim(0, 35)  # Escala anual fixa (0 a 35 eventos)
    ax_anos.set_ylabel('Eventos HILDCAA* por Ano', fontweight='bold')
    ax_anos.set_title('Distribuição Anual (Cores = Fase do Ciclo)', fontweight='bold')

    plt.tight_layout()
    caminho_dist = os.path.join(pasta_graficos, f"Distribuicao_Padronizada_{id_curto}.png")
    plt.savefig(caminho_dist, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  [GRÁFICO SALVO] {caminho_dist}")
    return caminho_dist


def gerar_comparativo_direto_entre_ciclos(dicionario_resultados_ciclos, pasta_graficos):
    """
    Recebe os resultados calculados de múltiplos Ciclos Solares (ex: Ciclo Solar 23
    e Ciclo Solar 24) e plota um Painel 2x5 sobrepondo diretamente as curvas médias
    de cada Ciclo Solar na mesma figura e na mesma escala!
    """
    if len(dicionario_resultados_ciclos) < 2:
        return None

    aplicar_estilo_padrao()
    os.makedirs(pasta_graficos, exist_ok=True)
    col_esquerda, col_direita = _ordenar_colunas_painel()

    fig, axes = plt.subplots(nrows=5, ncols=2, sharex=True, figsize=(15, 16))
    nomes_ciclos = " vs. ".join(dicionario_resultados_ciclos.keys())
    fig.suptitle(
        f"Comparação Direta da Superposição de Época (SEA) entre Ciclos Solares\n"
        f"{nomes_ciclos} — Eventos HILDCAA* (Escalas Padronizadas)",
        fontsize=14,
        fontweight='bold',
        y=0.985
    )

    for row in range(5):
        for col_idx, lista_vars in enumerate([col_esquerda, col_direita]):
            var_nome, cfg_var = lista_vars[row]
            ax = axes[row, col_idx]

            rotulo = cfg_var['rotulo']
            ylim_comp = cfg_var['ylim_comp']
            fator = cfg_var.get('fator_escala', 1.0)
            ref_val = cfg_var['ref_padrao']
            c_mean = f"{var_nome}_mean"
            c_low = f"{var_nome}_lowq"
            c_up = f"{var_nome}_upq"

            for nome_ciclo, pacote in dicionario_resultados_ciclos.items():
                res_sea = pacote['resultados_sea']
                if 'Ciclo Completo' not in res_sea:
                    continue
                sdat = res_sea['Ciclo Completo']['seadat']
                x_d = res_sea['Ciclo Completo']['x_dias']
                qtd = res_sea['Ciclo Completo']['qtd_eventos']
                cor_c = CORES_CICLOS.get(nome_ciclo, '#333333')

                if c_mean in sdat.columns:
                    media = sdat[c_mean].values * fator
                    ax.plot(x_d, media, label=f"{nome_ciclo} (N={qtd})", color=cor_c, linewidth=2.3)
                    if c_low in sdat.columns and c_up in sdat.columns:
                        ax.fill_between(
                            x_d,
                            sdat[c_low].values * fator,
                            sdat[c_up].values * fator,
                            color=cor_c,
                            alpha=0.12
                        )

            ax.axhline(ref_val, color='#666666', linestyle=':', linewidth=1.0, alpha=0.7)
            ax.axvline(0.0, color='#d62728', linestyle='--', linewidth=1.4, alpha=0.9)
            ax.set_ylim(ylim_comp)
            ax.set_xlim(XLIM_SEA_DIAS)
            ax.set_xticks(XTICKS_SEA_DIAS)
            ax.set_ylabel(rotulo, fontsize=10, fontweight='bold')

            if row == 0:
                ax.legend(loc='upper right', fontsize=8.5, framealpha=0.92)

    axes[-1, 0].set_xlabel('Tempo Relativo ao Início [Dias] (Época Zero $t_1 = 0$)', fontsize=10.5, fontweight='bold')
    axes[-1, 1].set_xlabel('Tempo Relativo ao Início [Dias] (Época Zero $t_1 = 0$)', fontsize=10.5, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    caminho_out = os.path.join(pasta_graficos, "SEA_Comparativo_Direto_Entre_Ciclos_Solares.png")
    plt.savefig(caminho_out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  [GRÁFICO COMPARATIVO ENTRE CICLOS SALVO] {caminho_out}")
    return caminho_out
