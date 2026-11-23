"""R10: consultas do painel e execução do app Streamlit sobre a tabela final sintética."""
import importlib
import os

import pytest

pytest.importorskip("dbt.cli.main")
pytest.importorskip("streamlit")

HOJE = "2026-03-01"


@pytest.fixture()
def final(banco):
    from dengue_mg import bronze, pipeline, tratada
    importlib.reload(tratada)
    importlib.reload(pipeline)
    assert pipeline.executar([], HOJE, tolerar_atraso=True) == 0
    return banco


def test_consultas(final):
    from dengue_mg import bronze, consulta
    c = bronze.con()
    assert consulta.regioes(c) and len(consulta.municipios(c)) == 853
    serie = consulta.serie(c, 202601, 202601, geocodigo="3100000")
    assert serie[0]["casos_notificados"] == 2 and serie[0]["internacoes"] == 2 and serie[0]["pressao_internacoes_por_leito"] == pytest.approx(0.2)
    # estado: soma dos municípios; a pressão é a razão das somas (2 internações / 10 leitos)
    estado = consulta.serie(c, 202601, 202601)[0]
    assert estado["internacoes"] == 2 and estado["leitos_clinicos_pediatricos"] == 10 and estado["pressao_internacoes_por_leito"] == pytest.approx(0.2)
    # depois do "dados até" do SIH o valor é nulo
    assert consulta.serie(c, 202608, 202608)[0]["pressao_internacoes_por_leito"] is None
    # municípios mais afetados: só o município 0 tem pressão conhecida (0,2); o de 202602 é incompleto no SIH
    r = consulta.mais_afetados(c, 202601, 202602, "pressao_pico")
    assert [x["municipio"] for x in r] == ["Município 0"]
    assert r[0]["pressao_pico"] == pytest.approx(0.2) and r[0]["internacoes"] == 2 and r[0]["leitos"] == 10 and r[0]["semana_do_pico"] == 202601
    # critério de casos: os dois municípios com casos; o piso de internações só vale para pressão
    casos = consulta.mais_afetados(c, 202601, 202602, "casos")
    assert [(x["municipio"], x["casos"]) for x in casos] == [("Município 0", 2), ("Município 2", 1)]
    # piso de internações elimina o município com poucas internações no critério de pressão
    assert consulta.mais_afetados(c, 202601, 202602, "pressao_media", minimo_internacoes=3) == []
    with pytest.raises(ValueError):
        consulta.mais_afetados(c, 202601, 202602, "inexistente")
    assert {f["indicador"] for f in consulta.frescor(c)} == {"casos_sinan", "infodengue", "leitos_cnes", "internacoes_sih"}
    c.close()


def test_app_executa_sem_erro(final, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("DENGUE_DATA", str(final / "data"))
    app = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "painel.py")
    at = AppTest.from_file(app, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    assert "Pressão da dengue" in at.title[0].value
    assert any("Dados até" in c.value for c in at.caption)
    # ajuda: a explicação do indicador de pressão está no painel (popover) e traz a fórmula
    assert any("internações por dengue na semana ÷ leitos clínicos e pediátricos" in m.value for m in at.markdown)

    # ranking com o piso de internações em 0: o município 0 aparece (gráfico e tabela renderizam sem erro)
    at.number_input[0].set_value(0).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Município 0" in df.value.to_string() for df in at.dataframe)


def test_relatorio_de_hipoteses_com_o_fluxo_publicado(final, tmp_path):
    """Ponta a ponta: o pipeline publica o fluxo agregado e o relatório de hipóteses (H1, H2 parcial e H3) o lê."""
    from dengue_mg import consulta, hipoteses
    c = consulta.abrir(str(final / "data" / "publicacao"))
    txt = open(hipoteses.relatorio(c, str(tmp_path / "h.md")), encoding="utf-8").read()
    c.close()
    assert "## H3: a capacidade relevante depende da região de saúde?" in txt
    assert "mesmo município" in txt and "Total" in txt
    # fluxo sintético: 3 internações; 2 no próprio município de residência e 1 de residente do município 0 internado no município 2
    assert "| Total | 3 | 2 | 1 |" in txt
