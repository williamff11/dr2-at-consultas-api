"""Ameaças: T10 (CORS/DoS) e T12 (headers) · docs/04_threat_model.md."""
def test_T12_headers_presentes(client):
    r = client.get("/health")
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["strict-transport-security"].startswith("max-age=")


def test_T10_cors_origem_maliciosa(client):
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"
