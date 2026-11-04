import json
import os
import uuid
from pathlib import Path

MAX_SERVERS = 5


def server_file(data_dir):
    return Path(data_dir) / "servers.json"


def default_localhost():
    return {
        "id": "localhost",
        "name": "This machine",
        "hostname": "127.0.0.1",
        "local": True,
    }


def load_servers(data_dir):
    path = server_file(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    if not path.exists():
        servers = [default_localhost()]
        save_servers(data_dir, servers)
        return servers
    servers = json.loads(path.read_text(encoding="utf-8"))
    if not any(server.get("local") for server in servers):
        servers.insert(0, default_localhost())
        save_servers(data_dir, servers)
    return servers


def save_servers(data_dir, servers):
    path = server_file(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(servers, indent=2), encoding="utf-8")
    os.chmod(path.parent, 0o700)
    os.chmod(path, 0o600)


def find_server(data_dir, server_id):
    for server in load_servers(data_dir):
        if server["id"] == server_id:
            return server
    return None


def parse_port(value):
    text = "22" if value is None or str(value).strip() == "" else str(value).strip()
    if not text.isdigit():
        return None
    port = int(text)
    if port < 1 or port > 65535:
        return None
    return port


def _clean(value, limit):
    text = (value or "").strip()
    if not text or len(text) > limit or any(char in text for char in "\r\n\t"):
        return None
    return text


def validate_new_server(form, current_count):
    if current_count >= MAX_SERVERS:
        return None, ["The demo holds up to 5 servers."]
    name = _clean(form.get("name"), 80)
    hostname = _clean(form.get("hostname"), 255)
    ssh_user = _clean(form.get("ssh_user"), 64)
    if hostname and any(char.isspace() for char in hostname):
        hostname = None
    if ssh_user and any(char.isspace() for char in ssh_user):
        ssh_user = None
    port = parse_port(form.get("ssh_port"))
    secret = form.get("ssh_secret") or ""
    errors = []
    if name is None:
        errors.append("Enter a display name.")
    if hostname is None:
        errors.append("Enter a hostname or IP address.")
    if ssh_user is None:
        errors.append("Enter an SSH user.")
    if port is None:
        errors.append("Enter a port from 1 to 65535.")
    if not secret.strip():
        errors.append("Enter an SSH password or private key path.")
    if errors:
        return None, errors
    return {
        "id": uuid.uuid4().hex,
        "name": name,
        "hostname": hostname,
        "local": False,
        "ssh_user": ssh_user,
        "ssh_port": port,
        "ssh_secret": secret,
    }, []


def add_server(data_dir, form):
    servers = load_servers(data_dir)
    server, errors = validate_new_server(form, len(servers))
    if errors:
        return None, errors
    servers.append(server)
    save_servers(data_dir, servers)
    return server, []


def remove_server(data_dir, server_id):
    servers = load_servers(data_dir)
    target = next((server for server in servers if server["id"] == server_id), None)
    if target is None or target.get("local"):
        return False
    save_servers(data_dir, [server for server in servers if server["id"] != server_id])
    return True
