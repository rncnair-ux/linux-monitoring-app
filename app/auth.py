import os
import secrets

from werkzeug.security import check_password_hash

# Hash of the local demo password. The plain password is not stored.
DEMO_PASSWORD_HASH = (
    "scrypt:32768:8:1$tYX2bsa3fmaziFqY$f2e339f8e64700a3e1adb0a8aefc73df4a7f3dfd"
    "492e4bd2d45953c49ecfe167ab150c1fdc6510e39c4f444cb1aab0e93d9f540091d76a2ac"
    "6468f3b1269fb8c"
)
LOGIN_ERROR = "Invalid username or password"


def configured_username():
    return os.environ.get("ADMIN_USERNAME", "admin")


def configured_password_hash():
    return os.environ.get("ADMIN_PASSWORD_HASH", DEMO_PASSWORD_HASH)


def credentials_match(username, password):
    expected = configured_username()
    supplied = username or ""
    user_ok = len(supplied) == len(expected) and secrets.compare_digest(supplied, expected)
    try:
        password_ok = check_password_hash(configured_password_hash(), password or "")
    except (TypeError, ValueError):
        password_ok = False
    return user_ok and password_ok
