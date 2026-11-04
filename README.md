# Demo Monitoring

Local read-only view of Linux server CPU, memory, network, and listening ports.

## Run locally

1. Install Python 3 and create a virtual environment in the project directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies from `requirements.txt`.

```bash
pip install -r requirements.txt
```

3. Start the Flask app bound to `127.0.0.1`.

```bash
python run.py
```

4. Open http://127.0.0.1:5056 and sign in as `admin` / `admin123`.
5. Confirm localhost metrics refresh on their own.
6. Optionally add one remote Linux host with SSH credentials and confirm the same four metrics.

The app listens on `127.0.0.1` only. Debug mode is off. Port 5056 is used because 5000 is already taken on this machine.

## Sign-in

- `ADMIN_USERNAME` defaults to `admin`.
- `ADMIN_PASSWORD_HASH` defaults to a hash of the demo password. The plain password is not stored.
- `SESSION_SECRET` defaults to `demo-local-session-secret` for this local demo.
- A failed sign-in shows “Invalid username or password” either way.

## Pages

- `/login` — sign-in
- `/` — dashboard
- `/servers/<id>` — server detail
- `/servers/add` — add a server
- `/servers/<id>/metrics` — JSON used by the detail page

## Session

`SESSION_SECRET` signs the session cookie. The cookie is HttpOnly and SameSite=Lax. Unsigned visitors are sent to `/login`.

## Servers file

`data/servers.json` is created on first run with one entry, “This machine” at `127.0.0.1`, and no SSH fields. The `data/` directory is gitignored. File mode is `0600`.

## Metrics

- CPU: percent
- Memory: percent, plus used and total bytes
- Network: bytes in and bytes out
- Listening ports: port, protocol, and address

Local metrics are read in-process. Remote metrics are optional: the app connects with SSH and runs a fixed command. The display name and hostname are not inserted into that command, and nothing is installed on the remote host. The first connection accepts the SSH host key.

The detail page requests `/servers/<id>/metrics` every 8 seconds. That response contains only the four metrics. A failed read shows “Host unreachable” and the page still renders.

## Add a server

- Display name
- Hostname or IP
- SSH user
- SSH port, default 22, from 1 to 65535
- SSH password or private key path

The secret is written only to `data/servers.json` and is not shown in the page. The list holds at most 5 servers. Localhost cannot be removed. Removing another server deletes the list entry and does not change the remote machine.

## Tests

```bash
pytest
```

`tests/test_auth.py` covers sign-in and sign-out. `tests/test_metrics.py` covers the local collector, including a failed read. `tests/test_ssh.py` covers remote success, timeout, and authentication failure with a fake SSH client.

## CI

GitHub Actions runs `pytest` on push and pull request. The workflow has no secrets and does not deploy. CI does not open an SSH connection. Run the app on this machine.
