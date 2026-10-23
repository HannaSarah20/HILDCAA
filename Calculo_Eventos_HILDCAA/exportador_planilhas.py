# -*- coding: utf-8 -*-
"""
================================================================================
BLOCO 5: EXPORTADOR DE PLANILHAS EXCEL (.XLSX) E CSV (exportador_planilhas.py)
================================================================================
Este módulo recebe os DataFrames calculados pelos blocos anteriores (eventos
HILDCAA*, eventos HILDCAA Tradicionais, resumos por Fase, resumos por Ano e
séries da Superposição de Época SEA) e gera:
  1. Planilhas Excel nativas (.xlsx) com múltiplas abas, cabeçalhos formatados,
     largura de colunas ajustada automaticamente e números padronizados.
  2. Tabelas CSV compatíveis com Excel em Português (separador ';' e UTF-8-BOM).
================================================================================
"""

import os
import zipfile
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd


def _col_letter(n):
    """Converte índice de coluna (1-based) para letra de coluna do Excel (A, B, ..., Z, AA, AB...)."""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def salvar_multiplas_abas_xlsx(dicionario_abas, caminho_xlsx):
    """
    Gera um arquivo Excel (.xlsx) nativo e estilizado com múltiplas abas a partir
    de um dicionário {nome_da_aba: DataFrame}, sem depender de pacotes externos!
    Inclui cabeçalho azul escuro com fonte branca em negrito e larguras de coluna
    auto-ajustadas.
    """
    os.makedirs(os.path.dirname(os.path.abspath(caminho_xlsx)), exist_ok=True)

    # Limpa nomes de abas (máx 31 chars, sem caracteres proibidos pelo Excel)
    abas_limpas = []
    for nome_aba, df in dicionario_abas.items():
        nome_seguro = (
            str(nome_aba)
            .replace('/', '_')
            .replace('\\', '_')
            .replace('*', 'Star')
            .replace(':', '')
            .replace('?', '')
            .replace('[', '')
            .replace(']', '')[:31]
        )
        abas_limpas.append((nome_seguro, df.copy() if df is not None else pd.DataFrame()))

    with zipfile.ZipFile(caminho_xlsx, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. [Content_Types].xml
        sheets_ct = "\n".join([
            f'  <Override PartName="/xl/worksheets/sheet{i}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, len(abas_limpas) + 1)
        ])
        content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
{sheets_ct}
</Types>"""
        zf.writestr('[Content_Types].xml', content_types)

        # 2. _rels/.rels
        rels_root = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
        zf.writestr('_rels/.rels', rels_root)

        # 3. xl/workbook.xml
        sheets_wb = "\n".join([
            f'    <sheet name="{escape(nome)}" sheetId="{i}" r:id="rId{i}"/>'
            for i, (nome, _) in enumerate(abas_limpas, start=1)
        ])
        workbook_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
{sheets_wb}
  </sheets>
</workbook>"""
        zf.writestr('xl/workbook.xml', workbook_xml)

        # 4. xl/_rels/workbook.xml.rels
        rels_wb = "\n".join([
            f'  <Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(abas_limpas) + 1)
        ])
        id_style = len(abas_limpas) + 1
        workbook_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels_wb}
  <Relationship Id="rId{id_style}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
        zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)

        # 5. xl/styles.xml (Estilo 0 = Padrão, Estilo 1 = Cabeçalho Azul Marinho + Fonte Branca Bold, Estilo 2 = Dados com borda leve)
        styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="10"/><name val="Arial"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFD9D9D9"/></left>
      <right style="thin"><color rgb="FFD9D9D9"/></right>
      <top style="thin"><color rgb="FFD9D9D9"/></top>
      <bottom style="thin"><color rgb="FFD9D9D9"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
  </cellXfs>
