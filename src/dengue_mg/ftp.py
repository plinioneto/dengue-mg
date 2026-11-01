import datetime as dt
import ftplib
import os
import re
from typing import List, Tuple

from .sources import HOST

MESES = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def listar(pasta: str, padrao: str) -> List[Tuple[str, dt.date, int]]:
    """Lista (arquivo, data de publicação, tamanho) que casam com `padrao`. Data = modificação no FTP."""
    hoje = dt.date.today()
    ftp = ftplib.FTP(HOST, timeout=60)
    ftp.login()
    ftp.cwd(pasta)
    linhas = []
    ftp.retrlines("LIST", linhas.append)
    itens = []
    for linha in linhas:
        nome = linha.split()[-1]
        if not re.match(padrao, nome):
            continue
        mod, tam = None, 0
        m = re.match(r"(\d\d)-(\d\d)-(\d\d,?\d{0,2})\s+\S+\s+(\d+)\s+", linha)  # formato IIS
        if m:
            a = int(m.group(3)[:2])
            mod, tam = dt.date(2000 + a if a < 70 else 1900 + a, int(m.group(1)), int(m.group(2))), int(m.group(4))
        else:
            p = linha.split()
            if len(p) >= 9 and p[5] in MESES:  # formato Unix
                tam, dia = int(p[4]), int(p[6])
                if ":" in p[7]:
                    mod = dt.date(hoje.year, MESES[p[5]], dia)
                    if mod > hoje:
                        mod = dt.date(hoje.year - 1, MESES[p[5]], dia)
                else:
                    mod = dt.date(int(p[7]), MESES[p[5]], dia)
        if mod is None:
            try:
                mod = dt.datetime.strptime(ftp.sendcmd("MDTM " + nome).split()[1][:8], "%Y%m%d").date()
            except Exception:
                continue
        itens.append((nome, mod, tam))
    ftp.quit()
    return sorted(itens)


def baixar(pasta: str, nome: str, destino_dir: str) -> str:
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, nome)
    ftp = ftplib.FTP(HOST, timeout=120)
    ftp.login()
    ftp.cwd(pasta)
    with open(destino + ".part", "wb") as f:
        ftp.retrbinary("RETR " + nome, f.write)
    ftp.quit()
    os.replace(destino + ".part", destino)
    return destino
