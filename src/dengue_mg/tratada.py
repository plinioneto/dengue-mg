"""Camada tratada e reconciliação: executa o projeto dbt (seed, run, test) sobre a bruta e guarda os resultados.

Uso (a partir da pasta do projeto):
    python -m dengue_mg.tratada                 # seed + run + test
    python -m dengue_mg.tratada --so-rodar      # sem testes
    python -m dengue_mg.tratada --hoje 2026-11-15   # data de referência fixa (reprodutível)
"""
import argparse
import json
import os
import sys
from typing import List, Optional

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJETO_DBT = os.path.join(RAIZ, "dbt")


def preparar_ambiente(data: Optional[str] = None) -> None:
    """Aponta o dbt para o mesmo `data/` da ingestão; caminhos relativos da bruta valem a partir da pasta atual."""
    os.environ["DENGUE_CWD"] = os.getcwd()
    os.environ["DENGUE_DATA"] = os.path.abspath(data or os.environ.get("DENGUE_DATA", "data"))


def dbt(args: List[str], hoje: Optional[str] = None):
    from dbt.cli.main import dbtRunner
    extra = ["--project-dir", PROJETO_DBT, "--profiles-dir", PROJETO_DBT]
    if hoje:
        extra += ["--vars", json.dumps({"data_referencia": hoje})]
    return dbtRunner().invoke(args + extra)


def executar(hoje: Optional[str] = None, testar: bool = True) -> int:
    preparar_ambiente()
    ok = True
    for etapa in (["seed"], ["run"]) + ([["test"]] if testar else []):
        res = dbt(etapa, hoje)
        ok = ok and res.success
        if not res.success and etapa[0] != "test":
            break  # sem tratada não há o que testar
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--so-rodar", action="store_true", help="não executa os testes")
    p.add_argument("--hoje", help="data de referência AAAA-MM-DD (padrão: hoje)")
    a = p.parse_args(argv)
    sys.exit(executar(a.hoje, not a.so_rodar))


if __name__ == "__main__":
    main()
