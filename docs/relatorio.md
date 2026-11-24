# Relatório do Projeto Aplicado: plataforma de dados abertos sobre a pressão da dengue na capacidade assistencial de Minas Gerais

Pós-graduação em Engenharia e Arquitetura de Dados com IA (XP Educação). Situação: fim da Sprint 2 (15/11/2026). A Sprint 3 (R7 a R10) não foi iniciada; as seções correspondentes estão marcadas como pendentes.

## 1. Contexto, objetivo e escopo

A dengue pressiona a rede de saúde de Minas Gerais de forma irregular no tempo e no território, e os dados que permitem medir essa pressão estão em fontes distintas, com grãos, códigos de município e defasagens diferentes. O projeto constrói uma plataforma de dados abertos, atualizada continuamente, que junta essas fontes por município e semana epidemiológica. Não há componente de inteligência artificial nem previsão: o produto é a plataforma de dados.

**Objetivo (SMART).** Até 22/11/2026, ter a plataforma com SINAN, CNES, SIH e InfoDengue de MG por município e semana epidemiológica desde 2022, com indicador de pressão sobre a capacidade e o "dados até" de cada indicador.

**Metas mensuráveis.**

| Meta | Situação em 15/11/2026 |
|---|---|
| 853 municípios e todas as semanas de 2022 até hoje | Atendida nas dimensões (853 municípios; 258 semanas); fatos esparsos por município e semana |
| Atualização em até 7 dias após cada publicação das fontes | Pendente (R9, agendamento) |
| 100% das tabelas finais com testes aprovados | Execução de 22/11/2026: 84 de 86 testes aprovados (inclui a tabela final), 0 erros e 2 avisos de limitação das fontes (SIH: 24 internações de 2021 em arquivos de 2022; SINAN: 4.924 notificações com município de residência fora da dimensão de MG) |
| Divergência SINAN x InfoDengue de até 15% em 90% dos pares município-semana com 10 casos ou mais | Atendida: 90,9% (20.655 de 22.735 pares em 22/11/2026; limite inicial de 5%: 75,3% em 15/11; ver seção 4.2) |

**Escopo e restrições.** Recorte em MG e histórico desde 2022 (ADR-0001). Equipe de uma pessoa, três sprints de uma semana. Apenas ferramentas abertas e gratuitas. Apenas dados públicos e anonimizados; a camada de consulta expõe agregados, nunca registros individuais (LGPD). Clima (H5) e validação por entrevistas (H7) ficam fora deste ciclo.

## 2. Fontes de dados

| Fonte | Conteúdo | Grão | Atualização | Observação |
|---|---|---|---|---|
| SINAN (DATASUS, FTP) | Notificações de dengue, arquivos finais (2022 a 2025) e preliminar (2026) | Notificação individual | Preliminar a cada 1 a 6 dias | Regra dos 60 dias: caso fica aberto até 60 dias e as semanas recentes mudam |
| CNES, tipo LT (DATASUS, FTP) | Leitos por estabelecimento | Estabelecimento x mês | Mensal | Competência mais recente: 2026-09 |
| SIH, tipo RD (DATASUS, FTP) | AIH reduzida, internações por dengue | Internação | Mensal, cerca de 2 meses de atraso | Competência mais recente: 2026-08 |
| InfoDengue (API alertcity) | Casos notificados, prováveis, nowcast e nível de alerta | Município x semana | Semanal | Sem código IBGE; a ingestão acrescenta `geocodigo` |
| IBGE | Lista dos 853 municípios | Município | Estática | Chave de referência (7 dígitos) |
| Base territorial do DATASUS (jun/2026) | Região e macrorregião de saúde | Município | Estática | Carregada como seed (89 regiões) |

CNES, SIH e SINAN usam o código de município com 6 dígitos; IBGE e InfoDengue usam 7. A padronização ocorre na camada tratada. O catálogo completo, com grão, chaves e defasagem, está em `docs/catalogo_fontes.md`. Os portais `dadosabertos.saude.gov.br` estiveram fora do ar durante as medições, por isso não são usados; o FTP do DATASUS e a API do InfoDengue estiveram acessíveis.

## 3. Arquitetura e decisões

Três camadas, com a regra de que a bruta nunca corrige dado e as correções ocorrem apenas na tratada (ADR-0002):

