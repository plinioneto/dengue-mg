# ADR-0004: Regras da camada tratada e da reconciliação SINAN x InfoDengue

**Status:** aceita (09/11/2026), limites a calibrar no R6

**Decisões da camada tratada (R4).**
- Cada fonte lê da bruta a **última versão de cada arquivo** (`bronze_loads`, maior `loaded_at`). As versões antigas ficam na bruta para o R8.
- **SINAN:** vale o arquivo final do ano, se existir; senão o preliminar. O arquivo público do SINAN não traz NU_NOTIFICA (anonimizado, verificado nos dados em 15/11/2026), então não há chave para deduplicar linhas; a sobreposição entre arquivos é evitada usando um arquivo por ano. Casos descartados (CLASSI_FIN = 5) não entram nos fatos. Casos são atribuídos ao **município de residência** (ID_MN_RESI; se vazio, o de notificação) e à semana da **data de notificação**.
- **SIH:** internações atribuídas ao **município onde ocorreram** (MUNIC_MOV), porque o indicador mede pressão sobre a capacidade local, e à semana da data de internação (DT_INTER). Internações de residentes (MUNIC_RES) ficam disponíveis na tratada para análises futuras.
- **CNES:** leitos por município e competência mensal. Exclui leito hospital-dia (TP_LEITO 7). `leitos_clinicos_pediatricos` (TP_LEITO 2 e 5) é a referência inicial de capacidade para dengue; a escolha final do denominador do indicador de pressão é do R7.
- **Código de município:** CNES, SIH e SINAN usam 6 dígitos; IBGE e InfoDengue, 7. A dimensão guarda os dois (`geocodigo`, `cod6`) e os fatos usam `geocodigo`.
- **Semana epidemiológica:** domingo a sábado; a semana 1 é a que contém 4 de janeiro (ancoras testadas em `dbt/tests/dim_semana_ancoras.sql`).
- **Datas fora do período** (ex.: 2026 no arquivo final de 2025, ou futuras): a tratada mantém o registro com `data_fora_periodo`; os fatos usam só datas de 2022 até a data de referência. O teste correspondente é aviso, não falha, porque é limitação conhecida da fonte (no SIH, internações de 2021 aparecem em arquivos de 2022 pela competência de saída).
- **Região de saúde:** vem do seed `dbt/seeds/regiao_saude_mg.csv` (cod6, regiao_saude, macrorregiao_saude), gerado da base territorial do DATASUS (`/territorio/tabelas/2026/06-base_territorial_jun26.zip`: `rl_municip_regsaud`, `tb_regsaud`, `rl_regsaud_macsaud`, `tb_macsaud`). Município fora do seed vira "Não informada"; não se inventa o dado.
- **"Dados até":** cada fato carrega `dados_ate`, a data mais recente da fonte (notificação, internação, competência ou fim da semana).

**Reconciliação (R6).** Divergência = |casos SINAN − casos InfoDengue| / casos SINAN, por município e semana, comparando com `casos` (notificados) do InfoDengue, não com o nowcast (`casos_est`, que fica na tabela para consulta). Par elegível: SINAN com 10 casos ou mais e semana com mais de 9 semanas de idade. Meta: 90% dos pares elegíveis com divergência de até 5%. Parâmetros em `dbt_project.yml` (`rec_*`), a calibrar com os dados reais.

**Testes (R5).** Genéricos do dbt (unique, not_null, relationships, accepted_values) mais próprios (`chave_unica`, `entre`, `data_no_periodo`) e singulares em `dbt/tests/` (853 municípios, semanas sem buracos, valores plausíveis, um arquivo por ano no SINAN). O relatório sai de `run_results.json` em `docs/evidencias/R5/`.

**Consequências.** Mudar a regra de atribuição (residência x ocorrência) altera os fatos e deve ser registrado aqui. Os testes de plausibilidade usam limites iniciais e podem ser ajustados após a primeira execução com dados reais.

**Achado da primeira execução (15/11/2026).** Com a regra inicial (SINAN por data de notificação, residência, sem descartados), apenas 8,6% dos 23.285 pares elegíveis ficaram dentro de 5% (meta: 90%). O InfoDengue tem, em mediana, cerca de 38% mais casos que o SINAN, de forma consistente em todos os anos (ex.: Belo Horizonte, SE 2024-10: 20.701 no SINAN e 28.890 no InfoDengue). Não há `CLASSI_FIN = 5` nos arquivos públicos, então a diferença não vem de descartados; mudar a data de notificação para a de primeiros sintomas altera pouco (20.508). Hipóteses a investigar antes de calibrar: o InfoDengue usar notificações que o arquivo público não traz, ou outra regra de contagem. Os limites não foram alterados para forçar a meta.
