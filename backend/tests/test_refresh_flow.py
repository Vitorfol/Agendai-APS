import os
import requests
import pytest

BASE = os.getenv("API_BASE", "http://localhost:8000")
LOGIN_URL = f"{BASE}/api/auth/login"
REFRESH_URL = f"{BASE}/api/auth/refresh"
ME_URL = f"{BASE}/api/users/me"


def do_login(email: str, password: str):
    r = requests.post(LOGIN_URL, json={"email": email, "password": password}, timeout=5)
    return r


def test_refresh_flow_basic():
    resp = do_login("contato@uece.br", "dedelbrabo")
    assert resp.status_code == 200, f"login failed: {resp.status_code} {resp.text}"
    data = resp.json()

    assert "access_token" in data and data["access_token"], "access_token missing"
    assert "refresh_token" in data and data["refresh_token"], "refresh_token missing"

    access = data["access_token"]
    refresh = data["refresh_token"]

    assert len(access) > 10
    assert len(refresh) > 10

    r2 = requests.post(REFRESH_URL, headers={"Authorization": f"Bearer {refresh}"}, timeout=5)
    assert r2.status_code == 200, f"refresh failed: {r2.status_code} {r2.text}"
    d2 = r2.json()

    assert "access_token" in d2 and d2["access_token"]
    assert "refresh_token" in d2 and d2["refresh_token"]

    new_access = d2["access_token"]
    new_refresh = d2["refresh_token"]

    assert len(new_access) > 10
    assert len(new_refresh) > 10

    r_me = requests.get(ME_URL, headers={"Authorization": f"Bearer {new_access}"}, timeout=5)
    assert r_me.status_code == 200, f"users/me with new access failed: {r_me.status_code} {r_me.text}"

    r_bad = requests.post(REFRESH_URL, headers={"Authorization": f"Bearer {access}"}, timeout=5)
    assert r_bad.status_code == 401, f"using access token for refresh should be 401, got {r_bad.status_code}"
