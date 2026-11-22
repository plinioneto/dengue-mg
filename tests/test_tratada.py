"""Teste de ponta a ponta da camada tratada: monta uma bruta mínima e roda o dbt (seed, run, test).

Pula se o dbt-duckdb não estiver instalado. Os valores abaixo são sintéticos, só para exercitar as regras.
"""
import importlib

import pytest

pytest.importorskip("dbt.cli.main")
pytest.importorskip("duckdb")

HOJE = "2026-03-01"


def test_tratada_ponta_a_ponta(banco, monkeypatch):
    from dengue_mg import bronze, tratada
    importlib.reload(tratada)
    tratada.preparar_ambiente(str(banco / "data"))
    assert tratada.dbt(["seed"], HOJE).success
    res = tratada.dbt(["run"], HOJE)
    assert res.success, res.exception
    c = bronze.con()
    # SINAN: 1 descartado e 1 duplicata saem; o preliminar de 2026 é ignorado; o de 2025 (sem final) entra
    assert c.execute("SELECT count(*) FROM tratada.stg_sinan").fetchone()[0] == 4
    assert c.execute("SELECT casos_notificados, casos_hospitalizados FROM tratada.fct_casos_semana WHERE semana_id = 202601").fetchone() == (2, 1)
    assert c.execute("SELECT internacoes, obitos FROM tratada.fct_internacoes_semana WHERE semana_id = 202601").fetchone() == (2, 1)
    # leito hospital-dia (tipo 7) não conta
    assert c.execute("SELECT leitos_existentes, leitos_clinicos_pediatricos FROM tratada.fct_leitos_mes").fetchone() == (10, 10)
    assert c.execute("SELECT count(*) FROM tratada.dim_municipio").fetchone()[0] == 853
    # reconciliação: 2 casos no SINAN, 2 no InfoDengue, nenhum par elegível (menos de 10 casos)
    assert c.execute("SELECT casos_sinan, casos_infodengue, divergencia FROM final.rec_sinan_infodengue WHERE semana_id = 202601").fetchone() == (2, 2, 0.0)
    assert c.execute("SELECT count(*) FROM final.rec_sinan_infodengue WHERE elegivel").fetchone()[0] == 0
    # R7: tabela final densa (853 municípios x semanas até a corrente), com "dados até" e pressão
    n_sem = c.execute("SELECT count(*) FROM tratada.dim_semana_epi WHERE inicio <= date '%s'" % HOJE).fetchone()[0]
    assert c.execute("SELECT count(*) FROM final.indicadores_municipio_semana").fetchone()[0] == 853 * n_sem
    linha = c.execute("SELECT casos_notificados, internacoes, leitos_clinicos_pediatricos, pressao_internacoes_por_leito, "
                      "sem_leito_clinico_pediatrico, leitos_competencia FROM final.indicadores_municipio_semana "
                      "WHERE geocodigo = '3100000' AND semana_id = 202601").fetchone()
    assert linha[:5] == (2, 2, 10, 0.2, False) and str(linha[5]) == "2026-01-01"
    # município sem leito: zero internações, pressão nula (não divide por zero) e sinalizado
    assert c.execute("SELECT internacoes, leitos_clinicos_pediatricos, pressao_internacoes_por_leito, sem_leito_clinico_pediatrico "
                     "FROM final.indicadores_municipio_semana WHERE geocodigo = '3100010' AND semana_id = 202601").fetchone() == (0, 0, None, True)
    # depois do "dados até" o valor é desconhecido (nulo), não zero; antes da primeira competência de leitos também
    assert c.execute("SELECT casos_notificados, internacoes, pressao_internacoes_por_leito FROM final.indicadores_municipio_semana "
                     "WHERE geocodigo = '3100000' AND semana_id = 202608").fetchone() == (None, None, None)
    assert c.execute("SELECT leitos_clinicos_pediatricos FROM final.indicadores_municipio_semana "
                     "WHERE geocodigo = '3100000' AND semana_id = 202552").fetchone() == (None,)
    c.close()
    # testes de qualidade: os dados sintéticos têm limitações propositais só como aviso (warn), nenhuma falha
    teste = tratada.dbt(["test"], HOJE)
    erros = [r for r in teste.result.results if str(r.status) in ("fail", "error")]
    assert not erros, [(r.node.name, r.message) for r in erros]
