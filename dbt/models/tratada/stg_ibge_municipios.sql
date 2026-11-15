-- Municípios de MG (IBGE, código de 7 dígitos). Última carga da bruta.
select
    cast(geocodigo as varchar)  as geocodigo,
    left(cast(geocodigo as varchar), 6) as cod6,
    nome                        as municipio,
    microrregiao,
    mesorregiao
from {{ bronze_atual('ibge_municipios') }}
