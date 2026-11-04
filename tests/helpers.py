def sign_in(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
    )
