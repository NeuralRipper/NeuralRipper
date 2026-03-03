"""
Integration tests: hit the real backend running in container.
PS: More tests to be implemented.

Run:  
    docker compose up -d && uv run pytest tests/ -v
"""

import httpx

BASE = "http://localhost:8000"


def test_health():
    res = httpx.get(f"{BASE}/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_list_models():
    res = httpx.get(f"{BASE}/models/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_model_not_found():
    res = httpx.get(f"{BASE}/models/9999")
    assert res.status_code == 404


def test_list_sessions():
    res = httpx.get(f"{BASE}/inference/sessions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_session_not_found():
    res = httpx.get(f"{BASE}/inference/sessions/9999")
    assert res.status_code == 404


def test_inference_requires_auth():
    res = httpx.post(f"{BASE}/inference/", json={"prompt": "test", "model_ids": [1]})
    assert res.status_code in (401, 403)


def test_auth_me_requires_token():
    res = httpx.get(f"{BASE}/auth/me")
    assert res.status_code in (401, 403)
