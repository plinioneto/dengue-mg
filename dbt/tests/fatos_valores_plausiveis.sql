-- Relações que precisam valer: hospitalizados <= notificados; óbitos <= internações; leitos SUS <= leitos existentes.
select 'fct_casos_semana' as tabela, geocodigo, cast(semana_id as varchar) as chave
from {{ ref('fct_casos_semana') }}
where casos_hospitalizados > casos_notificados or casos_confirmados > casos_notificados
union all
select 'fct_internacoes_semana', geocodigo, cast(semana_id as varchar)
from {{ ref('fct_internacoes_semana') }}
where obitos > internacoes
union all
select 'fct_leitos_mes', geocodigo, cast(competencia as varchar)
from {{ ref('fct_leitos_mes') }}
where leitos_sus > leitos_existentes
