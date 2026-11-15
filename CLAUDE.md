# CLAUDE.md: contexto do projeto para o Claude Code

## O que é
Plataforma de dados abertos, atualizada continuamente, sobre a pressão da dengue na capacidade assistencial de **Minas Gerais** (853 municípios), com histórico desde 2022. Não é análise pontual. É o Projeto Aplicado da pós-graduação em Engenharia e Arquitetura de Dados com IA (XP Educação), do aluno Plínio. **Sem componente de IA nem previsão.** Plataforma de dados apenas.

## Objetivo (SMART)
Até 22/11/2026, ter a plataforma com SINAN, CNES, SIH e InfoDengue de MG por município e semana epidemiológica desde 2022, com indicador de pressão sobre a capacidade e o "dados até" de cada indicador.
Metas: 853 municípios e todas as semanas de 2022 até hoje; atualização em até 7 dias após cada publicação das fontes; 100% das tabelas finais com testes aprovados; casos SINAN x InfoDengue com divergência de até 5% em 90% dos pares município-semana com 10 casos ou mais (semanas com mais de 9 semanas de idade). Os limites de 5% e 90% são iniciais e serão calibrados no R6.

## Prazo
3 sprints de 1 semana: S1 02/11 a 08/11, S2 09/11 a 15/11, S3 16/11 a 22/11/2026 (datas a confirmar). Equipe de uma pessoa.

## Backlog
Ver `docs/backlog.md` (R1 a R10, com artefato de evidência de cada um). Estado atual: Sprint 2 em andamento; R1 a R6 têm código e documentação, falta executar a ingestão (S1) e a tratada (S2) e coletar evidências.

## Decisões já tomadas (não reabrir sem motivo)
Ver `docs/adr/`. Resumo: MG e 2022+; bruta (Parquet, tudo texto) / tratada / final; ingestão idempotente e versionada, chave (fonte, arquivo, sha256); Python + DuckDB/Parquet + dbt-core (dbt-duckdb) + Streamlit; agendamento por GitHub Actions ou cron em VPS; só ferramentas open source e gratuitas.

## Fatos sobre as fontes (medidos em 25/10/2026)
- SINAN prelim: atualizado a cada 1 a 6 dias; maior DT_NOTIFIC 2026-10-18. Regra dos 60 dias: caso fica aberto até 60 dias, então semanas recentes mudam. O arquivo final de 2025 contém datas de 2026 (qualidade).
- CNES LT: mensal; competência 2026-09 publicada em 15/10. SIH RD: mensal, cerca de 2 meses de atraso (2026-08).
- InfoDengue alertcity: semanal (SE 2026-41), tem nowcast (`casos_est`); **não traz código IBGE** (a ingestão acrescenta `geocodigo`).
- CNES e SIH usam município de 6 dígitos; IBGE e InfoDengue usam 7. Padronizar na camada tratada.
- O FTP `ftp.datasus.gov.br` e a API do InfoDengue são acessíveis; os portais `dadosabertos.saude.gov.br` estiveram fora do ar, por isso não são usados.

## Hipóteses (priorizadas)
H1 (verificar com a tabela final): correlação entre casos (SINAN) e internações (SIH) por município. H6: reconciliação SINAN x InfoDengue. H4: revisão das semanas preliminares. H2/H3: ranking de municípios por incidência x por pressão. **H5 (clima) e H7 (validação por entrevistas) estão fora deste ciclo.**

## Convenções
- Textos, comentários, documentação e mensagens em português (Brasil). Redação impessoal na documentação do relatório (sem primeira pessoa).
- Código em `src/dengue_mg/`, testes em `tests/` (pytest), ADRs numerados em `docs/adr/`. Dados em `data/` (fora do Git).
- Bruta nunca corrige dado; correções só na tratada. Toda tabela nova tem teste. Todo indicador final carrega "dados até".
- Dados públicos e anonimizados apenas; a camada de consulta expõe agregados, nunca registros individuais (LGPD).

## Como rodar
Ver `README.md`. Testes: `PYTHONPATH=src pytest`.

## Limitações a ter em mente
- Os testes de `bronze` exigem DuckDB e PyArrow instalados; foram escritos mas **ainda não executados** (a Sprint 1 foi escrita sem acesso à rede). Rodar `pytest` primeiro e corrigir o que aparecer.
- A descompactação de .dbc é em Python puro (lenta em arquivos nacionais). Se passar de cerca de 30 minutos por arquivo, trocar por biblioteca nativa mantendo a interface de `dbc.ler_registros`.

## Definição de pronto de cada requisito
Código ou modelo no repositório + teste + o artefato de evidência listado em `docs/backlog.md` salvo em `docs/evidencias/Rn/` (log, relatório ou captura). Esses artefatos alimentam a seção 2 do relatório.
