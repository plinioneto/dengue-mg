"""Análise exploratória das hipóteses H1, H2 (parcial) e H3 sobre a tabela final (`final.indicadores_municipio_semana`).

H1: há correlação entre casos (SINAN) e internações (SIH) por município? Mede-se a correlação semanal, sem defasagem e com internações
    até 4 semanas depois dos casos, no estado e por município.
H1 (picos): em cada ano, a semana do pico de internações vem depois da semana do pico de casos? (média móvel de 3 semanas)
H3: a capacidade relevante depende da região de saúde, e não só do município? Mede-se o fluxo das internações entre o município de
    residência e o de ocorrência (`final.fluxo_internacoes_ano`, agregado) e quanto dele se fecha dentro da região de saúde.
H2 (parcial): o ranking de municípios por pressão difere do ranking por casos? A H2 compara com a incidência, que exige população
    (indisponível); o volume de casos é a referência disponível aqui.

É exploratória: correlação não é causalidade, e os resultados dependem das regras da tabela final (ADR-0005). Semanas de casos
provisórios (idade de até 9 semanas) ficam fora do H1, porque ainda mudam (R8).

Uso (a partir da pasta do projeto, depois de `python -m dengue_mg.pipeline`):
    python -m dengue_mg.hipoteses
Lê `data/publicacao/*.parquet` e grava `docs/evidencias/hipoteses/analise_hipoteses.md`.
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
COLUNAS_INTEIRAS = {"defasagem_semanas", "semanas", "ano", "municipios", "municipios_comparados", "semana_pico_casos", "semana_pico_internacoes",
                    "total", "mesmo município", "outro município da mesma região", "outra região de saúde", "residente fora de MG ou ignorado",
                    "internacoes_no_municipio", "recebidas_de_fora", "enviadas", "saldo", "municipios_com_10_ou_mais_internacoes", "com_metade_ou_mais_fora"}


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


def _suavizar(x: pd.Series) -> pd.Series:
    return x.rolling(3, center=True, min_periods=2).mean()


def h1_picos(df: pd.DataFrame) -> pd.DataFrame:
    """Estado, por ano: semana do pico de casos e de internações (média móvel de 3 semanas) e a diferença em semanas."""
    est = df.groupby("semana_id")[["casos", "internacoes"]].sum(min_count=1).sort_index().dropna()
    pos = {sid: i for i, sid in enumerate(est.index)}
    linhas = []
    for ano, g in est.groupby(est.index // 100):
        pc, pi = _suavizar(g["casos"]).idxmax(), _suavizar(g["internacoes"]).idxmax()
        linhas.append(dict(ano=int(ano), semanas=len(g), semana_pico_casos=int(pc), semana_pico_internacoes=int(pi),
                           defasagem_semanas=pos[pi] - pos[pc]))
    return pd.DataFrame(linhas)


def h1_picos_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Municípios-ano com casos e internações suficientes: diferença entre a semana do pico de internações e a do pico de casos."""
    pos = {sid: i for i, sid in enumerate(sorted(df["semana_id"].unique()))}
    linhas = []
    for (geo, ano), g in df.groupby(["geocodigo", df["semana_id"] // 100], sort=False):
        g = g.dropna(subset=["casos", "internacoes"]).sort_values("semana_id")
        if g["casos"].sum() < 20 or g["internacoes"].sum() < 10:
            continue
        pc = _suavizar(g.set_index("semana_id")["casos"]).idxmax()
        pi = _suavizar(g.set_index("semana_id")["internacoes"]).idxmax()
        linhas.append(dict(geocodigo=geo, ano=int(ano), defasagem_semanas=pos[pi] - pos[pc]))
    return pd.DataFrame(linhas)


def resumo_picos_municipios(m: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for ano, g in m.groupby("ano"):
        d = g["defasagem_semanas"]
        linhas.append(dict(ano=int(ano), municipios=len(g), mediana_defasagem=float(d.median()),
                           pct_internacao_depois=float((d > 0).mean()), pct_mesma_semana=float((d == 0).mean()), pct_internacao_antes=float((d < 0).mean())))
    return pd.DataFrame(linhas)


def carregar_fluxo(c) -> Optional[pd.DataFrame]:
    try:
        return c.execute("SELECT * FROM final.fluxo_internacoes_ano").df()
    except Exception:  # noqa: BLE001  (pipeline ainda não publicou a tabela)
        return None


def h3_fluxos(f: pd.DataFrame):
    """Fluxo das internações entre residência e ocorrência. Devolve (resumo por ano, polos, municípios que enviam)."""
    f = f.copy()
    fora = f["regiao_residencia"] == "Fora de MG ou ignorado"
    mesmo = f["cod6_residencia"] == f["cod6_ocorrencia"]
    f["categoria"] = "outra região de saúde"
    f.loc[~mesmo & ~fora & (f["regiao_residencia"] == f["regiao_ocorrencia"]), "categoria"] = "outro município da mesma região"
    f.loc[fora, "categoria"] = "residente fora de MG ou ignorado"
    f.loc[mesmo, "categoria"] = "mesmo município"
    tab = f.pivot_table(index="ano", columns="categoria", values="internacoes", aggfunc="sum", fill_value=0)
    for col in ("mesmo município", "outro município da mesma região", "outra região de saúde", "residente fora de MG ou ignorado"):
        if col not in tab:
            tab[col] = 0
    tab["total"] = tab.sum(axis=1)
    total = tab.sum()
    tab.loc["Total"] = total
    resumo = tab.reset_index()
    resumo["ano"] = resumo["ano"].astype(str)
    em_mg = resumo["total"] - resumo["residente fora de MG ou ignorado"]
    resumo["pct_fora_do_municipio"] = (resumo["outro município da mesma região"] + resumo["outra região de saúde"]) / em_mg.where(em_mg > 0)
    resumo["pct_dentro_da_regiao"] = (resumo["mesmo município"] + resumo["outro município da mesma região"]) / em_mg.where(em_mg > 0)
    resumo = resumo[["ano", "total", "mesmo município", "outro município da mesma região", "outra região de saúde",
                     "residente fora de MG ou ignorado", "pct_fora_do_municipio", "pct_dentro_da_regiao"]]

    # polos: municípios que mais recebem internações de residentes de outros municípios (período inteiro)
    rec = f[~mesmo].groupby(["cod6_ocorrencia", "municipio_ocorrencia", "regiao_ocorrencia"])["internacoes"].sum().rename("recebidas_de_fora")
    tot = f.groupby("cod6_ocorrencia")["internacoes"].sum().rename("internacoes_no_municipio")
    env = f[~mesmo & ~fora].groupby("cod6_residencia")["internacoes"].sum().rename("enviadas")
    polos = rec.reset_index().merge(tot, on="cod6_ocorrencia", how="left").merge(env, left_on="cod6_ocorrencia", right_index=True, how="left")
    polos["enviadas"] = polos["enviadas"].fillna(0).astype(int)
    polos["pct_de_fora"] = polos["recebidas_de_fora"] / polos["internacoes_no_municipio"]
    polos["saldo"] = polos["recebidas_de_fora"] - polos["enviadas"]
    polos = polos.sort_values("recebidas_de_fora", ascending=False).head(10)[
        ["municipio_ocorrencia", "regiao_ocorrencia", "internacoes_no_municipio", "recebidas_de_fora", "pct_de_fora", "enviadas", "saldo"]]

    # municípios de residência cujas internações ocorrem em outro município (visão do paciente)
    tot_res = f[~fora].groupby("cod6_residencia")["internacoes"].sum()
    fora_res = f[~fora & ~mesmo].groupby("cod6_residencia")["internacoes"].sum().reindex(tot_res.index, fill_value=0)
    res = pd.DataFrame({"total": tot_res, "fora": fora_res})
    res = res[res["total"] >= 10]
    res["pct_fora"] = res["fora"] / res["total"]
    envia = pd.DataFrame([dict(municipios_com_10_ou_mais_internacoes=len(res), com_metade_ou_mais_fora=int((res["pct_fora"] >= 0.5).sum()),
                               pct=float((res["pct_fora"] >= 0.5).mean()) if len(res) else None)])
    return resumo, polos, envia


def h2_parcial(c, ano_de: int, ano_ate: int) -> pd.DataFrame:
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
        if col in COLUNAS_INTEIRAS or col.startswith("topo"):
            try:
                return str(int(v))
            except (ValueError, TypeError):
                return str(v)
        return ("%.2f" % v).replace(".", ",") if isinstance(v, float) else str(v)
    return cab + "\n".join("| " + " | ".join(f(c, v) for c, v in r.items()) + " |" for _, r in df.iterrows()) + "\n"


def relatorio(c, saida: Optional[str] = None) -> str:
    saida = saida or os.path.join(os.environ.get("DENGUE_EVIDENCIAS", os.path.join(RAIZ, "docs", "evidencias")), "hipoteses", "analise_hipoteses.md")
    df = carregar(c)
    est, ano, mun = h1_estado(df), h1_por_ano(df), h1_municipios(df)
    res = resumo_municipios(mun) if not mun.empty else pd.DataFrame()
    anos = [int(i) // 100 for i in df["semana_id"].unique()]
    h2df = h2_parcial(c, min(anos), max(anos))
    pct = lambda v: ("%.1f%%" % (100 * v)).replace(".", ",")
    L = ["# Análise exploratória das hipóteses H1, H2 (parcial) e H3", "",
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
    picos = h1_picos(df)
    pm = h1_picos_municipios(df)
    L += ["### Picos: o pico de internações vem depois do pico de casos? (estado, por ano)", "",
          "Semana do pico com média móvel de 3 semanas; defasagem = semanas entre o pico de casos e o de internações (positiva: internações depois).", "",
          _tabela(picos), ""]
    if not pm.empty:
        L += ["### Picos nos municípios (por município e ano com 20 casos e 10 internações ou mais)", "",
              _tabela(resumo_picos_municipios(pm), {"pct_internacao_depois": pct, "pct_mesma_semana": pct, "pct_internacao_antes": pct}), ""]
    L += ["## H2 (parcial): ranking por pressão x ranking por volume de casos", "",
          "Sem população, a incidência não pode ser calculada (a H2 completa fica pendente); a referência é o volume de casos. Pressão: pico semanal, com mínimo de %d internações no período (como no painel). Compara-se o topo %d de cada critério e a correlação de postos (Spearman) entre casos e pressão nos municípios que têm os dois valores." % (MIN_INTERNACOES_RANKING, TOPO), "",
          _tabela(h2df), ""]
    fluxo = carregar_fluxo(c)
    L += ["## H3: a capacidade relevante depende da região de saúde?", ""]
    if fluxo is None or fluxo.empty:
        L += ["Tabela `final.fluxo_internacoes_ano` não encontrada na publicação: rode `python -m dengue_mg.pipeline --sem-ingestao`.", ""]
    else:
        resumo_f, polos, envia = h3_fluxos(fluxo)
        fmt = {"pct_fora_do_municipio": pct, "pct_dentro_da_regiao": pct, "pct_de_fora": pct, "pct": pct}
        L += ["Fluxo das internações por dengue entre o município de residência e o de ocorrência (SIH). Percentuais sobre as internações de residentes em MG.", "",
              _tabela(resumo_f, fmt), "",
              "### Municípios que mais recebem internações de residentes de outros municípios (2022 em diante)", "", _tabela(polos, fmt), "",
              "### Municípios de residência cujas internações ocorrem em outro município", "", _tabela(envia, fmt), ""]
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
    print("[hipóteses] relatório gravado em:", caminho)


if __name__ == "__main__":
    main()
