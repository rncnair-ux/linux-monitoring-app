import socket

METRIC_KEYS = (
    "cpu_percent",
    "memory_percent",
    "memory_used_bytes",
    "memory_total_bytes",
    "network_in_bytes",
    "network_out_bytes",
    "listening_ports",
)
UNREACHABLE = {"ok": False, "error": "Host unreachable"}


def unreachable():
    return dict(UNREACHABLE)


def public_metrics(result):
    if not result or not result.get("ok"):
        return None
    ports = []
    for item in result.get("listening_ports") or []:
        if not isinstance(item, dict):
            continue
        ports.append(
            {
                "port": item.get("port"),
                "protocol": item.get("protocol"),
                "address": item.get("address"),
            }
        )
    return {
        "cpu_percent": result.get("cpu_percent"),
        "memory_percent": result.get("memory_percent"),
        "memory_used_bytes": result.get("memory_used_bytes"),
        "memory_total_bytes": result.get("memory_total_bytes"),
        "network_in_bytes": result.get("network_in_bytes"),
        "network_out_bytes": result.get("network_out_bytes"),
        "listening_ports": ports,
    }


def collect_local(psutil_module=None):
    ps = psutil_module
    if ps is None:
        import psutil

        ps = psutil
    try:
        cpu = ps.cpu_percent(interval=0.2)
        memory = ps.virtual_memory()
        network = ps.net_io_counters()
        if network is None:
            raise OSError("network counters unavailable")
        ports = _listening_ports(ps)
    except Exception:
        return unreachable()
    return {
        "ok": True,
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_used_bytes": memory.used,
        "memory_total_bytes": memory.total,
        "network_in_bytes": network.bytes_recv,
        "network_out_bytes": network.bytes_sent,
        "listening_ports": ports,
    }


def _listening_ports(ps):
    try:
        connections = ps.net_connections(kind="inet")
    except Exception:
        return []
    ports = []
    for conn in connections:
        if getattr(conn, "status", None) != ps.CONN_LISTEN:
            continue
        address = getattr(conn, "laddr", None)
        if not address:
            continue
        protocol = "tcp" if conn.type == socket.SOCK_STREAM else "udp"
        ports.append(
            {"port": address.port, "protocol": protocol, "address": address.ip}
        )
    ports.sort(key=lambda item: (item["port"], item["protocol"], item["address"]))
    return ports
