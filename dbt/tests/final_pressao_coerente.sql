-- Coerência do indicador de pressão e dos "dados até": pressão só existe com numerador e denominador conhecidos;
-- nenhum valor em semana que não está completa até o "dados até"; leitos SUS não passam dos existentes.
select geocodigo, cast(semana_id as varchar) as chave, 'pressao sem leito ou sem internacoes' as problema
from {{ ref('indicadores_municipio_semana') }}
where pressao_internacoes_por_leito is not null and (internacoes is null or coalesce(leitos_clinicos_pediatricos, 0) = 0)
union all
select geocodigo, cast(semana_id as varchar), 'casos em semana incompleta'
from {{ ref('indicadores_municipio_semana') }}
where fim_semana > casos_dados_ate and casos_notificados is not null
union all
select geocodigo, cast(semana_id as varchar), 'internacoes em semana incompleta'
from {{ ref('indicadores_municipio_semana') }}
where fim_semana > internacoes_dados_ate and internacoes is not null
union all
select geocodigo, cast(semana_id as varchar), 'leitos sus maior que existentes'
from {{ ref('indicadores_municipio_semana') }}
where leitos_sus > leitos_existentes
