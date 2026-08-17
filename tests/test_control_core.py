import json

import pytest

import control_core as core


def use_temporary_files(
    monkeypatch,
    tmp_path,
):
    control_file = (
        tmp_path / "control.env"
    )
    device_file = (
        tmp_path / "devices.json"
    )
    usage_file = (
        tmp_path / "usage.csv"
    )

    monkeypatch.setattr(
        core,
        "CONTROL_FILE",
        control_file,
    )
    monkeypatch.setattr(
        core,
        "DEVICE_HISTORY_FILE",
        device_file,
    )
    monkeypatch.setattr(
        core,
        "USAGE_FILE",
        usage_file,
    )

    return (
        control_file,
        device_file,
        usage_file,
    )


def test_default_settings_are_available(
    monkeypatch,
    tmp_path,
):
    control_file, _, _ = (
        use_temporary_files(
            monkeypatch,
            tmp_path,
        )
    )

    assert not control_file.exists()

    settings = core.read_settings()

    assert settings[
        "NOWFRAME_SPOTIFY_POLL_INTERVAL"
    ] == "4"

    assert settings[
        "NOWFRAME_BACKGROUND_PROFILE"
    ] == "current"


def test_encoded_device_names_round_trip():
    names = [
        "AHILPC",
        "Living Room, TV",
        "Bedroom Speaker",
    ]

    encoded = core.encode_devices(names)

    settings = (
        core.DEFAULTS.copy()
    )

    settings[
        "NOWFRAME_ALLOWED_SPOTIFY_DEVICES_ENCODED"
    ] = encoded

    assert core.allowed_devices(
        settings
    ) == names


def test_discovery_history_is_persistent(
    monkeypatch,
    tmp_path,
):
    _, device_file, _ = (
        use_temporary_files(
            monkeypatch,
            tmp_path,
        )
    )

    devices = (
        core.refresh_device_history([
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
        ])
    )

    assert device_file.exists()
    assert len(devices) == 2
    assert devices[0]["name"] == "AHILPC"
    assert devices[0]["active"] is True

    stored = json.loads(
        device_file.read_text(
            encoding="utf-8"
        )
    )

    assert {
        item["name"]
        for item in stored
    } == {
        "AHILPC",
        "Living Room, TV",
    }


def test_save_merges_unrelated_settings(
    monkeypatch,
    tmp_path,
):
    control_file, _, _ = (
        use_temporary_files(
            monkeypatch,
            tmp_path,
        )
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

    original = (
        core.DEFAULTS.copy()
    )

    original[
        "NOWFRAME_BACKGROUND_PROFILE"
    ] = "dark"

    core.write_settings(original)

    core.save_changes({
        "NOWFRAME_CLOCK_ENABLED": "0",
    })

    saved = core.read_settings()

    assert saved[
        "NOWFRAME_CLOCK_ENABLED"
    ] == "0"

    assert saved[
        "NOWFRAME_BACKGROUND_PROFILE"
    ] == "dark"

    assert control_file.exists()


def test_failed_restart_restores_previous_file(
    monkeypatch,
    tmp_path,
):
    control_file, _, _ = (
        use_temporary_files(
            monkeypatch,
            tmp_path,
        )
    )

    monkeypatch.setattr(
        core,
        "validate_settings",
        lambda settings: None,
    )

    original = (
        core.DEFAULTS.copy()
    )

    core.write_settings(original)

    previous_content = (
        control_file.read_text(
            encoding="utf-8"
        )
    )

    calls = []

    def restart():
        calls.append(True)

        if len(calls) == 1:
            raise RuntimeError(
                "simulated restart failure"
            )

    monkeypatch.setattr(
        core,
        "restart_nowframe",
        restart,
    )

    with pytest.raises(
        RuntimeError,
        match="previous settings were restored",
    ):
        core.save_changes({
            "NOWFRAME_BACKGROUND_PROFILE": "vivid",
        })

    assert len(calls) == 2

    assert (
        control_file.read_text(
            encoding="utf-8"
        )
        ==
        previous_content
    )


def test_validation_failure_writes_nothing(
    monkeypatch,
    tmp_path,
):
    control_file, _, _ = (
        use_temporary_files(
            monkeypatch,
            tmp_path,
        )
    )

    original = (
        core.DEFAULTS.copy()
    )

    core.write_settings(original)

    previous_content = (
        control_file.read_text(
            encoding="utf-8"
        )
    )

    def reject(settings):
        raise RuntimeError(
            "simulated validation error"
        )

    monkeypatch.setattr(
        core,
        "validate_settings",
        reject,
    )

    with pytest.raises(
        RuntimeError,
        match="validation error",
    ):
        core.save_changes({
            "NOWFRAME_BACKGROUND_PROFILE": "vivid",
        })

    assert (
        control_file.read_text(
            encoding="utf-8"
        )
        ==
        previous_content
    )


def test_helper_validation_uses_temporary_pending_file(
    monkeypatch,
    tmp_path,
):
    control_file, _, _ = (
        use_temporary_files(
            monkeypatch,
            tmp_path,
        )
    )

    monkeypatch.setattr(
        core,
        "VALIDATE_COMMAND",
        ["/test/helper", "validate"],
    )

    observed = {}

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def run(command, **kwargs):
        pending = (
            control_file.parent
            /
            ".control.env.pending"
        )

        observed["command"] = command
        observed["exists"] = pending.exists()
        observed["content"] = pending.read_text(
            encoding="utf-8"
        )

        return Result()

    monkeypatch.setattr(
        core.subprocess,
        "run",
        run,
    )

    core.validate_settings(
        core.DEFAULTS.copy()
    )

    pending = (
        control_file.parent
        /
        ".control.env.pending"
    )

    assert observed["command"] == [
        "/test/helper",
        "validate",
    ]

    assert observed["exists"] is True

    assert (
        "NOWFRAME_SPOTIFY_POLL_INTERVAL=4\n"
        in observed["content"]
    )

    assert not pending.exists()
