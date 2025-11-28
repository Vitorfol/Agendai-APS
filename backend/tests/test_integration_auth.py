import os
import requests
import pytest

BASE = os.getenv("API_BASE", "http://localhost:8000")
LOGIN_URL = f"{BASE}/api/auth/login"
ME_URL = f"{BASE}/api/users/me"


def get_tokens(email: str, password: str):
    r = requests.post(LOGIN_URL, json={"email": email, "password": password}, timeout=5)
    return r


def test_login_success_and_users_me():
    # Use credentials that exist in the dev DB
    resp = get_tokens("contato@uece.br", "dedelbrabo")
    assert resp.status_code == 200, f"login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "access_token" in data and data["access_token"], "access_token missing"
    access = data["access_token"]

    # call /users/me with access token
    r = requests.get(ME_URL, headers={"Authorization": f"Bearer {access}"}, timeout=5)
    assert r.status_code == 200, f"users/me failed: {r.status_code} {r.text}"
    j = r.json()
    # Ensure password is NOT present in the returned JSON
    assert "senha" not in j and "password" not in j
    # Basic shape checks
    assert "email" in j
    assert "nome" in j


def test_login_wrong_password():
    r = get_tokens("contato@uece.br", "senha_errada")
    assert r.status_code == 401
    # WWW-Authenticate header should be present
    assert "www-authenticate" in r.headers or "WWW-Authenticate" in r.headers


def test_refresh_token_not_allowed_for_me():
    resp = get_tokens("contato@uece.br", "dedelbrabo")
    assert resp.status_code == 200
    data = resp.json()
    refresh = data.get("refresh_token")
    assert refresh, "refresh_token missing"

    r = requests.get(ME_URL, headers={"Authorization": f"Bearer {refresh}"}, timeout=5)
    assert r.status_code == 401
