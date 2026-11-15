{# Nomes de esquema exatos (tratada, final), sem prefixo do esquema do alvo. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}{{ target.schema }}{%- else -%}{{ custom_schema_name | trim }}{%- endif -%}
{%- endmacro %}

{# Última versão carregada de cada arquivo de uma fonte da bruta (ADR-0002). Falha se a fonte não foi carregada. #}
{% macro bronze_atual(fonte) -%}
    {%- if execute -%}
        {%- set q -%}
            select parquet_path from (
                select parquet_path, row_number() over (partition by file_name order by loaded_at desc) as rn
                from bronze_loads where source = '{{ fonte }}' and "rows" > 0
            ) where rn = 1
        {%- endset -%}
        {%- set caminhos = run_query(q).columns[0].values() -%}
        {%- if caminhos | length == 0 -%}
            {{ exceptions.raise_compiler_error("Fonte '" ~ fonte ~ "' sem carga na camada bruta (bronze_loads). Rode a ingestão antes.") }}
        {%- endif -%}
        {#- Caminhos relativos da bruta valem a partir da pasta onde a ingestão rodou (DENGUE_CWD, definido por dengue_mg.tratada). -#}
        {%- set barra = '\\' -%}
        read_parquet([
            {%- for p in caminhos -%}
                {%- set p = p | replace(barra, '/') -%}
                {%- if not (p.startswith('/') or p[1:2] == ':') -%}{%- set p = env_var('DENGUE_CWD', '.') | replace(barra, '/') ~ '/' ~ p -%}{%- endif -%}
                '{{ p | replace("'", "''") }}'{% if not loop.last %}, {% endif %}
            {%- endfor -%}
        ], union_by_name = true, filename = true)
    {%- else -%}
        (select 1)
    {%- endif -%}
{%- endmacro %}

{# Texto de data da fonte (AAAAMMDD ou AAAA-MM-DD) para DATE; vazio ou inválido vira nulo. #}
{% macro parse_data(col) -%}
    cast(coalesce(try_strptime(nullif(trim({{ col }}), ''), '%Y%m%d'), try_strptime(nullif(trim({{ col }}), ''), '%Y-%m-%d')) as date)
{%- endmacro %}

{# Data de referência ("hoje") da execução. #}
{% macro hoje() -%}
    {%- if var('data_referencia') | length > 0 -%}date '{{ var("data_referencia") }}'{%- else -%}current_date{%- endif -%}
{%- endmacro %}

{# Domingo que abre a semana epidemiológica da data (SE vai de domingo a sábado). #}
{% macro inicio_semana(col) -%}
    ({{ col }} - cast(dayofweek({{ col }}) as integer))
{%- endmacro %}
