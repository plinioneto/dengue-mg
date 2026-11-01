"""Ingestão incremental para a camada bruta.

Uso:
    python -m dengue_mg.ingest sinan_prelim sinan_final cnes_lt sih_rd infodengue ibge
    python -m dengue_mg.ingest --lista          # só mostra o que há para carregar
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time

from . import bronze, dbc, ftp
from .sources import ANO_INICIAL, FTP_FONTES


def selecionar(fonte: str, itens):
    """Mantém arquivos de 2022 em diante (SINAN: DENGBR22+; CNES/SIH: AAMM com AA>=22)."""
    cfg = FTP_FONTES[fonte]
    out = []
    for nome, mod, tam in itens:
        g = re.match(cfg["padrao"], nome).group(1)
        if 2000 + int(g[:2]) >= ANO_INICIAL:
            out.append((nome, mod, tam))
    return out


def ingerir_ftp(fonte: str, so_listar: bool = False):
    cfg = FTP_FONTES[fonte]
    c = bronze.con()
    itens = selecionar(fonte, ftp.listar(cfg["pasta"], cfg["padrao"]))
    for nome, mod, tam in itens:
        if bronze.remoto_inalterado(c, fonte, nome, tam, mod):
            print("[=] %s %s: sem mudança no servidor (%s, %d bytes)" % (fonte, nome, mod, tam))
            continue
        if so_listar:
            print("[+] %s %s: a carregar (%s, %d bytes)" % (fonte, nome, mod, tam))
            continue
        local = ftp.baixar(cfg["pasta"], nome, os.path.join(bronze.DATA, "download", fonte))
        sha = bronze.sha256_arquivo(local)
        t0 = time.time()
        destino = bronze.gravar(c, fonte, nome, sha, dbc.ler_registros(local, cfg["filtro"]), tam, mod)
        if destino is None:
            # conteúdo igual ao já carregado (data/tamanho mudaram, mas o hash não): registra o novo carimbo
            c.execute("UPDATE bronze_loads SET remote_size=?, remote_published=? WHERE source=? AND file_name=? AND sha256=?",
                      [tam, mod, fonte, nome, sha])
            print("[=] %s %s: conteúdo idêntico (hash)" % (fonte, nome))
        else:
            n = c.execute("SELECT rows FROM bronze_loads WHERE parquet_path=?", [destino]).fetchone()[0]
            print("[+] %s %s: %d linhas em %.0fs -> %s" % (fonte, nome, n, time.time() - t0, destino))
        os.remove(local)  # o .dbc bruto não é guardado; o Parquet e o hash ficam registrados
    c.close()


def ingerir_ibge():
    """Municípios de MG com código IBGE de 7 dígitos e região de saúde não disponível aqui (ver catálogo)."""
    import requests
    r = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios", timeout=60)
    r.raise_for_status()
    dados = r.json()
    linhas = [[str(d["id"]), d["nome"], d["microrregiao"]["nome"], d["microrregiao"]["mesorregiao"]["nome"]] for d in dados]
    c = bronze.con()
    corpo = json.dumps(dados, sort_keys=True).encode()
    import hashlib
    sha = hashlib.sha256(corpo).hexdigest()
    destino = bronze.gravar(c, "ibge_municipios", "municipios_mg.json", sha,
                            [(["geocodigo", "nome", "microrregiao", "mesorregiao"], linhas)], len(corpo), dt.date.today())
    print("[+] ibge: %d municípios" % len(linhas) if destino else "[=] ibge: sem mudança")
    c.close()


def ingerir_infodengue(pausa: float = 0.3):
    """InfoDengue alertcity para cada município de MG, de 2022 até hoje. Acrescenta o geocódigo à resposta."""
    import hashlib
    import requests
    c = bronze.con()
    muns = c.execute("""SELECT geocodigo FROM read_parquet(?)""",
                     [c.execute("SELECT parquet_path FROM bronze_loads WHERE source='ibge_municipios' "
                                "ORDER BY loaded_at DESC LIMIT 1").fetchone()[0]]).fetchall()
    ano = dt.date.today().year
    linhas, cols = [], None
    for (g,) in muns:
        for tentativa in range(3):
            try:
                r = requests.get("https://info.dengue.mat.br/api/alertcity",
                                 params=dict(geocode=g, disease="dengue", format="json", ew_start=1, ew_end=53,
                                             ey_start=ANO_INICIAL, ey_end=ano), timeout=90)
                r.raise_for_status()
                break
            except Exception as e:
                if tentativa == 2:
                    print("[!] infodengue %s: %s" % (g, e))
                    r = None
                time.sleep(2 * (tentativa + 1))
        if r is None:
            continue
        for d in r.json():
            d = {k: ("" if v is None else str(v)) for k, v in d.items()}
            d["geocodigo"] = str(g)
            cols = cols or sorted(d)
            linhas.append([d.get(k, "") for k in cols])
        time.sleep(pausa)
    if not linhas:
        print("[!] infodengue: nenhuma linha")
        return
    sha = hashlib.sha256(json.dumps(linhas, sort_keys=True).encode()).hexdigest()
    destino = bronze.gravar(c, "infodengue", "alertcity_mg_%s.json" % dt.date.today().isoformat(), sha,
                            [(cols, linhas)], 0, dt.date.today())
    print("[+] infodengue: %d linhas" % len(linhas) if destino else "[=] infodengue: sem mudança")
    c.close()


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("fontes", nargs="*", help="sinan_prelim sinan_final cnes_lt sih_rd ibge infodengue")
    p.add_argument("--lista", action="store_true", help="só lista o que seria carregado")
    a = p.parse_args(argv)
    for f in a.fontes:
        if f in FTP_FONTES:
            ingerir_ftp(f, a.lista)
        elif f == "ibge":
            ingerir_ibge()
        elif f == "infodengue":
            ingerir_infodengue()
        else:
            sys.exit("fonte desconhecida: " + f)


if __name__ == "__main__":
    main()
