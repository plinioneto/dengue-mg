-- A semana 1 de cada ano começa no domingo esperado (calendário epidemiológico) e todas as semanas têm 7 dias.
with esperado(semana_id, inicio) as (
    values (202201, date '2022-01-02'), (202301, date '2023-01-01'), (202401, date '2023-12-31'),
           (202501, date '2024-12-29'), (202601, date '2026-01-04')
)
select e.semana_id, e.inicio as esperado, d.inicio as obtido
from esperado e left join {{ ref('dim_semana_epi') }} d using (semana_id)
where d.inicio is distinct from e.inicio
union all
select semana_id, null, inicio from {{ ref('dim_semana_epi') }}
where dayofweek(inicio) <> 0 or fim - inicio <> 6
