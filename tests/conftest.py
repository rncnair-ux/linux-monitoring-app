import pytest

from app import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    application = create_app(data_dir=tmp_path)
    application.config["TESTING"] = True
    application.config["COLLECTOR"] = lambda server: {
        "ok": True,
        "cpu_percent": 1.5,
        "memory_percent": 40.0,
        "memory_used_bytes": 400,
        "memory_total_bytes": 1000,
        "network_in_bytes": 50,
        "network_out_bytes": 25,
        "listening_ports": [
            {"port": 22, "protocol": "tcp", "address": "127.0.0.1"}
        ],
    }
    return application


@pytest.fixture
def client(app):
    return app.test_client()
