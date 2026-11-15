# Backlog de produto

| ID | Requisito | Sprint | Artefato de evidência | Vínculo | Estado |
|---|---|---|---|---|---|
| R1 | Repositório, ADRs e catálogo de fontes com grão, chaves e defasagem | S1 | Repositório com ADRs e catálogo | Objetivo (S), H6 | Feito (revisar após a ingestão) |
| R2 | Ingestão do SINAN dengue (2022 a 2026, finais e preliminares) na camada bruta, incremental e idempotente | S1 | Script e log de duas execuções seguidas sem duplicar | H4, H6 | Executado em 15/11; falta a segunda execução (idempotência) |
| R3 | Ingestão de CNES (leitos), SIH (AIH reduzida) e InfoDengue de MG na bruta, com data de publicação e hash | S1 | Tabela `bronze_loads` | H6 | Executado em 15/11; falta a segunda execução (idempotência) |
| R4 | Camada tratada: dimensões de município (com região de saúde) e de semana epidemiológica; fatos de casos, leitos e internações por dengue | S2 | Diagrama do modelo e modelos SQL | H1 a H3, H6 | Feito (executado em 15/11) |
| R5 | Testes de qualidade: chaves, nulos, datas fora do período, valores plausíveis | S2 | Relatório de execução dos testes | Objetivo (M, qualidade) | Feito (66 de 68 testes passam, 2 avisos da fonte) |
| R6 | Reconciliação dos casos SINAN com InfoDengue | S2 | Relatório de divergência por município e semana | H6, Objetivo (M) | Executado; limite calibrado para 15%: 90,9% dos pares dentro (meta 90%); 75,3% dentro de 5% (ADR-0004) |
| R7 | Tabela final por município e semana: casos, internações, leitos, indicador de pressão, "dados até" por indicador | S3 | Tabela final e dicionário de dados | H1 a H3 | A fazer |
| R8 | Versionamento das cargas e medição da revisão das semanas preliminares | S3 | Relatório de revisão média por semana | H4 | A fazer (a base é o versionamento da bruta) |
| R9 | Atualização automática agendada e monitoramento de frescor | S3 | Fluxo agendado e log de execuções | Objetivo (M, frescor) | A fazer |
| R10 | Painel de consulta por município, região de saúde e semana | S3 | Capturas do painel | Objetivo (S) | A fazer |

Se o tempo faltar, o corte é pela ordem inversa de prioridade: primeiro R10, depois R8.
Indicador de pressão: a definir no R7 (proposta inicial: internações por dengue por leito disponível no município, por semana; registrar a decisão em ADR).
