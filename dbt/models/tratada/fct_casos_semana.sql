-- Casos de dengue do SINAN por município de notificação e semana epidemiológica dos primeiros sintomas (DT_SIN_PRI; se vazia, DT_NOTIFIC).
-- É a convenção do InfoDengue (verificada na reconciliação, ver ADR-0004); o município de notificação é onde se buscou atendimento.
-- Fato esparso: só há linha onde houve ao menos uma notificação. Descartados (CLASSI_FIN = 5) ficam de fora.
-- As semanas recentes mudam enquanto os casos estão abertos (regra dos 60 dias); `dados_ate` é a maior data de notificação.
with base as (
    select municipio_notificacao_6 as cod6,
           {{ inicio_semana('dt_ref') }} as inicio,
           hospitali, classi_fin
    from (select *, coalesce(dt_sin_pri, dt_notific) as dt_ref from {{ ref('stg_sinan') }})
    where not descartado
      and dt_ref between make_date({{ var('ano_inicial') }}, 1, 1) and {{ hoje() }}
)
select
    m.geocodigo,
    s.semana_id,
    count(*)                                                as casos_notificados,
    count(*) filter (where b.hospitali = 1)                 as casos_hospitalizados,
    count(*) filter (where b.classi_fin in (10, 11, 12))    as casos_confirmados,
    (select max(dt_notific) from {{ ref('stg_sinan') }} where not descartado and not data_fora_periodo) as dados_ate
from base b
join {{ ref('dim_municipio') }} m on m.cod6 = b.cod6
join {{ ref('dim_semana_epi') }} s on s.inicio = b.inicio
group by m.geocodigo, s.semana_id
