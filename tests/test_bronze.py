import importlib
import struct

from test_dbc import _dbf


def test_idempotencia_e_versionamento(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGUE_DATA", str(tmp_path / "data"))
    from dengue_mg import bronze, dbc
    importlib.reload(bronze)
    f = tmp_path / "DENGBR26.dbf"
    f.write_bytes(_dbf([("31", "310620"), ("31", "317010")]))
    c = bronze.con()
    sha = bronze.sha256_arquivo(str(f))
    assert bronze.gravar(c, "sinan_prelim", "DENGBR26.dbf", sha, dbc.ler_registros(str(f))) is not None
    # mesma carga de novo: não grava
    assert bronze.gravar(c, "sinan_prelim", "DENGBR26.dbf", sha, dbc.ler_registros(str(f))) is None
    assert c.execute("SELECT count(*) FROM bronze_loads").fetchone()[0] == 1
    # arquivo mudou (semana preliminar revisada): nova versão, a anterior é mantida
    f.write_bytes(_dbf([("31", "310620"), ("31", "317010"), ("31", "313670")]))
    sha2 = bronze.sha256_arquivo(str(f))
    assert bronze.gravar(c, "sinan_prelim", "DENGBR26.dbf", sha2, dbc.ler_registros(str(f))) is not None
    assert [r[0] for r in c.execute("SELECT rows FROM bronze_loads ORDER BY loaded_at").fetchall()] == [2, 3]
