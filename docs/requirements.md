# Demo Monitoring Infrastructure — Requirements

Local demo for watching Linux server health without signing in to each machine.

## 1. Problem

L1, L2, and L3 teams currently SSH into servers to check live memory, CPU, network, and port usage. That is slow when several hosts need a quick look.

## 2. Users

Internal infrastructure and application teams (L1, L2, L3). Everyone uses the same read-only dashboard. There is one sign-in account.

## 3. Goal

In about five minutes, a reviewer on this machine can sign in and see live CPU, memory, network I/O, and listening ports for the local host, without opening an SSH session themselves.

Remote Linux hosts are optional. The app can collect their metrics over SSH after they are added.

## 4. Out of scope

- Alerts and thresholds
- Metric history and graphs over time
- Agents installed on target hosts
- Role-based access, extra users, or multi-tenancy
- High availability, clustering, or production hardening
- Changing anything on a monitored host (no process kills, no config edits, no package installs)

## 5. Product decisions

| Topic | Decision |
| --- | --- |
| Demo success | Live CPU, memory, network, and listening ports |
| Auth | Single user `admin`; password stored as a hash |
| Default credentials | `admin` / `admin123` (demo only) |
| Collection | Local host read directly; remote hosts via SSH |
| Rollout | Localhost works first; remote hosts are optional |
| Metrics | CPU %, memory %, network I/O, listening ports |
| Refresh | Automatic every 5–10 seconds |
| UI | Flask + Jinja, dark ops-style dashboard |
| Capacity | 1–5 hosts |
| Runtime | Linux, on the same machine where Cursor is running |

## 6. Functional requirements

### 6.1 Sign-in

- Unauthenticated visitors see a sign-in page only.
- Username is `admin`.
- The password is checked against a hash, not stored in plain text.
- Demo hash and username come from environment or a local config file.
- Default demo password is `admin123`.
- Sign-out returns the user to the sign-in page.
- Failed sign-in shows a short error and does not reveal whether the username exists.

### 6.2 Read-only dashboard

- After sign-in, the home view lists monitored servers and their current status.
- Selecting a server shows:
  - CPU usage (percent)
  - Memory usage (percent, plus used / total when available)
  - Network I/O (bytes or a simple rate in and out)
  - Listening ports (port, protocol, and address when available)
- Values refresh on their own every 5–10 seconds.
- The UI does not offer controls that change the monitored host.
- If a host cannot be reached, the card shows an error state and the rest of the dashboard still loads.

### 6.3 Add a server

- A signed-in user can register a Linux server to monitor.
- Required fields: display name, hostname or IP.
- Localhost is present by default and needs no SSH settings.
- For a remote host, also collect SSH user, port (default 22), and an authentication secret (password or private key path). Store the secret for the demo only, outside the page HTML.
- The server list is capped at 5 hosts.
- Adding a host does not install software on that host. The app connects with SSH and reads metrics.
- Removing a host from the list is allowed so a wrong entry can be cleared. This does not change the remote machine.

### 6.4 Localhost

- On first run, the machine running the app is monitored without SSH.
- This path is enough to demonstrate the product when no remote server is available.

## 7. User experience

- Dark, simple operations layout: high contrast, large numbers, short labels.
- Readable on a laptop browser. No separate mobile layout.
- Empty and error states use plain language (for example, “Host unreachable”).
- Pages: sign-in, server list, server detail, add server.

## 8. Tech stack

- Python 3
- Flask
- Jinja templates, CSS, and a small amount of JavaScript for refresh
- Local metric reads via the standard library or `psutil`
- Remote reads via SSH (Paramiko or OpenSSH)
- Password hashing via a standard library (for example Werkzeug or `hashlib` with a salt)
- Server list stored in a local JSON file or SQLite database in the project directory
- No frontend framework and no external hosted service

## 9. Configuration

Environment variables or a single local config file:

- `ADMIN_USERNAME` (default `admin`)
- `ADMIN_PASSWORD_HASH` (hash of `admin123` for the demo)
- Bind address `127.0.0.1` and a fixed port (for example `5000`)

Do not commit real SSH keys or production passwords. Demo defaults are acceptable in this repository because the app is local-only.

## 10. Local setup

Run these on the Linux machine where Cursor is open:

1. Install Python 3 and create a virtual environment in the project directory.
2. Install dependencies from `requirements.txt`.
3. Start the Flask app bound to `127.0.0.1`.
4. Open `http://127.0.0.1:5000` and sign in as `admin` / `admin123`.
5. Confirm localhost metrics refresh on their own.
6. Optionally add one remote Linux host with SSH credentials and confirm the same four metrics.

## 11. Acceptance criteria

- Sign-in rejects a wrong password and accepts `admin` / `admin123`.
- The password is not stored in plain text.
- Without any remote host, localhost shows CPU, memory, network, and listening ports.
- Those values change on the page within 10 seconds without a manual reload.
- A second Linux host can be added and shows the same metrics, or a clear unreachable error.
- The UI exposes no action that modifies a monitored host.
- The app serves only on localhost and stays within five registered hosts.
