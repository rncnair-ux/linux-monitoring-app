from pathlib import Path

from app.store import load_servers
from tests.helpers import sign_in


def _remote(name, hostname):
    return {
        "name": name,
        "hostname": hostname,
        "ssh_user": "monitor",
        "ssh_port": "22",
        "ssh_secret": "stored-only-on-disk",
    }


def test_localhost_is_created_without_ssh_fields(app):
    servers = load_servers(app.config["DATA_DIR"])
    assert servers == [
        {
            "id": "localhost",
            "name": "This machine",
            "hostname": "127.0.0.1",
            "local": True,
        }
    ]
    mode = Path(app.config["DATA_DIR"], "servers.json").stat().st_mode & 0o777
    assert mode == 0o600


def test_dashboard_and_refresh_after_sign_in(client):
    sign_in(client)
    page = client.get("/")
    assert page.status_code == 200
    assert b"This machine" in page.data
    assert b"stored-only-on-disk" not in page.data
    detail = client.get("/servers/localhost")
    assert b"CPU" in detail.data
    assert b"Memory" in detail.data
    assert b"Network in" in detail.data
    assert b"Listening ports" in detail.data
    assert b'data-interval="8000"' in detail.data
    metrics = client.get("/servers/localhost/metrics")
    payload = metrics.get_json()
    assert set(payload) == {
        "cpu_percent",
        "memory_percent",
        "memory_used_bytes",
        "memory_total_bytes",
        "network_in_bytes",
        "network_out_bytes",
        "listening_ports",
    }


def test_unreachable_host_still_renders(app, client):
    app.config["COLLECTOR"] = lambda server: {"ok": False, "error": "boom"}
    sign_in(client)
    page = client.get("/")
    assert page.status_code == 200
    assert b"Host unreachable" in page.data
    assert b"This machine" in page.data
    detail = client.get("/servers/localhost")
    assert detail.status_code == 200
    assert b"Host unreachable" in detail.data


def test_add_rejects_bad_port_and_hides_secret(client):
    sign_in(client)
    response = client.post(
        "/servers/add",
        data=_remote("Bad", "10.2.2.2") | {"ssh_port": "70000"},
    )
    assert response.status_code == 400
    assert b"Enter a port from 1 to 65535." in response.data
    assert b"stored-only-on-disk" not in response.data


def test_server_cap_and_remove(client, app):
    sign_in(client)
    for index in range(4):
        response = client.post(
            "/servers/add",
            data=_remote(f"Host {index}", f"10.9.0.{index}"),
        )
        assert response.status_code == 302
    overflow = client.post("/servers/add", data=_remote("Host 4", "10.9.0.9"))
    assert overflow.status_code == 400
    assert b"The demo holds up to 5 servers." in overflow.data
    assert b"stored-only-on-disk" not in overflow.data
    servers = load_servers(app.config["DATA_DIR"])
    assert len(servers) == 5
    removed = client.post(f"/servers/{servers[1]['id']}/delete")
    assert removed.status_code == 302
    client.post("/servers/localhost/delete")
    remaining = load_servers(app.config["DATA_DIR"])
    assert any(server["id"] == "localhost" for server in remaining)
    assert len(remaining) == 4
    page = client.get("/")
    assert b"stored-only-on-disk" not in page.data


def test_app_binds_localhost_with_debug_off():
    text = Path("run.py").read_text(encoding="utf-8")
    assert 'host="127.0.0.1"' in text
    assert "debug=False" in text
