"""H1 e H3: análise exploratória sobre uma tabela final sintética com relações conhecidas."""
import duckdb
import pytest

pd = pytest.importorskip("pandas")


@pytest.fixture()
def c():
    con = duckdb.connect(":memory:")
    con.execute("CREATE SCHEMA final")
    # 3 municípios, 40 semanas consecutivas (202201..202240). A: internações = casos da semana anterior (lag 1 perfeito);
    # B: internações constantes (sem correlação); C: poucos casos (fica de fora da correlação por município).
    linhas = []
    import random
    random.seed(1)
    casos_a = [random.randint(1, 50) for _ in range(40)]
    for i in range(40):
        sem = 202201 + i
        ia = casos_a[i - 1] // 5 if i > 0 else 0
        linhas.append(("1", "A", "R1", sem, casos_a[i], ia, 10, False))
        linhas.append(("2", "B", "R1", sem, random.randint(1, 50), 3, 4, False))
        linhas.append(("3", "C", "R2", sem, 1 if i < 3 else 0, 0, 5, False))
    con.execute("CREATE TABLE final.t (geocodigo VARCHAR, municipio VARCHAR, regiao_saude VARCHAR, semana_id INTEGER, casos_notificados BIGINT, internacoes BIGINT, leitos_clinicos_pediatricos BIGINT, casos_provisorio BOOLEAN)")
    con.executemany("INSERT INTO final.t VALUES (?,?,?,?,?,?,?,?)", linhas)
    con.execute("""CREATE VIEW final.indicadores_municipio_semana AS
        SELECT *, internacoes * 1.0 / nullif(leitos_clinicos_pediatricos, 0) AS pressao_internacoes_por_leito FROM final.t""")
    yield con
    con.close()


def test_h1_estado_acha_a_defasagem_de_uma_semana(c):
    from dengue_mg import hipoteses
    est = hipoteses.h1_estado(hipoteses.carregar(c))
    assert list(est["defasagem_semanas"]) == [0, 1, 2, 3, 4]
    # o estado soma A (lag 1 perfeito) e B (ruído): a defasagem 1 deve ser a maior correlação
    assert est.loc[est["spearman"].idxmax(), "defasagem_semanas"] == 1


def test_h1_municipios_filtra_e_correlaciona(c):
    import pandas as pd
    from dengue_mg import hipoteses
    m = hipoteses.h1_municipios(hipoteses.carregar(c))
    # C não tem semanas com casos suficientes e fica de fora; B entra, mas com internações constantes a correlação é indefinida (nula)
    assert set(m["municipio"]) == {"A", "B"}
    a = m[m["municipio"] == "A"].iloc[0]
    b = m[m["municipio"] == "B"].iloc[0]
    assert a["lag1"] > 0.85 and a["lag1"] > a["lag0"]
    assert pd.isna(b["lag0"]) and pd.isna(b["lag1"])
    res = hipoteses.resumo_municipios(m)
    assert list(res["municipios"]) == [1, 1, 1, 1, 1]          # só A tem correlação definida
    assert int(res.loc[res["mediana"].idxmax(), "defasagem_semanas"]) == 1


def test_h3_compara_rankings(c):
    from dengue_mg import hipoteses
    h = hipoteses.h3(c, 2022, 2022)
    assert list(h["periodo"]) == ["2022", "2022 a 2022"]
    # com piso de 5 internações no período: A (internações somadas) e B passam; C (0 internações) não
    linha = h.iloc[0]
    assert linha["municipios_comparados"] == 2


def test_relatorio_grava_markdown(c, tmp_path):
    from dengue_mg import hipoteses
    saida = hipoteses.relatorio(c, str(tmp_path / "r.md"))
    txt = open(saida, encoding="utf-8").read()
    assert "H1: correlação entre casos e internações" in txt and "H3: ranking por pressão" in txt and "Defasagem com maior mediana" in txt
