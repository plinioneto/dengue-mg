"""Leitura de arquivos .dbc (DBF comprimido em PKWare DCL) do DATASUS, sem dependências nativas.

Formato: cabeçalho DBF (tamanho em bytes 8-9) + 4 bytes + fluxo comprimido (PKWare DCL, o "blast" do zlib).
A descompactação é em fluxo (memória constante), então arquivos grandes não precisam caber na RAM.
Se o pacote opcional `datasus-dbc` estiver instalado, não é usado: a implementação aqui é a referência
(mais lenta, porém sem compilação). Para arquivos nacionais grandes, filtre por UF durante a leitura.
"""
import struct
from typing import Callable, Dict, Iterator, List, Optional

_LIT = [11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8, 9, 7, 6, 7, 8, 7, 6, 55, 8, 23,
        24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5, 7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9,
        12, 8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27, 44, 253, 253, 253, 252, 252,
        252, 13, 12, 45, 12, 45, 12, 61, 12, 45, 44, 173]
_LEN = [2, 35, 36, 53, 38, 23]
_DIST = [2, 20, 53, 230, 247, 151, 248]
_BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]


def _construir(rep, n):
    compr = []
    for b in rep:
        compr.extend([b & 15] * ((b >> 4) + 1))
    assert len(compr) == n
    count = [0] * 16
    for c in compr:
        count[c] += 1
    offs = [0] * 16
    for i in range(1, 15):
        offs[i + 1] = offs[i] + count[i]
    symbol = [0] * n
    for s, c in enumerate(compr):
        if c:
            symbol[offs[c]] = s
            offs[c] += 1
    return count, symbol


_LITCODE, _LENCODE, _DISTCODE = _construir(_LIT, 256), _construir(_LEN, 16), _construir(_DIST, 64)


class _Bits:
    def __init__(self, data, pos):
        self.data, self.pos, self.buf, self.n = data, pos, 0, 0

    def bits(self, need):
        val = self.buf
        while self.n < need:
            val |= self.data[self.pos] << self.n
            self.pos += 1
            self.n += 8
        self.buf = val >> need
        self.n -= need
        return val & ((1 << need) - 1)

    def decode(self, tabela):
        count, symbol = tabela
        code = first = index = 0
        for compr in range(1, 14):
            code |= self.bits(1) ^ 1
            c = count[compr]
            if code < first + c:
                return symbol[index + (code - first)]
            index += c
            first += c
            first <<= 1
            code <<= 1
        raise ValueError("código inválido")


def blast_stream(data: bytes, pos: int = 0, chunk: int = 1 << 20, janela: int = 4096) -> Iterator[bytes]:
    """Descompacta PKWare DCL em blocos de ~`chunk` bytes."""
    b = _Bits(data, pos)
    lit, dic = b.bits(8), b.bits(8)
    if lit > 1 or dic < 4 or dic > 6:
        raise ValueError("cabeçalho PKWare inválido")
    out = bytearray()
    # `janela` deve ser >= distância máxima possível (4096 com dicionário de 6 bits)
    try:
        while True:
            if b.bits(1):
                s = b.decode(_LENCODE)
                ln = _BASE[s] + b.bits(_EXTRA[s])
                if ln == 519:
                    break
                sh = 2 if ln == 2 else dic
                dist = (b.decode(_DISTCODE) << sh) + b.bits(sh) + 1
                if dist > len(out):
                    raise ValueError("distância inválida")
                for _ in range(ln):
                    out.append(out[-dist])
            else:
                out.append(b.decode(_LITCODE) if lit else b.bits(8))
            if len(out) >= chunk + janela:
                yield bytes(out[:-janela])
                del out[:-janela]
    except IndexError:
        pass  # fim dos dados
    if out:
        yield bytes(out)


def blast(data: bytes, pos: int = 0) -> bytes:
    return b"".join(blast_stream(data, pos))


def _cabecalho(cab: bytes):
    n_total, hsize, rsize = struct.unpack("<IHH", cab[4:12])
    campos, off, i = [], 1, 32
    while cab[i] != 0x0D:
        nome = cab[i:i + 11].split(b"\x00")[0].decode("latin-1")
        tam = cab[i + 16]
        campos.append((nome, off, tam))
        off += tam
        i += 32
    return n_total, hsize, rsize, campos


def ler_registros(caminho: str, filtro: Optional[Callable[[Dict[str, str]], bool]] = None,
                  tamanho_lote: int = 50000) -> Iterator[tuple]:
    """Lê .dbc ou .dbf e devolve (colunas, lote) onde lote é lista de listas de str (texto cru, strip).

    `filtro` recebe um dict {coluna: valor} e decide se o registro entra no lote.
    """
    raw = open(caminho, "rb").read()
    n_total, hsize, rsize, campos = _cabecalho(raw[:max(32, struct.unpack("<H", raw[8:10])[0])])
    nomes = [c[0] for c in campos]
    if caminho.lower().endswith(".dbc"):
        fluxo = blast_stream(raw, hsize + 4)
    else:
        fluxo = iter([raw[hsize:]])
    buf, lido, lote = b"", 0, []
    for bloco in fluxo:
        buf += bloco
        n = len(buf) // rsize
        for r in range(n):
            if lido >= n_total:
                break
            reg = buf[r * rsize:(r + 1) * rsize]
            lido += 1
            vals = [reg[o:o + t].decode("latin-1").strip() for _, o, t in campos]
            if filtro is None or filtro(dict(zip(nomes, vals))):
                lote.append(vals)
                if len(lote) >= tamanho_lote:
                    yield nomes, lote
                    lote = []
        buf = buf[n * rsize:]
    if lote:
        yield nomes, lote
