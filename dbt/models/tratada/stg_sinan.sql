-- SINAN dengue (MG), uma linha por notificação, a partir da última versão de cada arquivo da bruta.
-- Para cada ano vale o arquivo final, se existir; senão o preliminar. Duplicatas pela chave do catálogo são removidas.
-- Datas fora do período (ex.: 2026 dentro do arquivo final de 2025) são mantidas e sinalizadas em `data_fora_periodo`;
-- a bruta nunca corrige, e os fatos usam só as datas dentro do período.
with fin as (
    select *, 1 as prioridade, 'sinan_final' as fonte from {{ bronze_atual('sinan_final') }}
),
pre as (
    select *, 2 as prioridade, 'sinan_prelim' as fonte from {{ bronze_atual('sinan_prelim') }}
),
todos as (
    select * from fin
    union all by name
    select * from pre
),
com_ano as (
    select *, 2000 + try_cast(regexp_extract(filename, 'DENGBR(\d{2})', 1) as integer) as ano_arquivo
    from todos
),
escolhidos as (
    -- descarta o preliminar dos anos que já têm arquivo final
    select * from com_ano
    where prioridade = 1
       or ano_arquivo not in (select distinct ano_arquivo from com_ano where prioridade = 1)
),
tratados as (
    select
        nullif(trim(nu_notifica), '')                                        as nu_notifica,
        nullif(trim(id_municip), '')                                         as municipio_notificacao_6,
        coalesce(nullif(trim(id_mn_resi), ''), nullif(trim(id_municip), '')) as municipio_residencia_6,
        {{ parse_data('dt_notific') }}                                       as dt_notific,
        {{ parse_data('dt_sin_pri') }}                                       as dt_sin_pri,
        try_cast(nullif(trim(classi_fin), '') as integer)                    as classi_fin,
        try_cast(nullif(trim(evolucao), '') as integer)                      as evolucao,
        try_cast(nullif(trim(hospitali), '') as integer)                     as hospitali,
        fonte, prioridade, ano_arquivo
    from escolhidos
),
dedup as (
    select *, row_number() over (
        partition by nu_notifica, municipio_notificacao_6, dt_notific order by prioridade, ano_arquivo desc
    ) as rn
    from tratados
)
select
    nu_notifica, municipio_notificacao_6, municipio_residencia_6, dt_notific, dt_sin_pri,
    classi_fin, evolucao, hospitali, fonte, ano_arquivo,
    coalesce(classi_fin = 5, false) as descartado,
    (dt_notific is null or dt_notific < make_date({{ var('ano_inicial') }}, 1, 1) or dt_notific > {{ hoje() }}) as data_fora_periodo
from dedup
where rn = 1 or nu_notifica is null
