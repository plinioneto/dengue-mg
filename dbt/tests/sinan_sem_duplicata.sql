-- A chave do catálogo (NU_NOTIFICA, município de notificação, DT_NOTIFIC) não se repete na tratada.
select nu_notifica, municipio_notificacao_6, dt_notific, count(*) as n
from {{ ref('stg_sinan') }}
where nu_notifica is not null
group by 1, 2, 3
having count(*) > 1
