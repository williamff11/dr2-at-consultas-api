# Ex. 11 — Persistência segura (SQLModel + BaseSettings)

**Rubrica:** R18 · **Tag:** `ex11` · Ameaças cobertas: T11 (segredo), pré-requisito de T02 (SQLi) · Ameaça associada ao commit ordenado: `ex11`

## Por que este exercício foi antecipado (executado como Etapa 8)

O plano executou o Ex. 11 **antes** dos Ex. 8–10. Motivo: a vulnerabilidade de **SQL injection** do Ex. 8 (V2) só é realista, e só pode ser demonstrada, sobre uma **camada de persistência SQL real**. Com o armazenamento em dicionários Python (Ex. 1–7), não há SQL para injetar — uma "SQLi" ali seria encenação. Migrando a persistência primeiro, a falha do Ex. 8 é introduzida e explorada sobre o banco de verdade, e a correção do Ex. 9 (parametrização) passa a ter significado. Os documentos seguem numerados pelo exercício.

## 1. Migração para SQLModel com queries parametrizadas

- **Tabelas** (`app/models/tables.py`): `Profissional`, `Paciente`, `Consulta` (com os campos de auditoria), `Usuario`, `ClienteM2M`. Os schemas Pydantic de entrada/saída (`app/models/consulta.py`) continuam **separados** das tabelas — o contrato da API não é o modelo do banco.
- **Engine e sessão** (`app/database.py`): `create_engine` a partir de `Settings.database_url`; `get_session()` injeta a sessão via `Depends` com `yield` (abre/fecha por request). `criar_tabelas()` roda no `lifespan`.
- **Queries parametrizadas:** todo acesso usa `select(...).where(...)` ou `session.get(...)`. **Nenhum `text()` com f-string.** A evidência `ex11/04_queries_parametrizadas_log.txt` (com `DB_ECHO=1`) mostra o SQL emitido como `WHERE paciente.nome = ?` e os valores em uma tupla separada (`('Ana Souza',)`): o valor nunca vira parte do texto da query, então não pode alterar sua estrutura. É o oposto do que o Ex. 8/V2 fará de propósito.
- **Injeção de sessão nas rotas:** todas as rotas passaram a receber `session: Session = Depends(get_session)`; a lógica de negócio não mudou, só a origem dos dados. `get_consulta_autorizada` agora faz `session.get(Consulta, id)` mantendo-se como ponto único de ownership.

## 2. Credenciais fora do código (BaseSettings + .env)

- `app/core/config.py`: `class Settings(BaseSettings)` com `model_config = SettingsConfigDict(env_file=".env")`. Todos os parâmetros vêm do ambiente.
- **Sem default para segredos:** `jwt_secret_key`, `seed_senha_*` e `lab_client_secret` **não têm valor padrão**. Se faltarem, o `Settings()` lança `ValidationError` e a aplicação **não sobe** (evidência `ex11/06_falha_sem_segredo.txt`). Falhar cedo é melhor do que rodar com um segredo previsível — um `JWT_SECRET_KEY` default permitiria a qualquer pessoa forjar tokens válidos (T04).
- **Segredo removido do código:** o `SECRET_KEY` hardcoded que existia em `security.py` (Ex. 6, capturado em `ex11/01_segredo_hardcoded_antes.txt`) foi substituído por `get_settings().jwt_secret_key`. A evidência `ex11/02_sem_credenciais_depois.txt` mostra o `grep` por segredo em `app/` **vazio** e o segredo vindo de `Settings`.
- **`.env` nunca versionado:** só `.env.example` (placeholders) vai no repositório/ZIP. `ex11/03_env_example.txt` mostra `git check-ignore` confirmando que `.env` está no `.gitignore` e que nenhum `.env` está versionado. Em DEV, `scripts/dev_env.sh` exporta valores fictícios equivalentes.

## 3. Antes × depois

| Aspecto | Antes (Ex. 6, tag `ex06`) | Depois (Ex. 11, tag `ex11`) |
|---|---|---|
| Persistência | dicts em memória (`db.consultas`, …) | SQLModel + SQLite (`select().where()`) |
| Sessão | — | `Depends(get_session)` com `yield` |
| Segredo JWT | hardcoded em `security.py:17` | `Settings.jwt_secret_key` (env/.env) |
| Falta de segredo | app subia com segredo fraco | app **não sobe** (fail-fast) |
| Evidência | `ex11/01_segredo_hardcoded_antes.txt` | `ex11/02..06` |

## Evidências

| Arquivo | O que prova |
|---|---|
| `ex11/01_segredo_hardcoded_antes.txt` | segredo no código (estado do Ex. 6) |
| `ex11/02_sem_credenciais_depois.txt` | `grep` de segredo em `app/` vazio; segredo vem de Settings |
| `ex11/03_env_example.txt` | `.env.example` com placeholders; `.env` ignorado |
| `ex11/04_queries_parametrizadas_log.txt` | SQL com `?` e parâmetros separados |
| `ex11/05_pytest.txt` | 20 testes verdes com SQLite em memória |
| `ex11/06_falha_sem_segredo.txt` | app recusa subir sem `JWT_SECRET_KEY` |
