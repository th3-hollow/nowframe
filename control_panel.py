import secrets

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)

import control_core as core


app = Flask(__name__)
csrf_token = secrets.token_urlsafe(24)


def verify_csrf():
    return secrets.compare_digest(
        request.form.get("csrf_token", ""),
        csrf_token,
    )


def number(field, label, minimum, maximum):
    raw_value = request.form.get(
        field,
        "",
    ).strip()

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{label} must be a number."
        ) from exc

    if not minimum <= value <= maximum:
        raise ValueError(
            f"{label} must be between "
            f"{minimum:g} and {maximum:g}."
        )

    return f"{value:g}"


def idle_timeout():
    raw_value = request.form.get(
        "idle_black_timeout",
        "never",
    ).strip().lower()

    if raw_value in (
        "",
        "0",
        "never",
        "none",
        "off",
    ):
        return "never"

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(
            "Idle-to-black must be a number "
            "of seconds or 'never'."
        ) from exc

    if not 1 <= value <= 86400:
        raise ValueError(
            "Idle-to-black must be between "
            "1 and 86400 seconds."
        )

    return f"{value:g}"


def context(page_name, **extra):
    return {
        "page_name": page_name,
        "csrf_token": csrf_token,
        "message": request.args.get("message"),
        "error": request.args.get("error") == "1",
        **extra,
    }


def saved(endpoint, message=None):
    return redirect(
        url_for(
            endpoint,
            message=(
                message
                or "Settings saved and NowFrame restarted."
            ),
        )
    )


def failed(endpoint, error):
    return redirect(
        url_for(
            endpoint,
            message=str(error),
            error="1",
        )
    )


@app.route("/")
def home():
    return redirect(
        url_for("status")
    )


@app.route("/status")
def status():
    return render_template(
        "status.html",
        **context(
            "status",
            usage=core.read_usage(),
            nowframe_state=core.service_state(
                "nowframe.service"
            ),
            panel_state=core.service_state(
                "nowframe-control.service"
            ),
            avahi_state=core.service_state(
                "avahi-daemon.service"
            ),
        ),
    )


@app.route("/devices", methods=["GET", "POST"])
def devices():
    if request.method == "POST":
        if not verify_csrf():
            return "Invalid form token", 400

        try:
            selected = []

            for name in request.form.getlist(
                "allowed_devices"
            ):
                name = name.strip()

                if (
                    name
                    and "\n" not in name
                    and "\r" not in name
                ):
                    selected.append(name)

            selected = list(
                dict.fromkeys(selected)
            )

            legacy = ",".join(
                name
                for name in selected
                if "," not in name
            )

            core.save_changes({
                "NOWFRAME_SPOTIFY_DEVICE_FILTER_ENABLED": "1",
                "NOWFRAME_ALLOWED_SPOTIFY_DEVICES": legacy,
                "NOWFRAME_ALLOWED_SPOTIFY_DEVICES_ENCODED": (
                    core.encode_devices(selected)
                ),
            })

            return saved("devices")

        except (ValueError, RuntimeError) as exc:
            return failed(
                "devices",
                exc,
            )

    settings = core.read_settings()

    return render_template(
        "devices.html",
        **context(
            "devices",
            devices=core.device_rows(settings),
        ),
    )


@app.post("/devices/refresh")
def refresh_devices():
    if not verify_csrf():
        return "Invalid form token", 400

    try:
        found = core.refresh_device_history()

        return saved(
            "devices",
            (
                f"Device refresh completed. "
                f"{len(found)} saved/discovered "
                "device(s) are listed."
            ),
        )

    except Exception as exc:
        return failed(
            "devices",
            f"Device refresh failed: {exc}",
        )


