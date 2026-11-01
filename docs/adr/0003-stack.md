# ADR-0003: Pilha de ferramentas

**Status:** aceita (01/11/2026)

**Decisão.** Python para ingestão; DuckDB e Parquet para armazenamento e consulta; dbt-core com adaptador DuckDB para a camada tratada e final (Sprint 2 em diante); GitHub Actions ou cron em VPS para agendar; Streamlit para o painel; Git para versionar.

**Alternativas.** Airflow e PostgreSQL: mais pesados para uma pessoa e para o volume (alguns GB). BigQuery: custo e dependência de nuvem.

**Descompactação de .dbc.** Implementação própria em Python puro (`dbc.py`, PKWare DCL), sem bibliotecas nativas, validada com o vetor do zlib. É mais lenta que bibliotecas em C; se o SINAN nacional demorar demais, trocar por uma biblioteca nativa mantendo a mesma interface de `ler_registros`.
