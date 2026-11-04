import logging
import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from app.auth import LOGIN_ERROR, configured_username, credentials_match
from app.collect import default_collector
from app.metrics import public_metrics
from app.store import add_server, find_server, load_servers, remove_server

REFRESH_MS = 8000


def create_app(data_dir=None):
    app = Flask(__name__)
    app.config["DEBUG"] = False
    app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "demo-local-session-secret")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    root = Path(__file__).resolve().parent.parent
    app.config["DATA_DIR"] = str(data_dir or (root / "data"))
    app.config["COLLECTOR"] = default_collector
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)

    @app.before_request
    def require_login():
        if request.endpoint in {"login", "login_post", "static"} or request.endpoint is None:
            return None
        if session.get("user") == configured_username():
            return None
        if request.endpoint == "server_metrics":
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for("login"))

    @app.get("/login")
    def login():
        if session.get("user") == configured_username():
            return redirect(url_for("dashboard"))
        return render_template("login.html", error=False)

    @app.post("/login")
    def login_post():
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if not credentials_match(username, password):
            return render_template("login.html", error=True), 401
        session.clear()
        session["user"] = configured_username()
        return redirect(url_for("dashboard"))

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    def dashboard():
        cards = []
        for server in load_servers(app.config["DATA_DIR"]):
            cards.append({"server": server, "metrics": _collect(app, server)})
        return render_template("dashboard.html", cards=cards)

    @app.get("/servers/add")
    def add_server_form():
        return render_template("add_server.html", errors=[], form=_blank_form())

    @app.post("/servers/add")
    def add_server_post():
        _server, errors = add_server(app.config["DATA_DIR"], request.form)
        if errors:
            return render_template(
                "add_server.html",
                errors=errors,
                form=_blank_secret(request.form),
            ), 400
        return redirect(url_for("dashboard"))

    @app.get("/servers/<server_id>")
    def server_detail(server_id):
        server = find_server(app.config["DATA_DIR"], server_id)
        if server is None:
            return render_template("detail.html", server=None, metrics=None), 404
        metrics = _collect(app, server)
        return render_template(
            "detail.html",
            server=server,
            metrics=metrics,
            refresh_ms=REFRESH_MS,
        )

    @app.get("/servers/<server_id>/metrics")
    def server_metrics(server_id):
        server = find_server(app.config["DATA_DIR"], server_id)
        if server is None:
            return jsonify({"error": "Host unreachable"}), 404
        payload = public_metrics(_collect(app, server))
        if payload is None:
            return jsonify({"error": "Host unreachable"})
        return jsonify(payload)

    @app.post("/servers/<server_id>/delete")
    def delete_server(server_id):
        remove_server(app.config["DATA_DIR"], server_id)
        return redirect(url_for("dashboard"))

    return app


def _collect(app, server):
    try:
        result = app.config["COLLECTOR"](server)
    except Exception:
        return {"ok": False, "error": "Host unreachable"}
    if not isinstance(result, dict) or not result.get("ok"):
        return {"ok": False, "error": "Host unreachable"}
    return result


def _blank_form():
    return {"name": "", "hostname": "", "ssh_user": "", "ssh_port": "22"}


def _blank_secret(form):
    return {
        "name": form.get("name", ""),
        "hostname": form.get("hostname", ""),
        "ssh_user": form.get("ssh_user", ""),
        "ssh_port": form.get("ssh_port", "22"),
    }
