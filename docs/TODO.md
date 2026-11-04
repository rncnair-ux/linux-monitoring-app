# Implementation TODO

Local demo only. Work one checkbox at a time. Leave the app runnable on `127.0.0.1` before starting the next item.

Reference: [requirements.md](requirements.md).

## 1. Project initialization and basic UI

- [x] Create a Python 3 Flask app with `requirements.txt`, a package layout, and a dark placeholder page (app title and empty server area).
  - [x] Security: bind to `127.0.0.1` only, keep Flask debug off by default, and add a `.gitignore` for `.venv/`, `__pycache__/`, `.env`, and local server data.
  - [x] Docs: add a short `README.md` with the venv, install, and run commands, plus the URL to open.

## 2. Sign-in functionality and unit tests

- [x] Add a sign-in page for `admin`, check the password against a hash from the environment, and add sign-out. Wrong credentials show one generic error.
  - [x] Security: store only the password hash, use an HttpOnly session cookie, and do not log the password or whether the username exists.
  - [x] Docs: document `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and the demo login `admin` / `admin123` in the README.
- [x] Add unit tests for a correct password, a wrong password, and sign-out.
  - [x] Security: tests must not print the password or the hash.
  - [x] Docs: note the `pytest` command in the README.

## 3. GitHub Actions CI

- [x] Add `.github/workflows/ci.yml` that installs dependencies and runs `pytest` on push and pull request.
  - [x] Security: do not put secrets in the workflow; the job only runs tests and does not deploy.
  - [x] Docs: add a CI section to the README stating that deployment stays local.

## 4. Protect pages

- [x] Send unauthenticated visitors to the sign-in page. After sign-in, show the placeholder dashboard.
  - [x] Security: set a secret session key from the environment and reject requests that are not signed in.
  - [x] Docs: list the pages (sign-in, dashboard) and the session setting in the README.

## 5. Localhost record

- [x] On first run, create a local server list that contains only this machine. No SSH fields.
  - [x] Security: write the list inside the project data directory, and keep that directory out of git.
  - [x] Docs: describe the file location and the default localhost entry.

## 6. Local metrics

- [x] Read CPU percent, memory percent (used and total), network bytes in and out, and listening ports for localhost.
  - [x] Security: read local metrics in-process only. Do not shell out to user-controlled commands.
  - [x] Docs: list the four metrics and their units in the README.
- [x] Unit-test the collector with fake inputs, including a failed read.
  - [x] Security: fixtures must not include real host secrets.
  - [x] Docs: mention the collector test module in the README test section.

## 7. Dashboard for localhost

- [x] Show the localhost metrics on a read-only detail view. If a read fails, show “Host unreachable” and still render the page.
  - [x] Security: escape all rendered values. Do not add buttons that change the host.
  - [x] Docs: describe what the dashboard shows for the default host.

## 8. Auto-refresh

- [x] Add a small JSON endpoint and refresh the numbers every 5–10 seconds without a full page reload.
  - [x] Security: require a signed-in session for the JSON endpoint, and return only the four metrics.
  - [x] Docs: record the refresh interval and the endpoint path.

## 9. Add and remove a server

- [x] Add a form for display name, hostname or IP, SSH user, port (default 22), and a password or private-key path. Allow remove. Stop at 5 hosts. Localhost cannot be removed.
  - [x] Security: do not render secrets in HTML, reject a 6th host, and validate the port as a number from 1 to 65535.
  - [x] Docs: document each form field and the five-host limit.

## 10. Remote metrics over SSH

- [x] For a non-local host, connect with SSH and read the same four metrics. Use a fixed set of commands and a short timeout.
  - [x] Security: do not build shell commands from the display name or hostname. Do not log the SSH password or key. On failure, show “Host unreachable” only.
  - [x] Docs: state that remote collection is optional and that nothing is installed on the remote host.
- [x] Unit-test success, timeout, and authentication failure with a fake SSH client.
  - [x] Security: fake credentials only. No live SSH connection in CI.
  - [x] Docs: note that CI does not reach any remote host.

## 11. Demo check

- [x] Walk through the acceptance criteria in `docs/requirements.md` on this machine and fix any gap that breaks a local run.
  - [x] Security: confirm the app listens on `127.0.0.1` only, the password is hashed, and secrets stay out of git.
  - [x] Docs: keep the README setup to the six local steps in the PRD.
