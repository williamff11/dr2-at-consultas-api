#!/usr/bin/env python3
"""Calcula os scores CVSS 3.1 das vulnerabilidades do Assessment (Ex. 12).

Usa a biblioteca `cvss` (PyPI). Os vetores foram revisados e justificados no
docs/12_pipeline_devsecops.md. Uso:
    scripts/.venv-tools/bin/pip install cvss
    scripts/.venv-tools/bin/python scripts/cvss_scores.py
"""
from cvss import CVSS3

# (id, descrição, vetor, impacto de negócio → prioridade final)
VULNS = [
    ("V1  BOLA prontuário", "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
     "Expõe prontuário (dado de saúde/LGPD) de terceiros → PRIORIDADE CRÍTICA (sobe acima do CVSS)"),
    ("V2  SQL injection", "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H",
     "Vaza pacientes + hashes de senha; base para tomada de conta → CRÍTICA"),
    ("V3  XSS stored", "AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N",
     "Sequestro de sessão da recepção; requer interação → ALTA"),
    ("V4  Mass assignment", "AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N",
     "Reatribuição indevida de consultas (integridade) → ALTA"),
    ("V5a CORS wildcard", "AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
     "Leitura cross-origin de respostas autenticadas → MÉDIA/ALTA"),
    ("V5b Força bruta", "AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N",
     "Adivinhação de senha sem limite → ALTA (mitigada por rate limit)"),
    ("V5c Sem headers", "AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N",
     "Clickjacking/downgrade → MÉDIA"),
    ("T11 Segredo hardcoded", "AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N",
     "Segredo JWT no código permite forjar tokens → ALTA/CRÍTICA"),
]

print(f"{'ID':<22}{'Vetor CVSS 3.1':<38}{'Score':>6}  {'Severidade':<10} Impacto de negócio / prioridade")
print("-" * 140)
for nome, vetor, negocio in VULNS:
    c = CVSS3(f"CVSS:3.1/{vetor}")
    score = c.scores()[0]
    sev = c.severities()[0]
    print(f"{nome:<22}{vetor:<38}{score:>6}  {sev:<10} {negocio}")
