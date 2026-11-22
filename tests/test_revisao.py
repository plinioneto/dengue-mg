"""R8: a revisão das semanas preliminares é medida entre versões da bruta (dados sintéticos)."""
import datetime as dt
import importlib

import pytest

pytest.importorskip("duckdb")

COLS = ["ID_MUNICIP", "DT_NOTIFIC", "DT_SIN_PRI", "CLASSI_FIN"]


@pytest.fixture()
def c(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGUE_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("DENGUE_EVIDENCIAS", str(tmp_path / "evidencias"))
    from dengue_mg import bronze
    importlib.reload(bronze)
    con = bronze.con()
    con.execute("CREATE SCHEMA tratada")
    # semanas 202601 (04/01 a 10/01) e 202602 (11/01 a 17/01)
    con.execute("""CREATE TABLE tratada.dim_semana_epi AS SELECT * FROM (VALUES
        (202601, DATE '2026-01-04', DATE '2026-01-10'), (202602, DATE '2026-01-11', DATE '2026-01-17')) t(semana_id, inicio, fim)""")
    yield bronze, con
    con.close()


def _carga(bronze, con, sha, linhas, publicada):
    bronze.gravar(con, "sinan_prelim", "DENGBR26.dbc", sha * 64, [(COLS, linhas)], 0, publicada)


def test_sem_segunda_versao_nao_ha_revisao(c):
    from dengue_mg import revisao
    bronze, con = c
    _carga(bronze, con, "a", [["310000", "20260105", "20260104", "10"]], dt.date(2026, 1, 20))
    assert revisao.calcular(con) == 1
    assert "Ainda não há o que medir" in open(revisao.relatorio(con, str(bronze.DATA) + "/r.md"), encoding="utf-8").read()


def test_revisao_entre_versoes(c):
    from dengue_mg import revisao
    bronze, con = c
    # versão 1 (publicada 13/01): semana 202601 com 10 casos; versão 2 (publicada 20/01): chegam 5 casos a mais (15), um descartado fica de fora
    v1 = [["310000", "20260105", "20260104", "10"]] * 10
    v2 = v1 + [["310000", "20260110", "20260109", "10"]] * 5 + [["310000", "20260110", "20260109", "5"]]
    _carga(bronze, con, "a", v1, dt.date(2026, 1, 13))
    _carga(bronze, con, "b", v2, dt.date(2026, 1, 20))
    assert revisao.calcular(con) == 2
    assert con.execute("SELECT versao, casos FROM final.revisao_sinan_versoes WHERE semana_id = 202601 ORDER BY versao").fetchall() == [(1, 10), (2, 15)]
    res = revisao.resumo_por_idade(con)
    # na versão 1, a semana 202601 (fim 10/01) tinha 0 semanas completas (13/01 - 10/01 = 3 dias); faltavam 5 de 15 casos
    assert len(res) == 1
    idade, semanas, rev, pares, rev_m, acima = res[0]
    assert (idade, semanas, pares) == (0, 1, 1)
    assert rev == pytest.approx(5 / 15) and rev_m == pytest.approx(5 / 15) and acima == 1.0
    assert "| 0 | 1 | 33.3%" in open(revisao.relatorio(con, str(bronze.DATA) + "/r.md"), encoding="utf-8").read()
