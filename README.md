# Demo Monitoring

Local read-only view of Linux server health. This step serves a placeholder page only.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5056

The app listens on `127.0.0.1` only. Debug mode is off. Port 5056 is used because 5000 is already taken on this machine.
