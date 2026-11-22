-- Internações por dengue (SIH, A90/A91) por município onde ocorreram e semana epidemiológica da data de internação.
-- Fato esparso. `dados_ate` é a maior data de internação carregada (a fonte tem cerca de 2 meses de atraso).
with base as (
    select municipio_ocorrencia_6 as cod6,
           {{ inicio_semana('dt_inter') }} as inicio,
           morte, dias_perm
    from {{ ref('stg_sih_dengue') }}
    where not data_fora_periodo
)
select
    m.geocodigo,
    s.semana_id,
    count(*)                                  as internacoes,
    count(*) filter (where b.morte = 1)       as obitos,
    sum(b.dias_perm)                          as dias_internacao,
    (select max(dt_inter) from {{ ref('stg_sih_dengue') }} where not data_fora_periodo) as dados_ate
from base b
join {{ ref('dim_municipio') }} m on m.cod6 = b.cod6
join {{ ref('dim_semana_epi') }} s on s.inicio = b.inicio
group by m.geocodigo, s.semana_id
