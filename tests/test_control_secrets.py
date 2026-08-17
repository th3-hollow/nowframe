import stat

import pytest

import control_secrets as secrets


def temporary_files(
    monkeypatch,
    tmp_path,
):
    environment_file = (
        tmp_path / "spotify.env"
    )

    pending_file = (
        tmp_path / ".spotify.env.pending"
    )

    monkeypatch.setattr(
        secrets,
        "SPOTIFY_ENV_FILE",
        environment_file,
    )

    monkeypatch.setattr(
        secrets,
        "SPOTIFY_PENDING_FILE",
        pending_file,
    )

    return environment_file, pending_file


def test_status_masks_credentials(
    monkeypatch,
    tmp_path,
):
    environment_file, _ = temporary_files(
        monkeypatch,
        tmp_path,
    )

    environment_file.write_text(
        "SPOTIPY_CLIENT_ID=abcdefgh12345678\n"
        "SPOTIPY_CLIENT_SECRET=secretvalue123456\n"
        "SPOTIPY_REDIRECT_URI="
        "http://127.0.0.1:8888/callback\n",
        encoding="utf-8",
    )

    status = secrets.spotify_status()

    assert status["configured"] is True
    assert status["client_id_hint"] == (
        "abcd…5678"
    )
    assert status["secret_configured"] is True
    assert (
        "secretvalue"
        not in str(status)
    )


def test_configure_invokes_helper_and_cleans_pending(
    monkeypatch,
    tmp_path,
):
    _, pending_file = temporary_files(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        secrets,
        "CONFIGURE_COMMAND",
        ["/test/helper", "configure-spotify"],
    )

    observed = {}

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def run(command, **kwargs):
        observed["command"] = command
        observed["exists"] = (
            pending_file.exists()
        )

        observed["content"] = (
            pending_file.read_text(
                encoding="utf-8",
            )
        )

        observed["mode"] = stat.S_IMODE(
            pending_file.stat().st_mode
        )

        return Result()

    monkeypatch.setattr(
        secrets.subprocess,
        "run",
        run,
    )

    secrets.configure_spotify(
        "clientid1234567890",
        "clientsecret1234567890",
        "http://127.0.0.1:8888/callback",
    )

    assert observed["command"] == [
        "/test/helper",
        "configure-spotify",
    ]

    assert observed["exists"] is True
    assert observed["mode"] == 0o600

    assert (
        "SPOTIPY_CLIENT_ID=clientid1234567890\n"
        in observed["content"]
    )

    assert (
        "SPOTIPY_CLIENT_SECRET="
        "clientsecret1234567890\n"
        in observed["content"]
    )

    assert pending_file.exists() is False


@pytest.mark.parametrize(
    "client_id,client_secret",
    (
        ("short", "clientsecret1234567890"),
        ("client;command", "clientsecret1234567890"),
        ("clientid1234567890", "bad secret value"),
        ("clientid1234567890", "$(command)"),
    ),
)
def test_invalid_credentials_are_rejected(
    monkeypatch,
    tmp_path,
    client_id,
    client_secret,
):
    _, pending_file = temporary_files(
        monkeypatch,
        tmp_path,
    )

    with pytest.raises(ValueError):
        secrets.configure_spotify(
            client_id,
            client_secret,
            "http://127.0.0.1:8888/callback",
        )

    assert pending_file.exists() is False


@pytest.mark.parametrize(
    "redirect_uri",
    (
        "",
        "javascript:alert(1)",
        "http://user:password@example.com/callback",
        "not-a-url",
    ),
)
def test_invalid_redirect_uri_is_rejected(
    redirect_uri,
):
    with pytest.raises(ValueError):
        secrets.validate_redirect_uri(
            redirect_uri
        )
