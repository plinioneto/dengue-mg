# Plataforma de dados abertos: dengue e capacidade assistencial em Minas Gerais

Projeto Aplicado (pós-graduação em Engenharia e Arquitetura de Dados com IA). Sprint 1: R1 (repositório, ADRs, catálogo), R2 (ingestão do SINAN) e R3 (CNES, SIH, InfoDengue) na camada bruta. Sprint 2: R4 (camada tratada), R5 (testes de qualidade) e R6 (reconciliação SINAN x InfoDengue), em dbt. Sprint 3: R7 (tabela final), R8 (revisão das semanas preliminares), R9 (atualização agendada e frescor) e R10 (painel).

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
- Região de saúde: preencher `dbt/seeds/regiao_saude_mg.csv` (cod6, regiao_saude, macrorregiao_saude). Preenchido com a base territorial do DATASUS (jun/2026).
- `--hoje AAAA-MM-DD` fixa a data de referência (execução reprodutível).

## Evidência da Sprint 2
- R4: `docs/modelo_dados.md` e `dbt/models/`. R5: `docs/evidencias/R5/relatorio_testes.md`. R6: `docs/evidencias/R6/relatorio_divergencia.md`.

## Sprint 3: tabela final, revisão, agendamento e painel
```
python -m dengue_mg.pipeline         # ingestão incremental + dbt (seed, run, test) + revisão (R8) + frescor + publicação em Parquet
python -m dengue_mg.pipeline --sem-ingestao   # só reprocessa tratada e final
python -m dengue_mg.revisao          # só o R8: docs/evidencias/R8/relatorio_revisao.md
streamlit run app/painel.py          # painel (R10), lê data/publicacao/*.parquet
```
- **R7:** `dbt/models/final/indicadores_municipio_semana.sql`; dicionário em `docs/dicionario_dados.md`; indicador de pressão no ADR-0005.
- **R8:** compara cada versão do SINAN preliminar da bruta com a mais recente. Precisa de duas ou mais cargas com conteúdo diferente; enquanto houver uma só, o relatório diz que não há o que medir.
- **R9:** `.github/workflows/atualizacao.yml` roda o pipeline todo dia (09:17 UTC) e pode ser disparado à mão. Código de saída: 0 certo, 1 etapa falhou, 2 fonte atrasada. O log fica em `data/logs/execucoes.jsonl` e na tabela `execucoes`, e sobe como artefato do fluxo. Alternativa em VPS (ADR-0003), a partir da pasta do projeto:
  `17 9 * * *  cd /caminho/dengue-mg && PYTHONPATH=src python -m dengue_mg.pipeline >> data/logs/cron.log 2>&1`
- **R10:** o painel não abre o DuckDB de trabalho (que fica travado durante a atualização): lê os Parquet que o pipeline publica em `data/publicacao/`. Expõe só agregados, com uma seção de municípios mais afetados (por pico ou média da pressão, internações ou casos, com mínimo de internações ajustável). Capturas: `python scripts/capturar_painel.py` (requer Playwright) grava em `docs/evidencias/R10/`.

## Evidência da Sprint 3
- R7: `docs/dicionario_dados.md` e a tabela `final.indicadores_municipio_semana`. R8: `docs/evidencias/R8/relatorio_revisao.md`. R9: `.github/workflows/atualizacao.yml` e o log de execuções. R10: `docs/evidencias/R10/`.
