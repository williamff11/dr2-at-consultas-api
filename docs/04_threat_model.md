# Ex. 4 — Misuse cases, STRIDE e threat model consolidado

**Rubrica:** R7, R8 · **Tag:** `ex04`

> Documento de referência oficial da entrega. Os IDs `MCxx` (misuse cases) e `Txx` (ameaças) são **estáveis** e citados depois:
> - nas vulnerabilidades do Ex. 8 (`docs/08_vulnerabilidades.md`);
> - nas docstrings dos testes `consultas-api/tests/security/test_Txx_*.py` (Ex. 12);
> - no relatório de rastreabilidade do capstone (`RELATORIO_RASTREABILIDADE_DR2_AT.md`).
>
> As colunas **"Teste que prova"** e **"Evidência"** da tabela da seção 4 começam como `(pendente)` e são preenchidas conforme cada mitigação é implementada. É isso que torna o modelo rastreável de ponta a ponta (R8, R22, R23).
>
> **Nota sobre payloads:** este documento descreve os vetores de forma conceitual. As strings de exploração concretas ficam apenas onde têm função de prova — nos comandos capturados por `scripts/evidencia.sh` (Ex. 8/9) e nos testes automatizados — nunca transcritas na prosa.

Base: DFD do Ex. 3 (`docs/img/dfd.png`). Superfícies consideradas: as rotas atuais e as já decididas para os próximos exercícios (`/auth/*`, `/pacientes`, `/consultas/{id}/prontuario`, `/horarios-disponiveis`, `/admin/*`, `/recepcao/*`).

---

## 1. Misuse cases

Formato: **ator · objetivo · pré-condição · passos (conceituais) · rota real · STRIDE → ameaça**.

### MC01 — Troca de identificador para ler dados clínicos de terceiro (BOLA)
- **Ator:** usuário autenticado (ex.: o profissional Dr. Diego) com um token legítimo.
- **Objetivo:** ler prontuário/anotações de um paciente que não está sob seus cuidados.
- **Passos:** obtém um JWT válido; acessa uma consulta própria; substitui o identificador do recurso na URL por outros valores sequenciais; a API responde com dados de pacientes de outro profissional, por não checar posse do recurso.
- **Rotas:** `GET /consultas/{id}`, `GET /consultas/{id}/prontuario`, `PATCH`/`DELETE /consultas/{id}`, página de detalhe da recepção.
- **STRIDE:** Information Disclosure, Elevation of Privilege → **T01**.

### MC02 — Injeção na busca textual de pacientes
- **Ator:** usuário autenticado com acesso à busca (recepção/profissional).
- **Objetivo:** contornar o filtro da busca para ler registros fora do escopo e, no limite, extrair credenciais.
- **Passos:** usa o parâmetro de busca por nome como ponto de entrada; em vez de um nome, envia conteúdo que altera a estrutura da consulta ao banco, aproveitando que o valor é concatenado direto na query em vez de parametrizado.
- **Rota:** `GET /pacientes?nome=`.
- **STRIDE:** Tampering, Information Disclosure → **T02**.

### MC03 — Comentário malicioso persistido que executa no navegador da recepção (XSS stored)
- **Ator:** quem consegue gravar o campo livre `observacoes` (usuário autenticado; ou, antes da autenticação, qualquer um).
- **Objetivo:** executar script no navegador de toda recepcionista que abrir a agenda, sequestrando a sessão.
- **Passos:** grava markup ativo no campo de observações; a página de detalhe renderiza esse campo sem escape (uso indevido de `|safe`), e o script roda no contexto da recepção.
- **Rotas:** `POST /consultas` (gravação) → página de detalhe/agenda da recepção (execução).
- **STRIDE:** Tampering, Elevation of Privilege → **T03**.

### MC04 — Token do laboratório usado para alcançar dados de paciente
- **Ator:** quem obtém o token M2M do laboratório parceiro (vazamento/comprometimento).
- **Objetivo:** ler ou criar consultas (PHI) com uma credencial que deveria ver só horários livres.
- **Passos:** apresenta o token M2M às rotas de consultas; se o escopo não for verificado, a credencial ultrapassa o combinado em contrato.
- **Rotas:** `GET/POST /consultas*` com token de escopo `horarios:read`.
- **STRIDE:** Elevation of Privilege, Information Disclosure → **T07** (escopo) e reforça **T01**.

