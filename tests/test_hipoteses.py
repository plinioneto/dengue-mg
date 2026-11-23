"""H1 e H2 (parcial): análise exploratória sobre uma tabela final sintética com relações conhecidas."""
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


def test_h2_parcial_compara_rankings(c):
    from dengue_mg import hipoteses
    h = hipoteses.h2_parcial(c, 2022, 2022)
    assert list(h["periodo"]) == ["2022", "2022 a 2022"]
    # com piso de 5 internações no período: A (internações somadas) e B passam; C (0 internações) não
    linha = h.iloc[0]
    assert linha["municipios_comparados"] == 2


def test_relatorio_grava_markdown(c, tmp_path):
    from dengue_mg import hipoteses
    saida = hipoteses.relatorio(c, str(tmp_path / "r.md"))
    txt = open(saida, encoding="utf-8").read()
    assert "| 0 | 40 |" in txt and "40,00" not in txt   # contagens aparecem como inteiros
    assert "H1: correlação entre casos e internações" in txt and "### Picos" in txt and "## H3" in txt and "H2 (parcial): ranking por pressão" in txt and "Defasagem com maior mediana" in txt


def _serie_com_picos():
    import math
    linhas = []
    for i in range(30):
        linhas.append(("1", "A", 202401 + i, round(100 * math.exp(-((i - 12) / 4) ** 2)) + 1, round(10 * math.exp(-((i - 14) / 4) ** 2)) + 1))
    return pd.DataFrame(linhas, columns=["geocodigo", "municipio", "semana_id", "casos", "internacoes"])


def test_h1_picos_estado_e_municipios():
    from dengue_mg import hipoteses
    df = _serie_com_picos()
    p = hipoteses.h1_picos(df)
    # casos picam na semana 13 (índice 12) e internações duas semanas depois
    assert list(p["ano"]) == [2024] and int(p.loc[0, "defasagem_semanas"]) == 2
    assert int(p.loc[0, "semana_pico_internacoes"]) - int(p.loc[0, "semana_pico_casos"]) == 2
    m = hipoteses.h1_picos_municipios(df)
    assert list(m["defasagem_semanas"]) == [2]
    r = hipoteses.resumo_picos_municipios(m)
    assert r.loc[0, "pct_internacao_depois"] == 1.0 and r.loc[0, "mediana_defasagem"] == 2


def test_h3_fluxos_residencia_x_ocorrencia():
    from dengue_mg import hipoteses
    F = "Fora de MG ou ignorado"
    linhas = [  # ano, res, município res, região res, oc, município oc, região oc, internações
        (2026, "1", "A", "R1", "1", "A", "R1", 12),   # mesmo município
        (2026, "2", "B", "R1", "1", "A", "R1", 2),    # outro município, mesma região
        (2026, "3", "C", "R2", "1", "A", "R1", 1),    # outra região
        (2026, None, F, F, "1", "A", "R1", 1),        # residente fora de MG
        (2026, "1", "A", "R1", "2", "B", "R1", 1),    # residente de A internado em B
    ]
    f = pd.DataFrame(linhas, columns=["ano", "cod6_residencia", "municipio_residencia", "regiao_residencia", "cod6_ocorrencia",
                                      "municipio_ocorrencia", "regiao_ocorrencia", "internacoes"])
    resumo, polos, envia = hipoteses.h3_fluxos(f)
    tot = resumo[resumo["ano"] == "Total"].iloc[0]
    assert (tot["total"], tot["mesmo município"], tot["outro município da mesma região"], tot["outra região de saúde"],
            tot["residente fora de MG ou ignorado"]) == (17, 12, 3, 1, 1)
    assert tot["pct_fora_do_municipio"] == pytest.approx(4 / 16) and tot["pct_dentro_da_regiao"] == pytest.approx(15 / 16)
    a = polos[polos["municipio_ocorrencia"] == "A"].iloc[0]
    assert (a["recebidas_de_fora"], a["internacoes_no_municipio"], a["enviadas"], a["saldo"]) == (4, 16, 1, 3)
    assert a["pct_de_fora"] == pytest.approx(0.25)
    # só A tem 10 ou mais internações de residentes; 1 de 13 fora (< 50%)
    assert (envia.loc[0, "municipios_com_10_ou_mais_internacoes"], envia.loc[0, "com_metade_ou_mais_fora"]) == (1, 0)
