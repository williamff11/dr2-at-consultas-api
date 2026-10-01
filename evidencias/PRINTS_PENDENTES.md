# Pendências manuais (só o William pode fazer)

Checklist do que não pôde ser capturado automaticamente pelo agente, com a etapa em que deveria ter sido feito e o estado (commit/tag) que precisa estar rodando.

| # | Etapa | O quê | Estado necessário | Status |
|---|---|---|---|---|
| P1 | 13 | Ligar o Docker/OrbStack para o scan OWASP ZAP (baseline passivo) | tag `ex13` rodando em localhost:8000 | **FEITO** — scan local com Docker: `ex13/02_zap_baseline_depois.{html,json,md}` + `02_zap_resumo.txt` (0 FAIL, 6 WARN, 61 PASS); também roda no job `dast` do CI |
| P2 | 12 | Criar repositório GitHub, push da main, branch protection exigindo o check `security-gate` | main protegida (ruleset `protect-main`) | **FEITO** — prints `ex12/08_ruleset_protecao_main.png`, `ex12/09_ruleset_regras.png` |
| P3 | 12 | Print do pipeline verde na main e do PR com merge bloqueado (branch demo reintroduz a V2) | PR #1 (demo/gate-bloqueio) | **FEITO** — PR bloqueado: `ex12/07_gate_bloqueou_pr.png`, `ex12/11_pr_bloqueado_3_checks.png` (sast/tests/security-gate ❌) e log do Bandit `ex12/12_sast_bandit_b608_log.png`; main verde: `ex12/10_pipeline_verde_main.png` |
| P4 | 12 | Validar/reescrever o critério do security gate com suas palavras | — | pendente (rascunho escrito no README, Ex. 12, "Critério de bloqueio do security gate" — revisar com suas palavras) |
| P5 | 13 | Decidir bloquear ou liberar o deploy diante do risco residual | — | pendente (rascunho escrito no `RELATORIO_RASTREABILIDADE_DR2_AT.md` §5 — revisar com suas palavras) |
| P6 | 14 | Gravar o vídeo (≤5 min, YouTube não listado) e colar o link | estado final | pendente |
