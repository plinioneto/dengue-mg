# ADR-0002: Camadas bruta/tratada/final, ingestão idempotente e versionada

**Status:** aceita (01/11/2026)

**Decisão.** A camada bruta guarda cada arquivo como Parquet, com todas as colunas como texto e sem correções. Cada carga é registrada em `bronze_loads` (fonte, arquivo, sha256, tamanho e data de publicação no servidor, linhas, caminho). A chave de idempotência é (fonte, arquivo, sha256): reexecutar não duplica. Se o conteúdo muda (SINAN preliminar), uma nova versão é gravada e a anterior é mantida, o que permite medir a revisão das semanas preliminares (R8). Antes de baixar, compara-se tamanho e data do servidor com a última carga.

**Consequências.** O .dbc original não é guardado (só o Parquet e o hash). Reprocessar uma versão antiga depende do Parquet.
