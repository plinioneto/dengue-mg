# Análise exploratória das hipóteses H1, H2 (parcial) e H3

Gerado em 23/11/2026 19:42 sobre `final.indicadores_municipio_semana` (semanas de casos não provisórios; internações até o último "dados até" do SIH).

Análise exploratória: correlação não é causalidade. Casos são do município de notificação e internações do município de ocorrência; o SIH só traz internações do SUS.

## H1: correlação entre casos e internações

### Estado (série semanal de Minas Gerais)

Internações com defasagem de 0 a 4 semanas depois dos casos.

| defasagem_semanas | semanas | pearson | spearman |
|---|---|---|---|
| 0 | 245 | 0,97 | 0,93 |
| 1 | 244 | 0,98 | 0,94 |
| 2 | 243 | 0,97 | 0,94 |
| 3 | 242 | 0,94 | 0,92 |
| 4 | 241 | 0,89 | 0,88 |


### Estado, por ano (Spearman)

| ano | semanas | spearman_lag0 | spearman_lag1 | spearman_lag2 |
|---|---|---|---|---|
| 2022 | 52 | 0,92 | 0,91 | 0,86 |
| 2023 | 52 | 0,98 | 0,98 | 0,96 |
| 2024 | 52 | 0,96 | 0,98 | 0,98 |
| 2025 | 53 | 0,92 | 0,95 | 0,96 |
| 2026 | 36 | 0,95 | 0,97 | 0,95 |


### Municípios (Spearman por município)

Entram os municípios com ao menos 20 semanas com casos e 10 internações no período: **332 de 853**.

| defasagem_semanas | municipios | mediana | p25 | p75 | pct_rho_ge_05 |
|---|---|---|---|---|---|
| 0 | 332 | 0,52 | 0,44 | 0,59 | 56,9% |
| 1 | 332 | 0,52 | 0,44 | 0,60 | 56,3% |
| 2 | 332 | 0,50 | 0,43 | 0,57 | 50,0% |
| 3 | 332 | 0,49 | 0,41 | 0,56 | 45,8% |
| 4 | 332 | 0,47 | 0,40 | 0,53 | 38,6% |


Defasagem com maior mediana: **1 semana(s)**.

### Picos: o pico de internações vem depois do pico de casos? (estado, por ano)

Semana do pico com média móvel de 3 semanas; defasagem = semanas entre o pico de casos e o de internações (positiva: internações depois).

| ano | semanas | semana_pico_casos | semana_pico_internacoes | defasagem_semanas |
|---|---|---|---|---|
| 2022 | 52 | 202217 | 202216 | -1 |
| 2023 | 52 | 202314 | 202315 | 1 |
| 2024 | 52 | 202411 | 202412 | 1 |
| 2025 | 53 | 202512 | 202513 | 1 |
| 2026 | 36 | 202615 | 202616 | 1 |


### Picos nos municípios (por município e ano com 20 casos e 10 internações ou mais)

| ano | municipios | mediana_defasagem | pct_internacao_depois | pct_mesma_semana | pct_internacao_antes |
|---|---|---|---|---|---|
| 2022 | 62 | 0,00 | 37,1% | 25,8% | 37,1% |
| 2023 | 170 | 0,00 | 48,8% | 15,3% | 35,9% |
| 2024 | 317 | 1,00 | 50,5% | 15,1% | 34,4% |
| 2025 | 106 | 0,00 | 47,2% | 7,5% | 45,3% |
| 2026 | 54 | 1,00 | 51,9% | 11,1% | 37,0% |


## H2 (parcial): ranking por pressão x ranking por volume de casos

Sem população, a incidência não pode ser calculada (a H2 completa fica pendente); a referência é o volume de casos. Pressão: pico semanal, com mínimo de 5 internações no período (como no painel). Compara-se o topo 20 de cada critério e a correlação de postos (Spearman) entre casos e pressão nos municípios que têm os dois valores.

| periodo | municipios_comparados | spearman_casos_x_pico | spearman_casos_x_media | topo20_em_comum_com_casos_pressao_pico | topo20_em_comum_com_casos_pressao_media | topo20_em_comum_com_casos_internacoes |
|---|---|---|---|---|---|---|
| 2022 | 95 | -0,04 | 0,13 | 3 | 3 | 11 |
| 2023 | 225 | -0,19 | 0,04 | 0 | 1 | 10 |
| 2024 | 337 | -0,01 | 0,19 | 0 | 0 | 9 |
| 2025 | 169 | 0,04 | 0,20 | 2 | 4 | 11 |
| 2026 | 103 | 0,05 | 0,18 | 7 | 8 | 12 |
| 2022 a 2026 | 350 | -0,03 | 0,23 | 0 | 1 | 10 |


## H3: a capacidade relevante depende da região de saúde?

Fluxo das internações por dengue entre o município de residência e o de ocorrência (SIH). Percentuais sobre as internações de residentes em MG.

| ano | total | mesmo município | outro município da mesma região | outra região de saúde | residente fora de MG ou ignorado | pct_fora_do_municipio | pct_dentro_da_regiao |
|---|---|---|---|---|---|---|---|
| 2022 | 2606 | 2297 | 218 | 83 | 8 | 11,6% | 96,8% |
| 2023 | 9294 | 8013 | 847 | 410 | 24 | 13,6% | 95,6% |
| 2024 | 35292 | 29448 | 3758 | 1968 | 118 | 16,3% | 94,4% |
| 2025 | 9675 | 8736 | 577 | 336 | 26 | 9,5% | 96,5% |
| 2026 | 4384 | 3524 | 505 | 331 | 24 | 19,2% | 92,4% |
| Total | 61251 | 52018 | 5905 | 3128 | 200 | 14,8% | 94,9% |


### Municípios que mais recebem internações de residentes de outros municípios (2022 em diante)

| municipio_ocorrencia | regiao_ocorrencia | internacoes_no_municipio | recebidas_de_fora | pct_de_fora | enviadas | saldo |
|---|---|---|---|---|---|---|
| Belo Horizonte | Belo Horizonte/Nova Lima/Santa Luzia   - MG | 6860 | 1933 | 28,2% | 142 | 1791 |
| Uberaba | Uberaba - MG | 1221 | 285 | 23,3% | 2 | 283 |
| Santo Antônio do Monte | Lagoa da Prata/Santo Antônio do Monte - MG | 421 | 223 | 53,0% | 4 | 219 |
| Araguari | Uberlândia/Araguari - MG | 1205 | 212 | 17,6% | 5 | 207 |
| Ipatinga | Ipatinga - MG | 712 | 207 | 29,1% | 9 | 198 |
| Montes Claros | Montes Claros  - MG | 1245 | 191 | 15,3% | 7 | 184 |
| Janaúba | Janaúba/Monte Azul - MG | 509 | 169 | 33,2% | 2 | 167 |
| Brasília de Minas | Brasília de Minas - MG | 248 | 149 | 60,1% | 3 | 146 |
| Contagem | Contagem - MG | 889 | 132 | 14,8% | 275 | -143 |
| Patos de Minas | Patos de Minas - MG | 429 | 122 | 28,4% | 5 | 117 |


### Municípios de residência cujas internações ocorrem em outro município

| municipios_com_10_ou_mais_internacoes | com_metade_ou_mais_fora | pct |
|---|---|---|
| 493 | 159 | 32,3% |

