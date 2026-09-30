#!/usr/bin/env python3
"""Auditoria da especificação OpenAPI (Ex. 13, R24).

Lê openapi.json e aponta falhas de design de segurança. Uso:
    curl -s localhost:8000/openapi.json > openapi.json
    python scripts/auditar_openapi.py openapi.json
"""
import json
import sys

spec = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "openapi.json"))
paths = spec.get("paths", {})
achados: list[str] = []

# Rotas públicas por design (não exigem token).
PUBLICAS = {("/", "get"), ("/health", "get"), ("/auth/token", "post"), ("/auth/mfa/verify", "post"),
            ("/auth/client-token", "post"), ("/recepcao/login", "get"), ("/recepcao/login", "post")}

for rota, metodos in paths.items():
    for metodo, op in metodos.items():
        if metodo not in ("get", "post", "patch", "delete", "put"):
            continue
        chave = (rota, metodo)
        # 1) rota sem declaração de segurança (informativo — a app usa Depends, não security scheme)
        if "security" not in op and chave not in PUBLICAS:
            achados.append(f"[info] {metodo.upper()} {rota}: sem 'security' na spec "
                           f"(protegida via Depends; considerar documentar o esquema)")
        # 2) respostas de erro não documentadas
        respostas = set(op.get("responses", {}).keys())
        if chave not in PUBLICAS and not ({"401", "403"} & respostas):
            achados.append(f"[medio] {metodo.upper()} {rota}: não documenta 401/403")
        # 3) parâmetros string sem maxLength/pattern
        for p in op.get("parameters", []):
            sch = p.get("schema", {})
            if sch.get("type") == "string" and "maxLength" not in sch and "pattern" not in sch:
                achados.append(f"[medio] {metodo.upper()} {rota}: parâmetro '{p.get('name')}' "
                               f"string sem maxLength/pattern")
        # 4) corpo de entrada sem additionalProperties=false (extra='forbid')
        rb = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        ref = rb.get("$ref", "")
        if ref:
            nome = ref.split("/")[-1]
            comp = spec.get("components", {}).get("schemas", {}).get(nome, {})
            if comp.get("additionalProperties", True) is not False:
                achados.append(f"[baixo] {metodo.upper()} {rota}: schema '{nome}' "
                               f"sem additionalProperties:false (verificar extra='forbid')")

# 5) /docs e /openapi.json expostos
if spec.get("info"):
    achados.append("[info] Verifique se /docs e /openapi.json ficam desabilitados em produção "
                   "(a app usa docs_url=None quando ENV=prod).")

# 6) IDs inteiros sequenciais (enumeração)
for rota in paths:
    if "{consulta_id}" in rota or "{id}" in rota:
        achados.append(f"[baixo] {rota}: id inteiro sequencial (enumeração); "
                       f"ownership mitiga, UUID seria defesa extra — risco residual")
        break

print(f"Auditoria OpenAPI — {len(achados)} apontamentos\n" + "-" * 60)
for a in achados:
    print(a)
