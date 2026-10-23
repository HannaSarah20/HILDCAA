# -*- coding: utf-8 -*-
"""
================================================================================
ORQUESTRADOR PRINCIPAL: PIPELINE MODULAR PARA QUALQUER CICLO SOLAR
Arquivo: executar_analise.py
Pasta: Calculo_Eventos_HILDCAA
================================================================================
Este script conecta todos os blocos funcionais independentes:
  - Bloco 1 (config_padrao.py)       : Configurações dos Ciclos e Escalas Padronizadas
  - Bloco 2 (leitor_omni.py)         : Leitura Universal dos Dados OMNIWeb
  - Bloco 3 (detector_hildcaa.py)    : Cálculo Universal de Eventos HILDCAA e HILDCAA*
  - Bloco 4 (motor_sea.py)           : Integração com sea_norm.py (Superposição de Época)
  - Bloco 5 (exportador_planilhas.py): Geração de Planilhas Excel (.xlsx) e CSV
  - Bloco 6 (gerador_graficos.py)    : Geração de Gráficos Padronizados (mesmas cores,
                                       mesmas fontes e mesmas variações/escalas)
================================================================================
"""

import os
import sys
import time
import pandas as pd

# Ajusta UTF-8 no terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Garante que a pasta atual esteja no caminho de importação
DIRETORIO_MODULO = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_MODULO, '..'))
if DIRETORIO_MODULO not in sys.path:
    sys.path.insert(0, DIRETORIO_MODULO)

from config_padrao import obter_configuracoes_ciclos
from leitor_omni import carregar_dados_ciclo
from detector_hildcaa import (
    calcular_eventos_hildcaa,
    gerar_resumo_por_fase,
    gerar_resumo_anual,
)
from motor_sea import executar_sea_por_ciclo
from exportador_planilhas import (
    exportar_relatorio_completo_ciclo,
    salvar_multiplas_abas_xlsx,
)
from gerador_graficos import (
    gerar_paineis_sea_padronizados_ciclo,
    gerar_grafico_distribuicao_ciclo,
    gerar_comparativo_direto_entre_ciclos,
)


def processar_ciclo_solar(nome_ciclo, config_ciclo, pasta_base_resultados):
    """
    Executa todo o fluxo modular para um Ciclo Solar específico:
      1. Carrega os dados OMNIWeb do ciclo.
      2. Calcula os eventos HILDCAA* (tolerância 4h) e HILDCAA Tradicionais (tolerância 2h).
      3. Gera as tabelas de resumo estatístico por Fase e por Ano.
      4. Executa a Análise de Sobreposição de Época (SEA) conversando com sea_norm.py.
      5. Exporta a planilha Excel (.xlsx) multi-abas e os CSVs.
      6. Gera todos os gráficos padronizados com escalas fixas.
    """
    print("\n" + "=" * 85)
    print(f"INICIANDO PROCESSAMENTO MODULAR: {config_ciclo['nome_exibicao'].upper()}")
    print("=" * 85)

    id_curto = config_ciclo['id_curto']
    pasta_ciclo = os.path.join(pasta_base_resultados, id_curto)
    pasta_planilhas = os.path.join(pasta_ciclo, 'planilhas_excel')
    pasta_graficos = os.path.join(pasta_ciclo, 'graficos_padronizados')

    # 1. Leitura Universal dos Dados OMNIWeb
    dados = carregar_dados_ciclo(config_ciclo)

    # 2. Cálculo Universal dos Eventos HILDCAA* (4h) e HILDCAA Tradicional (2h)
    _, df_eventos_star = calcular_eventos_hildcaa(
        dados=dados,
        config_ciclo=config_ciclo,
        max_gap_hours=4.0,
        min_dur_days=2.0,
        peak_ae_min=1000.0,
        symh_thresh=-50.0,
        tipo_criterio='HILDCAA* (4h)'
    )

    _, df_eventos_trad = calcular_eventos_hildcaa(
        dados=dados,
        config_ciclo=config_ciclo,
        max_gap_hours=2.0,
        min_dur_days=2.0,
        peak_ae_min=1000.0,
        symh_thresh=-50.0,
        tipo_criterio='HILDCAA Tradicional (2h)'
    )

    # 3. Resumos Estatísticos por Fase e por Ano
    df_resumo_fases = gerar_resumo_por_fase(df_eventos_star, df_eventos_trad, config_ciclo)
    df_resumo_anual = gerar_resumo_anual(dados, df_eventos_star, df_eventos_trad, config_ciclo)

    # 4. Superposição de Época (SEA) conversando com sea_norm.py
    resultados_sea = executar_sea_por_ciclo(
        dados=dados,
        df_eventos=df_eventos_star,
        nome_ciclo=config_ciclo['nome_exibicao'],
        usar_janela_segura=True,
        n_bins_fase=48
    )

    # 5. Exportação para Planilha Excel (.xlsx) e CSV
    caminho_xlsx = exportar_relatorio_completo_ciclo(
        config_ciclo=config_ciclo,
        df_eventos_star=df_eventos_star,
        df_eventos_trad=df_eventos_trad,
        df_resumo_fases=df_resumo_fases,
        df_resumo_anual=df_resumo_anual,
        resultados_sea=resultados_sea,
        pasta_saida=pasta_planilhas
    )

    # 6. Geração dos Gráficos Padronizados (mesmas cores, fontes e variações)
    graficos_sea = gerar_paineis_sea_padronizados_ciclo(
        config_ciclo=config_ciclo,
        resultados_sea=resultados_sea,
        pasta_graficos=pasta_graficos
    )
    grafico_dist = gerar_grafico_distribuicao_ciclo(
        config_ciclo=config_ciclo,
        df_resumo_fases=df_resumo_fases,
        df_resumo_anual=df_resumo_anual,
        pasta_graficos=pasta_graficos
    )

    return {
        'config': config_ciclo,
        'df_eventos_star': df_eventos_star,
        'df_eventos_trad': df_eventos_trad,
        'df_resumo_fases': df_resumo_fases,
        'df_resumo_anual': df_resumo_anual,
        'resultados_sea': resultados_sea,
        'caminho_xlsx': caminho_xlsx,
        'graficos': graficos_sea + [grafico_dist],
    }