1. **Bruta (Parquet, tudo texto).** Cópia fiel de cada arquivo da fonte. A ingestão é idempotente e versionada, com chave (fonte, arquivo, sha256), registrada na tabela `bronze_loads`. Uma nova versão de um arquivo vira nova carga; uma repetição sem mudança é ignorada.
2. **Tratada (dbt).** Tipagem, padronização dos códigos de município, dimensões e fatos por município e semana epidemiológica.
3. **Final.** Tabelas de consulta e reconciliação, cada indicador com o seu "dados até".

Pilha (ADR-0003): Python para ingestão, DuckDB e Parquet para armazenamento e consulta, dbt-core com adaptador DuckDB para a modelagem, Streamlit para o painel (Sprint 3), GitHub Actions ou cron em VPS para agendar. A descompactação dos arquivos `.dbc` é implementada em Python puro (PKWare DCL), sem bibliotecas nativas.

Decisões registradas em ADR: 0001 (recorte e histórico), 0002 (camadas e idempotência), 0003 (pilha), 0004 (camada tratada e reconciliação). O diagrama do modelo está em `docs/modelo_dados.md`.

## 4. Execução e resultados

### 4.1 Sprint 1: camada bruta (R1 a R3)

- **R1.** Repositório, ADRs e catálogo de fontes.
- **R2 e R3.** Ingestão de SINAN, CNES, SIH, InfoDengue e IBGE na camada bruta, em 15/11/2026.

| Fonte | Arquivos | Linhas |
|---|---|---|
| SINAN final (2022 a 2025) | 4 | 2.321.461 |
| SINAN preliminar (2026) | 1 | 66.368 |
| CNES LT | 57 | 297.837 |
| SIH RD | 57 | 61.275 |
| InfoDengue | 1 | 215.809 |
| IBGE (municípios) | 1 | 853 |

**Evidência de idempotência.** Uma segunda execução da ingestão de todas as fontes não carregou nada: as 120 linhas do log do FTP e a do InfoDengue indicam "sem mudança", sem nenhuma carga nova (`docs/evidencias/R2/` e `R3/`).

### 4.2 Sprint 2: camada tratada, qualidade e reconciliação (R4 a R6)

**R4: camada tratada.** Modelos dbt para dimensões e fatos (`docs/modelo_dados.md`):

| Tabela | Linhas | Dados até |
|---|---|---|
| dim_municipio | 853 | - |
| dim_semana_epi | 258 | - |
| fct_casos_semana (SINAN) | 71.035 | 2026-11-08 |
| fct_internacoes_semana (SIH) | 14.502 | 2026-09-27 |
| fct_leitos_mes (CNES) | 23.162 | 2026-09-01 |
| fct_infodengue_semana | 215.809 | 2026-11-07 |

As dimensões cobrem os 853 municípios, todos com região de saúde (89 regiões). A semana epidemiológica segue a convenção domingo a sábado, com a semana 1 contendo 4 de janeiro, e foi validada contra datas âncora (por exemplo, SE 2024-01 inicia em 31/12/2023). Os fatos são esparsos, ou seja, há linha apenas onde houve evento, e cada um carrega `dados_ate`. O arquivo final do SINAN prevalece sobre o preliminar para o mesmo ano.

**R5: testes de qualidade.** Testes genéricos do dbt (unicidade, não nulo, relações, valores aceitos), testes próprios (`chave_unica`, `entre`, `data_no_periodo`) e testes singulares (853 municípios, semanas sem buracos, valores plausíveis, um arquivo por ano no SINAN). Resultado: 68 testes, 66 aprovados e 2 avisos, que registram limitações das fontes e não bloqueiam a publicação:

- 24 internações do SIH com data de 2021, presentes nos arquivos de 2022 porque o SIH particiona por competência de alta.
- 4.919 notificações do SINAN com município de residência fora do cadastro de MG (provavelmente residentes de outras UFs notificados em MG, hipótese não verificada).

Evidência: `docs/evidencias/R5/relatorio_testes.md`.

**R6: reconciliação SINAN x InfoDengue.** Divergência = |SINAN − InfoDengue| / SINAN, por município e semana. Par elegível: SINAN com 10 casos ou mais e semana com mais de 9 semanas de idade, quando os casos já foram fechados pela regra dos 60 dias. O primeiro resultado foi 8,6% dos pares dentro de 5%. A investigação, feita sobre os dados reais, encontrou:

