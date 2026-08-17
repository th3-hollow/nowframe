import control_core as core
import control_panel as panel


def prepare(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        core,
        "CONTROL_FILE",
        tmp_path / "control.env",
    )

    monkeypatch.setattr(
        core,
        "DEVICE_HISTORY_FILE",
        tmp_path / "devices.json",
    )

    monkeypatch.setattr(
        core,
        "USAGE_FILE",
        tmp_path / "usage.csv",
    )

    monkeypatch.setattr(
        core,
        "validate_settings",
        lambda settings: None,
    )

    monkeypatch.setattr(
        core,
        "restart_nowframe",
        lambda: None,
    )

    return panel.app.test_client()


def test_home_redirects_to_status(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/status")


def test_every_page_renders(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    routes = {
        "/status": b"Service health",
        "/devices": b"Refresh devices",
        "/display": b"Pause grace period",
        "/background": b"Current smooth",
        "/polling": b"Low API usage",
        "/plugins": b"Show Spotify Code",
    }

    for route, marker in routes.items():
        response = client.get(route)

        assert response.status_code == 200
        assert marker in response.data


def test_device_refresh_and_save(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        core,
        "discover_spotify_devices",
        lambda: [
            {
                "name": "AHILPC",
                "type": "Computer",
                "is_active": True,
                "is_restricted": False,
            },
            {
                "name": "Living Room, TV",
                "type": "TV",
                "is_active": False,
                "is_restricted": False,
            },
        ],
    )

    response = client.post(
        "/devices/refresh",
        data={
            "csrf_token": panel.csrf_token,
        },
    )

    assert response.status_code == 302

    response = client.get("/devices")

    assert b"AHILPC" in response.data
    assert b"Living Room, TV" in response.data
    assert b"Active now" in response.data

    response = client.post(
        "/devices",
        data={
            "csrf_token": panel.csrf_token,
            "allowed_devices": [
                "AHILPC",
                "Living Room, TV",
            ],
        },
    )

    assert response.status_code == 302

    settings = core.read_settings()

    assert core.allowed_devices(
        settings
    ) == [
        "AHILPC",
        "Living Room, TV",
    ]


def test_display_save(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    response = client.post(
        "/display",
        data={
            "csrf_token": panel.csrf_token,
            "away_mode": "on",
            "idle_mode": "clock_black",
            "clock_enabled": "on",
            "pause_grace": "12",
            "idle_black_timeout": "never",
            "clock_darken": "0.5",
        },
    )

    assert response.status_code == 302

    settings = core.read_settings()

    assert settings[
        "NOWFRAME_AWAY_MODE"
    ] == "1"

    assert settings[
        "NOWFRAME_IDLE_DISPLAY_MODE"
    ] == "clock_black"

    assert settings[
        "NOWFRAME_PAUSE_GRACE_SECONDS"
    ] == "12"

    assert settings[
        "NOWFRAME_IDLE_BLACK_TIMEOUT"
    ] == "never"


def test_background_save(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    response = client.post(
        "/background",
        data={
            "csrf_token": panel.csrf_token,
            "background_profile": "vivid",
            "glow_enabled": "on",
        },
    )

    assert response.status_code == 302

    settings = core.read_settings()

    assert settings[
        "NOWFRAME_BACKGROUND_PROFILE"
    ] == "vivid"

    assert settings[
        "NOWFRAME_GLOW_ENABLED"
    ] == "1"


def test_polling_profile_save(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    response = client.post(
        "/polling",
        data={
            "csrf_token": panel.csrf_token,
            "polling_profile": "responsive",
        },
    )

    assert response.status_code == 302

    settings = core.read_settings()

    assert settings[
        "NOWFRAME_SPOTIFY_POLL_INTERVAL"
    ] == "3"

    assert settings[
        "NOWFRAME_SPOTIFY_IDLE_POLL_INTERVAL"
    ] == "12"


def test_plugin_save(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    response = client.post(
        "/plugins",
        data={
            "csrf_token": panel.csrf_token,
            "spotify_code_enabled": "on",
        },
    )

    assert response.status_code == 302

    assert core.read_settings()[
        "NOWFRAME_SPOTIFY_CODE_ENABLED"
    ] == "1"


def test_invalid_csrf_is_rejected(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    response = client.post(
        "/display",
        data={
            "csrf_token": "incorrect",
        },
    )

    assert response.status_code == 400
