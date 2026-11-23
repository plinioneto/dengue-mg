# Modelo de dados da camada tratada (R4)

Esquemas no DuckDB (`data/plataforma.duckdb`): `tratada` (dimensões, staging e fatos) e `final` (reconciliação; a tabela final do R7 entra aqui).

```mermaid
erDiagram
    dim_municipio ||--o{ fct_casos_semana : geocodigo
    dim_municipio ||--o{ fct_internacoes_semana : geocodigo
    dim_municipio ||--o{ fct_leitos_mes : geocodigo
    dim_municipio ||--o{ fct_infodengue_semana : geocodigo
    dim_semana_epi ||--o{ fct_casos_semana : semana_id
    dim_semana_epi ||--o{ fct_internacoes_semana : semana_id
    dim_semana_epi ||--o{ fct_infodengue_semana : semana_id
    fct_casos_semana ||--|| rec_sinan_infodengue : "geocodigo, semana_id"
    fct_infodengue_semana ||--|| rec_sinan_infodengue : "geocodigo, semana_id"
    rec_sinan_infodengue }o--|| rec_resumo : "agrega"
    dim_municipio ||--o{ indicadores_municipio_semana : geocodigo
    dim_semana_epi ||--o{ indicadores_municipio_semana : semana_id

    dim_municipio {
        varchar geocodigo PK "IBGE, 7 dígitos"
        varchar cod6 "6 dígitos (CNES, SIH, SINAN)"
        varchar municipio
        varchar microrregiao
        varchar mesorregiao
        varchar regiao_saude "seed"
        varchar macrorregiao_saude "seed"
    }
    dim_semana_epi {
        int semana_id PK "AAAASS"
        int epi_ano
        int epi_semana
        date inicio "domingo"
        date fim "sábado"
    }
    fct_casos_semana {
        varchar geocodigo FK
        int semana_id FK
        bigint casos_notificados
        bigint casos_hospitalizados
        bigint casos_confirmados
        date dados_ate
    }
    fct_internacoes_semana {
        varchar geocodigo FK
        int semana_id FK
        bigint internacoes
        bigint obitos
        bigint dias_internacao
        date dados_ate
    }
    fct_leitos_mes {
        varchar geocodigo FK
        date competencia
        bigint leitos_existentes
        bigint leitos_sus
        bigint leitos_clinicos_pediatricos
        bigint estabelecimentos
        date dados_ate
    }
    fct_infodengue_semana {
        varchar geocodigo FK
        int semana_id FK
        double casos
        double casos_est
        int nivel
        date dados_ate
    }
    indicadores_municipio_semana {
        varchar geocodigo FK
        int semana_id FK
        bigint casos_notificados
        bigint internacoes
        bigint leitos_clinicos_pediatricos
        double pressao_internacoes_por_leito
        date pressao_dados_ate "e um dados_ate por grupo"
    }
    rec_sinan_infodengue {
        varchar geocodigo
        int semana_id
        bigint casos_sinan
        double casos_infodengue
        double divergencia
        boolean elegivel
        boolean dentro_do_limite
    }
```

Os fatos são esparsos (só há linha onde houve registro); a densificação município x semana (853 municípios, todas as semanas) é feita na tabela final `final.indicadores_municipio_semana` (R7; dicionário em `docs/dicionario_dados.md`). Os modelos `stg_*` limpam e tipam a bruta; regras em `docs/adr/0004-tratada-e-reconciliacao.md`.
