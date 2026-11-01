# Plataforma de dados abertos: dengue e capacidade assistencial em Minas Gerais

Projeto Aplicado (pós-graduação em Engenharia e Arquitetura de Dados com IA). Esta é a Sprint 1: R1 (repositório, ADRs, catálogo), R2 (ingestão do SINAN) e R3 (CNES, SIH, InfoDengue) na camada bruta.

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
