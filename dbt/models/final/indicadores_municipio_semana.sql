-- R7: tabela final, um registro por município (853) x semana epidemiológica (de 2022 até a semana corrente), em formato denso.
-- Cada grupo de indicadores traz o seu "dados até" (data mais recente da fonte). Uma semana só conta como conhecida quando está COMPLETA
-- (o sábado que a fecha não é posterior ao "dados até"); semana incompleta ou posterior é NULA (desconhecida), não zero.
-- Em semana conhecida, ausência de registro no fato esparso significa zero ocorrência.
-- Indicador de pressão (ADR-0005): internações por dengue na semana por leito clínico e pediátrico existente no município.
with semanas as (
    select * from {{ ref('dim_semana_epi') }} where inicio <= {{ hoje() }}
),
grade as (
    select m.geocodigo, m.municipio, m.regiao_saude, m.macrorregiao_saude,
           s.semana_id, s.epi_ano, s.epi_semana, s.inicio, s.fim
    from {{ ref('dim_municipio') }} m cross join semanas s
),
limites as (
    select
        (select max(dados_ate) from {{ ref('fct_casos_semana') }})        as casos_ate,
        (select max(dados_ate) from {{ ref('fct_infodengue_semana') }})   as infodengue_ate,
        (select max(dados_ate) from {{ ref('fct_internacoes_semana') }})  as internacoes_ate,
        (select max(dados_ate) from {{ ref('fct_leitos_mes') }})          as leitos_ate,
        (select min(competencia) from {{ ref('fct_leitos_mes') }})        as leitos_desde
),
-- Leitos mensais: vale a competência mais recente carregada que não é posterior ao início da semana (depois da última
-- competência repete-se a última; `leitos_competencia` mostra qual foi usada). Município sem registro nessa competência tem 0 leito.
competencias as (select distinct competencia from {{ ref('fct_leitos_mes') }}),
vigente as (
    select g.geocodigo, g.semana_id,
           (select max(c.competencia) from competencias c where c.competencia <= g.inicio) as competencia
    from grade g
),
leitos as (
    select v.geocodigo, v.semana_id, v.competencia, l.leitos_existentes, l.leitos_sus, l.leitos_clinicos_pediatricos
    from vigente v
    left join {{ ref('fct_leitos_mes') }} l on l.geocodigo = v.geocodigo and l.competencia = v.competencia
),
base as (
    select
        g.*,
        c.casos_notificados, c.casos_hospitalizados, c.casos_confirmados,
        i.casos_provaveis as casos_provaveis_infodengue, i.casos_est as casos_estimados_infodengue, i.nivel as nivel_alerta_infodengue,
        n.internacoes, n.obitos, n.dias_internacao,
        lt.competencia as leitos_competencia, lt.leitos_existentes, lt.leitos_sus, lt.leitos_clinicos_pediatricos,
        x.casos_ate, x.infodengue_ate, x.internacoes_ate, x.leitos_ate, x.leitos_desde
    from grade g
    cross join limites x
    left join {{ ref('fct_casos_semana') }} c using (geocodigo, semana_id)
    left join {{ ref('fct_infodengue_semana') }} i using (geocodigo, semana_id)
    left join {{ ref('fct_internacoes_semana') }} n using (geocodigo, semana_id)
    left join leitos lt using (geocodigo, semana_id)
)
select
    geocodigo, municipio, regiao_saude, macrorregiao_saude,
    semana_id, epi_ano, epi_semana, inicio as inicio_semana, fim as fim_semana,

    -- casos (SINAN): município de notificação, semana dos primeiros sintomas
    case when fim <= casos_ate then coalesce(casos_notificados, 0) end        as casos_notificados,
    case when fim <= casos_ate then coalesce(casos_hospitalizados, 0) end     as casos_hospitalizados,
    case when fim <= casos_ate then coalesce(casos_confirmados, 0) end        as casos_confirmados,
    casos_ate                                                                    as casos_dados_ate,
    -- semana ainda aberta pela regra dos 60 dias: o valor pode ser revisto (ver R8)
    (cast(({{ hoje() }} - fim) // 7 as integer) <= {{ var('rec_min_semanas_idade') }}) as casos_provisorio,

    -- InfoDengue (casos prováveis, nowcast e nível de alerta)
    case when fim <= infodengue_ate then coalesce(casos_provaveis_infodengue, 0) end as casos_provaveis_infodengue,
    casos_estimados_infodengue,
    nivel_alerta_infodengue,
    infodengue_ate                                                               as infodengue_dados_ate,

    -- internações (SIH): município onde ocorreram, semana da data de internação
    case when fim <= internacoes_ate then coalesce(internacoes, 0) end        as internacoes,
    case when fim <= internacoes_ate then coalesce(obitos, 0) end             as obitos,
    case when fim <= internacoes_ate then coalesce(dias_internacao, 0) end    as dias_internacao,
    internacoes_ate                                                              as internacoes_dados_ate,

    -- leitos (CNES, mensal)
    case when inicio >= leitos_desde then coalesce(leitos_existentes, 0) end                 as leitos_existentes,
    case when inicio >= leitos_desde then coalesce(leitos_sus, 0) end                        as leitos_sus,
    case when inicio >= leitos_desde then coalesce(leitos_clinicos_pediatricos, 0) end       as leitos_clinicos_pediatricos,
    leitos_competencia,
    leitos_ate                                                                   as leitos_dados_ate,

    -- indicador de pressão: nulo quando falta o numerador (SIH ainda não chegou) ou o município não tem leito clínico/pediátrico
    case when fim <= internacoes_ate and inicio >= leitos_desde and coalesce(leitos_clinicos_pediatricos, 0) > 0
         then coalesce(internacoes, 0) * 1.0 / leitos_clinicos_pediatricos end   as pressao_internacoes_por_leito,
    case when inicio >= leitos_desde and coalesce(leitos_clinicos_pediatricos, 0) = 0 then true else false end as sem_leito_clinico_pediatrico,
    -- a pressão só é conhecida até a menor das datas de que depende
    least(internacoes_ate, leitos_ate)                                           as pressao_dados_ate
from base