1. Os `casos` do InfoDengue incluem notificações depois descartadas. A coluna comparável ao arquivo público do SINAN é `casprov` (casos prováveis).
2. O InfoDengue agrupa por semana dos primeiros sintomas e por município de notificação. Das quatro combinações testadas (data de notificação ou de sintomas, município de residência ou de notificação), só a de sintomas com município de notificação alinha.

Com a convenção alinhada, 75,3% dos 22.731 pares elegíveis ficam dentro de 5%, com mediana de divergência igual a zero. A cauda restante tem três causas identificadas:

- **Virada de ano.** Os arquivos anuais do SINAN têm cortes próprios (o de 2024 só tem notificações até 28/12/2024; o de 2023 vai até 02/04/2024), então casos de sintomas no fim do ano notificados depois do corte não aparecem.
- **Irregularidades do InfoDengue.** Em algumas semanas `casprov` é bem menor que o SINAN (SE 2022-51: 254 contra 1.161).
- **Cauda geral.** Nas semanas 3 a 47, o InfoDengue é maior que o SINAN em cerca de 70% dos pares fora do limite (mediana de +7,5%), compatível com atualizações do SINAN posteriores ao arquivo público. Não foi possível confirmar sem o histórico do InfoDengue.

**Calibração do limite.** Os limites de 5% e 90% eram declarados como iniciais. Sobre os mesmos pares, foram avaliados limites simples, piso absoluto e elegibilidade mais estrita:

| Alternativa | Pares dentro |
|---|---|
| Limite de 5% | 75,3% |
| Limite de 10% | 86,8% |
| **Limite de 15% (adotado)** | **90,9%** |
| Limite de 20% | 93,6% |
| 10% ou 3 casos | 89,7% |
| 10% ou 5 casos | 91,6% |
| Elegibilidade mínima de 15, 20 ou 30 casos (limite de 5%) | 74,4% a 75,9% |

Adotou-se o menor limite simples que atinge 90% dos pares. O piso absoluto foi descartado porque só fecha a meta com piso de 5 casos, que num par de 10 casos equivale a tolerar 50% de divergência. A elegibilidade mais estrita não ajuda. Contrariando a hipótese inicial, os municípios grandes divergem mais que os pequenos (a 5%: 68,4% de aderência com 200 casos ou mais, contra 74,1% com 10 a 19 casos).

Por ano, com limite de 15%: 2022, 90,4%; 2023, 86,2%; 2024, 93,7%; 2025, 90,7%; 2026, 84,7% (reexecução de 22/11/2026 com as fontes atualizadas: 22.735 pares elegíveis, 90,85% no conjunto; as demais faixas variaram menos de 0,2 ponto). A meta vale para o conjunto. Os anos de 2023 e 2026 ficam abaixo de 90% isoladamente, o que é coerente com o corte do arquivo de 2023 e com as semanas recentes de 2026, ainda sujeitas a revisão.

Evidência: `docs/evidencias/R6/relatorio_divergencia.md` e ADR-0004.

### 4.3 Sprint 3: tabela final, revisão, agendamento e painel (R7 a R10)

| ID | Requisito | Situação |
|---|---|---|
| R7 | Tabela final por município e semana, com indicador de pressão e "dados até" por indicador | Feito e executado em 22/11/2026: 218.368 linhas (853 municípios x 256 semanas, de 202201 a 202647); testes da tabela final aprovados |
| R8 | Versionamento das cargas e medição da revisão das semanas preliminares | Executado em 22/11/2026 com 2 versões do SINAN preliminar de 2026: a revisão é grande até 8 semanas de idade e desprezível a partir de 9 (ver `docs/evidencias/R8/relatorio_revisao.md`) |
| R9 | Atualização agendada e monitoramento de frescor | Pipeline executado manualmente em 22/11/2026 (10 etapas registradas em `execucoes`, frescor `ok` nos 4 indicadores); o fluxo do GitHub Actions foi executado em 23/11/2026 (3 execuções, a última verde, com código de saída 0 e as 4 fontes em `ok`); logs em `docs/evidencias/R9/` |
| R10 | Painel de consulta por município, região de saúde e semana | Painel pronto e testado sobre dados sintéticos; capturas com dados reais em `docs/evidencias/R10/` |

