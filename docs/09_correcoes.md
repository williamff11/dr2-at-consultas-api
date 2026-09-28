# Ex. 9 — Correção de vulnerabilidades de entrada e saída

**Rubrica:** R14, R15, R16 · **Tag:** `ex09` (correção) sobre `ex08-vulneravel` (falha) · Ameaças: T01, T02, T03, T06

Cada correção usa o **mesmo comando/payload** do "antes"; só o commit muda. O corretor compara `_antes` (tag `ex08-vulneravel`) com `_depois` (tag `ex09`).

## V1 — BOLA corrigida de forma centralizada (R14)

**Como:** as rotas de item migraram para um `item_router` cujo **prefixo** `/consultas/{consulta_id}` carrega `dependencies=[Depends(get_consulta_autorizada)]` (`app/routes/consultas.py`). `GET`, `PATCH`, `DELETE` e `/prontuario` herdam a checagem de posse. **Qualquer rota nova** sob esse prefixo é obrigada a passar pela verificação — é impossível esquecer, que era a causa da V1.

A regra de posse continua num **único lugar** (`app/auth/dependencies.py:113`), o que a evidência `ex09/08_ownership_centralizado.txt` comprova: a comparação `consulta.profissional_id == user...` só existe ali. As duas outras ocorrências de `profissional_id ==` são **filtros de listagem** (escopar a coleção que um profissional vê) — não decisões de posse sobre um objeto, e não reimplementam a regra.

| | Antes (`ex08-vulneravel`) | Depois (`ex09`) |
|---|---|---|
| Diego → `/consultas/1/prontuario` | 200 com CPF e observações | **404** |
| Evidência | `ex09/01_..._antes.txt` | `ex09/01_..._depois.txt` |

## Endpoint irmão descoberto (exigência do enunciado)

**Como foi encontrado:** procurando no código o **mesmo padrão** da V1 — "rota que busca um recurso por id vindo da URL e o devolve sem passar por `get_consulta_autorizada`". O `grep` por `session.get(Consulta, ...)` fora do `item_router` revelou `GET /recepcao/consultas/{id}` (página de detalhe HTML), acessível ao papel profissional. Ele **não foi citado** no doc do Ex. 8 de propósito: é o achado do Ex. 9.

**Correção:** a página passou a usar a **mesma** dependência `get_consulta_autorizada` (`app/routes/pages.py`). Evidência `ex09/02`: Diego → **404**, Carla (dona) → **200**. Como as rotas de item herdam ownership do `item_router`, futuras páginas/rotas sob esse recurso não repetem a falha.

## V2 — SQL injection corrigida (R15)

**Como:** a busca virou `select(Paciente).where(Paciente.nome.contains(nome))` (query parametrizada, `app/routes/pacientes.py`) **e** o parâmetro é validado por **whitelist/regex** `^[A-Za-zÀ-ÿ' ]{2,60}$` na borda (`Query(pattern=...)`).

Evidência `ex09/03_V2_sqli_depois.txt` (mesmos vetores do antes):
- payload com `=`/dígitos (`' OR 1=1`) → **422** (fora da whitelist);
- `UNION SELECT ...` longo → **422** (excede `max_length`);
- um nome legítimo com apóstrofo (`O'Brien`) → **200** e resultado `[]`: o valor é **literal**, ligado como parâmetro, não altera a estrutura da query. A extração de hashes via UNION do Ex. 8 deixou de funcionar.

Duas camadas: a regex barra a maioria dos vetores na borda; a parametrização garante que, mesmo um valor que passe pela regex (apóstrofo é válido em nomes), seja tratado como dado.

## V3 — XSS stored corrigido (R16)

**Como:** removido o `| safe` do template (`app/templates/detalhe_consulta.html`); as quebras de linha agora vêm de CSS (`white-space: pre-line`), não de HTML. O auto-escape do Jinja2 volta a tratar `<`, `>` como texto. Camada extra: a entrada rejeita `<`/`>` (regex `^[^<>]*$` em `observacoes`).

| | Antes | Depois |
|---|---|---|
| POST `observacoes=<img onerror=...>` | aceito (200) | **422** (regex) |
| Página de detalhe | `alert()` **executa** (`ex09/04_..._antes.png`) | conteúdo como texto, **`dialogs=0`** (`ex09/04_..._depois.png`) |

## V4 — Mass assignment corrigido (R15)

**Como:** `model_config = ConfigDict(extra="forbid")` em `ConsultaCreate` e `ConsultaUpdate` (`app/models/consulta.py`). Campos não declarados são **rejeitados** (422 `extra_forbidden`), não mais aplicados. `profissional_id` e `criado_por` não são campos de entrada. Somado: transições de status por **whitelist** (`TRANSICOES_VALIDAS`) e `status` só pelo enum.

| | Antes | Depois |
|---|---|---|
| PATCH com `profissional_id`, `criado_por` | aceito; consulta troca de dono | **422 extra_forbidden** (`ex09/05_..._depois`) |
| POST com `campo_inexistente` | aceito em silêncio | **422** (`ex09/06_..._depois`) |
| `status` inexistente / transição proibida | — | **422** (`ex09/07_regex_whitelist`) |

## Evidências

| Arquivo (par antes/depois) | Prova |
|---|---|
| `ex09/01_V1_bola_prontuario_*` | BOLA: 200 → 404 |
| `ex09/02_V1irmao_detalhe_html_*` | endpoint irmão: 200 → 404 (dona 200) |
| `ex09/03_V2_sqli_*` | SQLi: extração → 422 / literal |
| `ex09/04_V3_xss_*` (.txt + .png) | XSS: alert executa → rejeitado/escapado |
| `ex09/05_V4_mass_assignment_*` | mass assignment: aceito → 422 |
| `ex09/06_extra_campo_*` | campo extra: aceito → 422 |
| `ex09/07_regex_whitelist.txt` | válido × inválido (nome, status, transição) |
| `ex09/08_ownership_centralizado.txt` | posse decidida só em `dependencies.py` |
| `ex09/09_pytest.txt` | 29 testes verdes |
