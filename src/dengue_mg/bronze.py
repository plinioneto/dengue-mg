"""Camada bruta: grava Parquet (tudo como texto, como veio da fonte) e registra cada carga em `bronze_loads`.

Idempotência: a chave é (fonte, arquivo, sha256). Reexecutar com o mesmo conteúdo não grava nada novo.
Versionamento: se o arquivo mudou (ex.: SINAN preliminar), uma nova versão é gravada, e a anterior é mantida
(`data/bronze/<fonte>/<arquivo>__<sha8>.parquet`). Isso permite medir a revisão das semanas preliminares (R8).
"""
import datetime as dt
import hashlib
import os
from typing import Iterable, Optional

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

DATA = os.environ.get("DENGUE_DATA", "data")
DB = os.path.join(DATA, "plataforma.duckdb")

DDL = """
CREATE TABLE IF NOT EXISTS bronze_loads (
    source VARCHAR, file_name VARCHAR, sha256 VARCHAR, remote_size BIGINT, remote_published DATE,
    rows BIGINT, parquet_path VARCHAR, loaded_at TIMESTAMP, note VARCHAR
)"""


def con():
    os.makedirs(DATA, exist_ok=True)
    c = duckdb.connect(DB)
    c.execute(DDL)
    return c


def sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ja_carregado(c, source: str, file_name: str, sha: str) -> bool:
    return c.execute("SELECT count(*) FROM bronze_loads WHERE source=? AND file_name=? AND sha256=?",
                     [source, file_name, sha]).fetchone()[0] > 0


def remoto_inalterado(c, source: str, file_name: str, size: int, published: Optional[dt.date]) -> bool:
    """Evita baixar de novo quando tamanho e data de publicação são os da última carga."""
    return c.execute("SELECT count(*) FROM bronze_loads WHERE source=? AND file_name=? AND remote_size=? "
                     "AND remote_published IS NOT DISTINCT FROM ?", [source, file_name, size, published]).fetchone()[0] > 0


def gravar(c, source: str, file_name: str, sha: str, lotes: Iterable[tuple], remote_size: int = 0,
           remote_published: Optional[dt.date] = None, note: str = "") -> Optional[str]:
    """Grava os lotes (colunas, linhas) em Parquet e registra a carga. Retorna o caminho ou None se já existia."""
    if ja_carregado(c, source, file_name, sha):
        return None
    pasta = os.path.join(DATA, "bronze", source)
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, "%s__%s.parquet" % (os.path.splitext(file_name)[0], sha[:8]))
    tmp = destino + ".tmp"
    writer, total = None, 0
    for colunas, linhas in lotes:
        tabela = pa.table({k: pa.array([l[i] for l in linhas], type=pa.string()) for i, k in enumerate(colunas)})
        if writer is None:
            writer = pq.ParquetWriter(tmp, tabela.schema)
        writer.write_table(tabela)
        total += len(linhas)
    if writer is None:  # nenhum registro passou no filtro: grava arquivo vazio com 0 linhas
        pq.write_table(pa.table({"_vazio": pa.array([], type=pa.string())}), tmp)
    else:
        writer.close()
    os.replace(tmp, destino)  # só aparece o arquivo completo
    c.execute("INSERT INTO bronze_loads VALUES (?,?,?,?,?,?,?,?,?)",
              [source, file_name, sha, remote_size, remote_published, total, destino, dt.datetime.now(), note])
    return destino
