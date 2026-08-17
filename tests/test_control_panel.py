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

    monkeypatch.setattr(
        panel.auth,
        "auth_configured",
        lambda: True,
    )

    monkeypatch.setattr(
        panel.auth,
        "session_version",
        lambda: "test-version",
    )

    client = panel.app.test_client()

    with client.session_transaction() as session:
        session["authenticated"] = True
        session["auth_version"] = "test-version"

    return client


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



def test_unconfigured_panel_redirects_to_setup(
    monkeypatch,
):
    monkeypatch.setattr(
        panel.auth,
        "auth_configured",
        lambda: False,
    )

    client = panel.app.test_client()

    response = client.get("/status")

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/setup/admin")

    response = client.get("/setup/admin")

    assert response.status_code == 200
    assert b"Welcome to NowFrame" in response.data


def test_first_admin_password_setup(
    monkeypatch,
):
    configured = {"value": False}
    saved = {}

    monkeypatch.setattr(
        panel.auth,
        "auth_configured",
        lambda: configured["value"],
    )

    def set_password(password):
        saved["password"] = password
        configured["value"] = True

    monkeypatch.setattr(
        panel.auth,
        "set_password",
        set_password,
    )

    client = panel.app.test_client()

    response = client.post(
        "/setup/admin",
        data={
            "csrf_token": panel.csrf_token,
            "password": "a secure password",
            "password_confirm": "a secure password",
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/setup")

    assert saved["password"] == (
        "a secure password"
    )

    with client.session_transaction() as session:
        assert session["authenticated"] is True


def test_login_and_logout(
    monkeypatch,
):
    monkeypatch.setattr(
        panel.auth,
        "auth_configured",
        lambda: True,
    )

    monkeypatch.setattr(
        panel.auth,
        "verify_password",
        lambda password: password == "correct password",
    )

    client = panel.app.test_client()

    response = client.get("/status")

    assert response.status_code == 302
    assert "/login" in response.headers[
        "Location"
    ]

    response = client.post(
        "/login",
        data={
            "csrf_token": panel.csrf_token,
            "password": "correct password",
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/status")

    response = client.post(
        "/logout",
        data={
            "csrf_token": panel.csrf_token,
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/login")

    response = client.get("/status")

    assert response.status_code == 302
    assert "/login" in response.headers[
        "Location"
    ]


def test_incorrect_password_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        panel.auth,
        "auth_configured",
        lambda: True,
    )

    monkeypatch.setattr(
        panel.auth,
        "verify_password",
        lambda password: False,
    )

    client = panel.app.test_client()

    response = client.post(
        "/login",
        data={
            "csrf_token": panel.csrf_token,
            "password": "incorrect",
        },
    )

    assert response.status_code == 302
    assert "error=1" in response.headers[
        "Location"
    ]



def test_spotify_setup_page_masks_secret(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        panel.credential_store,
        "spotify_status",
        lambda: {
            "configured": True,
            "client_id_hint": "abcd…5678",
            "secret_configured": True,
            "redirect_uri": (
                "http://127.0.0.1:8888/callback"
            ),
        },
    )

    response = client.get(
        "/setup/spotify"
    )

    assert response.status_code == 200
    assert b"Spotify application" in response.data
    assert b"abcd" in response.data
    assert b"saved secret" in response.data
    assert b"clientsecret123456" not in response.data


def test_spotify_credentials_save(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        panel.credential_store,
        "spotify_status",
        lambda: {
            "configured": False,
            "client_id_hint": "",
            "secret_configured": False,
            "redirect_uri": "",
        },
    )

    saved = {}

    def configure(
        client_id,
        client_secret,
        redirect_uri,
    ):
        saved.update(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

    monkeypatch.setattr(
        panel.credential_store,
        "configure_spotify",
        configure,
    )

    response = client.post(
        "/setup/spotify",
        data={
            "csrf_token": panel.csrf_token,
            "client_id": "clientid1234567890",
            "client_secret": (
                "clientsecret1234567890"
            ),
            "redirect_uri": (
                "http://127.0.0.1:8888/callback"
            ),
        },
    )

    assert response.status_code == 302

    assert saved == {
        "client_id": "clientid1234567890",
        "client_secret": (
            "clientsecret1234567890"
        ),
        "redirect_uri": (
            "http://127.0.0.1:8888/callback"
        ),
    }

    location = response.headers["Location"]

    assert "clientsecret" not in location
    assert "credentials+saved" in location



def test_setup_overview_renders_readiness(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        panel.credential_store,
        "spotify_status",
        lambda: {
            "configured": True,
        },
    )

    monkeypatch.setattr(
        panel.setup_checks,
        "setup_summary",
        lambda credentials: {
            "panel_url": (
                "http://nowframe.local:8080"
            ),
            "credentials_configured": True,
            "spotify_authorized": True,
            "spotify_scope": (
                "user-read-playback-state"
            ),
            "hardware": {
                "device": "/dev/fb0",
                "exists": True,
                "width": 1920,
                "height": 1080,
                "bits_per_pixel": 16,
                "resolution_detected": True,
                "rgb565_compatible": True,
                "ready": True,
            },
            "ready": True,
        },
    )

    response = client.get("/setup")

    assert response.status_code == 200
    assert b"First-run setup" in response.data
    assert b"1920" in response.data
    assert b"16-bit RGB565" in response.data
    assert b"Setup complete" in response.data
    assert b"/setup/spotify" in response.data



def test_start_spotify_authorization(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        panel.spotify_oauth,
        "authorization_url",
        lambda: (
            "secure-state",
            "https://accounts.spotify.com/authorize"
            "?state=secure-state",
        ),
    )

    response = client.post(
        "/setup/spotify/authorize",
        data={
            "csrf_token": panel.csrf_token,
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].startswith(
        "https://accounts.spotify.com/"
    )

    with client.session_transaction() as session:
        assert session[
            "spotify_oauth_state"
        ] == "secure-state"


def test_complete_spotify_authorization(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    observed = {}
    restarted = {"value": False}

    def complete(
        callback_url,
        expected_state,
    ):
        observed["callback_url"] = (
            callback_url
        )

        observed["expected_state"] = (
            expected_state
        )

        return {
            "authorized": True,
        }

    monkeypatch.setattr(
        panel.spotify_oauth,
        "complete_authorization",
        complete,
    )

    monkeypatch.setattr(
        core,
        "restart_nowframe",
        lambda: restarted.update(
            value=True
        ),
    )

    with client.session_transaction() as session:
        session[
            "spotify_oauth_state"
        ] = "secure-state"

    callback = (
        "http://127.0.0.1:8888/callback"
        "?code=spotify-code&state=secure-state"
    )

    response = client.post(
        "/setup/spotify/complete",
        data={
            "csrf_token": panel.csrf_token,
            "callback_url": callback,
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].startswith("/setup?")

    assert observed == {
        "callback_url": callback,
        "expected_state": "secure-state",
    }

    assert restarted["value"] is True

    with client.session_transaction() as session:
        assert (
            "spotify_oauth_state"
            not in session
        )



def test_change_admin_password(
    monkeypatch,
    tmp_path,
):
    client = prepare(
        monkeypatch,
        tmp_path,
    )

    saved = {}

    monkeypatch.setattr(
        panel.auth,
        "verify_password",
        lambda password: (
            password == "current password"
        ),
    )

    monkeypatch.setattr(
        panel.auth,
        "set_password",
        lambda password: saved.update(
            password=password
        ),
    )

    response = client.post(
        "/setup/security",
        data={
            "csrf_token": panel.csrf_token,
            "current_password": (
                "current password"
            ),
            "new_password": (
                "new secure password"
            ),
            "new_password_confirm": (
                "new secure password"
            ),
        },
    )

    assert response.status_code == 302
    assert saved["password"] == (
        "new secure password"
    )

    with client.session_transaction() as session:
        assert session["authenticated"] is True
        assert session["auth_version"] == (
            "test-version"
        )


def test_old_session_version_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        panel.auth,
        "auth_configured",
        lambda: True,
    )

    monkeypatch.setattr(
        panel.auth,
        "session_version",
        lambda: "current-version",
    )

    client = panel.app.test_client()

    with client.session_transaction() as session:
        session["authenticated"] = True
        session["auth_version"] = "old-version"

    response = client.get("/status")

    assert response.status_code == 302
    assert "/login" in response.headers[
        "Location"
    ]