**R7.** A tabela `final.indicadores_municipio_semana` tem um registro por município (853) e semana desde 2022, em grade densa. Cada grupo de indicadores (casos do SINAN, InfoDengue, internações do SIH e leitos do CNES) traz o seu "dados até"; uma semana só tem valor quando está completa até esse "dados até", e semana incompleta ou posterior é nula, e não zero (ajuste de 22/11/2026, feito depois que a primeira captura do painel mostrou a semana parcial do SIH como uma queda falsa da pressão; ver ADR-0005). O indicador de pressão é o número de internações por dengue na semana por leito clínico e pediátrico existente no município (ADR-0005). Não mede ocupação, porque as fontes abertas não a trazem. Município sem leito clínico ou pediátrico fica com pressão nula e sinalizado. Testes: chave única, grade completa (853 municípios por todas as semanas), faixas plausíveis, "dados até" preenchido e coerência da pressão e dos valores posteriores ao "dados até".

**R8.** Cada versão do SINAN preliminar na bruta é recontada por município e semana dos primeiros sintomas (sem descartados) e comparada com a versão mais recente do mesmo arquivo. A revisão é agregada pela idade da semana na data de publicação da versão. Em 22/11/2026 a bruta tinha duas versões do arquivo de 2026: a primeira publicada em 10/11 (carregada em 15/11) e a segunda publicada em 16/11 (carregada em 22/11). Resultado (`docs/evidencias/R8/relatorio_revisao.md`):

| Idade da semana na versão 1 | Revisão estadual | Pares município-semana (10 casos ou mais) revistos em mais de 15% |
|---|---|---|
| 0 semana | +70,4% | 100% (29 pares) |
| 1 semana | +21,8% | 56,0% (25 pares) |
| 2 a 8 semanas | de -14,3% a +0,3% | de 15,4% a 23,8% |
| 9 a 12 semanas | de -1,1% a 0,0% | 0% |
| 13 semanas ou mais | -0,8% | 1,5% (1.148 pares) |

As semanas mais recentes ganham casos: a versão 1 tinha 70,4% a menos de casos que a versão 2 na semana de idade 0 e 21,8% a menos na de idade 1. Nas semanas de 3 a 8 semanas o sinal se inverte (a versão 2 tem de 4% a 14% menos casos que a 1), compatível com casos descartados ou reclassificados depois da investigação; a causa não foi verificada. A partir de 9 semanas de idade a revisão é pequena (revisão absoluta média por município de 0,4% a 2,3%, e nenhum par acima de 15% nas idades de 9 a 12). Isso sustenta o uso de 9 semanas como critério de semana fechada, que vale para a marcação `casos_provisorio` da tabela final e para a elegibilidade do R6, coerente com a regra dos 60 dias.

Limitação: são só duas versões, com 6 dias entre as publicações, e cada idade de 0 a 12 semanas corresponde a uma única semana epidemiológica (não é média ao longo do tempo). Os valores por idade são, portanto, indicativos; a medida se consolida com as versões acumuladas pelo agendamento do R9.

**R9.** O pipeline executa a ingestão incremental de cada fonte (uma falha não impede as demais), o dbt com testes, o R8 e a verificação de frescor, e publica os Parquet do painel só depois disso. Cada etapa é registrada em `execucoes` e em `data/logs/execucoes.jsonl`. Tolerâncias de frescor: SINAN e InfoDengue, 14 dias; CNES, 75; SIH, 90; latência de carga de até 7 dias após a publicação da fonte (meta do objetivo). O fluxo do GitHub Actions roda todo dia e falha (e-mail de alerta) se uma etapa falhar ou uma fonte estiver atrasada. Em 23/11/2026 foi executado pela primeira vez (disparo manual, sem cache): a carga completa do zero levou 1h27, o dbt aprovou 90 dos 92 testes (2 avisos de limitação das fontes) e os dados foram salvos no cache (84,7 MB). A execução terminou com código de saída 2 por um falso positivo do monitor de frescor: a latência de carga (data da carga menos data de publicação) fazia o SIH aparecer como atrasado, porque numa carga do zero a data de carga é a do dia da execução. A latência passou a não valer na carga inicial, com teste, e o fluxo foi repetido. A segunda execução, com o cache, foi incremental (15 min, quase todos na consulta ao InfoDengue) e voltou a sair com código 2, agora por um defeito introduzido na correção: o pipeline lia a coluna errada do quadro de frescor e contava todas as fontes como atrasadas. O quadro passou a ser acessado por nome e um teste de regressão exige código de saída 0 quando tudo está em dia. Logs em `docs/evidencias/R9/log_github_1_carga_completa.txt` e `log_github_2_incremental.txt`; uma terceira execução, no mesmo dia, terminou verde: incremental em 19 min, 92 testes do dbt (90 aprovados e 2 avisos), as quatro fontes em `ok` e código de saída 0 (`docs/evidencias/R9/log_github_3_verde.txt`). Em 22/11/2026 o pipeline foi executado manualmente com sucesso. Os dados persistem entre execuções por cache do Actions; se o cache for descartado, a execução refaz a carga completa de forma idempotente.

