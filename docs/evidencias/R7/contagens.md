# Tabela final (R7): contagens da execução de 22/11/2026

Saída da consulta executada na máquina do autor, sobre `data/plataforma.duckdb` após `python -m dengue_mg.pipeline`:

```
select count(*), count(distinct geocodigo), min(semana_id), max(semana_id) from final.indicadores_municipio_semana
[(218368, 853, 202201, 202647)]
```

218.368 linhas = 853 municípios x 256 semanas epidemiológicas (202201 a 202647).

"Dados até" por grupo de indicadores (`final.frescor`, mesma execução): casos SINAN 14/11/2026; InfoDengue 14/11/2026; leitos CNES 01/10/2026; internações SIH 27/09/2026. A pressão é conhecida até o menor dos dois últimos (27/09/2026).

Testes do dbt: 86 (84 aprovados, 2 avisos, 0 erros), dos quais 18 sobre `indicadores_municipio_semana`.

Reconciliação reexecutada (`final.rec_resumo`): total 22.735 pares elegíveis, 20.655 dentro do limite de 15% (90,85%); por ano: 2022 1.879/1.699 (90,4%); 2023 5.318/4.582 (86,2%); 2024 11.578/10.853 (93,7%); 2025 2.784/2.525 (90,7%); 2026 1.176/996 (84,7%).
