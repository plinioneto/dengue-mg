# Plataforma de dados abertos: dengue e capacidade assistencial em Minas Gerais

Projeto Aplicado (pós-graduação em Engenharia e Arquitetura de Dados com IA). Sprint 1: R1 (repositório, ADRs, catálogo), R2 (ingestão do SINAN) e R3 (CNES, SIH, InfoDengue) na camada bruta. Sprint 2: R4 (camada tratada), R5 (testes de qualidade) e R6 (reconciliação SINAN x InfoDengue), em dbt.

## Instalação
```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso (a partir da pasta do projeto)
```
export PYTHONPATH=src                                  # Windows (PowerShell): $env:PYTHONPATH="src"
python -m dengue_mg.ingest --lista sinan_prelim sinan_final cnes_lt sih_rd   # o que há para carregar
python -m dengue_mg.ingest cnes_lt sih_rd ibge         # começar pelas fontes menores
python -m dengue_mg.ingest sinan_final sinan_prelim
python -m dengue_mg.ingest infodengue                  # depende de `ibge` ter rodado
python -m dengue_mg.ingest cnes_lt sih_rd              # segunda execução: deve dizer "sem mudança"
pytest
```
Saídas em `data/` (ignorada pelo Git): `data/bronze/<fonte>/*.parquet` e a tabela `bronze_loads` em `data/plataforma.duckdb`.

## Evidência da Sprint 1
- `docs/adr/` e `docs/catalogo_fontes.md` (R1).
- Log de duas execuções seguidas sem duplicar (R2, R3) e a consulta `SELECT * FROM bronze_loads` (tabela de metadados).

## Sprint 2: camada tratada, testes e reconciliação
Pré-requisito: a bruta carregada (comandos acima, incluindo `ibge` e `infodengue`).
```
python -m dengue_mg.tratada          # dbt seed + run + test (esquemas `tratada` e `final` no DuckDB)
python -m dengue_mg.relatorio        # gera docs/evidencias/R5/relatorio_testes.md e R6/relatorio_divergencia.md
pytest tests/test_tratada.py         # teste de ponta a ponta com dados sintéticos
```
- Modelos em `dbt/` (staging, dimensões, fatos e `rec_*`); modelo de dados em `docs/modelo_dados.md`; regras em `docs/adr/0004-tratada-e-reconciliacao.md`.
- Região de saúde: preencher `dbt/seeds/regiao_saude_mg.csv` (geocodigo, regiao_saude, macrorregiao_saude). Enquanto vazio, a dimensão traz "Não informada".
- `--hoje AAAA-MM-DD` fixa a data de referência (execução reprodutível).

## Evidência da Sprint 2
- R4: `docs/modelo_dados.md` e `dbt/models/`. R5: `docs/evidencias/R5/relatorio_testes.md`. R6: `docs/evidencias/R6/relatorio_divergencia.md`.