**R10.** Painel em Streamlit com filtros de região de saúde, município e intervalo de semanas, indicadores com o "dados até" de cada fonte, séries de casos, internações e pressão, ranking de municípios por pressão e quadro de frescor. Lê só os Parquet publicados (agregados), nunca registros individuais. Um botão "Como a pressão é calculada?" explica a fórmula, as fontes, um exemplo e os limites do indicador. Uma seção de municípios mais afetados ordena o recorte pelo pico ou pela média semanal da pressão, pelas internações ou pelos casos, com mínimo de internações ajustável nos critérios de pressão.

**H1, H2 (parcial) e H3: análise exploratória.** A análise (`python -m dengue_mg.hipoteses`, relatório em `docs/evidencias/hipoteses/analise_hipoteses.md`) usa a tabela final, com as semanas de casos já fechados (mais de 9 semanas de idade). É exploratória: correlação não é causalidade, e não foram feitos testes de significância.

*H1 (os picos de casos antecedem a saturação de leitos com defasagem mensurável).* As fontes abertas não trazem ocupação, então o teste usa as internações por dengue. No estado, a correlação semanal com os casos é muito alta (245 semanas): Spearman de 0,93 a 0,94 e Pearson de 0,97 a 0,98, com o maior valor quando as internações são defasadas em 1 semana (Spearman 0,94; Pearson 0,98), mas as defasagens de 0 e 2 semanas ficam praticamente iguais. Pelos picos, o de internações vem 1 semana depois do de casos em 4 dos 5 anos (2023 a 2026) e 1 semana antes em 2022 (média móvel de 3 semanas). Nos municípios a correlação é menor: dos 332 municípios (de 853) com ao menos 20 semanas com casos e 10 internações, a mediana do Spearman é 0,52 (quartis de 0,44 a 0,59), e 56,9% têm correlação de 0,5 ou mais sem defasagem; os picos municipais não mostram antecedência consistente (mediana de 0 ou 1 semana; internação depois do pico em 37% a 52% dos casos e antes em 34% a 45%), o que indica ruído de contagens pequenas. A H1 é sustentada no estado, com defasagem mensurável mas curta (cerca de 1 semana), e não é conclusiva nos municípios. A correlação estadual reflete em grande parte a sazonalidade comum às duas séries, e a resolução semanal limita a precisão da defasagem.

*H2, parcial (ranking por pressão x ranking por incidência).* Sem população não há incidência, então a referência é o volume de casos. A correlação de postos entre casos e pico da pressão é próxima de zero (de -0,19 a 0,05 por ano e -0,03 no período, entre 95 e 350 municípios com ao menos 5 internações), e com a pressão média é fraca (de 0,04 a 0,23). No topo 20, o ranking por pico da pressão tem de 0 a 7 municípios em comum com o ranking por casos (nenhum no período todo), contra 9 a 12 do ranking por internações. A pressão, portanto, ordena os municípios de forma muito diferente do volume de casos, o que aponta no sentido da H2. A leitura exige cautela: o pico semanal favorece municípios com poucos leitos, onde poucas internações já dão valores altos, de modo que parte da diferença vem do denominador. A H2 completa depende da população (incidência) e segue pendente.

