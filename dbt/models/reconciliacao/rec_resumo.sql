-- Resumo da meta de reconciliação (R6): % de pares elegíveis com divergência dentro do limite, por ano e no total.
with por_ano as (
    select cast(semana_id // 100 as varchar) as recorte, *
    from {{ ref('rec_sinan_infodengue') }} where elegivel
),
todos as (
    select 'total' as recorte, * exclude (recorte) from por_ano
),
juntos as (
    select * from por_ano
    union all by name
    select * from todos
)
select
    recorte,
    count(*)                                                  as pares_elegiveis,
    count(*) filter (where dentro_do_limite)                  as pares_dentro_do_limite,
    count(*) filter (where dentro_do_limite) * 1.0 / nullif(count(*), 0) as pct_dentro_do_limite,
    {{ var('rec_meta_pares') }}                               as meta,
    {{ var('rec_limite_divergencia') }}                       as limite_divergencia,
    median(divergencia)                                       as divergencia_mediana
from juntos
group by recorte
order by recorte
