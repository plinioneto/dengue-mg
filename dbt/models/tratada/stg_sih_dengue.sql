-- SIH AIH reduzida (RD) filtrada na ingestão por diagnóstico principal A90/A91. Uma linha por internação.
-- Município de movimento (MUNIC_MOV) = onde a internação ocorreu; é ele que mede a pressão sobre a capacidade local.
with t as (
    select
        nullif(trim(n_aih), '')                          as n_aih,
        nullif(trim(munic_mov), '')                      as municipio_ocorrencia_6,
        nullif(trim(munic_res), '')                      as municipio_residencia_6,
        {{ parse_data('dt_inter') }}                     as dt_inter,
        {{ parse_data('dt_saida') }}                     as dt_saida,
        trim(diag_princ)                                 as diag_princ,
        try_cast(nullif(trim(morte), '') as integer)     as morte,
        try_cast(nullif(trim(dias_perm), '') as integer) as dias_perm
    from {{ bronze_atual('sih_rd') }}
)
select *,
       (dt_inter is null or dt_inter < make_date({{ var('ano_inicial') }}, 1, 1) or dt_inter > {{ hoje() }}) as data_fora_periodo
from t