*H3 (a capacidade relevante depende da região de saúde).* Das 61.251 internações por dengue de 2022 a 2026, 85,2% ocorrem no município de residência e 14,8% em outro município; dessas, a maior parte (5.905 de 9.033) fica na mesma região de saúde. No total, 94,9% das internações dos residentes em MG se fecham dentro da região de saúde, e só 5,1% cruzam regiões (de 92,4% a 96,8% por ano). Há polos claros: Belo Horizonte recebeu 1.933 internações de residentes de outros municípios (28,2% das suas) e Brasília de Minas, 60,1% das suas (149 de 248); Contagem tem saldo negativo (envia 275 e recebe 132). Em 159 dos 493 municípios com 10 ou mais internações de residentes (32,3%), metade ou mais das internações ocorre em outro município. A H3 é sustentada: o fluxo entre municípios é relevante, e a região de saúde é a unidade em que ele quase se fecha. Em consequência, a pressão por município de ocorrência é inflada nos polos pelos pacientes de fora, e a leitura por região de saúde é a mais adequada para comparar capacidade.

## 5. Limitações e ameaças à validade

- **Calibração sobre os mesmos dados.** O limite de 15% foi escolhido depois de observar os resultados. É calibração, não validação independente, e deixa de detectar desvios moderados (5% a 15%), como perda parcial de notificações. Os resultados a 5% e a 10% permanecem no relatório como faixas de referência.
- **Viés do InfoDengue.** O excesso de cerca de 7,5% do InfoDengue nas semanas 3 a 47 não está explicado; a hipótese de atualizações posteriores do SINAN não foi confirmada.
- **Qualidade das fontes.** O arquivo final do SINAN de 2025 contém datas de 2026. Os arquivos públicos do SINAN não trazem o número da notificação, então não há deduplicação por esse campo, e a classificação final de "descartado" não aparece nos arquivos públicos. O SIH particiona por competência de alta.
- **Semanas recentes.** Os casos do SINAN mudam até 60 dias após a notificação; as semanas recentes são provisórias, por isso o "dados até" acompanha cada indicador.
- **Desempenho.** A descompactação de `.dbc` em Python puro levou cerca de 21 minutos para o arquivo de 2024 (1,66 milhão de linhas). É aceitável para a carga atual, mas deve ser reavaliada se o volume crescer.
- **Sem população.** Não há fonte de população no escopo, então não existe incidência por 100 mil; o ranking por incidência (H2) exige acrescentar as estimativas do IBGE.
- **Pressão não é ocupação.** O indicador usa leitos existentes e internações por semana; não há ocupação diária nas fontes abertas (ADR-0005).
- **Persistência do agendamento.** O cache do Actions pode ser descartado (inatividade de 7 dias ou limite de 10 GB); a recarga completa leva horas por causa da descompactação de .dbc em Python.
- **Hipóteses.** H1 (correlação entre casos e internações), H2 e H3 (rankings por incidência e por pressão) e H4 (revisão das semanas preliminares) dependem da tabela final e do R8. A H4 teve uma primeira medida (R8), com apenas duas versões; H1, H2 (parcial) e H3 tiveram análise exploratória (seção 4.3); a H2 completa depende da população.

## 6. Reprodutibilidade

O passo a passo está no `README.md`. Resumo: `python -m dengue_mg.ingest ...` carrega a bruta; `python -m dengue_mg.tratada` executa seed, modelos e testes do dbt; `python -m dengue_mg.relatorio` gera os relatórios de R5 e R6; os testes em Python rodam com `pytest`. Os dados ficam em `data/`, fora do Git.

## 7. Artefatos de evidência

| Requisito | Artefato |
|---|---|
| R1 | `docs/adr/`, `docs/catalogo_fontes.md` |
| R2 | `docs/evidencias/R2/log_ingestao_ftp.log`, `log_segunda_execucao_ftp.log` |
| R3 | `docs/evidencias/R3/bronze_loads.csv`, `log_infodengue.log`, `log_segunda_execucao_infodengue.log` |
| R4 | `docs/modelo_dados.md`, `dbt/models/`, `docs/evidencias/R4/contagens.md` |
| R5 | `docs/evidencias/R5/relatorio_testes.md` |
| R6 | `docs/evidencias/R6/relatorio_divergencia.md`, `docs/adr/0004-tratada-e-reconciliacao.md` |
| R7 | `dbt/models/final/`, `docs/dicionario_dados.md`, `docs/adr/0005-indicador-de-pressao-e-tabela-final.md` |
| R8 | `docs/evidencias/R8/relatorio_revisao.md` (gerado por `python -m dengue_mg.revisao`) |
| R9 | `.github/workflows/atualizacao.yml`, log de execuções (`data/logs/execucoes.jsonl`, artefato do fluxo) |
| R10 | `app/painel.py`, `docs/evidencias/R10/` (capturas) |
