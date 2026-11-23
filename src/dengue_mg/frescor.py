"""R9: monitoramento de frescor. Compara o "dados até" de cada indicador e a latência de atualização com as tolerâncias de cada fonte.

Tolerâncias (dias) derivadas da periodicidade medida em 25/10/2026 (`CLAUDE.md`, `docs/catalogo_fontes.md`), com margem:
- SINAN preliminar: atualizado a cada 1 a 6 dias; a maior data de notificação ficava 7 dias atrás -> 14.
- InfoDengue: semanal; "dados até" é o fim da última semana carregada -> 14.
- CNES: mensal, publicado em meados do mês seguinte; "dados até" é o primeiro dia da competência -> 75.
- SIH: mensal, cerca de 2 meses de atraso -> 90.
Meta do objetivo: atualizar em até 7 dias após cada publicação da fonte (`LIMITE_LATENCIA`), medida em `bronze_loads`.
"""
import datetime as dt
from typing import Optional

TOLERANCIA_DIAS = {"casos_sinan": 14, "infodengue": 14, "leitos_cnes": 75, "internacoes_sih": 90}
COLUNAS_DADOS_ATE = {"casos_sinan": "casos_dados_ate", "infodengue": "infodengue_dados_ate",
                     "leitos_cnes": "leitos_dados_ate", "internacoes_sih": "internacoes_dados_ate"}
FONTE_BRUTA = {"casos_sinan": "sinan_prelim", "infodengue": "infodengue", "leitos_cnes": "cnes_lt", "internacoes_sih": "sih_rd"}
LIMITE_LATENCIA = 7


def verificar(c, hoje: Optional[dt.date] = None) -> list:
    """Grava `final.frescor` (uma linha por indicador) e devolve as linhas. `situacao`: ok, atrasado ou sem_dados."""
    hoje = hoje or dt.date.today()
    c.execute("CREATE SCHEMA IF NOT EXISTS final")
    c.execute("""CREATE OR REPLACE TABLE final.frescor (
        indicador VARCHAR, fonte VARCHAR, dados_ate DATE, idade_dias INTEGER, tolerancia_dias INTEGER,
        ultima_publicacao DATE, ultima_carga TIMESTAMP, latencia_dias INTEGER, limite_latencia_dias INTEGER,
        situacao VARCHAR, verificado_em TIMESTAMP)""")
    linhas = []
    for ind, col in COLUNAS_DADOS_ATE.items():
        ate = c.execute("SELECT max(%s) FROM final.indicadores_municipio_semana" % col).fetchone()[0]
        fonte = FONTE_BRUTA[ind]
        pub, carga = c.execute(
            "SELECT remote_published, loaded_at FROM bronze_loads WHERE source = ? AND \"rows\" > 0 "
            "ORDER BY remote_published DESC NULLS LAST, loaded_at DESC LIMIT 1", [fonte]).fetchone() or (None, None)
        idade = (hoje - ate).days if ate else None
        latencia = (carga.date() - pub).days if pub and carga else None
        if ate is None:
            situacao = "sem_dados"
        elif idade > TOLERANCIA_DIAS[ind] or (latencia is not None and latencia > LIMITE_LATENCIA):
            situacao = "atrasado"
        else:
            situacao = "ok"
        linhas.append((ind, fonte, ate, idade, TOLERANCIA_DIAS[ind], pub, carga, latencia, LIMITE_LATENCIA, situacao, dt.datetime.now()))
    c.executemany("INSERT INTO final.frescor VALUES (?,?,?,?,?,?,?,?,?,?,?)", linhas)
    return linhas
