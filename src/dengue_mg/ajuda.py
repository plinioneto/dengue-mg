"""Textos de ajuda do painel. A definição do indicador vem do ADR-0005; mudar a regra exige atualizar o ADR e este texto."""

PRESSAO = """
**O que mede.** Quantas internações por dengue entram, em uma semana, para cada leito clínico e pediátrico existente no município (ou no recorte escolhido). Quanto maior, mais a dengue pesa sobre a capacidade de internação local.

**Como é calculada.**

`pressão = internações por dengue na semana ÷ leitos clínicos e pediátricos existentes`

- **Internações:** SIH (internações pagas pelo SUS) com diagnóstico principal de dengue (A90 ou A91), no município **onde ocorreram**, pela semana epidemiológica da data de internação.
- **Leitos:** CNES, leitos clínicos e pediátricos existentes na competência (mês) vigente, sem contar hospital-dia.
- **Semana epidemiológica:** de domingo a sábado. O valor só aparece quando a semana está **completa** até o "dados até" da fonte.
- **Estado, região ou vários municípios:** é a razão das somas (total de internações ÷ total de leitos), e não a média das razões.

**Exemplo ilustrativo.** Um município com 3 internações por dengue na semana e 40 leitos clínicos e pediátricos tem pressão 3 ÷ 40 = 0,075. Se não houver internação, a pressão é 0.

**Como ler os valores.** Os números costumam ser pequenos, porque se compara o fluxo semanal de internações com o estoque total de leitos. Use para comparar semanas e municípios entre si, e não como valor absoluto. Nos rankings, "pico" é a maior pressão semanal no período e "média" é a média das semanas com pressão conhecida.

**Quando fica em branco.**
- O SIH atrasa cerca de 2 meses: semanas recentes ficam sem valor (desconhecido, e não zero).
- Município sem leito clínico ou pediátrico no CNES: a pressão é indefinida, em vez de dividir por zero.

**O que não é.**
- Não é taxa de ocupação: as fontes abertas não informam quantos leitos estão ocupados. O leito contado é o **existente**, e não o livre.
- Não considera internações de residentes em outros municípios: um polo regional recebe pacientes de fora, o que aumenta a pressão local (é de propósito, mede a carga sobre a capacidade do município). A leitura por região de saúde ajuda a compensar.
- Só inclui internações do SUS, enquanto os leitos do CNES incluem leitos privados.
- Não é incidência: sem população, não há casos por 100 mil habitantes.

Definição completa e limitações: `docs/adr/0005-indicador-de-pressao-e-tabela-final.md`.
"""
