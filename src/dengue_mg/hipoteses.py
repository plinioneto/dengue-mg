"""Análise exploratória das hipóteses H1 e H3 sobre a tabela final (`final.indicadores_municipio_semana`).

H1: há correlação entre casos (SINAN) e internações (SIH) por município? Mede-se a correlação semanal, sem defasagem e com internações
    até 4 semanas depois dos casos, no estado e por município.
H3: o ranking de municípios por pressão difere do ranking por volume de casos? Sem população não há incidência (H2 fica de fora);
    o volume de casos é a referência disponível.

É exploratória: correlação não é causalidade, e os resultados dependem das regras da tabela final (ADR-0005). Semanas de casos
provisórios (idade de até 9 semanas) ficam fora do H1, porque ainda mudam (R8).

Uso (a partir da pasta do projeto, depois de `python -m dengue_mg.pipeline`):
    python -m dengue_mg.hipoteses
Lê `data/publicacao/*.parquet` e grava `docs/evidencias/hipoteses/analise_h1_h3.md`.
"""
import datetime as dt
import os
from typing import Optional

import pandas as pd

from . import consulta
from .tratada import RAIZ

T = consulta.T
LAGS = range(0, 5)
MIN_SEMANAS_COM_CASOS = 20      # município entra na correlação com ao menos 20 semanas com casos
MIN_INTERNACOES = 10            # e ao menos 10 internações somadas no período
TOPO = 20
MIN_INTERNACOES_RANKING = 5     # mesmo piso do painel nos critérios de pressão


def carregar(c) -> pd.DataFrame:
    """Casos e internações por município e semana, só semanas de casos não provisórios, em ordem de semana."""
    return c.execute(f"""
        SELECT geocodigo, municipio, semana_id, casos_notificados AS casos, internacoes
        FROM {T} WHERE NOT casos_provisorio ORDER BY geocodigo, semana_id""").df()


def _corr(x: pd.Series, y: pd.Series, metodo: str) -> Optional[float]:
    """Pearson, ou Spearman calculado como Pearson dos postos (média nos empates; não exige scipy). Nulo se não houver variação."""
    par = pd.concat([x, y], axis=1).dropna()
    if len(par) < 3 or par.iloc[:, 0].nunique() < 2 or par.iloc[:, 1].nunique() < 2:
        return None
    if metodo == "spearman":
        par = par.rank(method="average")
    return float(par.iloc[:, 0].corr(par.iloc[:, 1]))


def h1_estado(df: pd.DataFrame) -> pd.DataFrame:
    """Correlação semanal no estado (casos de MG x internações de MG), por defasagem das internações."""
    est = df.groupby("semana_id")[["casos", "internacoes"]].sum(min_count=1).sort_index()
    linhas = []
    for k in LAGS:
        y = est["internacoes"].shift(-k)
        n = int(pd.concat([est["casos"], y], axis=1).dropna().shape[0])
        linhas.append(dict(defasagem_semanas=k, semanas=n, pearson=_corr(est["casos"], y, "pearson"),
                           spearman=_corr(est["casos"], y, "spearman")))
    return pd.DataFrame(linhas)


