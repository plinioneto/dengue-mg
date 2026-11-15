"""Gera data/ca-bundle.pem = certificados do `certifi` + raízes confiáveis do Windows.

Serve para redes/antivírus que reassinam o HTTPS com certificado próprio (o Windows confia, o Python não).
Mantém a verificação TLS ligada. Uso:
    .venv\\Scripts\\python scripts\\exportar_certificados.py
    set REQUESTS_CA_BUNDLE=data\\ca-bundle.pem
"""
import os
import ssl
import sys

import certifi

destino = os.path.join("data", "ca-bundle.pem")
os.makedirs("data", exist_ok=True)
with open(certifi.where(), encoding="ascii") as f:
    partes = [f.read()]
n = 0
if sys.platform == "win32":
    for loja in ("ROOT", "CA"):
        for der, codificacao, _ in ssl.enum_certificates(loja):
            if codificacao == "x509_asn":
                partes.append(ssl.DER_cert_to_PEM_cert(der))
                n += 1
with open(destino, "w", encoding="ascii") as f:
    f.write("\n".join(partes))
print("%s gerado (%d certificados do Windows somados ao certifi)" % (destino, n))
