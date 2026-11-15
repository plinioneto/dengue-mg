-- Dimensão de município: um registro por município de MG (853), com região de saúde (seed `regiao_saude_mg`).
-- Região de saúde não informada no seed vira 'Não informada' (não se inventa o dado).
select
    m.geocodigo,
    m.cod6,
    m.municipio,
    m.microrregiao,
    m.mesorregiao,
    coalesce(r.regiao_saude, 'Não informada')       as regiao_saude,
    coalesce(r.macrorregiao_saude, 'Não informada') as macrorregiao_saude
from {{ ref('stg_ibge_municipios') }} m
left join {{ ref('regiao_saude_mg') }} r on r.cod6 = m.cod6
