# Dicionário de dados: tabela final (R7)

`final.indicadores_municipio_semana` (publicada em `data/publicacao/indicadores_municipio_semana.parquet`). Grão: **um registro por município de MG (853) e semana epidemiológica**, de 2022 até a semana corrente (domingo a sábado; a SE 1 é a que contém 4 de janeiro). Chave: (`geocodigo`, `semana_id`). Regras e limitações em `docs/adr/0005-indicador-de-pressao-e-tabela-final.md`.

**Nulo não é zero.** Até o "dados até" de cada grupo, ausência de registro na fonte significa zero ocorrência. Depois dele, o valor é nulo (ainda desconhecido).

| Coluna | Tipo | Descrição | Fonte |
|---|---|---|---|
| `geocodigo` | varchar | Código IBGE do município, 7 dígitos | IBGE |
| `municipio`, `regiao_saude`, `macrorregiao_saude` | varchar | Nome e regiões de saúde (base territorial DATASUS, jun/2026) | IBGE, DATASUS |
| `semana_id` | int | Semana epidemiológica no formato AAAASS (ex.: 202641) | calculada |
| `epi_ano`, `epi_semana` | int | Ano e número da semana epidemiológica | calculada |
| `inicio_semana`, `fim_semana` | date | Domingo e sábado da semana | calculada |
| `casos_notificados` | bigint | Notificações de dengue, sem descartados, no município de notificação, pela semana dos primeiros sintomas (DT_SIN_PRI; se vazia, DT_NOTIFIC) | SINAN |
| `casos_hospitalizados` | bigint | Das notificações, as com hospitalização (HOSPITALI = 1) | SINAN |
| `casos_confirmados` | bigint | Das notificações, as com CLASSI_FIN 10, 11 ou 12 | SINAN |
| `casos_dados_ate` | date | Maior data de notificação carregada | SINAN |
| `casos_provisorio` | boolean | A semana tem até 9 semanas de idade: ainda pode mudar (regra dos 60 dias; ver R8) | derivada |
| `casos_provaveis_infodengue` | bigint | Casos prováveis (`casprov`) do InfoDengue | InfoDengue |
| `casos_estimados_infodengue` | double | Casos estimados com nowcast (`casos_est`) | InfoDengue |
| `nivel_alerta_infodengue` | int | Nível de alerta do InfoDengue (1 a 4) | InfoDengue |
| `infodengue_dados_ate` | date | Fim da última semana carregada | InfoDengue |
| `internacoes` | bigint | Internações por dengue (A90, A91) no município onde ocorreram, pela semana da data de internação | SIH |
| `obitos` | bigint | Das internações, as com óbito (MORTE = 1) | SIH |
| `dias_internacao` | bigint | Soma dos dias de permanência | SIH |
| `internacoes_dados_ate` | date | Maior data de internação carregada (atraso de cerca de 2 meses) | SIH |
| `leitos_existentes` | bigint | Leitos existentes (QT_EXIST), sem hospital-dia, na competência vigente | CNES |
| `leitos_sus` | bigint | Dos existentes, os disponíveis ao SUS (QT_SUS) | CNES |
| `leitos_clinicos_pediatricos` | bigint | Leitos clínicos e pediátricos (TP_LEITO 2 e 5): denominador do indicador de pressão | CNES |
| `leitos_competencia` | date | Competência mensal de leitos usada nesta semana | CNES |
| `leitos_dados_ate` | date | Última competência carregada | CNES |
| `pressao_internacoes_por_leito` | double | **Indicador de pressão**: `internacoes / leitos_clinicos_pediatricos`. Nulo sem internações conhecidas ou sem leito | derivada |
| `sem_leito_clinico_pediatrico` | boolean | Município sem leito clínico ou pediátrico na competência (pressão indefinida) | derivada |
| `pressao_dados_ate` | date | O menor entre `internacoes_dados_ate` e `leitos_dados_ate` | derivada |

**Leitura da pressão.** Valor 0,5 = meia internação por dengue na semana para cada leito clínico ou pediátrico existente. Não é ocupação: a fonte não traz ocupação, e o leito existente não é o livre.

## Tabelas auxiliares

- `final.frescor` (uma linha por indicador): `indicador`, `fonte`, `dados_ate`, `idade_dias`, `tolerancia_dias`, `ultima_publicacao`, `ultima_carga`, `latencia_dias` (da publicação da fonte à carga; meta de até 7), `situacao` (`ok`, `atrasado` ou `sem_dados`), `verificado_em`.
- `final.revisao_sinan_versoes` (R8): casos por município e semana em cada versão do SINAN preliminar.
- `final.rec_sinan_infodengue` e `final.rec_resumo` (R6): reconciliação SINAN x InfoDengue.
- `execucoes` (R9): uma linha por etapa de cada execução do pipeline (`execucao`, `etapa`, `status`, `inicio`, `duracao_s`, `detalhe`).
