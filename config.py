import os


def environment_bool(name, default):

    value = os.environ.get(name)

    if value is None:
        return bool(default)

    return value.strip().lower() in (
        "1",
        "true",
        "yes",
        "on"
    )


def environment_float(
    name,
    default,
    minimum=None,
    maximum=None
):

    raw_value = os.environ.get(name)

    if raw_value is None:
        value = float(default)

    else:

        try:
            value = float(raw_value)

        except ValueError:

            print(
                f"Invalid {name}; using {default}"
            )
            value = float(default)

    if minimum is not None:
        value = max(value, minimum)

    if maximum is not None:
        value = min(value, maximum)

    return value


def environment_optional_seconds(
    name,
    default
):

    raw_value = os.environ.get(name)

    if raw_value is None:
        return default

    value = raw_value.strip().lower()

    if value in (
        "",
        "none",
        "never",
        "off",
        "0"
    ):
        return None

    try:
        return max(float(value), 1.0)

    except ValueError:

        print(
            f"Invalid {name}; using {default}"
        )
        return default


# ============================================================
# NOWFRAME CONFIGURATION
# ============================================================


# ==========================
# DISPLAY
# ==========================

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Linux framebuffer device.
# NowFrame currently expects 16-bit RGB565 output.

FRAMEBUFFER_DEVICE = "/dev/fb0"

# Options:
# "premium"
# "classic"

RENDERER_MODE = "premium"


# ==========================
# SPOTIFY
# ==========================

# Spotify polling intervals in seconds for playing,
# paused, and idle states. Progress is interpolated
# locally between polls.

SPOTIFY_POLL_INTERVAL = 5.0
SPOTIFY_PAUSED_POLL_INTERVAL = 10.0
SPOTIFY_IDLE_POLL_INTERVAL = 30.0

# Optional Spotify playback-device filter. Leave empty
# to display playback from every device. This can also
# be set privately with NOWFRAME_ALLOWED_SPOTIFY_DEVICES.

SPOTIFY_DEVICE_FILTER_ENABLED = False
SPOTIFY_ALLOWED_DEVICES = ()
SPOTIFY_UNAPPROVED_DEVICE_POLL_INTERVAL = 30.0

# Persistent daily Spotify API usage statistics.

SPOTIFY_USAGE_LOG_ENABLED = True
SPOTIFY_USAGE_LOG_PATH = os.environ.get(
    "NOWFRAME_SPOTIFY_USAGE_LOG_PATH",
    "~/.local/state/nowframe/spotify_api_usage.csv"
)
SPOTIFY_USAGE_LOG_FLUSH_SECONDS = 300

# Network timeout when downloading album artwork.

SPOTIFY_REQUEST_TIMEOUT = 10

# Runtime cache directory.
# Temporary artwork and other generated Spotify
# assets are stored here instead of inside Git.

RUNTIME_CACHE_DIR = "/tmp/nowframe"
ALBUM_CACHE_PATH = "/tmp/nowframe/album.jpg"

# ==========================
# SPOTIFY CODE
# ==========================

# Show Spotify Code below artist name.

SPOTIFY_CODE_ENABLED = environment_bool(
    "NOWFRAME_SPOTIFY_CODE_ENABLED",
    True
)

# Size of the Spotify Code graphic.

SPOTIFY_CODE_WIDTH = 350
SPOTIFY_CODE_HEIGHT = 80

# Maximum number of generated codes retained in
# the runtime cache. Oldest entries are removed first.

SPOTIFY_CODE_CACHE_LIMIT = 100

# Position:
# "above_progress"
# "bottom_center"

SPOTIFY_CODE_POSITION = "above_progress"

# ==========================
# IDLE / CLOCK
# ==========================

# How long the current album screen remains visible
# after playback is paused before switching to clock.

PAUSE_GRACE_SECONDS = environment_float(
    "NOWFRAME_PAUSE_GRACE_SECONDS",
    10.0,
    minimum=0.0,
    maximum=3600.0
)

# ==========================
# ADVANCED IDLE BEHAVIOR
# ==========================

# What the display should show after the
# pause grace period ends.
#
# Options:
# "clock_album" = clock over the last album background
# "clock_black" = clock over a pure black background
# "black"       = completely black screen

IDLE_DISPLAY_MODE = os.environ.get(
    "NOWFRAME_IDLE_DISPLAY_MODE",
    "clock_album"
).strip().lower()

if IDLE_DISPLAY_MODE not in (
    "clock_album",
    "clock_black",
    "black",
    "keep_album"
):
    print(
        "Invalid NOWFRAME_IDLE_DISPLAY_MODE; "
        "using clock_album"
    )
    IDLE_DISPLAY_MODE = "clock_album"