### MC05 — Força bruta no login
- **Ator:** atacante externo não autenticado.
- **Objetivo:** descobrir a senha de um profissional/admin por tentativa e erro.
- **Passos:** repete requisições ao endpoint de token com muitas combinações de senha, sem qualquer limite de taxa.
- **Rota:** `POST /auth/token`.
- **STRIDE:** Spoofing, Denial of Service → **T05** e **T10**.

### MC06 — Campos extras no corpo para se apropriar de uma consulta (mass assignment)
- **Ator:** usuário autenticado.
- **Objetivo:** alterar campos que não deveriam ser editáveis pelo cliente (ex.: dono da consulta, autor do registro).
- **Passos:** inclui no corpo do PATCH/POST campos além dos declarados; se o modelo aceitar chaves extras e fizer atribuição em massa, o cliente sobrescreve `profissional_id`/`criado_por`.
- **Rota:** `PATCH /consultas/{id}`, `POST /consultas`.
- **STRIDE:** Tampering, Elevation of Privilege → **T06**.

---

## 2. STRIDE por componente

Ameaça concreta ou "n/a" com o motivo. Componentes escolhidos: os quatro processos do DFD.

### 2.1 `/auth/*` (login, MFA, token M2M)
| STRIDE | Ameaça nesta API |
|---|---|
| **S** poofing | passar-se por um usuário: força bruta de senha (**T05**), token forjado/assinatura inválida (**T04**) |
| **T** ampering | alterar claims do JWT (papel, sub) se a assinatura não for verificada (**T04**) |
| **R** epudiation | login sem trilha de auditoria — não se sabe quem tentou/entrou (**T09**) |
| **I** nfo disclosure | mensagem de erro que distingue "usuário não existe" de "senha errada" (enumeração) → mitigado por resposta genérica (**T05**) |
| **D** oS | flood no login sem rate limit (**T10**) |
| **E** levation | conta comum obtém privilégio de admin sem MFA (**T08**) |

### 2.2 `/consultas/{id}` e `/consultas/{id}/prontuario`
| STRIDE | Ameaça |
|---|---|
| **S** | acesso sem token (rota hoje aberta) → mitigado por `OAuth2PasswordBearer` (**T01**) |
| **T** | mass assignment via campos extras no PATCH (**T06**) |
| **R** | alteração de consulta sem registro de autor (**T09**) |
| **I** | **BOLA**: ler consulta/prontuário de terceiro (**T01**) |
| **D** | enumeração de IDs sequenciais para varrer a base (**T01**, risco residual no Ex. 13) |
| **E** | profissional agindo sobre paciente de outro profissional (**T01**) |

### 2.3 `/recepcao/*` (páginas HTML)
| STRIDE | Ameaça |
|---|---|
| **S** | acesso à agenda sem autenticação da recepção → cookie de sessão (**T01**) |
| **T** | **XSS stored** via `observacoes` renderizado sem escape (**T03**) |
| **R** | n/a direto (páginas são leitura); a gravação ocorre em `/consultas` |
| **I** | agenda expõe mais dado do que o necessário (CPF) → minimização no `pages.py` |
| **D** | página pesada sob flood → rate limit global (**T10**) |
| **E** | recepcionista alcançar rota de admin (**T08**) |

### 2.4 Integração M2M (`/auth/client-token`, `/horarios-disponiveis`)
| STRIDE | Ameaça |
|---|---|
| **S** | cliente M2M sem `client_secret` forte / secret em texto (**T07**) |
| **T** | trocar `grant_type` para obter um token humano (**T07**) |
| **R** | ações do parceiro sem correlação (`client_type: m2m` nas claims) (**T09**) |
| **I** | token M2M alcançar PHI (**T07** + **T01**) |
| **D** | parceiro consumindo a API sem limite (**T10**) |
| **E** | escopo amplo demais concedido ao parceiro (**T07**) |

---

## 3. Ativos

| Ativo | Sensibilidade | Onde vive |
|---|---|---|
| Dados de saúde (consultas, prontuário, observações) | **PHI / LGPD art. 11** | Banco, respostas JSON, agenda HTML |
| Credenciais e hashes de senha | crítico | Banco (bcrypt) |
| `JWT_SECRET_KEY` | crítico (assina todos os tokens) | `.env` (Ex. 11) |
| `client_secret` do laboratório | alto | Banco (bcrypt) |
| Segredo TOTP do admin | alto | Banco / `.env` |
| Logs / trilha de auditoria | médio (integridade) | `criado_por`, `atualizado_em` |

