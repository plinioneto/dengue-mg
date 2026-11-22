"""R8: revisão das semanas preliminares do SINAN entre versões da camada bruta (hipótese H4).

Cada vez que o arquivo preliminar muda, a ingestão guarda uma nova versão (ADR-0002). Aqui, para cada versão, contam-se os casos por
município de notificação e semana dos primeiros sintomas (mesma regra de `fct_casos_semana`) e compara-se com a versão mais recente do
mesmo arquivo. A revisão é medida pela idade da semana na data de publicação da versão, o que mostra quanto uma semana recente
ainda muda (regra dos 60 dias).

Uso (a partir da pasta do projeto, depois de `python -m dengue_mg.tratada`, que cria `tratada.dim_semana_epi`):
    python -m dengue_mg.revisao
Saídas: tabela `final.revisao_sinan_versoes`, `docs/evidencias/R8/relatorio_revisao.md` e `revisao_por_idade.csv`.
"""
import csv
import datetime as dt
import os
from typing import Optional

from . import bronze
from .tratada import RAIZ

FONTE = "sinan_prelim"
LIMITE = 0.15      # mesmo limite da reconciliação (ADR-0004)
MIN_CASOS = 10     # pares município-semana com ao menos 10 casos na versão mais recente
IDADE_MAX = 12     # idades acima disso são agrupadas


def _caminho(p: str) -> str:
    p = p.replace("\\", "/")
    return p if p.startswith("/") or p[1:2] == ":" else os.path.join(os.getcwd(), p).replace("\\", "/")


def versoes(c, fonte: str = FONTE):
    """Versões de cada arquivo, da mais antiga para a mais nova (uma linha por carga com linhas)."""
    return c.execute("""
        SELECT file_name, sha256, parquet_path, loaded_at, coalesce(remote_published, CAST(loaded_at AS DATE)) AS publicada,
               row_number() OVER (PARTITION BY file_name ORDER BY loaded_at) AS versao,
               count(*) OVER (PARTITION BY file_name) AS n_versoes
        FROM bronze_loads WHERE source = ? AND "rows" > 0 ORDER BY file_name, loaded_at""", [fonte]).fetchall()


def calcular(c, fonte: str = FONTE) -> int:
    """Grava `final.revisao_sinan_versoes` (arquivo, versão, publicada, cod6, semana_id, casos). Retorna o número de versões."""
    c.execute("CREATE SCHEMA IF NOT EXISTS final")
    c.execute("""CREATE OR REPLACE TABLE final.revisao_sinan_versoes (
        arquivo VARCHAR, versao INTEGER, n_versoes INTEGER, publicada DATE, cod6 VARCHAR, semana_id INTEGER, casos BIGINT)""")
    vs = versoes(c, fonte)
    for arquivo, sha, caminho, _, publicada, versao, n in vs:
        c.execute("""
            INSERT INTO final.revisao_sinan_versoes
            WITH b AS (
                SELECT nullif(trim(ID_MUNICIP), '') AS cod6,
                       cast(coalesce(try_strptime(nullif(trim(DT_SIN_PRI), ''), '%Y%m%d'), try_strptime(nullif(trim(DT_SIN_PRI), ''), '%Y-%m-%d'),
                                     try_strptime(nullif(trim(DT_NOTIFIC), ''), '%Y%m%d'), try_strptime(nullif(trim(DT_NOTIFIC), ''), '%Y-%m-%d')) AS date) AS dt_ref
                FROM read_parquet(?) WHERE coalesce(trim(CLASSI_FIN), '') <> '5')
            SELECT ?, ?, ?, ?, b.cod6, s.semana_id, count(*)
            FROM b JOIN tratada.dim_semana_epi s ON s.inicio = b.dt_ref - cast(dayofweek(b.dt_ref) AS integer)
            GROUP BY b.cod6, s.semana_id""", [_caminho(caminho), arquivo, int(versao), int(n), publicada])
    return len(vs)


