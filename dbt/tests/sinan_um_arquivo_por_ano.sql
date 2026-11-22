-- Cada ano de arquivo vem de uma única fonte (final ou preliminar), nunca das duas (evita contar a notificação duas vezes).
select ano_arquivo, count(distinct fonte) as fontes
from {{ ref('stg_sinan') }}
group by ano_arquivo
having count(distinct fonte) > 1