# Optional second idle stage.
#
# After this many seconds in idle mode,
# switch the display to completely black.
#
# Examples:
# None = never switch to black
# 600  = switch to black after 10 minutes
# 1800 = switch to black after 30 minutes

IDLE_BLACK_TIMEOUT = environment_optional_seconds(
    "NOWFRAME_IDLE_BLACK_TIMEOUT",
    600
)

CLOCK_ENABLED = environment_bool(
    "NOWFRAME_CLOCK_ENABLED",
    True
)

CLOCK_FONT_SIZE = 120
CLOCK_DATE_FONT_SIZE = 34

# Amount the previous album background is darkened
# while displaying the clock.
#
# 0.0 = unchanged
# 1.0 = completely black

CLOCK_BACKGROUND_DARKEN = environment_float(
    "NOWFRAME_CLOCK_BACKGROUND_DARKEN",
    0.35,
    minimum=0.0,
    maximum=1.0
)

CLOCK_TIME_Y_OFFSET = -35
CLOCK_DATE_Y_OFFSET = 85


# ==========================
# TRANSITIONS
# ==========================

CROSSFADE_ENABLED = True

# More steps = smoother but slightly slower.

CROSSFADE_STEPS = 6


# ==========================
# ALBUM ART
# ==========================

ALBUM_SIZE = 300
ALBUM_RADIUS = 28
ALBUM_Y = 110


# ==========================
# ALBUM GLOW
# ==========================

GLOW_ENABLED = environment_bool(
    "NOWFRAME_GLOW_ENABLED",
    True
)

# Normalized maximum brightness of the selected
# album glow color.

GLOW_TARGET_PEAK = 165

# Outer atmospheric glow

OUTER_GLOW_ALPHA = 35
OUTER_GLOW_BLUR = 80

# Inner glow around artwork

INNER_GLOW_ALPHA = 52
INNER_GLOW_BLUR = 34


# ==========================
# TYPOGRAPHY
# ==========================

TITLE_MAX_FONT_SIZE = 50
TITLE_MIN_FONT_SIZE = 30
TITLE_MAX_WIDTH = 1450

ARTIST_FONT_SIZE = 30

TITLE_Y = 465
ARTIST_Y = 525


# ==========================
# PROGRESS BAR
# ==========================

PROGRESS_WIDTH = 1100
PROGRESS_HEIGHT = 18

PROGRESS_BACKGROUND = (65, 65, 65)
PROGRESS_FOREGROUND = (255, 255, 255)


# ==========================
# BACKGROUND
# ==========================

# Background is generated at this lower resolution
# and then scaled to the display.

BACKGROUND_WORK_SIZE = (640, 360)

BACKGROUND_PROFILE = os.environ.get(
    "NOWFRAME_BACKGROUND_PROFILE",
    "current"
).strip().lower()

BACKGROUND_PROFILES = {
    "current": {
        "blur": 32,
        "second_blur": 10,
        "saturation": 1.25,
        "contrast": 1.08,
        "brightness": 0.43,
        "dither": True,
    },
    "vivid": {
        "blur": 28,
        "second_blur": 8,
        "saturation": 1.55,
        "contrast": 1.15,
        "brightness": 0.48,
        "dither": True,
    },
    "soft": {
        "blur": 42,
        "second_blur": 16,
        "saturation": 1.10,
        "contrast": 1.02,
        "brightness": 0.38,
        "dither": True,
    },
    "dark": {
        "blur": 36,
        "second_blur": 12,
        "saturation": 1.20,
        "contrast": 1.08,
        "brightness": 0.28,
        "dither": True,
    },
}

if BACKGROUND_PROFILE not in BACKGROUND_PROFILES:

    print(
        "Invalid NOWFRAME_BACKGROUND_PROFILE; "
        "using current"
    )
    BACKGROUND_PROFILE = "current"

_BACKGROUND = BACKGROUND_PROFILES[
    BACKGROUND_PROFILE
]

BACKGROUND_BLUR = _BACKGROUND["blur"]
BACKGROUND_SECOND_BLUR = _BACKGROUND["second_blur"]
BACKGROUND_SATURATION = _BACKGROUND["saturation"]
BACKGROUND_CONTRAST = _BACKGROUND["contrast"]
BACKGROUND_BRIGHTNESS = _BACKGROUND["brightness"]
BACKGROUND_DITHER = _BACKGROUND["dither"]


# ==========================
# PERFORMANCE / DEBUG
# ==========================

PERFORMANCE_LOGGING = True

# Print performance statistics every N seconds.

PERFORMANCE_REPORT_SECONDS = 5.0


# ==========================
# FONTS
# ==========================

FONT_REGULAR = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans.ttf"
)

FONT_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)
