# ============================================================
# NOWFRAME CONFIGURATION
# ============================================================


# ==========================
# DISPLAY
# ==========================

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Options:
# "premium"
# "classic"

RENDERER_MODE = "premium"


# ==========================
# SPOTIFY
# ==========================

# How often NowFrame asks Spotify for fresh playback state.
# Progress is interpolated locally between polls.

SPOTIFY_POLL_INTERVAL = 2.0

# Network timeout when downloading album artwork.

SPOTIFY_REQUEST_TIMEOUT = 10


# ==========================
# IDLE / CLOCK
# ==========================

# How long the current album screen remains visible
# after playback is paused before switching to clock.

PAUSE_GRACE_SECONDS = 10.0

CLOCK_ENABLED = True

CLOCK_FONT_SIZE = 120
CLOCK_DATE_FONT_SIZE = 34

# Amount the previous album background is darkened
# while displaying the clock.
#
# 0.0 = unchanged
# 1.0 = completely black

CLOCK_BACKGROUND_DARKEN = 0.35

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

GLOW_ENABLED = True

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

BACKGROUND_BLUR = 32
BACKGROUND_SECOND_BLUR = 10

BACKGROUND_SATURATION = 1.25
BACKGROUND_CONTRAST = 1.08
BACKGROUND_BRIGHTNESS = 0.43

BACKGROUND_DITHER = True


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
