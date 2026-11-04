import json

import paramiko

from app.metrics import public_metrics
from app.ssh_metrics import COMMAND, SCRIPT, collect_remote


class FakeRunner:
    def __init__(self, payload=None, exc=None):
        self.payload = payload
        self.exc = exc
        self.calls = []

    def run(self, hostname, port, username, secret, timeout):
        self.calls.append(
            {
                "hostname": hostname,
                "port": port,
                "username": username,
                "secret": secret,
                "timeout": timeout,
            }
        )
        if self.exc:
            raise self.exc
        return self.payload


def _server():
    return {
        "hostname": "10.1.1.8",
        "ssh_port": 22,
        "ssh_user": "monitor",
        "ssh_secret": "not-a-real-secret",
        "name": "ignored-name",
    }


def _payload():
    return {
        "ok": True,
        "cpu_percent": 3,
        "memory_percent": 4,
        "memory_used_bytes": 5,
        "memory_total_bytes": 6,
        "network_in_bytes": 7,
        "network_out_bytes": 8,
        "listening_ports": [{"port": 22, "protocol": "tcp", "address": "0.0.0.0"}],
        "ssh_secret": "should-not-leak",
    }


def test_remote_success_uses_fixed_command_inputs():
    assert COMMAND == "python3 -"
    compile(SCRIPT, "<remote>", "exec")
    assert "10.1.1.8" not in SCRIPT
    assert "ignored-name" not in SCRIPT
    runner = FakeRunner(payload=json.dumps(_payload()))
    result = collect_remote(_server(), runner)
    assert result["ok"] is True
    assert result["cpu_percent"] == 3
    rendered = json.dumps(public_metrics(result))
    assert "should-not-leak" not in rendered
    assert "not-a-real-secret" not in rendered
    assert runner.calls[0]["hostname"] == "10.1.1.8"
    assert runner.calls[0]["timeout"] == 5


def test_remote_timeout():
    result = collect_remote(_server(), FakeRunner(exc=TimeoutError("timed out")))
    assert result == {"ok": False, "error": "Host unreachable"}


def test_remote_authentication_failure():
    error = paramiko.AuthenticationException("authentication failed")
    result = collect_remote(_server(), FakeRunner(exc=error))
    assert result == {"ok": False, "error": "Host unreachable"}
    assert "authentication failed" not in str(result)
