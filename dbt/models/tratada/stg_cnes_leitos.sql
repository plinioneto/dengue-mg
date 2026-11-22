-- CNES LT (leitos por estabelecimento e competência), última versão de cada arquivo mensal.
-- Competência AAAAMM vira o primeiro dia do mês. Município de 6 dígitos (como na fonte).
select
    nullif(trim(cnes), '')                                       as cnes,
    nullif(trim(codufmun), '')                                   as municipio_6,
    cast(try_strptime(trim(competen) || '01', '%Y%m%d') as date) as competencia,
    try_cast(nullif(trim(tp_leito), '') as integer)              as tp_leito,
    try_cast(nullif(trim(codleito), '') as integer)              as codleito,
    try_cast(nullif(trim(qt_exist), '') as integer)              as qt_exist,
    try_cast(nullif(trim(qt_contr), '') as integer)              as qt_contr,
    try_cast(nullif(trim(qt_sus), '') as integer)                as qt_sus
from {{ bronze_atual('cnes_lt') }}
