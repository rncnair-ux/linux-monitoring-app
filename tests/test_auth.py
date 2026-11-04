from pathlib import Path

from app.auth import configured_password_hash, credentials_match
from tests.helpers import sign_in


def test_correct_password(client):
    response = sign_in(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_wrong_password(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "not-the-password"},
    )
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    follow = client.get("/")
    assert follow.status_code == 302
    assert follow.headers["Location"].endswith("/login")


def test_unknown_username_has_the_same_error(client):
    response = client.post(
        "/login",
        data={"username": "other", "password": "not-the-password"},
    )
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    assert b"does not exist" not in response.data


def test_sign_out(client):
    sign_in(client)
    response = client.post("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    page = client.get("/")
    assert page.status_code == 302
    assert page.headers["Location"].endswith("/login")


def test_password_is_stored_as_a_hash():
    stored = configured_password_hash()
    source = Path("app/auth.py").read_text(encoding="utf-8")
    assert stored != "admin123"
    assert stored.startswith("scrypt:")
    assert "admin123" not in source
    assert credentials_match("admin", "admin123")
    assert not credentials_match("admin", "not-the-password")
    assert not credentials_match("other", "admin123")


def test_metrics_require_sign_in(client):
    response = client.get("/servers/localhost/metrics")
    assert response.status_code == 401
    assert b"cpu_percent" not in response.data
