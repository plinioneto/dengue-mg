-- Minas Gerais tem 853 municípios.
select count(*) as n from {{ ref('dim_municipio') }} having count(*) <> 853
