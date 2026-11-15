"""Gera os artefatos de evidência da Sprint 2 em docs/evidencias/: R5 (testes) e R6 (reconciliação).

Uso (depois de `python -m dengue_mg.tratada`):
    python -m dengue_mg.relatorio
"""
import datetime as dt
import json
import os
from typing import Optional

from . import bronze
from .tratada import RAIZ

EVID = os.path.join(RAIZ, "docs", "evidencias")


def relatorio_testes(run_results: Optional[str] = None, saida: Optional[str] = None) -> str:
    """R5: tabela com o resultado de cada teste do dbt (a partir de run_results.json)."""
    run_results = run_results or os.path.join(bronze.DATA, "dbt_target", "run_results.json")
    saida = saida or os.path.join(EVID, "R5", "relatorio_testes.md")
    with open(run_results, encoding="utf-8") as f:
        dados = json.load(f)
    res = [r for r in dados["results"] if r["unique_id"].startswith("test.")]
    cont = {}
    for r in res:
        cont[r["status"]] = cont.get(r["status"], 0) + 1
    linhas = ["# Relatório de execução dos testes (R5)", "",
              "Gerado em %s. Total: %d testes (%s)." % (
                  dt.datetime.now().strftime("%d/%m/%Y %H:%M"), len(res),
                  ", ".join("%s: %d" % kv for kv in sorted(cont.items()))), "",
              "| Teste | Resultado | Linhas com falha |", "|---|---|---|"]
    for r in sorted(res, key=lambda r: (r["status"] == "pass", r["unique_id"])):
        linhas.append("| %s | %s | %s |" % (r["unique_id"].split(".")[2], r["status"], r.get("failures") or 0))
    linhas += ["", "`warn` indica limitação conhecida da fonte (ex.: datas de 2026 no arquivo final de 2025); `fail`/`error` bloqueia a publicação."]
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return saida


def relatorio_reconciliacao(saida: Optional[str] = None, c=None) -> str:
    """R6: resumo da meta e as piores divergências por município e semana (final.rec_*)."""
    saida = saida or os.path.join(EVID, "R6", "relatorio_divergencia.md")
    c = c or bronze.con()
    resumo = c.execute("SELECT * FROM final.rec_resumo ORDER BY recorte").fetchall()
    piores = c.execute("""
        SELECT m.municipio, r.semana_id, r.casos_sinan, r.casos_infodengue, r.divergencia
        FROM final.rec_sinan_infodengue r JOIN tratada.dim_municipio m USING (geocodigo)
        WHERE r.elegivel AND NOT r.dentro_do_limite ORDER BY r.divergencia DESC NULLS LAST, r.casos_sinan DESC LIMIT 30
    """).fetchall()
    por_mun = c.execute("""
        SELECT m.municipio, count(*) AS pares, round(100.0 * avg(CASE WHEN r.dentro_do_limite THEN 1 ELSE 0 END), 1) AS pct_dentro
        FROM final.rec_sinan_infodengue r JOIN tratada.dim_municipio m USING (geocodigo)
        WHERE r.elegivel GROUP BY 1 HAVING count(*) >= 5 ORDER BY pct_dentro, pares DESC LIMIT 20
    """).fetchall()
    L = ["# Reconciliação SINAN x InfoDengue (R6)", "",
         "Gerado em %s. Divergência = |SINAN - InfoDengue| / SINAN. Par elegível: SINAN com 10 casos ou mais e semana com mais de 9 semanas de idade." % dt.datetime.now().strftime("%d/%m/%Y %H:%M"), "",
         "## Meta (90%% dos pares com divergência até %.0f%%)" % (100 * resumo[0][5]), "",
         "| Recorte | Pares elegíveis | Dentro do limite | % dentro | Meta | Mediana da divergência |", "|---|---|---|---|---|---|"]
    for rec, n, ok, pct, meta, _lim, med in resumo:
        L.append("| %s | %d | %d | %s | %.0f%% | %s |" % (
            rec, n, ok, "%.1f%%" % (100 * pct) if pct is not None else "-", 100 * meta,
            "%.1f%%" % (100 * med) if med is not None else "-"))
    sens = c.execute("""
        SELECT lim, round(100.0 * avg((divergencia <= lim)::int), 1),
               round(100.0 * avg((divergencia <= lim)::int) FILTER (WHERE semana_id % 100 BETWEEN 3 AND 47), 1)
        FROM final.rec_sinan_infodengue, (VALUES (0.05), (0.10), (0.15), (0.20)) t(lim) WHERE elegivel GROUP BY lim ORDER BY lim""").fetchall()
    L += ["", "## Sensibilidade ao limite de divergência", "",
          "| Limite | % dos pares dentro | % dentro, sem semanas 1-2 e 48-53 (virada de ano) |", "|---|---|---|"]
    L += ["| %.0f%% | %s | %s |" % (100 * lim, a, b) for lim, a, b in sens]
    L += ["", "Limite calibrado no R6 (ADR-0004): 15%, o menor entre 5%, 10% e 15% que atinge 90% dos pares. As faixas de 5% e 10% ficam como referência.", "",
          "## Municípios com menor aderência (pelo menos 5 pares elegíveis)", "",
          "| Município | Pares | % dentro do limite |", "|---|---|---|"]
    L += ["| %s | %d | %s |" % r for r in por_mun]
    L += ["", "## 30 maiores divergências entre pares elegíveis", "",
          "| Município | Semana | SINAN | InfoDengue | Divergência |", "|---|---|---|---|---|"]
    L += ["| %s | %s | %d | %d | %.1f%% |" % (m, s, a, b, 100 * (d or 0)) for m, s, a, b, d in piores]
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return saida


def main():
    print(relatorio_testes())
    print(relatorio_reconciliacao())


if __name__ == "__main__":
    main()
