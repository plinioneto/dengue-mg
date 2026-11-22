# Catálogo de fontes (R1)

Medições de 25/10/2026.

| Fonte | Onde | Grão | Chave | Cadência / defasagem | Observações |
|---|---|---|---|---|---|
| SINAN dengue (final) | FTP DATASUS `/dissemin/publicos/SINAN/DADOS/FINAIS/DENGBRaa.dbc` | notificação | sem chave pública (NU_NOTIFICA não existe no arquivo); um arquivo por ano | anual | Pode conter datas do ano seguinte; filtro de UF por SG_UF_NOT ou SG_UF |
| SINAN dengue (prelim) | `.../PRELIM/DENGBRaa.dbc` | notificação | idem | arquivo atualizado em cerca de 1 a 6 dias | Casos abertos; regra de 60 dias para encerramento |
| CNES leitos (LT) | `/dissemin/publicos/CNES/200508_/Dados/LT/LTMGaamm.dbc` | estabelecimento × competência | CNES, COMPETEN | mensal (competência 2026-09 publicada em 15/10) | Arquivo já é de MG |
| SIH AIH reduzida (RD) | `/dissemin/publicos/SIHSUS/200801_/Dados/RDMGaamm.dbc` | internação | N_AIH, MUNIC_RES, DT_INTER | mensal, cerca de 2 meses de atraso (2026-08) | Filtro por DIAG_PRINC A90/A91 na ingestão |
| InfoDengue | `https://info.dengue.mat.br/api/alertcity` | município × semana epidemiológica | geocode, SE | semanal (SE 2026-41 em 25/10) | Resposta sem código IBGE: a ingestão acrescenta `geocodigo`. Traz nowcast (casos_est) |
| IBGE municípios | `https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios` | município | id (7 dígitos) | estável | Região de saúde vem de tabela própria (a definir no R4) |

Atenção: o CNES e o SIH usam código de município de 6 dígitos (sem dígito verificador); o IBGE e o InfoDengue usam 7. A padronização é feita na camada tratada (R4).
