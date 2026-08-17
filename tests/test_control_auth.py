import json
import stat

import pytest

import control_auth as auth


def temporary_auth(
    monkeypatch,
    tmp_path,
):
    auth_file = tmp_path / "auth.json"
    session_file = tmp_path / "session.key"

    monkeypatch.setattr(
        auth,
        "AUTH_FILE",
        auth_file,
    )

    monkeypatch.setattr(
        auth,
        "SESSION_KEY_FILE",
        session_file,
    )

    return auth_file, session_file


def test_password_is_hashed(
    monkeypatch,
    tmp_path,
):
    auth_file, _ = temporary_auth(
        monkeypatch,
        tmp_path,
    )

    password = "correct horse battery staple"

    auth.set_password(password)

    content = auth_file.read_text(
        encoding="utf-8",
    )

    data = json.loads(content)

    assert password not in content
    assert data["version"] == 1
    assert data["password_hash"].startswith(
        "scrypt:"
    )

    assert auth.auth_configured() is True
    assert auth.verify_password(password) is True
    assert auth.verify_password("incorrect") is False


def test_short_password_is_rejected(
    monkeypatch,
    tmp_path,
):
    temporary_auth(
        monkeypatch,
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="at least 10",
    ):
        auth.set_password("too-short")


def test_auth_file_is_private(
    monkeypatch,
    tmp_path,
):
    auth_file, _ = temporary_auth(
        monkeypatch,
        tmp_path,
    )

    auth.set_password(
        "a sufficiently long password"
    )

    mode = stat.S_IMODE(
        auth_file.stat().st_mode
    )

    assert mode == 0o600


def test_session_key_is_private_and_persistent(
    monkeypatch,
    tmp_path,
):
    _, session_file = temporary_auth(
        monkeypatch,
        tmp_path,
    )

    first = auth.session_key()
    second = auth.session_key()

    assert first == second
    assert len(first) >= 32

    mode = stat.S_IMODE(
        session_file.stat().st_mode
    )

    assert mode == 0o600


def test_invalid_auth_file_fails_closed(
    monkeypatch,
    tmp_path,
):
    auth_file, _ = temporary_auth(
        monkeypatch,
        tmp_path,
    )

    auth_file.write_text(
        "not-json",
        encoding="utf-8",
    )

    assert auth.auth_configured() is False
    assert auth.verify_password("anything") is False



def test_password_change_rotates_session_version(
    monkeypatch,
    tmp_path,
):
    temporary_auth(
        monkeypatch,
        tmp_path,
    )

    auth.set_password(
        "first secure password"
    )

    first = auth.session_version()

    auth.set_password(
        "second secure password"
    )

    second = auth.session_version()

    assert first
    assert second
    assert first != second
