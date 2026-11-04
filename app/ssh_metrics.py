import json
import os

from app.metrics import unreachable

# Fixed remote command. Display names and hostnames are never inserted here.
COMMAND = "python3 -"
SCRIPT = r"""
import json, time

def cpu_percent():
    def snap():
        parts = open("/proc/stat").readline().split()
        nums = [int(value) for value in parts[1:8]]
        idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
        return idle, sum(nums)
    idle1, total1 = snap()
    time.sleep(0.2)
    idle2, total2 = snap()
    delta = total2 - total1
    if delta <= 0:
        return 0.0
    return round((1 - (idle2 - idle1) / delta) * 100, 1)

def memory():
    info = {}
    for line in open("/proc/meminfo"):
        key, value = line.split(":", 1)
        info[key] = int(value.strip().split()[0]) * 1024
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", info.get("MemFree", 0))
    used = max(total - available, 0)
    percent = 0.0 if total == 0 else round(used / total * 100, 1)
    return percent, used, total

def network():
    received = 0
    sent = 0
    for line in open("/proc/net/dev"):
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        if name.strip() == "lo":
            continue
        parts = rest.split()
        received += int(parts[0])
        sent += int(parts[8])
    return received, sent

def ipv4(hex_ip):
    raw = bytes.fromhex(hex_ip)
    return ".".join(str(number) for number in raw[::-1])

def ipv6(hex_ip):
    raw = bytes.fromhex(hex_ip)
    groups = [raw[index:index + 4][::-1] for index in range(0, 16, 4)]
    text = b"".join(groups)
    return ":".join(text[index:index + 2].hex() for index in range(0, 16, 2))

def listening_ports():
    ports = []
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            lines = open(path).read().splitlines()[1:]
        except FileNotFoundError:
            continue
        for line in lines:
            parts = line.split()
            if len(parts) < 4 or parts[3] != "0A":
                continue
            address, port_hex = parts[1].split(":")
            ip = ipv4(address) if len(address) == 8 else ipv6(address)
            ports.append({"port": int(port_hex, 16), "protocol": "tcp", "address": ip})
    return ports

mem_percent, mem_used, mem_total = memory()
net_in, net_out = network()
print(json.dumps({
    "ok": True,
    "cpu_percent": cpu_percent(),
    "memory_percent": mem_percent,
    "memory_used_bytes": mem_used,
    "memory_total_bytes": mem_total,
    "network_in_bytes": net_in,
    "network_out_bytes": net_out,
    "listening_ports": listening_ports(),
}))
"""


class ParamikoSSHRunner:
    def run(self, hostname, port, username, secret, timeout):
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        options = {
            "hostname": hostname,
            "port": int(port),
            "username": username,
            "timeout": timeout,
            "banner_timeout": timeout,
            "auth_timeout": timeout,
            "look_for_keys": False,
            "allow_agent": False,
        }
        if secret and os.path.isfile(secret):
            options["key_filename"] = secret
        else:
            options["password"] = secret
        try:
            client.connect(**options)
            stdin, stdout, _stderr = client.exec_command(COMMAND, timeout=timeout)
            stdin.write(SCRIPT)
            stdin.channel.shutdown_write()
            stdout.channel.settimeout(timeout)
            return stdout.read().decode("utf-8", "replace")
        finally:
            client.close()


def parse_metrics(raw):
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return unreachable()
    if not isinstance(payload, dict) or not payload.get("ok"):
        return unreachable()
    required = (
        "cpu_percent",
        "memory_percent",
        "memory_used_bytes",
        "memory_total_bytes",
        "network_in_bytes",
        "network_out_bytes",
        "listening_ports",
    )
    if any(key not in payload for key in required):
        return unreachable()
    if not isinstance(payload["listening_ports"], list):
        return unreachable()
    return {
        "ok": True,
        "cpu_percent": payload["cpu_percent"],
        "memory_percent": payload["memory_percent"],
        "memory_used_bytes": payload["memory_used_bytes"],
        "memory_total_bytes": payload["memory_total_bytes"],
        "network_in_bytes": payload["network_in_bytes"],
        "network_out_bytes": payload["network_out_bytes"],
        "listening_ports": payload["listening_ports"],
    }


def collect_remote(server, runner, timeout=5):
    try:
        raw = runner.run(
            hostname=server.get("hostname"),
            port=server.get("ssh_port") or 22,
            username=server.get("ssh_user"),
            secret=server.get("ssh_secret"),
            timeout=timeout,
        )
    except Exception:
        return unreachable()
    return parse_metrics(raw)
