"""Teste de ponta a ponta da camada tratada: monta uma bruta mínima e roda o dbt (seed, run, test).

Pula se o dbt-duckdb não estiver instalado. Os valores abaixo são sintéticos, só para exercitar as regras.
"""
import importlib

import pytest

pytest.importorskip("dbt.cli.main")
pytest.importorskip("duckdb")

HOJE = "2026-03-01"


def _carregar(bronze, c, fonte, nome, colunas, linhas):
    bronze.gravar(c, fonte, nome, "%064x" % abs(hash((fonte, nome))), [(colunas, linhas)])


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGUE_DATA", str(tmp_path / "data"))
    from dengue_mg import bronze
    importlib.reload(bronze)
    c = bronze.con()
    # 853 municípios sintéticos (código de 7 dígitos; o 6 primeiros são o código do SINAN/CNES/SIH)
    muns = [["%06d0" % (310000 + i), "Município %d" % i, "Micro", "Meso"] for i in range(853)]
    _carregar(bronze, c, "ibge_municipios", "municipios_mg.json", ["geocodigo", "nome", "microrregiao", "mesorregiao"], muns)
    cod = "310000"  # primeiro município
    sinan_cols = ["ID_MUNICIP", "ID_MN_RESI", "DT_NOTIFIC", "DT_SIN_PRI", "CLASSI_FIN", "EVOLUCAO", "HOSPITALIZ"]
    # semana 202601 (04/01 a 10/01): 3 notificações, 1 descartada
    final = [[cod, cod, "20260105", "20260103", "10", "1", "1"],
             [cod, cod, "20260106", "20260104", "5", "", "2"],   # descartado
             [cod, cod, "20260107", "20260105", "11", "1", "2"]]  # sem duplicata
    _carregar(bronze, c, "sinan_final", "DENGBR26.dbc", sinan_cols, final)
    # preliminar do mesmo ano não deve entrar (já há final)
    _carregar(bronze, c, "sinan_prelim", "DENGBR26.dbc", sinan_cols, [[cod, cod, "20260108", "", "10", "", "2"]])
    _carregar(bronze, c, "sinan_prelim", "DENGBR25.dbc", sinan_cols, [[cod, cod, "20251231", "", "10", "", "2"]])
    _carregar(bronze, c, "cnes_lt", "LTMG2601.dbc", ["CNES", "CODUFMUN", "COMPETEN", "TP_LEITO", "CODLEITO", "QT_EXIST", "QT_CONTR", "QT_SUS"],
              [["100", cod, "202601", "2", "33", "10", "10", "8"], ["100", cod, "202601", "7", "1", "5", "5", "5"]])
    _carregar(bronze, c, "sih_rd", "RDMG2601.dbc", ["N_AIH", "MUNIC_MOV", "MUNIC_RES", "DT_INTER", "DT_SAIDA", "DIAG_PRINC", "MORTE", "DIAS_PERM"],
              [["a1", cod, cod, "20260106", "20260110", "A90", "0", "4"], ["a2", cod, cod, "20260107", "20260112", "A91", "1", "5"]])
    _carregar(bronze, c, "infodengue", "alertcity_mg_2026-02-01.json", ["SE", "casos", "casos_est", "nivel", "geocodigo"],
              [["202601", "2", "2.5", "1", muns[0][0]]])
    c.close()
    return tmp_path


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
    c.close()
    # testes de qualidade: os dados sintéticos têm limitações propositais só como aviso (warn), nenhuma falha
    teste = tratada.dbt(["test"], HOJE)
    erros = [r for r in teste.result.results if str(r.status) in ("fail", "error")]
    assert not erros, [(r.node.name, r.message) for r in erros]
