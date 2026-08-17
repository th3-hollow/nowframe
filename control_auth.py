import json
import os
import secrets
import tempfile

from pathlib import Path

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)


AUTH_FILE = Path(
    os.environ.get(
        "NOWFRAME_AUTH_FILE",
        "/etc/nowframe/auth.json",
    )
)

SESSION_KEY_FILE = Path(
    os.environ.get(
        "NOWFRAME_SESSION_KEY_FILE",
        "/var/lib/nowframe-control/session.key",
    )
)

PASSWORD_MIN_LENGTH = 10


def atomic_private_write(path, content):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )

    temporary = Path(temporary_name)

    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(temporary, 0o600)
        os.replace(temporary, path)

    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def load_auth():
    if not AUTH_FILE.exists():
        return {}

    try:
        data = json.loads(
            AUTH_FILE.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def auth_configured():
    return bool(
        load_auth().get("password_hash")
    )


def validate_password(password):
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            "Admin password must contain at least "
            f"{PASSWORD_MIN_LENGTH} characters."
        )

    if password.isspace():
        raise ValueError(
            "Admin password cannot contain only spaces."
        )


def set_password(password):
    validate_password(password)

    data = {
        "version": 1,
        "password_hash": generate_password_hash(
            password,
            method="scrypt:16384:8:1",
        ),
        "session_version": secrets.token_urlsafe(
            24
        ),
    }

    atomic_private_write(
        AUTH_FILE,
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        ) + "\n",
    )


def session_version():
    data = load_auth()

    return data.get(
        "session_version",
        data.get(
            "password_hash",
            "",
        ),
    )


def verify_password(password):
    password_hash = load_auth().get(
        "password_hash",
        "",
    )

    if not password_hash:
        return False

    try:
        return check_password_hash(
            password_hash,
            password,
        )
    except ValueError:
        return False


def session_key():
    try:
        existing = SESSION_KEY_FILE.read_text(
            encoding="utf-8",
        ).strip()
    except OSError:
        existing = ""

    if len(existing) >= 32:
        return existing

    key = secrets.token_urlsafe(48)

    atomic_private_write(
        SESSION_KEY_FILE,
        key + "\n",
    )

    return key
