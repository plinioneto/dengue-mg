"""Catálogo executável das fontes (espelha docs/catalogo_fontes.md)."""
HOST = "ftp.datasus.gov.br"
UF_MG = "31"

# nome -> configuração. `filtro` recebe dict coluna->valor e mantém só Minas Gerais.
FTP_FONTES = {
    "sinan_final": dict(pasta="/dissemin/publicos/SINAN/DADOS/FINAIS", padrao=r"^DENGBR(\d{2})\.dbc$",
                        filtro=lambda r: r.get("SG_UF_NOT") == UF_MG or r.get("SG_UF") == UF_MG),
    "sinan_prelim": dict(pasta="/dissemin/publicos/SINAN/DADOS/PRELIM", padrao=r"^DENGBR(\d{2})\.dbc$",
                         filtro=lambda r: r.get("SG_UF_NOT") == UF_MG or r.get("SG_UF") == UF_MG),
    "cnes_lt": dict(pasta="/dissemin/publicos/CNES/200508_/Dados/LT", padrao=r"^LTMG(\d{4})\.dbc$", filtro=None),
    # SIH: mantém só internações com diagnóstico principal de dengue (A90, A91) para reduzir o volume
    "sih_rd": dict(pasta="/dissemin/publicos/SIHSUS/200801_/Dados", padrao=r"^RDMG(\d{4})\.dbc$",
                   filtro=lambda r: r.get("DIAG_PRINC", "")[:3] in ("A90", "A91")),
}
ANO_INICIAL = 2022  # histórico a partir de 2022 (decisão registrada no ADR-0001)
