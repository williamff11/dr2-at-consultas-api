"""Testes das correções do Ex. 9 (V1-V4 + endpoint irmão).

Provam que o mesmo ataque do Ex. 8 deixa de funcionar.
"""
from tests.test_consultas import _payload


def _cria_consulta_carla(client, auth, **kw):
    return client.post("/consultas", json=_payload(**kw), headers=auth("dra_carla")).json()


# ---- V1: BOLA no prontuário corrigida (ownership no item_router) ----
def test_prontuario_bloqueia_outro_profissional(client, auth):
    c = _cria_consulta_carla(client, auth)
    # Diego não é dono → 404
    assert client.get(f"/consultas/{c['id']}/prontuario", headers=auth("dr_diego")).status_code == 404
    # dona acessa
    assert client.get(f"/consultas/{c['id']}/prontuario", headers=auth("dra_carla")).status_code == 200


# ---- V1-irmão: página de detalhe agora exige ownership ----
def test_detalhe_html_bloqueia_outro_profissional(client, auth, cookie):
    c = _cria_consulta_carla(client, auth)
    r = client.get(f"/recepcao/consultas/{c['id']}", cookies=cookie("dr_diego"))
    assert r.status_code == 404
    r = client.get(f"/recepcao/consultas/{c['id']}", cookies=cookie("dra_carla"))
    assert r.status_code == 200


# ---- V2: SQL injection neutralizada (regex na borda + query parametrizada) ----
def test_busca_pacientes_rejeita_injecao(client, auth):
    h = auth("recepcao")
    # payload com dígitos/'=' está fora da whitelist → 422 (nem chega ao banco)
    assert client.get("/pacientes", params={"nome": "' OR '1'='1"}, headers=h).status_code == 422

    # payload só com letras/apóstrofo/espaço PASSA a whitelist (nomes tipo O'Brien),
    # mas agora é tratado como LITERAL pela query parametrizada: nenhuma linha extra,
    # nenhum hash vazado (a antiga UNION deixou de funcionar).
    r = client.get("/pacientes", params={"nome": "x' UNION SELECT"}, headers=h)
    assert r.status_code == 200
    assert r.json() == []                       # não casa nenhum paciente
    assert "$2b$" not in r.text                 # nenhum hash bcrypt vazado

    # busca legítima funciona e trata o valor como literal
    r = client.get("/pacientes", params={"nome": "Ana"}, headers=h)
    assert r.status_code == 200
    assert any(p["nome"] == "Ana Souza" for p in r.json())


# ---- V3: XSS stored neutralizado (entrada rejeita < >, saída escapa) ----
def test_observacoes_com_html_rejeitada_na_entrada(client, auth):
    r = client.post("/consultas", json=_payload(observacoes="<img src=x onerror=alert(1)>"),
                    headers=auth("dra_carla"))
    assert r.status_code == 422  # regex ^[^<>]*$


def test_detalhe_html_escapa_conteudo(client, auth, cookie):
    # grava um caractere & (permitido) e confere que sai escapado no HTML
    c = _cria_consulta_carla(client, auth, observacoes="Pressao alta & arritmia")
    r = client.get(f"/recepcao/consultas/{c['id']}", cookies=cookie("dra_carla"))
    assert "Pressao alta &amp; arritmia" in r.text
    assert "|safe" not in r.text


# ---- V4: mass assignment bloqueado (extra='forbid') ----
def test_patch_rejeita_campos_extras(client, auth):
    c = _cria_consulta_carla(client, auth)
    r = client.patch(f"/consultas/{c['id']}",
                     json={"observacoes": "ok", "profissional_id": 2, "criado_por": "hacker"},
                     headers=auth("dra_carla"))
    assert r.status_code == 422  # extra_forbidden


def test_post_rejeita_campo_inexistente(client, auth):
    r = client.post("/consultas", json=_payload(campo_inexistente=1), headers=auth("dra_carla"))
    assert r.status_code == 422


# ---- transição de status por whitelist ----
def test_transicao_status_invalida_rejeitada(client, auth):
    c = _cria_consulta_carla(client, auth)  # status agendada
    # agendada → realizada não é permitido
    r = client.patch(f"/consultas/{c['id']}", json={"status": "realizada"}, headers=auth("dra_carla"))
    assert r.status_code == 422
    # agendada → confirmada é permitido
    r = client.patch(f"/consultas/{c['id']}", json={"status": "confirmada"}, headers=auth("dra_carla"))
    assert r.status_code == 200
