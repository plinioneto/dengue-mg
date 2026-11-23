"""R9: atualização completa e agendável. Ingestão incremental, camada tratada e final (dbt, com testes), revisão do SINAN e frescor.

Uso (a partir da pasta do projeto):
    python -m dengue_mg.pipeline                       # tudo
    python -m dengue_mg.pipeline --sem-ingestao        # só reprocessa tratada/final
    python -m dengue_mg.pipeline --tolerar-atraso      # fonte atrasada não derruba o código de saída

Cada etapa é registrada em `data/logs/execucoes.jsonl` e na tabela `execucoes` do DuckDB. Código de saída: 0 tudo certo;
1 etapa falhou (a ingestão de uma fonte não impede as demais; testes do dbt reprovados bloqueiam a revisão e o frescor);
2 fonte atrasada em relação à tolerância.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import traceback
import uuid
from typing import Callable, List, Optional

from . import bronze

FONTES = ["ibge", "cnes_lt", "sih_rd", "sinan_final", "sinan_prelim", "infodengue"]  # ibge antes de infodengue (geocodigo)


def _registrar(execucao: str, etapa: str, status: str, inicio: float, detalhe: str = "") -> None:
    ev = dict(execucao=execucao, etapa=etapa, status=status, inicio=dt.datetime.fromtimestamp(inicio).isoformat(timespec="seconds"),
              duracao_s=round(time.time() - inicio, 1), detalhe=detalhe[:2000])
    pasta = os.path.join(bronze.DATA, "logs")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "execucoes.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    c = bronze.con()
    c.execute("CREATE TABLE IF NOT EXISTS execucoes (execucao VARCHAR, etapa VARCHAR, status VARCHAR, inicio TIMESTAMP, duracao_s DOUBLE, detalhe VARCHAR)")
    c.execute("INSERT INTO execucoes VALUES (?,?,?,?,?,?)", [ev["execucao"], etapa, status, ev["inicio"], ev["duracao_s"], ev["detalhe"]])
    c.close()
    print("[%s] %s: %s %s" % (status.upper(), etapa, "%.0fs" % ev["duracao_s"], detalhe[:200]))


def _etapa(execucao: str, nome: str, fn: Callable[[], Optional[str]]) -> bool:
    t0 = time.time()
    try:
        detalhe = fn() or ""
        _registrar(execucao, nome, "ok", t0, detalhe)
        return True
    except BaseException as e:  # noqa: BLE001  (o log precisa registrar até SystemExit de uma fonte)
        if isinstance(e, KeyboardInterrupt):
            raise
        _registrar(execucao, nome, "erro", t0, "%s: %s | %s" % (type(e).__name__, e, traceback.format_exc().splitlines()[-3:]))
        return False


def executar(fontes: List[str], hoje: Optional[str] = None, tolerar_atraso: bool = False) -> int:
    from . import frescor, ingest, revisao, tratada
    execucao = dt.datetime.now().strftime("%Y%m%dT%H%M%S-") + uuid.uuid4().hex[:6]
    print("Execução %s" % execucao)
    ok = True
    for f in fontes:
        ok &= _etapa(execucao, "ingestao:" + f, lambda f=f: ingest.main([f]))
    # a tratada roda mesmo com falha em uma fonte (usa a última versão carregada); mas só publica se os testes passarem
    if not _etapa(execucao, "tratada_e_final", lambda: _dbt(tratada, hoje)):
        return 1
    ok &= _etapa(execucao, "revisao_sinan", lambda: _revisao(revisao))
    atrasadas: list = []
    ok &= _etapa(execucao, "frescor", lambda: _frescor(frescor, hoje, atrasadas))
    ok &= _etapa(execucao, "publicacao", _publicar)
    if atrasadas and not tolerar_atraso:
        return 2 if ok else 1
    return 0 if ok else 1


def _dbt(tratada, hoje):
    if tratada.executar(hoje) != 0:
        raise RuntimeError("dbt (seed, run ou test) falhou; ver data/dbt_logs")
    return "seed, run e test aprovados"


def _revisao(revisao):
    c = bronze.con()
    try:
        n = revisao.calcular(c)
        return "%d versões; relatório %s" % (n, revisao.relatorio(c))
    finally:
        c.close()


def _publicar():
    """Parquet que alimentam o painel (data/publicacao); só depois dos testes e do frescor."""
    from . import consulta
    c = bronze.con()
    try:
        return ", ".join(os.path.basename(a) for a in consulta.publicar(c, os.path.join(bronze.DATA, "publicacao")))
    finally:
        c.close()


def _frescor(frescor, hoje, atrasadas):
    c = bronze.con()
    try:
        linhas = frescor.verificar(c, dt.date.fromisoformat(hoje) if hoje else None)
    finally:
        c.close()
    atrasadas.extend(l[0] for l in linhas if l[-2] != "ok")
    return "; ".join("%s=%s (dados até %s)" % (l[0], l[-2], l[2]) for l in linhas)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--sem-ingestao", action="store_true")
    p.add_argument("--fontes", nargs="*", default=FONTES)
    p.add_argument("--hoje", help="data de referência AAAA-MM-DD")
    p.add_argument("--tolerar-atraso", action="store_true")
    a = p.parse_args(argv)
    sys.exit(executar([] if a.sem_ingestao else a.fontes, a.hoje, a.tolerar_atraso))


if __name__ == "__main__":
    main()
