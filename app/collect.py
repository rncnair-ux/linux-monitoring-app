from app.metrics import collect_local
from app.ssh_metrics import ParamikoSSHRunner, collect_remote

_runner = None


def default_collector(server):
    global _runner
    if server.get("local"):
        return collect_local()
    if _runner is None:
        _runner = ParamikoSSHRunner()
    return collect_remote(server, _runner)
