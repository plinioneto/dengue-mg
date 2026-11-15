# Relatório de execução dos testes (R5)

Gerado em 15/11/2026 12:14. Total: 67 testes (pass: 65, warn: 2).

| Teste | Resultado | Linhas com falha |
|---|---|---|
| data_no_periodo_stg_sih_dengue_dt_inter | warn | 24 |
| relationships_stg_sinan_municipio_residencia_6__cod6__ref_dim_municipio_ | warn | 4919 |
| accepted_values_stg_sih_dengue_morte__False__0__1 | pass | 0 |
| accepted_values_stg_sinan_fonte__sinan_final__sinan_prelim | pass | 0 |
| chave_unica_fct_casos_semana_geocodigo__semana_id | pass | 0 |
| chave_unica_fct_infodengue_semana_geocodigo__semana_id | pass | 0 |
| chave_unica_fct_internacoes_semana_geocodigo__semana_id | pass | 0 |
| chave_unica_fct_leitos_mes_geocodigo__competencia | pass | 0 |
| chave_unica_rec_sinan_infodengue_geocodigo__semana_id | pass | 0 |
| data_no_periodo_stg_cnes_leitos_competencia | pass | 0 |
| data_no_periodo_stg_sinan_dt_notific | pass | 0 |
| dim_municipio_853 | pass | 0 |
| dim_semana_ancoras | pass | 0 |
| dim_semana_sem_buracos | pass | 0 |
| entre_dim_semana_epi_epi_semana__53__1 | pass | 0 |
| entre_fct_casos_semana_casos_notificados__1 | pass | 0 |
| entre_fct_infodengue_semana_casos__0 | pass | 0 |
| entre_fct_internacoes_semana_internacoes__1 | pass | 0 |
| entre_fct_leitos_mes_leitos_existentes__0 | pass | 0 |
| entre_rec_sinan_infodengue_divergencia__0 | pass | 0 |
| entre_stg_cnes_leitos_qt_exist__5000__0 | pass | 0 |
| entre_stg_infodengue_casos__0 | pass | 0 |
| entre_stg_sih_dengue_dias_perm__365__0 | pass | 0 |
| fatos_valores_plausiveis | pass | 0 |
| not_null_dim_municipio_cod6 | pass | 0 |
| not_null_dim_municipio_geocodigo | pass | 0 |
| not_null_dim_municipio_municipio | pass | 0 |
| not_null_dim_municipio_regiao_saude | pass | 0 |
| not_null_dim_semana_epi_epi_semana | pass | 0 |
| not_null_dim_semana_epi_inicio | pass | 0 |
| not_null_dim_semana_epi_semana_id | pass | 0 |
| not_null_fct_casos_semana_casos_notificados | pass | 0 |
| not_null_fct_casos_semana_dados_ate | pass | 0 |
| not_null_fct_casos_semana_geocodigo | pass | 0 |
| not_null_fct_casos_semana_semana_id | pass | 0 |
| not_null_fct_infodengue_semana_dados_ate | pass | 0 |
| not_null_fct_internacoes_semana_dados_ate | pass | 0 |
| not_null_fct_internacoes_semana_geocodigo | pass | 0 |
| not_null_fct_internacoes_semana_semana_id | pass | 0 |
| not_null_fct_leitos_mes_dados_ate | pass | 0 |
| not_null_fct_leitos_mes_geocodigo | pass | 0 |
| not_null_fct_leitos_mes_leitos_existentes | pass | 0 |
| not_null_regiao_saude_mg_cod6 | pass | 0 |
| not_null_regiao_saude_mg_macrorregiao_saude | pass | 0 |
| not_null_regiao_saude_mg_regiao_saude | pass | 0 |
| not_null_stg_cnes_leitos_competencia | pass | 0 |
| not_null_stg_cnes_leitos_municipio_6 | pass | 0 |
| not_null_stg_infodengue_geocodigo | pass | 0 |
| not_null_stg_infodengue_semana_id | pass | 0 |
| not_null_stg_sih_dengue_diag_princ | pass | 0 |
| not_null_stg_sih_dengue_dt_inter | pass | 0 |
| not_null_stg_sinan_dt_notific | pass | 0 |
| not_null_stg_sinan_municipio_residencia_6 | pass | 0 |
| relationships_fct_casos_semana_geocodigo__geocodigo__ref_dim_municipio_ | pass | 0 |
| relationships_fct_casos_semana_semana_id__semana_id__ref_dim_semana_epi_ | pass | 0 |
| relationships_fct_internacoes_semana_geocodigo__geocodigo__ref_dim_municipio_ | pass | 0 |
| relationships_fct_internacoes_semana_semana_id__semana_id__ref_dim_semana_epi_ | pass | 0 |
| relationships_fct_leitos_mes_geocodigo__geocodigo__ref_dim_municipio_ | pass | 0 |
| relationships_stg_cnes_leitos_municipio_6__cod6__ref_dim_municipio_ | pass | 0 |
| relationships_stg_infodengue_geocodigo__geocodigo__ref_dim_municipio_ | pass | 0 |
| relationships_stg_infodengue_semana_id__semana_id__ref_dim_semana_epi_ | pass | 0 |
| sinan_um_arquivo_por_ano | pass | 0 |
| unique_dim_municipio_cod6 | pass | 0 |
| unique_dim_municipio_geocodigo | pass | 0 |
| unique_dim_semana_epi_inicio | pass | 0 |
| unique_dim_semana_epi_semana_id | pass | 0 |
| unique_regiao_saude_mg_cod6 | pass | 0 |

`warn` indica limitação conhecida da fonte (ex.: datas de 2026 no arquivo final de 2025); `fail`/`error` bloqueia a publicação.
