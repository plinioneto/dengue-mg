-- Dimensão de semana epidemiológica (domingo a sábado; a SE 1 é a que contém 4 de janeiro), de 2022 até hoje + 3 semanas.
with dias as (
    select cast(d as date) as d
    from generate_series(date '2021-12-01', cast({{ hoje() }} + interval 21 day as date), interval 1 day) t(d)
),
ini as (
    select d, year(d) as y,
           make_date(year(d) - 1, 1, 4) - cast(dayofweek(make_date(year(d) - 1, 1, 4)) as integer) as ini_ant,
           make_date(year(d), 1, 4)     - cast(dayofweek(make_date(year(d), 1, 4)) as integer)     as ini_ano,
           make_date(year(d) + 1, 1, 4) - cast(dayofweek(make_date(year(d) + 1, 1, 4)) as integer) as ini_prox
    from dias
),
epi as (
    select d,
           case when d >= ini_prox then y + 1 when d < ini_ano then y - 1 else y end as epi_ano,
           case when d >= ini_prox then ini_prox when d < ini_ano then ini_ant else ini_ano end as ini_sem1
    from ini
),
semanas as (
    select distinct epi_ano,
           cast((d - ini_sem1) // 7 + 1 as integer) as epi_semana,
           cast(ini_sem1 + 7 * cast((d - ini_sem1) // 7 as integer) as date) as inicio
    from epi
)
select
    epi_ano * 100 + epi_semana as semana_id,
    epi_ano,
    epi_semana,
    inicio,
    cast(inicio + 6 as date)   as fim
from semanas
where epi_ano >= {{ var('ano_inicial') }}
