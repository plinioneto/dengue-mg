-- Semanas consecutivas: cada semana começa 7 dias depois da anterior.
select semana_id, inicio, anterior
from (select semana_id, inicio, lag(inicio) over (order by inicio) as anterior from {{ ref('dim_semana_epi') }})
where anterior is not null and inicio - anterior <> 7
