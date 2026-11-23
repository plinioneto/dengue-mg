"""Fixtures compartilhadas: bruta sintética mínima para exercitar a tratada, a final e o pipeline."""
import importlib

import pytest

pytest.importorskip("duckdb")

def _carregar(bronze, c, fonte, nome, colunas, linhas):
    bronze.gravar(c, fonte, nome, "%064x" % abs(hash((fonte, nome))), [(colunas, linhas)])


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGUE_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("DENGUE_EVIDENCIAS", str(tmp_path / "evidencias"))  # relatórios de teste não vão para docs/evidencias
    from dengue_mg import bronze
    importlib.reload(bronze)
    c = bronze.con()
    # 853 municípios sintéticos (código de 7 dígitos; o 6 primeiros são o código do SINAN/CNES/SIH)
    muns = [["%06d0" % (310000 + i), "Município %d" % i, "Micro", "Meso"] for i in range(853)]
    _carregar(bronze, c, "ibge_municipios", "municipios_mg.json", ["geocodigo", "nome", "microrregiao", "mesorregiao"], muns)
    cod = "310000"  # primeiro município
    sinan_cols = ["ID_MUNICIP", "ID_MN_RESI", "DT_NOTIFIC", "DT_SIN_PRI", "CLASSI_FIN", "EVOLUCAO", "HOSPITALIZ"]
    # semana 202601 (04/01 a 10/01): 3 notificações, 1 descartada
    final = [[cod, cod, "20260105", "20260104", "10", "1", "1"],
             [cod, cod, "20260106", "20260104", "5", "", "2"],   # descartado
             [cod, cod, "20260107", "20260105", "11", "1", "2"],  # sem duplicata
             ["310002", "310002", "20260117", "20260117", "10", "1", "2"]]  # sábado que fecha a semana 202602
    _carregar(bronze, c, "sinan_final", "DENGBR26.dbc", sinan_cols, final)
    # preliminar do mesmo ano não deve entrar (já há final)
    _carregar(bronze, c, "sinan_prelim", "DENGBR26.dbc", sinan_cols, [[cod, cod, "20260108", "", "10", "", "2"]])
    _carregar(bronze, c, "sinan_prelim", "DENGBR25.dbc", sinan_cols, [[cod, cod, "20251231", "", "10", "", "2"]])
    _carregar(bronze, c, "cnes_lt", "LTMG2601.dbc", ["CNES", "CODUFMUN", "COMPETEN", "TP_LEITO", "CODLEITO", "QT_EXIST", "QT_CONTR", "QT_SUS"],
              [["100", cod, "202601", "2", "33", "10", "10", "8"], ["100", cod, "202601", "7", "1", "5", "5", "5"]])
    _carregar(bronze, c, "sih_rd", "RDMG2601.dbc", ["N_AIH", "MUNIC_MOV", "MUNIC_RES", "DT_INTER", "DT_SAIDA", "DIAG_PRINC", "MORTE", "DIAS_PERM"],
              [["a1", cod, cod, "20260106", "20260110", "A90", "0", "4"], ["a2", cod, cod, "20260107", "20260112", "A91", "1", "5"],
               # quarta 14/01: o "dados até" do SIH cai no meio da semana 202602, que fica incompleta; residente do município 0 internado no município 2
               ["a3", "310002", "310000", "20260114", "20260115", "A90", "0", "1"]])
    _carregar(bronze, c, "infodengue", "alertcity_mg_2026-02-01.json", ["SE", "casos", "casprov", "casos_est", "nivel", "geocodigo"],
              [["202601", "4", "2", "2.5", "1", muns[0][0]]])
    c.close()
    return tmp_path
