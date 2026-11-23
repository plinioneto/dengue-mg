# ADR-0005: Indicador de pressão e regras da tabela final

**Status:** aceita (22/11/2026)

**Decisão (indicador).** Pressão = internações por dengue (SIH, A90 e A91) na semana epidemiológica da data de internação, no município onde ocorreram, dividido pelos **leitos clínicos e pediátricos existentes** (CNES, TP_LEITO 2 e 5, sem hospital-dia) na competência vigente no início da semana. Confirma a proposta inicial do backlog, com o denominador restrito ao tipo de leito em que a dengue é internada, em vez do total de leitos (que inclui UTI, obstétricos e psiquiátricos e diluiria o indicador). O total e os leitos SUS seguem na tabela para consulta.

**Por que não ocupação.** Nenhuma das fontes abertas traz a ocupação diária. O indicador mede quantas internações por dengue entram por leito disponível na semana; é uma aproximação da pressão, não a taxa de ocupação, e não deve ser lido como tal. O leito é uma capacidade total, não a capacidade livre.

**Casos de borda.**
- Município sem leito clínico ou pediátrico: pressão **nula** e `sem_leito_clinico_pediatrico = true`. Não se divide por zero nem se inventa valor; é informação relevante (a população depende de outro município).
- Semana sem internação, com leito: pressão 0.
- Semana que não está completa até o "dados até" do SIH (atraso de cerca de 2 meses): pressão nula, não zero. Semana "completa" é aquela cujo sábado de fechamento não é posterior ao "dados até".
- Leitos são mensais: vale a competência mais carregada mais recente cujo primeiro dia não é posterior ao início da semana; município sem registro nela tem 0 leito. Depois da última competência carregada repete-se a última, e `leitos_competencia` informa qual foi usada.

**Decisão (tabela final).** `final.indicadores_municipio_semana`, grade densa de 853 municípios por todas as semanas de 2022 até a corrente. Cada grupo (casos SINAN, InfoDengue, internações, leitos) tem a sua coluna `*_dados_ate`; a pressão carrega o menor dos dois (`pressao_dados_ate`). Até o "dados até", ausência de registro no fato esparso é zero; depois, é nulo. `casos_provisorio` marca as semanas com idade de até 9 semanas, ainda abertas pela regra dos 60 dias.

**Limitações.** (1) Sem população não há incidência por 100 mil: o H2 (ranking por incidência) exige acrescentar uma fonte de população (estimativas do IBGE), fora do escopo atual. (2) Internações no município de ocorrência incluem pacientes de outros municípios, o que infla a pressão nos polos regionais; isso é intencional (mede a carga sobre a capacidade local), e a região de saúde permite a leitura agregada. (3) O SIH contém só internações financiadas pelo SUS, e o CNES lista leitos existentes, inclusive privados; o `leitos_sus` fica como denominador alternativo.

**Consequências.** Mudar o denominador ou a regra de borda altera a tabela final e deve ser registrado aqui.

**Ajuste de 22/11/2026: só semana completa é conhecida.** Na primeira captura do painel com dados reais, a curva de pressão do estado terminava em um ponto quase zero. A causa estava na regra inicial, que tratava como conhecida qualquer semana que começasse até o "dados até" do grupo: o "dados até" do SIH era um domingo (27/09), e a semana que começava nele tinha 1 dia de internações. A regra passou a ser: uma semana só tem valor quando o sábado que a fecha não é posterior ao "dados até" do grupo; caso contrário, o valor é nulo. Vale para casos do SINAN, casos do InfoDengue e internações (e, por consequência, para a pressão). Para o SINAN e o InfoDengue o efeito prático é nulo (o "dados até" já fecha em sábado); para o SIH, a semana parcial deixa de aparecer. Os testes cobrem os dois casos (semana completa e incompleta).

**Municípios mais afetados (painel).** O painel ordena os municípios do recorte (estado ou região de saúde) no período escolhido por um destes critérios: pico semanal da pressão (padrão), média semanal da pressão, internações somadas ou casos somados. Só entram municípios com valor maior que zero no critério. Nos critérios de pressão há um mínimo de internações no período (padrão 5), para que 1 internação em poucos leitos não lidere o ranking; o mínimo é ajustável. A tabela traz casos, internações, leitos (última semana do período com leito informado), pressão média, pressão no pico e semana do pico. Casos de semanas provisórias podem mudar (ver R8).

**Explicação no painel.** O painel traz um botão "Como a pressão é calculada?" com a definição, a fórmula, as fontes, um exemplo ilustrativo, os casos em que o valor fica em branco e o que o indicador não é (ocupação, incidência). O texto está em `src/dengue_mg/ajuda.py` e deve ser atualizado junto com este ADR.
