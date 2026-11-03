from app import create_app

app = create_app()

if __name__ == "__main__":
    # 127.0.0.1 only. Port 5000 is already taken on this machine.
    app.run(host="127.0.0.1", port=5056, debug=False)
