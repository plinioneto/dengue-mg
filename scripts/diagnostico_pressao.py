"""Diagnóstico do indicador de pressão: mostra de onde vêm os valores máximos e se a ordem de grandeza é plausível.

Uso (a partir da pasta do projeto, depois de `python -m dengue_mg.pipeline`):
    PYTHONPATH=src python scripts/diagnostico_pressao.py
Lê só `data/publicacao/*.parquet`.
"""
import os

from dengue_mg import consulta

pasta = os.path.join(os.environ.get("DENGUE_DATA", "data"), "publicacao")
c = consulta.abrir(pasta)
T = "final.indicadores_municipio_semana"


def mostrar(titulo, sql):
    print("\n== " + titulo)
    cur = c.execute(sql)
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    for r in cur.fetchall():
        print(" | ".join("-" if v is None else (("%.4f" % v) if isinstance(v, float) else str(v)) for v in r))


mostrar("1. Estado: 5 semanas de maior pressão (razão das somas)", f"""
    SELECT semana_id, sum(internacoes) AS internacoes, sum(leitos_clinicos_pediatricos) AS leitos,
           sum(internacoes) * 1.0 / nullif(sum(leitos_clinicos_pediatricos), 0) AS pressao
    FROM {T} GROUP BY semana_id HAVING sum(internacoes) IS NOT NULL ORDER BY pressao DESC NULLS LAST LIMIT 5""")

mostrar("2. Estado: as 5 últimas semanas com pressão conhecida", f"""
    SELECT semana_id, sum(internacoes) AS internacoes, sum(leitos_clinicos_pediatricos) AS leitos,
           sum(internacoes) * 1.0 / nullif(sum(leitos_clinicos_pediatricos), 0) AS pressao
    FROM {T} GROUP BY semana_id HAVING sum(internacoes) IS NOT NULL ORDER BY semana_id DESC LIMIT 5""")

mostrar("3. Município-semana: 10 maiores pressões em todo o período", f"""
    SELECT municipio, semana_id, internacoes, leitos_clinicos_pediatricos AS leitos, pressao_internacoes_por_leito AS pressao
    FROM {T} WHERE pressao_internacoes_por_leito IS NOT NULL ORDER BY pressao DESC, internacoes DESC LIMIT 10""")

mostrar("4. Distribuição da pressão (município-semana com pressão conhecida e ao menos 1 internação)", f"""
    SELECT count(*) AS n, quantile_cont(pressao_internacoes_por_leito, 0.5) AS mediana,
           quantile_cont(pressao_internacoes_por_leito, 0.9) AS p90, quantile_cont(pressao_internacoes_por_leito, 0.99) AS p99,
           max(pressao_internacoes_por_leito) AS maximo
    FROM {T} WHERE pressao_internacoes_por_leito IS NOT NULL AND internacoes > 0""")

mostrar("5. Escala do denominador: leitos clínicos e pediátricos no estado, por competência usada", f"""
    SELECT leitos_competencia, sum(leitos_clinicos_pediatricos) AS leitos_cp, sum(leitos_existentes) AS leitos_total
    FROM (SELECT DISTINCT geocodigo, leitos_competencia, leitos_clinicos_pediatricos, leitos_existentes FROM {T} WHERE leitos_competencia IS NOT NULL)
    GROUP BY leitos_competencia ORDER BY leitos_competencia DESC LIMIT 4""")

mostrar("6. Internações por ano no estado (SIH, dengue)", f"""
    SELECT epi_ano, sum(internacoes) AS internacoes FROM {T} GROUP BY epi_ano ORDER BY epi_ano""")