def h1_por_ano(df: pd.DataFrame) -> pd.DataFrame:
    """Correlação (Spearman) no estado por ano epidemiológico, sem defasagem e com defasagem de 1 e 2 semanas."""
    est = df.groupby("semana_id")[["casos", "internacoes"]].sum(min_count=1).sort_index()
    linhas = []
    for ano in sorted({i // 100 for i in est.index}):
        parte = est[(est.index // 100) == ano]
        linhas.append(dict(ano=ano, semanas=int(parte.dropna().shape[0]),
                           **{f"spearman_lag{k}": _corr(parte["casos"], parte["internacoes"].shift(-k), "spearman") for k in (0, 1, 2)}))
    return pd.DataFrame(linhas)


def h1_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Spearman por município e defasagem. Só municípios com semanas com casos e internações suficientes."""
    linhas = []
    for geo, g in df.groupby("geocodigo", sort=False):
        g = g.sort_values("semana_id")
        if (g["casos"] > 0).sum() < MIN_SEMANAS_COM_CASOS or (g["internacoes"].sum(min_count=1) or 0) < MIN_INTERNACOES:
            continue
        linha = dict(geocodigo=geo, municipio=g["municipio"].iloc[0], casos=int(g["casos"].sum()), internacoes=int(g["internacoes"].sum()))
        for k in LAGS:
            linha[f"lag{k}"] = _corr(g["casos"], g["internacoes"].shift(-k), "spearman")
        linhas.append(linha)
    return pd.DataFrame(linhas)


def resumo_municipios(m: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for k in LAGS:
        v = m[f"lag{k}"].dropna()
        linhas.append(dict(defasagem_semanas=k, municipios=len(v), mediana=v.median() if len(v) else None,
                           p25=v.quantile(0.25) if len(v) else None, p75=v.quantile(0.75) if len(v) else None,
                           pct_rho_ge_05=float((v >= 0.5).mean()) if len(v) else None))
    return pd.DataFrame(linhas)


def h3(c, ano_de: int, ano_ate: int) -> pd.DataFrame:
    """Compara o topo por casos com o topo por pressão (pico) e por internações, por ano e no período inteiro."""
    linhas = []
    recortes = [(str(a), a * 100 + 1, a * 100 + 53) for a in range(ano_de, ano_ate + 1)] + [("2022 a %d" % ano_ate, ano_de * 100 + 1, ano_ate * 100 + 53)]
    for rotulo, de, ate in recortes:
        base = {k: pd.DataFrame(consulta.mais_afetados(c, de, ate, k, minimo_internacoes=MIN_INTERNACOES_RANKING, limite=10000))
                for k in ("casos", "internacoes", "pressao_pico", "pressao_media")}
        if base["casos"].empty or base["pressao_pico"].empty:
            continue
        top_casos = set(base["casos"].head(TOPO)["geocodigo"])
        # municípios com os dois valores (casos > 0 e pressão conhecida com o piso de internações)
        comum = base["casos"][["geocodigo", "casos"]].merge(base["pressao_pico"][["geocodigo", "pressao_pico", "pressao_media"]], on="geocodigo")
        linha = dict(periodo=rotulo, municipios_comparados=len(comum),
                     spearman_casos_x_pico=_corr(comum["casos"], comum["pressao_pico"], "spearman"),
                     spearman_casos_x_media=_corr(comum["casos"], comum["pressao_media"], "spearman"))
        for k in ("pressao_pico", "pressao_media", "internacoes"):
            linha[f"topo{TOPO}_em_comum_com_casos_{k}"] = len(top_casos & set(base[k].head(TOPO)["geocodigo"]))
        linhas.append(linha)
    return pd.DataFrame(linhas)


def _tabela(df: pd.DataFrame, formatos: Optional[dict] = None) -> str:
    formatos = formatos or {}
    cab = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    def f(col, v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "-"
        if col in formatos:
            return formatos[col](v)
        return ("%.2f" % v).replace(".", ",") if isinstance(v, float) else str(v)
    return cab + "\n".join("| " + " | ".join(f(c, v) for c, v in r.items()) + " |" for _, r in df.iterrows()) + "\n"


def relatorio(c, saida: Optional[str] = None) -> str:
    saida = saida or os.path.join(os.environ.get("DENGUE_EVIDENCIAS", os.path.join(RAIZ, "docs", "evidencias")), "hipoteses", "analise_h1_h3.md")
    df = carregar(c)
    est, ano, mun = h1_estado(df), h1_por_ano(df), h1_municipios(df)
    res = resumo_municipios(mun) if not mun.empty else pd.DataFrame()
    anos = [int(i) // 100 for i in df["semana_id"].unique()]
    h3df = h3(c, min(anos), max(anos))
    pct = lambda v: ("%.1f%%" % (100 * v)).replace(".", ",")
    L = ["# Análise exploratória das hipóteses H1 e H3", "",
         "Gerado em %s sobre `final.indicadores_municipio_semana` (semanas de casos não provisórios; internações até o último \"dados até\" do SIH)." % dt.datetime.now().strftime("%d/%m/%Y %H:%M"), "",
         "Análise exploratória: correlação não é causalidade. Casos são do município de notificação e internações do município de ocorrência; o SIH só traz internações do SUS.", "",
         "## H1: correlação entre casos e internações", "",
         "### Estado (série semanal de Minas Gerais)", "",
         "Internações com defasagem de 0 a 4 semanas depois dos casos.", "", _tabela(est), "",
         "### Estado, por ano (Spearman)", "", _tabela(ano), ""]
    if mun.empty:
        L += ["### Municípios", "", "Nenhum município com semanas e internações suficientes.", ""]
    else:
        melhor = int(res.loc[res["mediana"].idxmax(), "defasagem_semanas"])
        L += ["### Municípios (Spearman por município)", "",
              "Entram os municípios com ao menos %d semanas com casos e %d internações no período: **%d de 853**." % (MIN_SEMANAS_COM_CASOS, MIN_INTERNACOES, len(mun)), "",
              _tabela(res, {"pct_rho_ge_05": pct}), "",
              "Defasagem com maior mediana: **%d semana(s)**." % melhor, ""]
    L += ["## H3: ranking por pressão x ranking por volume de casos", "",
          "Sem população, a incidência não pode ser calculada (H2 fica pendente); a referência é o volume de casos. Pressão: pico semanal, com mínimo de %d internações no período (como no painel). Compara-se o topo %d de cada critério e a correlação de postos (Spearman) entre casos e pressão nos municípios que têm os dois valores." % (MIN_INTERNACOES_RANKING, TOPO), "",
          _tabela(h3df), ""]
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return saida


def main():
    pasta = os.path.join(os.environ.get("DENGUE_DATA", "data"), "publicacao")
    c = consulta.abrir(pasta)
    caminho = relatorio(c)
    c.close()
    print(open(caminho, encoding="utf-8").read())
    print("[H1/H3] relatório gravado em:", caminho)


if __name__ == "__main__":
    main()
