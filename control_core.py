import csv
import json
import os
import shlex
import subprocess
import tempfile
import time

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

import spotipy

from spotipy.oauth2 import SpotifyOAuth


CONTROL_FILE = Path(
    os.environ.get(
        "NOWFRAME_CONTROL_FILE",
        "/etc/nowframe/control.env",
    )
)

DEVICE_HISTORY_FILE = Path(
    os.environ.get(
        "NOWFRAME_DEVICE_HISTORY_FILE",
        "/etc/nowframe/devices.json",
    )
)

USAGE_FILE = Path(
    os.path.expanduser(
        os.environ.get(
            "NOWFRAME_USAGE_FILE",
            "~/.local/state/nowframe/spotify_api_usage.csv",
        )
    )
)

RESTART_ENABLED = (
    os.environ.get(
        "NOWFRAME_CONTROL_RESTART",
        "1",
    ).strip().lower()
    in ("1", "true", "yes", "on")
)

NOWFRAME_APP_DIR = Path(
    os.environ.get(
        "NOWFRAME_APP_DIR",
        Path(__file__).resolve().parent,
    )
)

NOWFRAME_PYTHON = os.environ.get(
    "NOWFRAME_PYTHON",
    "/root/spotify-display/spotify-env/bin/python",
)

NOWFRAME_SERVICE = os.environ.get(
    "NOWFRAME_SERVICE",
    "nowframe.service",
)

VALIDATE_COMMAND = shlex.split(
    os.environ.get(
        "NOWFRAME_VALIDATE_COMMAND",
        "",
    )
)

RESTART_COMMAND = shlex.split(
    os.environ.get(
        "NOWFRAME_RESTART_COMMAND",
        "",
    )
)

POLLING_PROFILES = {
    "responsive": {
        "playing": "3",
        "paused": "8",
        "idle": "12",
        "unapproved": "20",
    },
    "balanced": {
        "playing": "4",
        "paused": "10",
        "idle": "15",
        "unapproved": "30",
    },
    "low_usage": {
        "playing": "8",
        "paused": "20",
        "idle": "60",
        "unapproved": "120",
    },
}

DEFAULTS = {
    "NOWFRAME_SPOTIFY_DEVICE_FILTER_ENABLED": "1",
    "NOWFRAME_ALLOWED_SPOTIFY_DEVICES": "AHILPC",
    "NOWFRAME_ALLOWED_SPOTIFY_DEVICES_ENCODED": "AHILPC",
    "NOWFRAME_AWAY_MODE": "0",
    "NOWFRAME_IDLE_DISPLAY_MODE": "clock_album",
    "NOWFRAME_SPOTIFY_POLL_INTERVAL": "4",
    "NOWFRAME_SPOTIFY_PAUSED_POLL_INTERVAL": "10",
    "NOWFRAME_SPOTIFY_IDLE_POLL_INTERVAL": "15",
    "NOWFRAME_SPOTIFY_UNAPPROVED_POLL_INTERVAL": "30",
    "NOWFRAME_POLLING_PROFILE": "balanced",
    "NOWFRAME_PAUSE_GRACE_SECONDS": "10",
    "NOWFRAME_CLOCK_ENABLED": "1",
    "NOWFRAME_IDLE_BLACK_TIMEOUT": "600",
    "NOWFRAME_CLOCK_BACKGROUND_DARKEN": "0.35",
    "NOWFRAME_BACKGROUND_PROFILE": "current",
    "NOWFRAME_GLOW_ENABLED": "1",
    "NOWFRAME_SPOTIFY_CODE_ENABLED": "1",
}


def enabled(value):
    return str(value).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def read_settings():
    settings = DEFAULTS.copy()

    try:
        lines = CONTROL_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
    except FileNotFoundError:
        return settings

    for raw_line in lines:
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        name, value = line.split("=", 1)

        if name in settings:
            settings[name] = value.strip()

    return settings


def atomic_write(path, content, mode=0o644):
    path.parent.mkdir(
        mode=0o755,
        parents=True,
        exist_ok=True,
    )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)

        temporary_path.chmod(mode)
        os.replace(temporary_path, path)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def settings_content(settings):
    return "".join(
        f"{name}={settings[name]}\n"
        for name in DEFAULTS
    )


def write_settings(settings):
    atomic_write(
        CONTROL_FILE,
        settings_content(settings),
    )