def main():
    t_inicio_global = time.time()
    pasta_resultados = os.path.join(DIRETORIO_MODULO, 'Resultados_Padronizados')
    os.makedirs(pasta_resultados, exist_ok=True)

    configuracoes = obter_configuracoes_ciclos(DIRETORIO_RAIZ)
    resultados_todos_ciclos = {}

    for nome_ciclo, cfg in configuracoes.items():
        try:
            pacote = processar_ciclo_solar(nome_ciclo, cfg, pasta_resultados)
            resultados_todos_ciclos[nome_ciclo] = pacote
        except FileNotFoundError as e:
            print(f"\n[AVISO] Pulando {nome_ciclo}: {e}")

    # Gera Planilha Excel Comparativa Geral e Gráfico Comparativo Direto entre Ciclos
    if len(resultados_todos_ciclos) >= 2:
        pasta_comparativo = os.path.join(pasta_resultados, 'Comparativo_Entre_Ciclos')
        os.makedirs(pasta_comparativo, exist_ok=True)

        resumos_fases_unidos = pd.concat(
            [p['df_resumo_fases'] for p in resultados_todos_ciclos.values()],
            ignore_index=True
        )
        resumos_anuais_unidos = pd.concat(
            [p['df_resumo_anual'] for p in resultados_todos_ciclos.values()],
            ignore_index=True
        )

        abas_comp = {
            'Comparativo_Fases_Ciclos': resumos_fases_unidos,
            'Comparativo_Anual_Ciclos': resumos_anuais_unidos,
        }
        for nome_c, pac in resultados_todos_ciclos.items():
            id_c = pac['config']['id_curto']
            cols_drop = ['t0_Background', 't1_Inicio', 't2_Termino', 't2_Janela_Segura']
            abas_comp[f'HILDCAA_Star_{id_c}'] = pac['df_eventos_star'].drop(
                columns=[c for c in cols_drop if c in pac['df_eventos_star'].columns]
            )
            abas_comp[f'HILDCAA_Trad_{id_c}'] = pac['df_eventos_trad'].drop(
                columns=[c for c in cols_drop if c in pac['df_eventos_trad'].columns]
            )

        caminho_xlsx_comp = os.path.join(
            pasta_comparativo, 'Planilha_Comparativa_Todos_Os_Ciclos.xlsx'
        )
        salvar_multiplas_abas_xlsx(abas_comp, caminho_xlsx_comp)
        resumos_fases_unidos.to_csv(
            os.path.join(pasta_comparativo, 'Comparativo_Fases_Todos_Os_Ciclos.csv'),
            index=False, sep=';', encoding='utf-8-sig'
        )
        resumos_anuais_unidos.to_csv(
            os.path.join(pasta_comparativo, 'Comparativo_Anual_Todos_Os_Ciclos.csv'),
            index=False, sep=';', encoding='utf-8-sig'
        )
        print(f"\n[PLANILHA COMPARATIVA GERAL SALVA] {caminho_xlsx_comp}")

        gerar_comparativo_direto_entre_ciclos(resultados_todos_ciclos, pasta_comparativo)

    tempo_total = time.time() - t_inicio_global
    print("\n" + "=" * 85)
    print(f"PIPELINE COMPLETO FINALIZADO COM SUCESSO EM {tempo_total:.1f}s!")
    print(f"Todos os resultados (Planilhas Excel e Gráficos Padronizados) estão em:")
    print(f"  -> {pasta_resultados}")
    print("=" * 85)


if __name__ == '__main__':
    main()
