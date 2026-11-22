-- InfoDengue alertcity: município x semana epidemiológica (SE = AAAASS). `geocodigo` foi acrescentado na ingestão.
-- Se houver mais de uma carga, vale a mais recente de cada município-semana.
with t as (
    select
        cast(geocodigo as varchar)                      as geocodigo,
        try_cast(nullif(trim("SE"), '') as integer)     as semana_id,
        try_cast(nullif(trim(casos), '') as double)     as casos,
        try_cast(nullif(trim(casprov), '') as double)   as casprov,
        try_cast(nullif(trim(casos_est), '') as double) as casos_est,
        try_cast(nullif(trim(nivel), '') as integer)    as nivel,
        filename
    from {{ bronze_atual('infodengue') }}
)
select * exclude (rn) from (
    select *, row_number() over (partition by geocodigo, semana_id order by filename desc) as rn from t
) where rn = 1
