# ADR-0001: Recorte (Minas Gerais) e histórico (2022 em diante)

**Status:** aceita (01/11/2026)

**Contexto.** As fontes cobrem o país, mas o projeto tem 3 sprints e uma pessoa. A defasagem do SIH (cerca de 2 meses) e as regras de fechamento do SINAN (60 dias) pedem um histórico que inclua anos já consolidados.

**Decisão.** Recorte em Minas Gerais (853 municípios; código UF 31). Histórico a partir de 2022, para ter anos finais e o ano corrente preliminar.

**Consequências.** SINAN e SIH nacionais são filtrados por UF durante a leitura. CNES (arquivos LTMG) e SIH (RDMG) já são por UF. Mudar de estado exige trocar a UF em `sources.py`.
