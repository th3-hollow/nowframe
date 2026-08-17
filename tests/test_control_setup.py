import json

import control_setup as setup


def temporary_paths(
    monkeypatch,
    tmp_path,
):
    framebuffer = tmp_path / "fb0"
    sysfs = tmp_path / "sysfs"
    cache = tmp_path / "spotify-cache"

    sysfs.mkdir()

    monkeypatch.setattr(
        setup,
        "FRAMEBUFFER_DEVICE",
        framebuffer,
    )

    monkeypatch.setattr(
        setup,
        "FRAMEBUFFER_SYSFS",
        sysfs,
    )

    monkeypatch.setattr(
        setup,
        "SPOTIFY_CACHE_FILE",
        cache,
    )

    return framebuffer, sysfs, cache


def test_ready_framebuffer(
    monkeypatch,
    tmp_path,
):
    framebuffer, sysfs, _ = temporary_paths(
        monkeypatch,
        tmp_path,
    )

    framebuffer.touch()

    (sysfs / "virtual_size").write_text(
        "1920,1080\n",
        encoding="utf-8",
    )

    (sysfs / "bits_per_pixel").write_text(
        "16\n",
        encoding="utf-8",
    )

    status = setup.framebuffer_status()

    assert status["ready"] is True
    assert status["width"] == 1920
    assert status["height"] == 1080
    assert status["bits_per_pixel"] == 16


def test_incompatible_framebuffer(
    monkeypatch,
    tmp_path,
):
    framebuffer, sysfs, _ = temporary_paths(
        monkeypatch,
        tmp_path,
    )

    framebuffer.touch()

    (sysfs / "virtual_size").write_text(
        "1280,720\n",
        encoding="utf-8",
    )

    (sysfs / "bits_per_pixel").write_text(
        "32\n",
        encoding="utf-8",
    )

    status = setup.framebuffer_status()

    assert status["ready"] is False
    assert status["rgb565_compatible"] is False


def test_spotify_authorization_is_boolean_only(
    monkeypatch,
    tmp_path,
):
    _, _, cache = temporary_paths(
        monkeypatch,
        tmp_path,
    )

    cache.write_text(
        json.dumps(
            {
                "access_token": "private-access",
                "refresh_token": "private-refresh",
                "scope": (
                    "user-read-playback-state"
                ),
            }
        ),
        encoding="utf-8",
    )

    status = (
        setup.spotify_authorization_status()
    )

    assert status["authorized"] is True
    assert status["refresh_token_present"] is True
    assert "private-access" not in str(status)
    assert "private-refresh" not in str(status)


def test_summary_requires_every_core_step(
    monkeypatch,
):
    monkeypatch.setattr(
        setup,
        "framebuffer_status",
        lambda: {
            "ready": True,
        },
    )

    monkeypatch.setattr(
        setup,
        "spotify_authorization_status",
        lambda: {
            "authorized": True,
            "scope": "scope",
        },
    )

    status = setup.setup_summary(
        {
            "configured": True,
        }
    )

    assert status["ready"] is True
