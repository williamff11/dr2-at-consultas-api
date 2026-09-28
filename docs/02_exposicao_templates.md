# Ex. 2 — Controle de exposição de dados e templates seguros

**Rubrica:** R2, R3, R4 · **Tag:** `ex02` · **Branch de demonstração:** `demo/ex02-sem-response-model` (commit `f3b26ec`)

## 1. response_model controla exatamente os campos expostos (R2)

O registro armazenado de cada consulta tem campos internos de auditoria: `criado_por`, `ip_origem`, `criado_em`, `atualizado_em` (`consultas-api/app/routes/consultas.py`, no `criar_consulta`). O contrato público é outro modelo:

- `consultas-api/app/models/consulta.py:40`: `ConsultaPublic` (id, paciente_id, profissional_id, data_hora, status, observacoes). É uma **allowlist** de saída.
- `consultas-api/app/routes/consultas.py:16,21,27,49`: todas as rotas que devolvem consulta declaram `response_model=ConsultaPublic` (ou `list[ConsultaPublic]`).

O FastAPI valida e **filtra** o objeto retornado pela rota através do `response_model`: um campo que não está declarado em `ConsultaPublic` não sai na resposta, mesmo que exista no registro. Também separamos os modelos de **entrada** (`ConsultaCreate`/`ConsultaUpdate`: o que o cliente pode enviar) dos de **saída** (o que ele pode ver). Assim, nenhum dos dois contratos é derivado do modelo de persistência.

## 2. Por que é arriscado não definir response_model (R3)

**Mecanismo.** Sem `response_model`, o FastAPI serializa *tudo* o que a função retorna (`jsonable_encoder` do objeto inteiro). A resposta passa a ser definida pelo **modelo de persistência**, não pelo contrato da API. Com isso:

1. **Todo campo interno vaza hoje.** Na evidência `ex02/01_sem_response_model_antes.txt`, o mesmo POST/GET devolve `criado_por`, `ip_origem` (IP de quem cadastrou) e os carimbos de data/hora.
2. **Todo campo adicionado no futuro também vaza.** Se amanhã alguém acrescentar `cpf`, `senha_hash` ou `anotacoes_clinicas` ao registro, eles aparecem na API sem nenhuma mudança na rota. Esse vazamento é silencioso e não é detectado em code review da rota, porque a rota não mudou.
3. **O filtro vira responsabilidade do cliente.** Confiar que o frontend "não mostra" o campo não adianta: o dado já trafegou e está visível no DevTools, em proxies e em logs.

**Por que isso é grave aqui.** O IP de origem, somado ao autor da operação e aos horários, permite **correlacionar e identificar** o paciente e a recepção/unidade que o atendeu, a partir do momento em que ele passou pelo sistema. Isso é o que o enunciado descreve no "caso público" ("um campo interno vazado facilitou a identificação de usuários por terceiros não autorizados"). O IP é dado pessoal (LGPD, art. 5º, I). Associado a uma consulta médica, ele passa a revelar dado **sensível** de saúde (art. 5º, II, e art. 11), que exige tratamento com salvaguardas reforçadas. Um vazamento assim é incidente comunicável à ANPD (art. 48).

**Classificação.**
- OWASP API Security Top 10:2023 → **API3:2023, Broken Object Property Level Authorization** (antiga "Excessive Data Exposure"): o cliente recebe propriedades do objeto que não deveria ver.
- OWASP Top 10:2021 → **A01:2021, Broken Access Control** (exposição de informação a ator não autorizado).
- **CWE-213** (Exposure of Sensitive Information Due to Incompatible Policies) / **CWE-200**.

**Prova executável.** `consultas-api/tests/test_consultas.py::test_sem_response_model_vazaria_campos_internos` registra a **mesma função de rota** em um app auxiliar *sem* `response_model` e verifica que os quatro campos de auditoria aparecem. No app real, eles não aparecem. A justificativa deixa de ser só texto e passa a ser um teste que falha se o comportamento mudar.

## 3. Jinja2 com herança e auto-escape (R4)

- **Herança:** `consultas-api/app/templates/base.html:5,14,15` define o layout e os blocos `title`, `heading` e `content`. `agenda.html:1` faz `{% extends "base.html" %}` e só preenche os blocos. Cabeçalho, rodapé (aviso LGPD) e, depois, a CSP ficam em um único lugar.
- **Auto-escape explícito:** `consultas-api/app/routes/pages.py:16-19` cria o `Environment` com `autoescape=select_autoescape(["html"])`. Não dependemos do default implícito do Starlette: se alguém trocar o loader ou a forma de instanciar, o escape continua declarado no código.
- **O que o escape faz:** `{{ c.observacoes }}` (`agenda.html:21`) converte `<`, `>`, `&`, `"` e `'` em entidades HTML. O navegador exibe `<script>` como **texto** e não o executa.
- **Por que `|safe` nunca deve ser usado em conteúdo de usuário:** `|safe` (ou `Markup()`) marca a string como "HTML confiável" e **desliga o escape** naquele ponto. Um único `|safe` sobre `observacoes` basta para transformar o campo em XSS **stored**: o payload fica gravado no banco e executa no navegador de *toda* recepcionista que abrir a agenda, com acesso à sessão dela. Esse é o segundo incidente citado no enunciado. No Ex. 8 isso é demonstrado de propósito (V3).
- **Minimização na página:** `pages.py` monta um dicionário só com hora, nome, profissional, status e observações. CPF e campos de auditoria nem chegam ao template.

**JSON sem escape é o correto.** Em `ex02/03_xss_post_payload.txt`, a API JSON devolve `observacoes` com `<script>` cru. Isso não é falha. O encoding de saída depende do **contexto** em que o dado é renderizado: JSON é dado, não markup. Quem insere o valor em HTML (o Jinja2 aqui, ou o frontend via `textContent`) é que deve codificar para aquele contexto. Escapar no JSON corromperia o dado para outros consumidores e daria falsa sensação de segurança (a mesma string pode ir para um atributo, uma URL ou JS, e cada um exige um encoding diferente). A validação na **entrada** (rejeitar `<`/`>` em `observacoes`) entra no Ex. 9 como defesa em profundidade, não como substituto do escape.

## Evidências

| Arquivo | O que prova |
|---|---|
| `evidencias/ex02/01_sem_response_model_antes.txt` | commit `f3b26ec` (branch demo): sem response_model, POST e GET vazam os 4 campos de auditoria |
| `evidencias/ex02/02_com_response_model_depois.txt` | **mesmo comando** em `main`: só os campos de `ConsultaPublic` |
| `evidencias/ex02/03_xss_post_payload.txt` | payloads `<script>` e `<img onerror>` gravados (JSON devolve cru, correto) |
| `evidencias/ex02/04_agenda_html_escapada.txt` | HTML contém `&lt;script&gt;`; contagem de `<script` = 0 |
| `evidencias/ex02/05_agenda_escapada.png` (+ `.txt`) | página exibe o payload como texto, `dialogs=0` (nenhum alert disparado) |
| `evidencias/ex02/06_pytest.txt` | 4 testes verdes, incluindo o teste do vazamento sem response_model |
