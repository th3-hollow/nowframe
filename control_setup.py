import json
import os
import socket

from pathlib import Path


FRAMEBUFFER_DEVICE = Path(
    os.environ.get(
        "NOWFRAME_FRAMEBUFFER_DEVICE",
        "/dev/fb0",
    )
)

FRAMEBUFFER_SYSFS = Path(
    os.environ.get(
        "NOWFRAME_FRAMEBUFFER_SYSFS",
        "/sys/class/graphics/fb0",
    )
)

SPOTIFY_CACHE_FILE = Path(
    os.path.expanduser(
        os.environ.get(
            "NOWFRAME_SPOTIFY_CACHE_PATH",
            "/var/lib/nowframe-control/spotify-cache",
        )
    )
)


def read_text(path):
    try:
        return path.read_text(
            encoding="utf-8",
        ).strip()
    except OSError:
        return ""


def framebuffer_status():
    virtual_size = read_text(
        FRAMEBUFFER_SYSFS / "virtual_size"
    )

    bits_per_pixel = read_text(
        FRAMEBUFFER_SYSFS / "bits_per_pixel"
    )

    width = None
    height = None

    if "," in virtual_size:
        raw_width, raw_height = (
            virtual_size.split(",", 1)
        )

        try:
            width = int(raw_width)
            height = int(raw_height)
        except ValueError:
            width = None
            height = None

    try:
        bpp = int(bits_per_pixel)
    except ValueError:
        bpp = None

    exists = FRAMEBUFFER_DEVICE.exists()

    return {
        "device": str(FRAMEBUFFER_DEVICE),
        "exists": exists,
        "width": width,
        "height": height,
        "bits_per_pixel": bpp,
        "resolution_detected": bool(
            width and height
        ),
        "rgb565_compatible": bpp == 16,
        "ready": bool(
            exists
            and width
            and height
            and bpp == 16
        ),
    }


def spotify_authorization_status():
    try:
        data = json.loads(
            SPOTIFY_CACHE_FILE.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        data = {}

    if not isinstance(data, dict):
        data = {}

    return {
        "authorized": bool(
            data.get("access_token")
            and data.get("refresh_token")
        ),
        "refresh_token_present": bool(
            data.get("refresh_token")
        ),
        "scope": data.get("scope", ""),
    }


def setup_summary(
    credential_status,
):
    hardware = framebuffer_status()
    authorization = (
        spotify_authorization_status()
    )

    hostname = socket.gethostname()

    return {
        "hostname": hostname,
        "panel_url": (
            f"http://{hostname}.local:8080"
        ),
        "credentials_configured": bool(
            credential_status.get(
                "configured"
            )
        ),
        "spotify_authorized": (
            authorization["authorized"]
        ),
        "spotify_scope": (
            authorization["scope"]
        ),
        "hardware": hardware,
        "ready": bool(
            credential_status.get(
                "configured"
            )
            and authorization[
                "authorized"
            ]
            and hardware["ready"]
        ),
    }