def resumo_por_idade(c):
    """Revisão por idade da semana na publicação da versão, contra a versão mais recente do mesmo arquivo."""
    return c.execute(f"""
        WITH ult AS (SELECT * FROM final.revisao_sinan_versoes WHERE versao = n_versoes),
        ant AS (SELECT * FROM final.revisao_sinan_versoes WHERE versao < n_versoes),
        chaves AS (SELECT DISTINCT arquivo, versao, publicada, n_versoes, cod6, semana_id FROM ant
                   UNION SELECT DISTINCT a.arquivo, a.versao, a.publicada, a.n_versoes, u.cod6, u.semana_id
                   FROM (SELECT DISTINCT arquivo, versao, publicada, n_versoes FROM ant) a JOIN ult u USING (arquivo)),
        pares AS (
            SELECT k.arquivo, k.versao, k.cod6, k.semana_id, w.fim,
                   cast(least((k.publicada - w.fim) // 7, {IDADE_MAX + 1}) AS integer) AS idade,
                   coalesce(a.casos, 0) AS antes, coalesce(u.casos, 0) AS depois
            FROM chaves k JOIN tratada.dim_semana_epi w ON w.semana_id = k.semana_id
            LEFT JOIN ant a ON a.arquivo = k.arquivo AND a.versao = k.versao AND a.cod6 = k.cod6 AND a.semana_id = k.semana_id
            LEFT JOIN ult u ON u.arquivo = k.arquivo AND u.cod6 = k.cod6 AND u.semana_id = k.semana_id
            WHERE w.fim <= k.publicada),
        estadual AS (
            SELECT arquivo, versao, semana_id, idade, sum(antes) AS antes, sum(depois) AS depois FROM pares GROUP BY ALL)
        SELECT e.idade,
               count(*) AS semanas,
               avg((e.depois - e.antes) * 1.0 / nullif(e.depois, 0)) AS revisao_estadual_media,
               (SELECT count(*) FROM pares p WHERE p.idade = e.idade AND p.depois >= {MIN_CASOS}) AS pares_municipais,
               (SELECT avg(abs(p.depois - p.antes) * 1.0 / p.depois) FROM pares p WHERE p.idade = e.idade AND p.depois >= {MIN_CASOS}) AS revisao_municipal_abs_media,
               (SELECT avg(CASE WHEN abs(p.depois - p.antes) * 1.0 / p.depois > {LIMITE} THEN 1.0 ELSE 0.0 END)
                  FROM pares p WHERE p.idade = e.idade AND p.depois >= {MIN_CASOS}) AS pct_pares_revistos_acima_do_limite
        FROM estadual e GROUP BY e.idade ORDER BY e.idade""").fetchall()


def relatorio(c, saida: Optional[str] = None) -> str:
    saida = saida or os.path.join(os.environ.get("DENGUE_EVIDENCIAS", os.path.join(RAIZ, "docs", "evidencias")), "R8", "relatorio_revisao.md")
    vs = versoes(c)
    n_arq = len({v[0] for v in vs})
    comparaveis = [v for v in vs if v[6] > 1 and v[5] < v[6]]
    linhas = ["# Revisão das semanas preliminares do SINAN (R8)", "",
              "Gerado em %s a partir de `bronze_loads` (fonte `%s`): %d versões de %d arquivo(s)." % (
                  dt.datetime.now().strftime("%d/%m/%Y %H:%M"), FONTE, len(vs), n_arq), "",
              "| Arquivo | Versão | Publicada | Carregada em | SHA-256 |", "|---|---|---|---|---|"]
    for arq, sha, _, carg, pub, ver, n in vs:
        linhas.append("| %s | %d de %d | %s | %s | %s |" % (arq, ver, n, pub, carg.strftime("%d/%m/%Y %H:%M"), sha[:12]))
    linhas.append("")
    if not comparaveis:
        linhas += ["**Ainda não há o que medir:** cada arquivo tem uma só versão. A revisão aparece a partir da segunda carga com conteúdo "
                   "diferente (o agendamento do R9 produz uma versão nova a cada publicação do SINAN preliminar, a cada 1 a 6 dias).", ""]
    else:
        res = resumo_por_idade(c)
        linhas += ["Cada versão anterior é comparada com a mais recente do mesmo arquivo. Idade = semanas completas entre o fim da semana "
                   "epidemiológica e a publicação da versão (%d+ agrupa as mais antigas). Revisão positiva = casos que a versão ainda não tinha." % (IDADE_MAX + 1), "",
                   "| Idade (semanas) | Semanas comparadas | Revisão média estadual | Pares município-semana (≥%d casos) | Revisão absoluta média por município | Pares revistos em mais de %d%% |" % (MIN_CASOS, int(LIMITE * 100)),
                   "|---|---|---|---|---|---|"]
        pct = lambda x: "-" if x is None else "%.1f%%" % (100 * x)
        for idade, sem, rev, pares, rev_m, acima in res:
            linhas.append("| %s | %d | %s | %d | %s | %s |" % (
                ("%d+" % idade) if idade > IDADE_MAX else idade, sem, pct(rev), pares, pct(rev_m), pct(acima)))
        os.makedirs(os.path.dirname(saida), exist_ok=True)
        with open(os.path.join(os.path.dirname(saida), "revisao_por_idade.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["idade_semanas", "semanas", "revisao_estadual_media", "pares_municipais", "revisao_municipal_abs_media", "pct_pares_acima_do_limite"])
            w.writerows(res)
        linhas += ["", "Leitura: a revisão tende a zero com a idade da semana; a idade a partir da qual fica abaixo de %d%% mostra quando o valor "
                   "pode ser tratado como fechado (a regra dos 60 dias prevê cerca de 9 semanas)." % int(LIMITE * 100)]
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return saida


def main():
    c = bronze.con()
    n = calcular(c)
    print("[R8] %d versões processadas" % n)
    print("[R8] relatório: %s" % relatorio(c))
    c.close()


if __name__ == "__main__":
    main()
