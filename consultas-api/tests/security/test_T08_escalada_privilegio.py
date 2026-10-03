"""Ameaça: T08 (escalada de privilégio) · README.md, Ex. 4.

Expande o teste de autorização iniciado no Ex. 6 (test_recepcionista_nao_acessa_rota_admin),
cobrindo os demais vetores: profissional em rota admin, admin sem MFA, token M2M em rota humana.
"""
CLIENT = {"grant_type": "client_credentials", "client_id": "lab-parceiro",
          "client_secret": "lab-secret-dev-2026!"}


def test_T08_recepcao_nao_acessa_admin(client, auth):
    # teste-semente do Ex. 6, agora na suíte de segurança
    assert client.get("/admin/usuarios", headers=auth("recepcao")).status_code == 403


def test_T08_profissional_nao_acessa_admin(client, auth):
    assert client.get("/admin/usuarios", headers=auth("dr_diego")).status_code == 403


def test_T08_admin_sem_mfa_barrado(client):
    r = client.post("/auth/token", data={"username": "admin", "password": "admin-dev-2026!"})
    mfa_token = r.json()["mfa_token"]
    assert client.get("/admin/usuarios",
                      headers={"Authorization": f"Bearer {mfa_token}"}).status_code == 403


def test_T08_m2m_em_rota_humana(client):
    tok = client.post("/auth/client-token", data=CLIENT).json()["access_token"]
    assert client.get("/consultas", headers={"Authorization": f"Bearer {tok}"}).status_code == 403


def test_T08_login_html_nao_contorna_mfa(client):
    import os
    r = client.post("/recepcao/login", follow_redirects=False,
                    data={"username": "admin", "password": os.environ["SEED_SENHA_ADMIN"]})
    assert r.status_code == 403
    assert "access_token" not in r.cookies
