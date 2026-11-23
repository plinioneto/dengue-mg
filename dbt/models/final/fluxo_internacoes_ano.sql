-- Apoio à H3: fluxo AGREGADO das internações por dengue (SIH) entre o município de residência e o de ocorrência, por ano da internação.
-- Só contagens por par de municípios (nunca registros individuais). A residência fora de MG, ou não informada, fica como "Fora de MG ou ignorado".
with base as (
    select year(dt_inter) as ano,
           municipio_residencia_6 as cod6_residencia,
           municipio_ocorrencia_6 as cod6_ocorrencia
    from {{ ref('stg_sih_dengue') }}
    where not data_fora_periodo
)
select
    b.ano,
    b.cod6_residencia,
    coalesce(r.municipio, 'Fora de MG ou ignorado')    as municipio_residencia,
    coalesce(r.regiao_saude, 'Fora de MG ou ignorado') as regiao_residencia,
    b.cod6_ocorrencia,
    o.municipio                                          as municipio_ocorrencia,
    o.regiao_saude                                       as regiao_ocorrencia,
    count(*)                                             as internacoes
from base b
left join {{ ref('dim_municipio') }} r on r.cod6 = b.cod6_residencia
left join {{ ref('dim_municipio') }} o on o.cod6 = b.cod6_ocorrencia
group by all
