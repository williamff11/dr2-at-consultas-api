# Pendências manuais (só o William pode fazer)

Checklist do que não pôde ser capturado automaticamente pelo agente, com a etapa em que deveria ter sido feito e o estado (commit/tag) que precisa estar rodando.

| # | Etapa | O quê | Estado necessário | Status |
|---|---|---|---|---|
| P1 | 13 | Ligar o Docker/OrbStack para o scan OWASP ZAP (baseline passivo) | tag `ex13` rodando em localhost:8000 | pendente (Docker estava parado em 28/09) |
| P2 | 12 | Criar repositório GitHub, push da main, branch protection exigindo o check `security-gate` | main protegida (ruleset `protect-main`) | **FEITO** — prints `ex12/08_ruleset_protecao_main.png`, `ex12/09_ruleset_regras.png` |
| P3 | 12 | Print do pipeline verde na main e do PR com merge bloqueado (branch demo reintroduz a V2) | PR #1 (demo/gate-bloqueio) | **PARCIAL** — PR bloqueado: `ex12/07_gate_bloqueou_pr.png` (security-gate Required ❌). Falta: print do run verde da main (opcional) |
| P4 | 12 | Validar/reescrever o critério do security gate com suas palavras | — | pendente (proposta no README, Ex. 12, "DECISÃO DO WILLIAM") |
| P5 | 13 | Decidir bloquear ou liberar o deploy diante do risco residual | — | pendente (proposta no relatório) |
| P6 | 14 | Gravar o vídeo (≤5 min, YouTube não listado) e colar o link | estado final | pendente |
