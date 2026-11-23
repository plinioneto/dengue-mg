# Análise exploratória das hipóteses H1 e H3

Gerado em 23/11/2026 19:06 sobre `final.indicadores_municipio_semana` (semanas de casos não provisórios; internações até o último "dados até" do SIH).

Análise exploratória: correlação não é causalidade. Casos são do município de notificação e internações do município de ocorrência; o SIH só traz internações do SUS.

## H1: correlação entre casos e internações

### Estado (série semanal de Minas Gerais)

Internações com defasagem de 0 a 4 semanas depois dos casos.

| defasagem_semanas | semanas | pearson | spearman |
|---|---|---|---|
| 0,00 | 245,00 | 0,97 | 0,93 |
| 1,00 | 244,00 | 0,98 | 0,94 |
| 2,00 | 243,00 | 0,97 | 0,94 |
| 3,00 | 242,00 | 0,94 | 0,92 |
| 4,00 | 241,00 | 0,89 | 0,88 |


### Estado, por ano (Spearman)

| ano | semanas | spearman_lag0 | spearman_lag1 | spearman_lag2 |
|---|---|---|---|---|
| 2022,00 | 52,00 | 0,92 | 0,91 | 0,86 |
| 2023,00 | 52,00 | 0,98 | 0,98 | 0,96 |
| 2024,00 | 52,00 | 0,96 | 0,98 | 0,98 |
| 2025,00 | 53,00 | 0,92 | 0,95 | 0,96 |
| 2026,00 | 36,00 | 0,95 | 0,97 | 0,95 |


### Municípios (Spearman por município)

Entram os municípios com ao menos 20 semanas com casos e 10 internações no período: **332 de 853**.

| defasagem_semanas | municipios | mediana | p25 | p75 | pct_rho_ge_05 |
|---|---|---|---|---|---|
| 0,00 | 332,00 | 0,52 | 0,44 | 0,59 | 56,9% |
| 1,00 | 332,00 | 0,52 | 0,44 | 0,60 | 56,3% |
| 2,00 | 332,00 | 0,50 | 0,43 | 0,57 | 50,0% |
| 3,00 | 332,00 | 0,49 | 0,41 | 0,56 | 45,8% |
| 4,00 | 332,00 | 0,47 | 0,40 | 0,53 | 38,6% |


Defasagem com maior mediana: **1 semana(s)**.

## H3: ranking por pressão x ranking por volume de casos

Sem população, a incidência não pode ser calculada (H2 fica pendente); a referência é o volume de casos. Pressão: pico semanal, com mínimo de 5 internações no período (como no painel). Compara-se o topo 20 de cada critério e a correlação de postos (Spearman) entre casos e pressão nos municípios que têm os dois valores.

| periodo | municipios_comparados | spearman_casos_x_pico | spearman_casos_x_media | topo20_em_comum_com_casos_pressao_pico | topo20_em_comum_com_casos_pressao_media | topo20_em_comum_com_casos_internacoes |
|---|---|---|---|---|---|---|
| 2022 | 95 | -0,04 | 0,13 | 3 | 3 | 11 |
| 2023 | 225 | -0,19 | 0,04 | 0 | 1 | 10 |
| 2024 | 337 | -0,01 | 0,19 | 0 | 0 | 9 |
| 2025 | 169 | 0,04 | 0,20 | 2 | 4 | 11 |
| 2026 | 103 | 0,05 | 0,18 | 7 | 8 | 12 |
| 2022 a 2026 | 350 | -0,03 | 0,23 | 0 | 1 | 10 |

