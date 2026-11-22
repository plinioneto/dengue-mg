{# Testes genéricos próprios (sem dependência de pacotes externos). #}

{# A combinação de colunas é única. #}
{% test chave_unica(model, colunas) %}
select {{ colunas | join(', ') }}, count(*) as n
from {{ model }}
group by {{ colunas | join(', ') }}
having count(*) > 1
{% endtest %}

{# Valor numérico dentro de [minimo, maximo] (nulos são ignorados; use not_null para exigir). #}
{% test entre(model, column_name, minimo=none, maximo=none) %}
select * from {{ model }}
where {{ column_name }} is not null
  and (false
       {% if minimo is not none %} or {{ column_name }} < {{ minimo }} {% endif %}
       {% if maximo is not none %} or {{ column_name }} > {{ maximo }} {% endif %})
{% endtest %}

{# Data dentro do período do projeto: de ano_inicial até a data de referência. #}
{% test data_no_periodo(model, column_name) %}
select * from {{ model }}
where {{ column_name }} < make_date({{ var('ano_inicial') }}, 1, 1) or {{ column_name }} > {{ hoje() }}
{% endtest %}
