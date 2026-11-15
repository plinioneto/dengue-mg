-- InfoDengue por município e semana epidemiológica: casos notificados, nowcast (casos_est) e nível de alerta.
-- `dados_ate` é o último dia da semana mais recente carregada.
select
    i.geocodigo,
    i.semana_id,
    i.casos,
    i.casos_est,
    i.nivel,
    (select max(s2.fim) from {{ ref('dim_semana_epi') }} s2 where s2.semana_id = (select max(semana_id) from {{ ref('stg_infodengue') }})) as dados_ate
from {{ ref('stg_infodengue') }} i
join {{ ref('dim_municipio') }} m on m.geocodigo = i.geocodigo
join {{ ref('dim_semana_epi') }} s on s.semana_id = i.semana_id
