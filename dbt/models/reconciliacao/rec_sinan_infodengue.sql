-- R6: reconciliação dos casos SINAN com os do InfoDengue, por município e semana epidemiológica.
-- divergencia = |SINAN - InfoDengue| / SINAN (o SINAN é a fonte primária). Par elegível para a meta: SINAN >= rec_min_casos
-- e semana com mais de rec_min_semanas_idade semanas de idade (casos já fechados pela regra dos 60 dias).
-- Ausência de linha numa das fontes conta como 0 caso.
with pares as (
    select coalesce(s.geocodigo, i.geocodigo) as geocodigo,
           coalesce(s.semana_id, i.semana_id) as semana_id,
           coalesce(s.casos_notificados, 0)   as casos_sinan,
           coalesce(i.casos, 0)               as casos_infodengue,
           i.casos_est                        as casos_est_infodengue
    from {{ ref('fct_casos_semana') }} s
    full outer join {{ ref('fct_infodengue_semana') }} i using (geocodigo, semana_id)
),
com_idade as (
    select p.*, w.fim as fim_semana,
           cast(({{ hoje() }} - w.fim) // 7 as integer) as semanas_idade
    from pares p
    join {{ ref('dim_semana_epi') }} w using (semana_id)
)
select
    geocodigo, semana_id, fim_semana, semanas_idade,
    casos_sinan, casos_infodengue, casos_est_infodengue,
    abs(casos_sinan - casos_infodengue) as diferenca,
    case when casos_sinan > 0 then abs(casos_sinan - casos_infodengue) / casos_sinan end as divergencia,
    (casos_sinan >= {{ var('rec_min_casos') }} and semanas_idade > {{ var('rec_min_semanas_idade') }}) as elegivel,
    (casos_sinan > 0 and abs(casos_sinan - casos_infodengue) / casos_sinan <= {{ var('rec_limite_divergencia') }}) as dentro_do_limite
from com_idade
