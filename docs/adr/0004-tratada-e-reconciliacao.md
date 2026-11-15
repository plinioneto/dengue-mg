# ADR-0004: Regras da camada tratada e da reconciliação SINAN x InfoDengue

**Status:** aceita (09/11/2026), limites a calibrar no R6

**Decisões da camada tratada (R4).**
- Cada fonte lê da bruta a **última versão de cada arquivo** (`bronze_loads`, maior `loaded_at`). As versões antigas ficam na bruta para o R8.
- **SINAN:** vale o arquivo final do ano, se existir; senão o preliminar. O arquivo público do SINAN não traz NU_NOTIFICA (anonimizado, verificado nos dados em 15/11/2026), então não há chave para deduplicar linhas; a sobreposição entre arquivos é evitada usando um arquivo por ano. Casos descartados (CLASSI_FIN = 5) não entram nos fatos. Casos são atribuídos ao **município de notificação** (ID_MUNICIP) e à semana dos **primeiros sintomas** (DT_SIN_PRI; se vazia, DT_NOTIFIC). É a convenção do InfoDengue, verificada na reconciliação (ver o achado abaixo); o município de notificação é onde se buscou atendimento. O município de residência continua na tratada (`stg_sinan`).
- **SIH:** internações atribuídas ao **município onde ocorreram** (MUNIC_MOV), porque o indicador mede pressão sobre a capacidade local, e à semana da data de internação (DT_INTER). Internações de residentes (MUNIC_RES) ficam disponíveis na tratada para análises futuras.
- **CNES:** leitos por município e competência mensal. Exclui leito hospital-dia (TP_LEITO 7). `leitos_clinicos_pediatricos` (TP_LEITO 2 e 5) é a referência inicial de capacidade para dengue; a escolha final do denominador do indicador de pressão é do R7.
- **Código de município:** CNES, SIH e SINAN usam 6 dígitos; IBGE e InfoDengue, 7. A dimensão guarda os dois (`geocodigo`, `cod6`) e os fatos usam `geocodigo`.
- **Semana epidemiológica:** domingo a sábado; a semana 1 é a que contém 4 de janeiro (ancoras testadas em `dbt/tests/dim_semana_ancoras.sql`).
- **Datas fora do período** (ex.: 2026 no arquivo final de 2025, ou futuras): a tratada mantém o registro com `data_fora_periodo`; os fatos usam só datas de 2022 até a data de referência. O teste correspondente é aviso, não falha, porque é limitação conhecida da fonte (no SIH, internações de 2021 aparecem em arquivos de 2022 pela competência de saída).
- **Região de saúde:** vem do seed `dbt/seeds/regiao_saude_mg.csv` (cod6, regiao_saude, macrorregiao_saude), gerado da base territorial do DATASUS (`/territorio/tabelas/2026/06-base_territorial_jun26.zip`: `rl_municip_regsaud`, `tb_regsaud`, `rl_regsaud_macsaud`, `tb_macsaud`). Município fora do seed vira "Não informada"; não se inventa o dado.
- **"Dados até":** cada fato carrega `dados_ate`, a data mais recente da fonte (notificação, internação, competência ou fim da semana).

**Reconciliação (R6).** Divergência = |casos SINAN − casos InfoDengue| / casos SINAN, por município e semana, comparando com `casos` (notificados) do InfoDengue, não com o nowcast (`casos_est`, que fica na tabela para consulta). Par elegível: SINAN com 10 casos ou mais e semana com mais de 9 semanas de idade. Meta: 90% dos pares elegíveis com divergência de até 5%. Parâmetros em `dbt_project.yml` (`rec_*`), a calibrar com os dados reais.

**Testes (R5).** Genéricos do dbt (unique, not_null, relationships, accepted_values) mais próprios (`chave_unica`, `entre`, `data_no_periodo`) e singulares em `dbt/tests/` (853 municípios, semanas sem buracos, valores plausíveis, um arquivo por ano no SINAN). O relatório sai de `run_results.json` em `docs/evidencias/R5/`.

**Consequências.** Mudar a regra de atribuição (residência x notificação x ocorrência) altera os fatos e deve ser registrado aqui. Os testes de plausibilidade usam limites iniciais e podem ser ajustados após a primeira execução com dados reais.

**Achado da reconciliação (15/11/2026).** A primeira versão (SINAN por data de notificação e residência, contra os `casos` do InfoDengue) deu 8,6% dos pares dentro de 5%. Duas causas, encontradas por teste nos dados reais:
1. Os `casos` do InfoDengue incluem notificações depois descartadas. A coluna `casprov` (casos prováveis) é a comparável ao arquivo público do SINAN: razão `casprov`/SINAN de 0,97 (2022), 1,04 (2023), 1,06 (2024), 1,05 (2025) e 1,06 (2026), contra 1,4 a 3,0 com `casos`.
2. O InfoDengue agrupa por semana dos primeiros sintomas e por município de notificação. Das quatro combinações testadas (data de notificação ou de sintomas x município de residência ou de notificação), só a de sintomas e notificação alinha: 75,3% dos pares dentro de 5%, mediana da divergência 0.
Com isso a meta de 90% ainda não é atingida. Restante: o InfoDengue tem 4% a 9% mais casos prováveis que o arquivo público em 2023 a 2026 (provável efeito de atualizações do SINAN posteriores ao arquivo e de critério de classificação); excluir inconclusivos (CLASSI_FIN 8) piora o resultado. Os limites (5% e 90%) seguem como iniciais e a calibração é decisão do autor, com base nestes números.

**Investigação do restante (15/11/2026).** Dos 22.731 pares elegíveis, 75,3% ficam dentro de 5%, 86,8% dentro de 10% e 90,9% dentro de 15% (relatório R6, tabela de sensibilidade). O que explica a cauda:
- **Virada de ano.** O alinhamento cai nas semanas 48 a 52 (16% na semana 52) e 1 e 2 (cerca de 65%). Os arquivos anuais do SINAN têm cortes próprios: o de 2024 só tem notificações até 28/12/2024 e o de 2022 até 31/12/2022, enquanto o de 2023 vai até 02/04/2024. Casos de sintomas no fim do ano notificados depois do corte não estão no arquivo público. Excluir essas semanas leva o resultado só a 77,4%.
- **Irregularidades do InfoDengue.** Em algumas semanas a coluna `casprov` é bem menor que o SINAN (ex.: SE 2022-51: 254 contra 1.161), enquanto `casos` é 2.332. Parte da lacuna vem da fonte comparada.
- **Cauda geral.** Nas semanas 3 a 47, o InfoDengue é maior que o SINAN em cerca de 70% dos pares fora do limite (mediana de +7,5%), compatível com atualizações do SINAN posteriores ao arquivo público. Não foi possível confirmar sem o histórico do InfoDengue.
Conclusão: a meta de 90% é atingida com tolerância de 15%, não de 5%. Mudar o limite é decisão do autor (a meta do objetivo SMART cita 5%).
