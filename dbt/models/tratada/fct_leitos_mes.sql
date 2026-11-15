-- Leitos do CNES por município e competência (mensal). Exclui leito hospital-dia (TP_LEITO 7), que não é internação.
-- `leitos_clinicos_pediatricos` (TP_LEITO 2 e 5) é a referência inicial de capacidade para dengue (ver ADR-0004).
-- `dados_ate` é a última competência carregada.
select
    m.geocodigo,
    l.competencia,
    sum(l.qt_exist)                                                   as leitos_existentes,
    sum(l.qt_sus)                                                     as leitos_sus,
    sum(l.qt_exist) filter (where l.tp_leito in (2, 5))               as leitos_clinicos_pediatricos,
    count(distinct l.cnes)                                            as estabelecimentos,
    (select max(competencia) from {{ ref('stg_cnes_leitos') }})       as dados_ate
from {{ ref('stg_cnes_leitos') }} l
join {{ ref('dim_municipio') }} m on m.cod6 = l.municipio_6
where l.tp_leito is distinct from 7
  and l.competencia >= make_date({{ var('ano_inicial') }}, 1, 1)
group by m.geocodigo, l.competencia
