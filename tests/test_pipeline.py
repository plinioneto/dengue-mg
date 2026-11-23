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
