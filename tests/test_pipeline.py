"""R9: pipeline completo (sem ingestão) e monitoramento de frescor, com a bruta sintética."""
import datetime as dt
import importlib
import json
import os

import pytest

pytest.importorskip("dbt.cli.main")

HOJE = "2026-03-01"


def test_pipeline_registra_etapas_e_frescor(banco):
    from dengue_mg import bronze, pipeline, tratada
    importlib.reload(tratada)
    importlib.reload(pipeline)
    # os dados sintéticos têm "dados até" de janeiro: com tolerância ao atraso, a execução termina com 0
    assert pipeline.executar([], HOJE, tolerar_atraso=True) == 0
    # sem tolerância, as fontes antigas derrubam o código de saída (2) depois de gravar tudo
    assert pipeline.executar([], HOJE, tolerar_atraso=False) == 2
    c = bronze.con()
    assert c.execute("SELECT count(*) FROM execucoes WHERE etapa = 'tratada_e_final' AND status = 'ok'").fetchone()[0] == 2
    assert c.execute("SELECT count(DISTINCT execucao) FROM execucoes").fetchone()[0] == 2
    frescor = {r[0]: r[1:] for r in c.execute("SELECT indicador, situacao, idade_dias, tolerancia_dias FROM final.frescor").fetchall()}
    assert set(frescor) == {"casos_sinan", "infodengue", "leitos_cnes", "internacoes_sih"}
    assert frescor["casos_sinan"][0] == "atrasado" and frescor["casos_sinan"][1] == (dt.date(2026, 3, 1) - dt.date(2026, 1, 17)).days
    c.close()
    linhas = [json.loads(l) for l in open(os.path.join(bronze.DATA, "logs", "execucoes.jsonl"), encoding="utf-8")]
    assert {l["etapa"] for l in linhas} == {"tratada_e_final", "revisao_sinan", "frescor", "publicacao"} and all(l["status"] == "ok" for l in linhas)


def test_etapa_com_falha_e_registrada_e_nao_para_as_outras(banco):
    from dengue_mg import bronze, pipeline
    importlib.reload(pipeline)
    assert pipeline._etapa("x", "ingestao:fonte_ruim", lambda: (_ for _ in ()).throw(RuntimeError("sem rede"))) is False
    assert pipeline._etapa("x", "outra", lambda: "ok") is True
    c = bronze.con()
    assert c.execute("SELECT etapa, status FROM execucoes ORDER BY etapa").fetchall() == [("ingestao:fonte_ruim", "erro"), ("outra", "ok")]
    assert c.execute("SELECT count(*) FROM execucoes WHERE status = 'erro' AND detalhe LIKE '%sem rede%'").fetchone()[0] == 1
    c.close()


def _preparar_frescor(c, cargas, recente):
    """Tabela final mínima (só os 'dados até', todos dentro da tolerância de idade em `recente`) e cargas: (fonte, publicada, carregada_em)."""
    c.execute("CREATE SCHEMA IF NOT EXISTS final")
    c.execute("""CREATE OR REPLACE TABLE final.indicadores_municipio_semana AS SELECT
        CAST(? AS DATE) AS casos_dados_ate, CAST(? AS DATE) AS infodengue_dados_ate,
        CAST(? AS DATE) - 40 AS internacoes_dados_ate, CAST(? AS DATE) - 40 AS leitos_dados_ate""", [recente] * 4)
    for i, (fonte, pub, carga) in enumerate(cargas):
        c.execute("INSERT INTO bronze_loads VALUES (?,?,?,?,?,?,?,?,?)", [fonte, "f%d" % i, "%064x" % i, 0, pub, 10, "x", carga, ""])


def test_frescor_latencia_nao_se_aplica_na_carga_inicial(tmp_path, monkeypatch):
    """Falso positivo visto no 1º fluxo do GitHub: carga do zero de arquivos antigos não é atraso de atualização."""
    import datetime as dt
    monkeypatch.setenv("DENGUE_DATA", str(tmp_path / "data"))
    from dengue_mg import bronze, frescor
    importlib.reload(bronze)
    c = bronze.con()
    carga = dt.datetime(2026, 2, 1, 9, 0)
    _preparar_frescor(c, [("sinan_prelim", dt.date(2026, 1, 10), carga), ("infodengue", dt.date(2026, 2, 1), carga),
                          ("cnes_lt", dt.date(2026, 1, 15), carga), ("sih_rd", dt.date(2026, 1, 5), carga)], recente=dt.date(2026, 1, 28))
    linhas = {l[0]: l for l in frescor.verificar(c, dt.date(2026, 2, 1))}
    # publicado há 22 dias e carregado agora: sem a regra, seria "atrasado" por latência; na carga inicial a latência é nula
    assert linhas["casos_sinan"][7] is None and linhas["casos_sinan"][-1] is True and linhas["casos_sinan"][9] == "ok"
    c.close()


def test_frescor_latencia_vale_depois_da_carga_inicial(tmp_path, monkeypatch):
    import datetime as dt
    monkeypatch.setenv("DENGUE_DATA", str(tmp_path / "data"))
    from dengue_mg import bronze, frescor
    importlib.reload(bronze)
    c = bronze.con()
    inicial = dt.datetime(2026, 2, 1, 9, 0)
    _preparar_frescor(c, [("infodengue", dt.date(2026, 2, 1), inicial), ("cnes_lt", dt.date(2026, 1, 15), inicial), ("sih_rd", dt.date(2026, 1, 5), inicial),
                          ("sinan_prelim", dt.date(2026, 1, 10), inicial),
                          # versão nova do preliminar: publicada em 03/02 e só carregada em 15/02 (12 dias depois)
                          ("sinan_prelim", dt.date(2026, 2, 3), dt.datetime(2026, 2, 15, 9, 0))], recente=dt.date(2026, 2, 10))
    linhas = {l[0]: l for l in frescor.verificar(c, dt.date(2026, 2, 15))}
    assert linhas["casos_sinan"][7] == 12 and linhas["casos_sinan"][-1] is False and linhas["casos_sinan"][9] == "atrasado"
    assert linhas["infodengue"][9] == "ok"   # mesma idade dos dados, mas sem atraso de carga
    c.close()


def test_pipeline_sai_com_zero_quando_tudo_esta_em_dia(banco):
    """Regressão: o código de saída 2 só vale para fonte realmente atrasada (o 2º fluxo do GitHub saiu com 2 por ler a coluna errada)."""
    from dengue_mg import bronze, pipeline, tratada
    importlib.reload(tratada)
    importlib.reload(pipeline)
    # com a data de referência logo depois dos "dados até" sintéticos (17/01), nenhuma fonte passa da tolerância
    assert pipeline.executar([], "2026-01-20", tolerar_atraso=False) == 0
    c = bronze.con()
    assert {r[0] for r in c.execute("SELECT situacao FROM final.frescor").fetchall()} == {"ok"}
    c.close()
    linhas = [json.loads(l) for l in open(os.path.join(bronze.DATA, "logs", "execucoes.jsonl"), encoding="utf-8")]
    frescor = next(l for l in linhas if l["etapa"] == "frescor")
    assert "casos_sinan=ok" in frescor["detalhe"] and "internacoes_sih=ok" in frescor["detalhe"]