</styleSheet>"""
        zf.writestr('xl/styles.xml', styles_xml)

        # 6. Gera cada aba xl/worksheets/sheet{i}.xml
        for i, (nome_aba, df) in enumerate(abas_limpas, start=1):
            colunas = list(df.columns)
            n_cols = len(colunas)

            if n_cols == 0:
                sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Sem registros</t></is></c></row></sheetData>
</worksheet>"""
                zf.writestr(f'xl/worksheets/sheet{i}.xml', sheet_xml)
                continue

            # Calcula larguras ideais das colunas
            larguras = []
            for col in colunas:
                max_len = len(str(col)) + 4
                if len(df) > 0:
                    amostra = df[col].head(200).astype(str).map(len).max()
                    if pd.notna(amostra):
                        max_len = max(max_len, int(amostra) + 4)
                larguras.append(min(max(max_len, 12), 38))

            cols_xml = "\n".join([
                f'    <col min="{c_idx}" max="{c_idx}" width="{larg}" customWidth="1"/>'
                for c_idx, larg in enumerate(larguras, start=1)
            ])

            linhas_xml = []
            # Linha 1: Cabeçalho (Estilo s="1")
            celulas_cab = []
            for c_idx, col_nome in enumerate(colunas, start=1):
                ref = f"{_col_letter(c_idx)}1"
                celulas_cab.append(
                    f'<c r="{ref}" s="1" t="inlineStr"><is><t>{escape(str(col_nome))}</t></is></c>'
                )
            linhas_xml.append(f'    <row r="1" ht="22" customHeight="1">{"".join(celulas_cab)}</row>')

            # Linhas de dados (Estilo s="2")
            valores_matriz = df.values
            for r_idx, linha_vals in enumerate(valores_matriz, start=2):
                celulas_linha = []
                for c_idx, val in enumerate(linha_vals, start=1):
                    ref = f"{_col_letter(c_idx)}{r_idx}"
                    if val is None or (isinstance(val, (float, np.floating)) and np.isnan(val)) or pd.isna(val):
                        celulas_linha.append(f'<c r="{ref}" s="2"/>')
                    elif isinstance(val, (int, np.integer, float, np.floating)) and not isinstance(val, bool):
                        celulas_linha.append(f'<c r="{ref}" s="2"><v>{val}</v></c>')
                    else:
                        texto = escape(str(val))
                        celulas_linha.append(f'<c r="{ref}" s="2" t="inlineStr"><is><t>{texto}</t></is></c>')
                linhas_xml.append(f'    <row r="{r_idx}">{"".join(celulas_linha)}</row>')

            sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>
{cols_xml}
  </cols>
  <sheetData>
{chr(10).join(linhas_xml)}
  </sheetData>
</worksheet>"""
            zf.writestr(f'xl/worksheets/sheet{i}.xml', sheet_xml)


def exportar_relatorio_completo_ciclo(
    config_ciclo,
    df_eventos_star,
    df_eventos_trad,
    df_resumo_fases,
    df_resumo_anual,
    resultados_sea,
    pasta_saida
):
    """
    Exporta a planilha Excel (.xlsx) completa do Ciclo Solar (com todas as abas)
    e os arquivos CSV complementares.
    """
    os.makedirs(pasta_saida, exist_ok=True)
    id_curto = config_ciclo['id_curto']

    # Remove colunas do tipo Timestamp bruto para exibição limpa no Excel
    colunas_ocultar_ts = ['t0_Background', 't1_Inicio', 't2_Termino', 't2_Janela_Segura']
    df_star_excel = df_eventos_star.drop(columns=[c for c in colunas_ocultar_ts if c in df_eventos_star.columns])
    df_trad_excel = df_eventos_trad.drop(columns=[c for c in colunas_ocultar_ts if c in df_eventos_trad.columns])

    abas = {
        'Resumo_Por_Fase': df_resumo_fases,
        'Resumo_Anual': df_resumo_anual,
        'Eventos_HILDCAA_Star_4h': df_star_excel,
        'Eventos_HILDCAA_Trad_2h': df_trad_excel,
    }

    # Adiciona as tabelas da Superposição de Época (SEA)
    for nome_grupo, res in resultados_sea.items():
        sdat = res['seadat'].copy()
        # Coloca Tempo_Dias e Tempo_Horas nas primeiras colunas
        cols_tempo = [c for c in ['Tempo_Dias', 'Tempo_Horas'] if c in sdat.columns]
        outras_cols = [c for c in sdat.columns if c not in cols_tempo]
        sdat = sdat[cols_tempo + outras_cols].round(3)
        nome_aba = f"SEA_{nome_grupo.replace(' ', '_')}"[:31]
        abas[nome_aba] = sdat

    caminho_xlsx = os.path.join(pasta_saida, f"Planilha_Completa_HILDCAA_{id_curto}.xlsx")
    salvar_multiplas_abas_xlsx(abas, caminho_xlsx)
    print(f"[PLANILHA EXCEL] Salva com sucesso: {caminho_xlsx}")

    # Salva também CSVs individuais para fácil importação
    df_star_excel.to_csv(
        os.path.join(pasta_saida, f"Catalogo_HILDCAA_Star_{id_curto}.csv"),
        index=False, sep=';', encoding='utf-8-sig'
    )
    df_trad_excel.to_csv(
        os.path.join(pasta_saida, f"Catalogo_HILDCAA_Tradicional_{id_curto}.csv"),
        index=False, sep=';', encoding='utf-8-sig'
    )
    df_resumo_fases.to_csv(
        os.path.join(pasta_saida, f"Resumo_Fases_{id_curto}.csv"),
        index=False, sep=';', encoding='utf-8-sig'
    )
    df_resumo_anual.to_csv(
        os.path.join(pasta_saida, f"Resumo_Anual_{id_curto}.csv"),
        index=False, sep=';', encoding='utf-8-sig'
    )

    return caminho_xlsx