@app.route("/display", methods=["GET", "POST"])
def display():
    if request.method == "POST":
        if not verify_csrf():
            return "Invalid form token", 400

        try:
            idle_mode = request.form.get(
                "idle_mode",
                "clock_album",
            )

            if idle_mode not in (
                "clock_album",
                "clock_black",
                "keep_album",
                "black",
            ):
                raise ValueError(
                    "Invalid idle display mode."
                )

            core.save_changes({
                "NOWFRAME_AWAY_MODE": (
                    "1"
                    if request.form.get("away_mode")
                    else "0"
                ),
                "NOWFRAME_IDLE_DISPLAY_MODE": idle_mode,
                "NOWFRAME_CLOCK_ENABLED": (
                    "1"
                    if request.form.get("clock_enabled")
                    else "0"
                ),
                "NOWFRAME_PAUSE_GRACE_SECONDS": number(
                    "pause_grace",
                    "Pause grace period",
                    0,
                    3600,
                ),
                "NOWFRAME_IDLE_BLACK_TIMEOUT": idle_timeout(),
                "NOWFRAME_CLOCK_BACKGROUND_DARKEN": number(
                    "clock_darken",
                    "Clock background darkening",
                    0,
                    1,
                ),
            })

            return saved("display")

        except (ValueError, RuntimeError) as exc:
            return failed(
                "display",
                exc,
            )

    settings = core.read_settings()

    return render_template(
        "display.html",
        **context(
            "display",
            settings=settings,
            away_mode=core.enabled(
                settings["NOWFRAME_AWAY_MODE"]
            ),
            clock_enabled=core.enabled(
                settings["NOWFRAME_CLOCK_ENABLED"]
            ),
        ),
    )


@app.route("/background", methods=["GET", "POST"])
def background():
    if request.method == "POST":
        if not verify_csrf():
            return "Invalid form token", 400

        try:
            profile = request.form.get(
                "background_profile",
                "current",
            )

            if profile not in (
                "current",
                "vivid",
                "soft",
                "dark",
            ):
                raise ValueError(
                    "Invalid background profile."
                )

            core.save_changes({
                "NOWFRAME_BACKGROUND_PROFILE": profile,
                "NOWFRAME_GLOW_ENABLED": (
                    "1"
                    if request.form.get("glow_enabled")
                    else "0"
                ),
            })

            return saved("background")

        except (ValueError, RuntimeError) as exc:
            return failed(
                "background",
                exc,
            )

    settings = core.read_settings()

    return render_template(
        "background.html",
        **context(
            "background",
            settings=settings,
            glow_enabled=core.enabled(
                settings["NOWFRAME_GLOW_ENABLED"]
            ),
        ),
    )


@app.route("/polling", methods=["GET", "POST"])
def polling():
    if request.method == "POST":
        if not verify_csrf():
            return "Invalid form token", 400

        try:
            profile = request.form.get(
                "polling_profile",
                "balanced",
            )

            if profile in core.POLLING_PROFILES:
                intervals = core.POLLING_PROFILES[
                    profile
                ]

            elif profile == "custom":
                intervals = {
                    "playing": number(
                        "playing",
                        "Playing interval",
                        1,
                        3600,
                    ),
                    "paused": number(
                        "paused",
                        "Paused interval",
                        1,
                        3600,
                    ),
                    "idle": number(
                        "idle",
                        "Idle interval",
                        1,
                        3600,
                    ),
                    "unapproved": number(
                        "unapproved",
                        "Unapproved interval",
                        1,
                        3600,
                    ),
                }

            else:
                raise ValueError(
                    "Invalid polling profile."
                )

            core.save_changes({
                "NOWFRAME_POLLING_PROFILE": profile,
                "NOWFRAME_SPOTIFY_POLL_INTERVAL": intervals[
                    "playing"
                ],
                "NOWFRAME_SPOTIFY_PAUSED_POLL_INTERVAL": intervals[
                    "paused"
                ],
                "NOWFRAME_SPOTIFY_IDLE_POLL_INTERVAL": intervals[
                    "idle"
                ],
                "NOWFRAME_SPOTIFY_UNAPPROVED_POLL_INTERVAL": intervals[
                    "unapproved"
                ],
            })

            return saved("polling")

        except (ValueError, RuntimeError) as exc:
            return failed(
                "polling",
                exc,
            )

    settings = core.read_settings()

    return render_template(
        "polling.html",
        **context(
            "polling",
            settings=settings,
            profiles=core.POLLING_PROFILES,
        ),
    )


@app.route("/plugins", methods=["GET", "POST"])
def plugins():
    if request.method == "POST":
        if not verify_csrf():
            return "Invalid form token", 400

        try:
            core.save_changes({
                "NOWFRAME_SPOTIFY_CODE_ENABLED": (
                    "1"
                    if request.form.get(
                        "spotify_code_enabled"
                    )
                    else "0"
                ),
            })

            return saved("plugins")

        except RuntimeError as exc:
            return failed(
                "plugins",
                exc,
            )

    settings = core.read_settings()

    return render_template(
        "plugins.html",
        **context(
            "plugins",
            spotify_code_enabled=core.enabled(
                settings[
                    "NOWFRAME_SPOTIFY_CODE_ENABLED"
                ]
            ),
        ),
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
        threaded=False,
    )
