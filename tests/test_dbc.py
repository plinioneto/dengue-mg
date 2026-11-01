import struct
from dengue_mg import dbc

VETOR = bytes([0x00, 0x04, 0x82, 0x24, 0x25, 0x8F, 0x80, 0x7F])  # vetor do zlib/blast.c -> "AIAIAIAIAIAIA"


def test_blast_vetor_zlib():
    assert dbc.blast(VETOR) == b"AIAIAIAIAIAIA"


def test_blast_stream_em_blocos_pequenos_igual_ao_inteiro():
    blocos = list(dbc.blast_stream(VETOR, chunk=1, janela=4))
    assert len(blocos) > 1
    assert b"".join(blocos) == b"AIAIAIAIAIAIA"


def _dbf(registros, campos=(("SG_UF_NOT", 2), ("ID_MUNICIP", 6))):
    hsize = 32 + 32 * len(campos) + 1
    rsize = 1 + sum(t for _, t in campos)
    cab = bytearray(32)
    cab[0] = 3
    struct.pack_into("<IHH", cab, 4, len(registros), hsize, rsize)
    for nome, tam in campos:
        d = bytearray(32)
        d[:len(nome)] = nome.encode()
        d[11] = ord("C")
        d[16] = tam
        cab += d
    cab += b"\x0d"
    corpo = b"".join(b" " + b"".join(v.ljust(t).encode("latin-1") for v, (_, t) in zip(r, campos)) for r in registros)
    return bytes(cab) + corpo + b"\x1a"


def test_ler_dbf_com_filtro(tmp_path):
    f = tmp_path / "x.dbf"
    f.write_bytes(_dbf([("31", "310620"), ("35", "355030"), ("31", "317010")]))
    lotes = list(dbc.ler_registros(str(f), filtro=lambda r: r["SG_UF_NOT"] == "31"))
    assert lotes[0][0] == ["SG_UF_NOT", "ID_MUNICIP"]
    assert lotes[0][1] == [["31", "310620"], ["31", "317010"]]


def test_ler_dbf_sem_filtro_em_lotes(tmp_path):
    f = tmp_path / "x.dbf"
    f.write_bytes(_dbf([("31", "%06d" % i) for i in range(25)]))
    lotes = list(dbc.ler_registros(str(f), tamanho_lote=10))
    assert [len(l[1]) for l in lotes] == [10, 10, 5]
