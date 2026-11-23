"""R10: consultas do painel sobre `final.indicadores_municipio_semana` e `final.frescor`. Só agregados, nunca registros individuais (LGPD).

Os recortes são estado (todas as regiões), região de saúde ou município. Em recortes com mais de um município, os totais são somas e a
pressão é a razão das somas (internações / leitos clínicos e pediátricos), nula se faltar o numerador ou o denominador (ADR-0005).
"""
import os
from typing import List, Optional

import duckdb

PUBLICADAS = ["indicadores_municipio_semana", "frescor"]

T = "final.indicadores_municipio_semana"
AGREGADOS = """
    sum(casos_notificados) AS casos_notificados, sum(casos_hospitalizados) AS casos_hospitalizados,
    sum(casos_provaveis_infodengue) AS casos_provaveis_infodengue,
    sum(internacoes) AS internacoes, sum(obitos) AS obitos,
    sum(leitos_clinicos_pediatricos) AS leitos_clinicos_pediatricos, sum(leitos_existentes) AS leitos_existentes,
    sum(internacoes) * 1.0 / nullif(sum(leitos_clinicos_pediatricos), 0) AS pressao_internacoes_por_leito,
    bool_or(casos_provisorio) AS casos_provisorio"""


def _filtro(regiao: Optional[str], geocodigo: Optional[str]):
    where, params = [], []
    if regiao:
        where.append("regiao_saude = ?"); params.append(regiao)
    if geocodigo:
        where.append("geocodigo = ?"); params.append(geocodigo)
    return (" WHERE " + " AND ".join(where)) if where else "", params


def regioes(c) -> List[str]:
    return [r[0] for r in c.execute("SELECT DISTINCT regiao_saude FROM %s ORDER BY 1" % T).fetchall()]


def municipios(c, regiao: Optional[str] = None):
    """[(geocodigo, nome)] dos municípios da região (ou do estado)."""
    w, p = _filtro(regiao, None)
    return c.execute("SELECT DISTINCT geocodigo, municipio FROM %s%s ORDER BY 2" % (T, w), p).fetchall()


def semanas(c):
    """[(semana_id, inicio, fim)] em ordem crescente."""
    return c.execute("SELECT DISTINCT semana_id, inicio_semana, fim_semana FROM %s ORDER BY 1" % T).fetchall()


def serie(c, semana_de: int, semana_ate: int, regiao: Optional[str] = None, geocodigo: Optional[str] = None):
    """Série semanal do recorte (linhas: dict)."""
    w, p = _filtro(regiao, geocodigo)
    w += (" AND" if w else " WHERE") + " semana_id BETWEEN ? AND ?"
    cur = c.execute("SELECT semana_id, any_value(inicio_semana) AS inicio_semana, %s FROM %s%s GROUP BY semana_id ORDER BY semana_id"
                    % (AGREGADOS, T, w), p + [semana_de, semana_ate])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


CRITERIOS = {
    "pressao_pico": ("Pressão: pico semanal", "pressao_pico"),
    "pressao_media": ("Pressão: média semanal", "pressao_media"),
    "internacoes": ("Internações no período", "internacoes"),
    "casos": ("Casos notificados no período", "casos"),
}


def mais_afetados(c, semana_de: int, semana_ate: int, criterio: str = "pressao_pico", regiao: Optional[str] = None,
                  minimo_internacoes: int = 0, limite: int = 20):
    """Municípios mais afetados no período, ordenados pelo critério (chaves de CRITERIOS); só entram os que têm valor maior que zero no critério.

    Por município: casos e internações somados nas semanas conhecidas, leitos clínicos e pediátricos da última semana do período com leito
    informado, pressão média e pico semanal (só semanas com pressão conhecida) e a semana do pico. `minimo_internacoes` evita ordenar a
    pressão por poucas internações (ex.: 1 internação em 3 leitos); vale para os critérios de pressão.
    """
    if criterio not in CRITERIOS:
        raise ValueError("critério desconhecido: %s" % criterio)
    w, p = _filtro(regiao, None)
    w += (" AND" if w else " WHERE") + " semana_id BETWEEN ? AND ?"
    p += [semana_de, semana_ate]
    minimo = minimo_internacoes if criterio.startswith("pressao") else 0
    ordem = CRITERIOS[criterio][1]
    cur = c.execute(f"""
        SELECT geocodigo, any_value(municipio) AS municipio, any_value(regiao_saude) AS regiao_saude,
               sum(casos_notificados) AS casos, sum(internacoes) AS internacoes,
               arg_max(leitos_clinicos_pediatricos, semana_id) FILTER (WHERE leitos_clinicos_pediatricos IS NOT NULL) AS leitos,
               avg(pressao_internacoes_por_leito) AS pressao_media,
               max(pressao_internacoes_por_leito) AS pressao_pico,
               arg_max(semana_id, pressao_internacoes_por_leito) FILTER (WHERE pressao_internacoes_por_leito IS NOT NULL) AS semana_do_pico
        FROM {T}{w} GROUP BY geocodigo
        HAVING coalesce(sum(internacoes), 0) >= ?
           AND {ordem} > 0
        ORDER BY {ordem} DESC, internacoes DESC NULLS LAST, casos DESC NULLS LAST, municipio LIMIT ?""", p + [minimo, limite])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def dados_ate(c):
    """\"Dados até\" de cada grupo de indicadores (um valor por fonte, vale para o estado todo)."""
    r = c.execute("SELECT max(casos_dados_ate), max(infodengue_dados_ate), max(internacoes_dados_ate), max(leitos_dados_ate), max(pressao_dados_ate) FROM %s" % T).fetchone()
    return dict(zip(["casos", "infodengue", "internacoes", "leitos", "pressao"], r))


def frescor(c):
    try:
        cur = c.execute("SELECT indicador, dados_ate, idade_dias, tolerancia_dias, latencia_dias, situacao FROM final.frescor ORDER BY indicador")
    except Exception:  # noqa: BLE001  (pipeline ainda não gerou a tabela)
        return []
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def publicar(c, pasta: str) -> List[str]:
    """Exporta as tabelas finais do painel para Parquet (substituição atômica). O painel lê só estes arquivos, nunca o DuckDB de trabalho."""
    os.makedirs(pasta, exist_ok=True)
    out = []
    for t in PUBLICADAS:
        destino = os.path.join(pasta, t + ".parquet")
        c.execute("COPY final.%s TO '%s' (FORMAT parquet, COMPRESSION zstd)" % (t, destino + ".tmp"))
        os.replace(destino + ".tmp", destino)
        out.append(destino)
    return out


def abrir(pasta: str):
    """Conexão em memória com o esquema `final` apontando para os Parquet publicados (somente leitura na prática)."""
    c = duckdb.connect(":memory:")
    c.execute("CREATE SCHEMA final")
    for t in PUBLICADAS:
        arq = os.path.join(pasta, t + ".parquet").replace("\\", "/")
        if os.path.exists(arq):
            c.execute("CREATE VIEW final.%s AS SELECT * FROM read_parquet('%s')" % (t, arq))
    return c
