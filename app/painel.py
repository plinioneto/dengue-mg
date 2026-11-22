"""Painel de consulta (R10): município, região de saúde e semana epidemiológica.

Uso (a partir da pasta do projeto, depois de `python -m dengue_mg.pipeline`):
    PYTHONPATH=src streamlit run app/painel.py
Lê os Parquet de `data/publicacao/` (ou DENGUE_DATA), gerados pelo pipeline; não abre o DuckDB de trabalho. Só agregados.
"""
import os

import duckdb
import pandas as pd
import streamlit as st

from dengue_mg import consulta

st.set_page_config(page_title="Dengue e capacidade assistencial em MG", layout="wide")


@st.cache_resource
def conexao(pasta: str, versao: float):
    """Abre os Parquet publicados; `versao` (data de modificação) renova a conexão quando o pipeline republica."""
    return consulta.abrir(pasta)


pasta = os.path.join(os.environ.get("DENGUE_DATA", "data"), "publicacao")
arquivo = os.path.join(pasta, "indicadores_municipio_semana.parquet")
if not os.path.exists(arquivo):
    st.error("Dados publicados não encontrados em `%s`. Rode `python -m dengue_mg.pipeline` antes." % pasta)
    st.stop()
c = conexao(pasta, os.path.getmtime(arquivo))
try:
    sems = consulta.semanas(c)
except duckdb.Error:
    st.error("A tabela final ainda não existe. Rode `python -m dengue_mg.pipeline`.")
    st.stop()

st.title("Pressão da dengue na capacidade assistencial: Minas Gerais")
st.caption("Dados abertos (SINAN, CNES, SIH e InfoDengue), agregados por município e semana epidemiológica. "
           "A pressão é **internações por dengue na semana por leito clínico e pediátrico**; não é taxa de ocupação (ADR-0005).")

with st.sidebar:
    st.header("Recorte")
    todas = "Todas as regiões (estado)"
    regiao_sel = st.selectbox("Região de saúde", [todas] + consulta.regioes(c))
    regiao = None if regiao_sel == todas else regiao_sel
    muns = consulta.municipios(c, regiao)
    todos = "Todos os municípios do recorte"
    nome_por_cod = {g: n for g, n in muns}
    mun_sel = st.selectbox("Município", [todos] + [g for g, _ in muns], format_func=lambda g: g if g == todos else nome_por_cod[g])
    geocodigo = None if mun_sel == todos else mun_sel
    ids = [s[0] for s in sems]
    rotulo = {s[0]: "%d-SE%02d (%s)" % (s[0] // 100, s[0] % 100, s[1].strftime("%d/%m/%Y")) for s in sems}
    de, ate = st.select_slider("Semanas epidemiológicas", options=ids, value=(ids[max(0, len(ids) - 53)], ids[-1]), format_func=lambda i: rotulo[i])

linhas = consulta.serie(c, de, ate, regiao, geocodigo)
df = pd.DataFrame(linhas)
da = consulta.dados_ate(c)
recorte = nome_por_cod.get(geocodigo) or regiao_sel

st.subheader("Recorte: %s" % recorte)
k = st.columns(4)
def ultimo(col):
    v = df[df[col].notna()]
    return (v.iloc[-1][col], v.iloc[-1]["semana_id"]) if len(v) else (None, None)
for col_ui, (rot, col, chave) in zip(k, [("Casos notificados (SINAN)", "casos_notificados", "casos"),
                                          ("Internações (SIH)", "internacoes", "internacoes"),
                                          ("Leitos clínicos e pediátricos (CNES)", "leitos_clinicos_pediatricos", "leitos"),
                                          ("Pressão (internações por leito)", "pressao_internacoes_por_leito", "pressao")]):
    val, sem = ultimo(col)
    col_ui.metric(rot, "-" if val is None else ("%.2f" % val if col == "pressao_internacoes_por_leito" else "{:,.0f}".format(val).replace(",", ".")),
                  help="Última semana do recorte com valor conhecido: %s" % (rotulo.get(int(sem)) if sem else "nenhuma"))
    col_ui.caption("Dados até %s" % (da[chave].strftime("%d/%m/%Y") if da[chave] else "-"))

if df.empty:
    st.info("Nenhuma semana no período escolhido.")
    st.stop()
if df["casos_provisorio"].any():
    st.warning("As semanas mais recentes de casos são **provisórias**: o SINAN reabre casos por até 60 dias (ver relatório de revisão, R8).")

st.markdown("#### Casos e internações por semana")
st.line_chart(df.set_index("inicio_semana")[["casos_notificados", "casos_provaveis_infodengue", "internacoes"]]
              .rename(columns={"casos_notificados": "Casos SINAN", "casos_provaveis_infodengue": "Casos prováveis InfoDengue", "internacoes": "Internações SIH"}))
st.markdown("#### Pressão sobre a capacidade (internações por leito)")
st.line_chart(df.set_index("inicio_semana")[["pressao_internacoes_por_leito"]].rename(columns={"pressao_internacoes_por_leito": "Internações por leito"}))
st.caption("A linha de pressão para onde faltam internações (o SIH atrasa cerca de 2 meses) ou leitos. Nulo não é zero.")

if not geocodigo:
    st.markdown("#### Municípios com maior pressão na semana")
    sem_rank = st.selectbox("Semana do ranking", [i for i in reversed(ids) if de <= i <= ate], format_func=lambda i: rotulo[i])
    r = pd.DataFrame(consulta.ranking(c, sem_rank, regiao))
    if r.empty:
        st.info("Sem pressão conhecida nessa semana (SIH ainda não chegou ou sem leitos).")
    else:
        st.dataframe(r.rename(columns={"municipio": "Município", "regiao_saude": "Região de saúde", "casos_notificados": "Casos",
                                       "internacoes": "Internações", "leitos_clinicos_pediatricos": "Leitos", "pressao_internacoes_por_leito": "Pressão"}),
                     hide_index=True, use_container_width=True)

st.markdown("#### Frescor das fontes")
f = consulta.frescor(c)
if f:
    st.dataframe(pd.DataFrame(f).rename(columns={"indicador": "Indicador", "dados_ate": "Dados até", "idade_dias": "Idade (dias)", "tolerancia_dias": "Tolerância (dias)",
                                                 "latencia_dias": "Latência de carga (dias)", "situacao": "Situação"}), hide_index=True, use_container_width=True)
else:
    st.caption("Frescor indisponível: rode o pipeline.")
