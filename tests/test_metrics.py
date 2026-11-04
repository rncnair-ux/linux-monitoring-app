import socket

from app.metrics import collect_local, public_metrics


class _Address:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port


class _Conn:
    def __init__(self, status, sock_type, address):
        self.status = status
        self.type = sock_type
        self.laddr = address


class _Memory:
    percent = 11.0
    used = 100
    total = 1000


class _Network:
    bytes_recv = 20
    bytes_sent = 30


class FakePsutil:
    CONN_LISTEN = "LISTEN"

    def cpu_percent(self, interval=None):
        return 12.5

    def virtual_memory(self):
        return _Memory()

    def net_io_counters(self):
        return _Network()

    def net_connections(self, kind="inet"):
        return [
            _Conn("LISTEN", socket.SOCK_STREAM, _Address("127.0.0.1", 22)),
            _Conn("ESTABLISHED", socket.SOCK_STREAM, _Address("10.0.0.1", 443)),
        ]


class FailingPsutil:
    def cpu_percent(self, interval=None):
        raise OSError("private-token")


class PortsDenied(FakePsutil):
    def net_connections(self, kind="inet"):
        raise PermissionError("denied")


def test_local_collector_reads_four_metrics():
    result = collect_local(FakePsutil())
    assert result["ok"] is True
    payload = public_metrics(result)
    assert payload["cpu_percent"] == 12.5
    assert payload["memory_percent"] == 11.0
    assert payload["memory_used_bytes"] == 100
    assert payload["memory_total_bytes"] == 1000
    assert payload["network_in_bytes"] == 20
    assert payload["network_out_bytes"] == 30
    assert payload["listening_ports"] == [
        {"port": 22, "protocol": "tcp", "address": "127.0.0.1"}
    ]
    assert set(payload) == {
        "cpu_percent",
        "memory_percent",
        "memory_used_bytes",
        "memory_total_bytes",
        "network_in_bytes",
        "network_out_bytes",
        "listening_ports",
    }


def test_failed_read_is_unreachable():
    result = collect_local(FailingPsutil())
    assert result == {"ok": False, "error": "Host unreachable"}
    assert "private-token" not in str(result)


def test_port_read_failure_keeps_other_metrics():
    result = collect_local(PortsDenied())
    assert result["ok"] is True
    assert result["listening_ports"] == []
