-- A tabela final tem exatamente um registro por município da dimensão e por semana até a corrente (grade completa, sem buracos).
with esperado as (
    select (select count(*) from {{ ref('dim_municipio') }}) * (select count(*) from {{ ref('dim_semana_epi') }} where inicio <= {{ hoje() }}) as n
),
real as (select count(*) as n from {{ ref('indicadores_municipio_semana') }})
select e.n as esperado, r.n as real from esperado e, real r where e.n <> r.n