def validate_settings(settings):
    pending_path = (
        CONTROL_FILE.parent
        /
        ".control.env.pending"
    )

    if VALIDATE_COMMAND:
        atomic_write(
            pending_path,
            settings_content(settings),
            mode=0o640,
        )

        try:
            result = subprocess.run(
                VALIDATE_COMMAND,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        finally:
            try:
                pending_path.unlink()
            except FileNotFoundError:
                pass

    else:
        environment = os.environ.copy()
        environment.update(
            {
                name: str(value)
                for name, value in settings.items()
            }
        )

        result = subprocess.run(
            [
                NOWFRAME_PYTHON,
                "-c",
                "import config",
            ],
            cwd=NOWFRAME_APP_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    if result.returncode != 0:
        raise RuntimeError(
            "Settings validation failed: "
            + (
                result.stderr.strip()
                or result.stdout.strip()
                or "unknown validation error"
            )
        )


def restart_nowframe():
    if not RESTART_ENABLED:
        return

    command = (
        RESTART_COMMAND
        or
        [
            "systemctl",
            "restart",
            NOWFRAME_SERVICE,
        ]
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or "NowFrame restart failed."
        )

    deadline = time.monotonic() + 10.0

    while time.monotonic() < deadline:
        state = subprocess.run(
            [
                "systemctl",
                "is-active",
                NOWFRAME_SERVICE,
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.strip()

        if state == "active":
            return

        if state in (
            "failed",
            "inactive",
        ):
            break

        time.sleep(0.5)

    raise RuntimeError(
        "NowFrame did not become active after restart."
    )


def save_changes(changes):
    settings = read_settings()
    settings.update(changes)

    validate_settings(settings)

    existed = CONTROL_FILE.exists()
    previous = (
        CONTROL_FILE.read_text(
            encoding="utf-8"
        )
        if existed
        else None
    )

    write_settings(settings)

    try:
        restart_nowframe()

    except Exception as error:
        if existed:
            atomic_write(
                CONTROL_FILE,
                previous,
            )
        else:
            try:
                CONTROL_FILE.unlink()
            except FileNotFoundError:
                pass

        rollback_error = None

        try:
            restart_nowframe()
        except Exception as second_error:
            rollback_error = second_error

        message = (
            "New settings could not be activated. "
            "The previous settings were restored."
        )

        if rollback_error is not None:
            message += (
                " The rollback restart also failed: "
                f"{rollback_error}"
            )

        raise RuntimeError(
            message
        ) from error


def service_state(name):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )

        return result.stdout.strip() or "unknown"

    except Exception:
        return "unknown"


def integer(row, field):
    try:
        return int(row.get(field, 0) or 0)
    except (TypeError, ValueError):
        return 0


def read_usage():
    rows = []

    try:
        with USAGE_FILE.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file))
    except (
        FileNotFoundError,
        OSError,
        csv.Error,
    ):
        pass

    today = datetime.now().date().isoformat()

    today_row = next(
        (
            row
            for row in reversed(rows)
            if row.get("date") == today
        ),
        {},
    )

    total = integer(
        today_row,
        "total_requests",
    )

    now = datetime.now()
    elapsed_hours = max(
        (
            now.hour * 3600
            + now.minute * 60
            + now.second
        ) / 3600,
        1 / 60,
    )

    return {
        "total": total,
        "requests_per_hour": total / elapsed_hours,
        "successful": integer(
            today_row,
            "successful_requests",
        ),
        "failed": integer(
            today_row,
            "failed_requests",
        ),
        "rate_limits": integer(
            today_row,
            "rate_limit_events",
        ),
        "quota_events": integer(
            today_row,
            "quota_events",
        ),
        "playing": integer(
            today_row,
            "playing_responses",
        ),
        "paused": integer(
            today_row,
            "paused_responses",
        ),
        "idle": integer(
            today_row,
            "idle_responses",
        ),
        "unapproved": integer(
            today_row,
            "unapproved_device_responses",
        ),
        "history": rows[-7:][::-1],
    }


def allowed_devices(settings):
    encoded = settings.get(
        "NOWFRAME_ALLOWED_SPOTIFY_DEVICES_ENCODED",
        "",
    )

    if encoded:
        return [
            unquote(name)
            for name in encoded.split(",")
            if name
        ]

    return [
        name.strip()
        for name in settings[
            "NOWFRAME_ALLOWED_SPOTIFY_DEVICES"
        ].split(",")
        if name.strip()
    ]


def encode_devices(names):
    return ",".join(
        quote(name, safe="")
        for name in names
    )


def read_device_history():
    try:
        data = json.loads(
            DEVICE_HISTORY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except (
        FileNotFoundError,
        OSError,
        ValueError,
    ):
        pass

    return []


def write_device_history(devices):
    atomic_write(
        DEVICE_HISTORY_FILE,
        json.dumps(
            devices,
            indent=2,
            sort_keys=True,
        ) + "\n",
    )


def discover_spotify_devices():
    spotify = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=[
                "user-read-playback-state",
                "user-read-currently-playing",
            ],
            redirect_uri=os.environ.get(
                "SPOTIPY_REDIRECT_URI",
                "http://127.0.0.1:8888/callback",
            ),
            cache_path=os.path.expanduser(
                os.environ.get(
                    "NOWFRAME_SPOTIFY_CACHE_PATH",
                    "~/.nowframe_spotify_cache",
                )
            ),
            open_browser=False,
        ),
        requests_timeout=10,
        retries=0,
        status_retries=0,
    )

    return spotify.devices().get(
        "devices",
        []
    )


def refresh_device_history(discovery=None):
    discovered = (
        discover_spotify_devices()
        if discovery is None
        else discovery
    )

    by_name = {
        item["name"]: item
        for item in read_device_history()
        if item.get("name")
    }

    now = datetime.now(
        timezone.utc
    ).isoformat()

    for device in discovered:
        name = str(
            device.get("name")
            or "Unnamed device"
        ).strip()

        if not name:
            continue

        by_name[name] = {
            "name": name,
            "type": str(
                device.get("type")
                or "Unknown"
            ),
            "active": bool(
                device.get("is_active")
            ),
            "restricted": bool(
                device.get("is_restricted")
            ),
            "last_seen": now,
        }

    devices = sorted(
        by_name.values(),
        key=lambda item: (
            not item.get("active", False),
            item["name"].casefold(),
        ),
    )

    write_device_history(devices)

    return devices


def device_rows(settings):
    allowed = set(
        allowed_devices(settings)
    )

    by_name = {
        item["name"]: item
        for item in read_device_history()
        if item.get("name")
    }

    for name in allowed:
        by_name.setdefault(
            name,
            {
                "name": name,
                "type": "Previously configured",
                "active": False,
                "restricted": False,
                "last_seen": None,
            },
        )

    rows = sorted(
        by_name.values(),
        key=lambda item: (
            not item.get("active", False),
            item["name"].casefold(),
        ),
    )

    for row in rows:
        row["allowed"] = (
            row["name"] in allowed
        )

    return rows