---

## 4. Threat model consolidado (tabela rastreável)

STRIDE: S/T/R/I/D/E. As duas últimas colunas são preenchidas nas Etapas 10, 12 e 13.

| ID | Ameaça | STRIDE | Ativo | Superfície (rota) | Mitigação | Exercício | Teste que prova | Evidência |
|---|---|---|---|---|---|---|---|---|
| **T01** | BOLA em consulta/prontuário | I, E | dados de saúde | `GET/PATCH/DELETE /consultas/{id}`, `/prontuario`, detalhe HTML | ownership centralizado (`get_consulta_autorizada`) num único `APIRouter` | 6, 9 | `test_correcoes::test_prontuario_bloqueia_outro_profissional`, `test_detalhe_html_bloqueia_outro_profissional` | `ex09/01,02 antes→depois` |
| **T02** | SQL injection na busca | T, I | dados de saúde, hashes | `GET /pacientes?nome=` | query parametrizada SQLModel + validação regex do parâmetro | 9, 11 | `test_correcoes::test_busca_pacientes_rejeita_injecao` | `ex09/03 antes→depois` |
| **T03** | XSS stored em `observacoes` | T, E | sessão da recepção | `POST /consultas` → agenda/detalhe HTML | auto-escape Jinja2 (sem `\|safe`) + rejeição de `<`/`>` na entrada | 2, 9 | `test_correcoes::test_observacoes_com_html_rejeitada_na_entrada`, `test_detalhe_html_escapa_conteudo` | `ex09/04 antes→depois` |
| **T04** | JWT forjado / expirado aceito | S, T | todas as sessões | qualquer rota autenticada | assinatura HS256 verificada + validação de `exp`/`iss`/`aud` | 6 | `test_auth::test_token_expirado_401`, `test_token_assinado_com_outra_chave_401` | `ex06/04` |
| **T05** | Força bruta de senha | S, D | credenciais | `POST /auth/token` | rate limit dedicado + resposta genérica + MFA no admin | 10 | `(Ex.12)` | `ex10/02 antes` |
| **T06** | Mass assignment | T, E | integridade da consulta | `POST`/`PATCH /consultas` | `extra='forbid'` + whitelist de campos; `profissional_id` vem do token | 9 | `test_correcoes::test_patch_rejeita_campos_extras`, `test_post_rejeita_campo_inexistente` | `ex09/05,06 antes→depois` |
| **T07** | Token M2M além do escopo | E, I | dados de saúde | `/consultas*` com token de laboratório | escopos OAuth (`horarios:read`) verificados por `Security(scopes=...)` | 7 | `test_m2m::test_lab_nao_acessa_consultas` | `ex07/04` |
| **T08** | Escalada de privilégio (recepção/prof → admin; admin sem MFA) | E | funções administrativas | `/admin/*` | RBAC (`require_roles`) + `require_mfa` | 6 | `test_auth::test_recepcionista_nao_acessa_rota_admin`, `test_admin_sem_mfa_barrado_e_com_mfa_liberado` | `ex06/07`, `ex06/11-13` |
| **T09** | Repúdio: ação sem trilha | R | integridade/auditoria | escrita em `/consultas`, `/auth` | `criado_por`=usuário autenticado, `atualizado_em`; log centralizado = risco residual | 6, 13 | `(pendente)` | `(pendente)` |
| **T10** | DoS por volume / CORS permissivo | D, (S) | disponibilidade | toda a API; preflight CORS | rate limit global + CORS allowlist + headers | 10 | `(Ex.12)` | `ex10/01 antes` |
| **T11** | Segredo hardcoded no código | I | `JWT_SECRET_KEY`, credenciais | código-fonte | `BaseSettings` + `.env` (fora do git); sem defaults para segredos | 11 | `ex11/06` (fail-fast) | `ex11/01→02` |
| **T12** | Falta de headers de segurança (clickjacking, sniffing, downgrade) | T, I | sessão da recepção | respostas HTTP | HSTS, X-Frame-Options, X-Content-Type-Options, CSP | 10 | `(Ex.12)` | `ex10/03 antes` |

## Evidências

| Arquivo | O que prova |
|---|---|
| `docs/img/dfd.png` | superfícies e fronteiras que embasam os componentes STRIDE |
| tabela da seção 4 | ativos, superfícies e mitigações com colunas de rastreio (preenchidas nos Ex. 9–13) |
