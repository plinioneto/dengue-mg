# Reconciliação SINAN x InfoDengue (R6)

Gerado em 15/11/2026 15:09. Divergência = |SINAN - InfoDengue| / SINAN. Par elegível: SINAN com 10 casos ou mais e semana com mais de 9 semanas de idade.

## Meta (90% dos pares com divergência até 15%)

| Recorte | Pares elegíveis | Dentro do limite | % dentro | Meta | Mediana da divergência |
|---|---|---|---|---|---|
| 2022 | 1879 | 1699 | 90.4% | 90% | 0.0% |
| 2023 | 5318 | 4582 | 86.2% | 90% | 0.2% |
| 2024 | 11578 | 10853 | 93.7% | 90% | 0.0% |
| 2025 | 2784 | 2525 | 90.7% | 90% | 0.0% |
| 2026 | 1172 | 994 | 84.8% | 90% | 0.0% |
| total | 22731 | 20653 | 90.9% | 90% | 0.0% |

## Sensibilidade ao limite de divergência

| Limite | % dos pares dentro | % dentro, sem semanas 1-2 e 48-53 (virada de ano) |
|---|---|---|
| 5% | 75.3 | 77.4 |
| 10% | 86.8 | 88.7 |
| 15% | 90.9 | 92.6 |
| 20% | 93.6 | 95.2 |

Limite calibrado no R6 (ADR-0004): 15%, o menor entre 5%, 10% e 15% que atinge 90% dos pares. As faixas de 5% e 10% ficam como referência.

## Municípios com menor aderência (pelo menos 5 pares elegíveis)

| Município | Pares | % dentro do limite |
|---|---|---|
| Bertópolis | 5 | 0.0 |
| Cambuí | 11 | 18.2 |
| Uberaba | 162 | 28.4 |
| Belo Horizonte | 244 | 35.7 |
| Antônio Dias | 10 | 40.0 |
| Contagem | 183 | 41.5 |
| Chiador | 12 | 41.7 |
| Matozinhos | 24 | 45.8 |
| Simão Pereira | 13 | 46.2 |
| Ribeirão das Neves | 113 | 47.8 |
| Vespasiano | 48 | 47.9 |
| Fama | 6 | 50.0 |
| Abaeté | 27 | 51.9 |
| Além Paraíba | 44 | 54.5 |
| Esmeraldas | 43 | 60.5 |
| Nazareno | 13 | 61.5 |
| Funilândia | 13 | 61.5 |
| Presidente Olegário | 19 | 63.2 |
| Pirapora | 69 | 63.8 |
| Berilo | 14 | 64.3 |

## 30 maiores divergências entre pares elegíveis

| Município | Semana | SINAN | InfoDengue | Divergência |
|---|---|---|---|---|
| Uberaba | 202338 | 11 | 186 | 1590.9% |
| Uberaba | 202330 | 10 | 166 | 1560.0% |
| Uberaba | 202332 | 10 | 164 | 1540.0% |
| Vespasiano | 202420 | 19 | 300 | 1478.9% |
| Vespasiano | 202411 | 78 | 1138 | 1359.0% |
| Uberaba | 202346 | 10 | 143 | 1330.0% |
| Vespasiano | 202412 | 76 | 1060 | 1294.7% |
| Uberaba | 202337 | 11 | 152 | 1281.8% |
| Uberaba | 202340 | 10 | 130 | 1200.0% |
| Vespasiano | 202418 | 29 | 361 | 1144.8% |
| Uberaba | 202329 | 15 | 184 | 1126.7% |
| Uberaba | 202334 | 13 | 152 | 1069.2% |
| Uberaba | 202336 | 12 | 131 | 991.7% |
| Uberaba | 202333 | 13 | 132 | 915.4% |
| Uberaba | 202345 | 18 | 176 | 877.8% |
| Vespasiano | 202410 | 133 | 1300 | 877.4% |
| Uberaba | 202328 | 17 | 166 | 876.5% |
| Uberaba | 202335 | 16 | 146 | 812.5% |
| Uberaba | 202331 | 12 | 106 | 783.3% |
| Vespasiano | 202417 | 26 | 209 | 703.8% |
| Uberaba | 202341 | 16 | 128 | 700.0% |
| Uberaba | 202327 | 30 | 219 | 630.0% |
| Uberaba | 202326 | 40 | 280 | 600.0% |
| Bocaiúva | 202352 | 21 | 144 | 585.7% |
| Esmeraldas | 202414 | 68 | 443 | 551.5% |
| Antônio Dias | 202349 | 11 | 70 | 536.4% |
| Uberaba | 202611 | 14 | 84 | 500.0% |
| Presidente Olegário | 202217 | 13 | 77 | 492.3% |
| Vespasiano | 202409 | 148 | 860 | 481.1% |
| Ribeirão das Neves | 202427 | 10 | 58 | 480.0% |
