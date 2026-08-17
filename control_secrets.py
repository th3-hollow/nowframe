import os
import re
import shlex
import subprocess
import tempfile

from pathlib import Path
from urllib.parse import urlparse


SPOTIFY_ENV_FILE = Path(
    os.environ.get(
        "NOWFRAME_SPOTIFY_ENV_FILE",
        "/etc/nowframe/spotify.env",
    )
)

SPOTIFY_PENDING_FILE = Path(
    os.environ.get(
        "NOWFRAME_SPOTIFY_PENDING_FILE",
        "/etc/nowframe/.spotify.env.pending",
    )
)

CONFIGURE_COMMAND = shlex.split(
    os.environ.get(
        "NOWFRAME_CONFIGURE_SPOTIFY_COMMAND",
        "",
    )
)

CREDENTIAL_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{10,256}$"
)


def parse_environment_file(path):
    values = {}

    try:
        lines = path.read_text(
            encoding="utf-8",
        ).splitlines()
    except OSError:
        return values

    for line in lines:
        line = line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        name, value = line.split("=", 1)

        values[name.strip()] = (
            value.strip().strip("'\"")
        )

    return values


def spotify_status():
    values = parse_environment_file(
        SPOTIFY_ENV_FILE
    )

    client_id = values.get(
        "SPOTIPY_CLIENT_ID",
        "",
    )

    client_secret = values.get(
        "SPOTIPY_CLIENT_SECRET",
        "",
    )

    redirect_uri = values.get(
        "SPOTIPY_REDIRECT_URI",
        "",
    )

    return {
        "configured": bool(
            client_id
            and client_secret
            and redirect_uri
        ),
        "client_id_hint": (
            f"{client_id[:4]}…{client_id[-4:]}"
            if len(client_id) >= 10
            else ""
        ),
        "secret_configured": bool(
            client_secret
        ),
        "redirect_uri": redirect_uri,
    }


def validate_credential(
    value,
    label,
):
    value = value.strip()

    if not CREDENTIAL_PATTERN.fullmatch(value):
        raise ValueError(
            f"{label} must contain 10–256 letters, "
            "numbers, dots, underscores, or hyphens."
        )

    return value


def validate_redirect_uri(value):
    value = value.strip()

    if len(value) > 500:
        raise ValueError(
            "Spotify redirect URI is too long."
        )

    parsed = urlparse(value)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            "Spotify redirect URI must begin "
            "with http:// or https://."
        )

    if not parsed.hostname:
        raise ValueError(
            "Spotify redirect URI must include "
            "a hostname."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "Spotify redirect URI cannot include "
            "a username or password."
        )

    if "\n" in value or "\r" in value:
        raise ValueError(
            "Spotify redirect URI is invalid."
        )

    return value


def pending_content(
    client_id,
    client_secret,
    redirect_uri,
):
    values = {
        "SPOTIPY_CLIENT_ID": client_id,
        "SPOTIPY_CLIENT_SECRET": client_secret,
        "SPOTIPY_REDIRECT_URI": redirect_uri,
    }

    return "".join(
        f"{name}={shlex.quote(value)}\n"
        for name, value in values.items()
    )


def write_pending(content):
    SPOTIFY_PENDING_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".spotify.env.",
        dir=SPOTIFY_PENDING_FILE.parent,
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

        os.replace(
            temporary,
            SPOTIFY_PENDING_FILE,
        )

    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def configure_spotify(
    client_id,
    client_secret,
    redirect_uri,
):
    existing = parse_environment_file(
        SPOTIFY_ENV_FILE
    )

    client_id = (
        client_id.strip()
        or existing.get(
            "SPOTIPY_CLIENT_ID",
            "",
        )
    )

    client_secret = (
        client_secret.strip()
        or existing.get(
            "SPOTIPY_CLIENT_SECRET",
            "",
        )
    )

    client_id = validate_credential(
        client_id,
        "Spotify Client ID",
    )

    client_secret = validate_credential(
        client_secret,
        "Spotify Client Secret",
    )

    redirect_uri = validate_redirect_uri(
        redirect_uri
    )

    parsed_redirect = urlparse(
        redirect_uri
    )

    if (
        parsed_redirect.query
        or parsed_redirect.fragment
    ):
        raise ValueError(
            "Spotify redirect URI cannot include "
            "a query string or fragment."
        )

    write_pending(
        pending_content(
            client_id,
            client_secret,
            redirect_uri,
        )
    )

    try:
        if not CONFIGURE_COMMAND:
            raise RuntimeError(
                "Spotify credential helper "
                "is not configured."
            )

        result = subprocess.run(
            CONFIGURE_COMMAND,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Credential helper failed."
            )

            raise RuntimeError(message)

    finally:
        SPOTIFY_PENDING_FILE.unlink(
            missing_ok=True
        )
