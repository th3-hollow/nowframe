# Configuration

NowFrame’s behavior and appearance are controlled by `/opt/nowframe/config.py`.

After changing the configuration, restart the service:

```bash
sudo systemctl restart nowframe.service
```

## Display

```python
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FRAMEBUFFER_DEVICE = "/dev/fb0"
RENDERER_MODE = "premium"
```

`SCREEN_WIDTH` and `SCREEN_HEIGHT` must match the framebuffer resolution.

Check the current resolution with:

```bash
cat /sys/class/graphics/fb0/virtual_size
```

NowFrame currently expects a 16-bit RGB565 framebuffer. Check it with:

```bash
cat /sys/class/graphics/fb0/bits_per_pixel
```

Renderer modes:

- `"premium"` enables adaptive backgrounds, glow, Spotify Codes, and optimized progress-region updates.
- `"classic"` uses the simpler fallback layout.

## Spotify

```python
SPOTIFY_POLL_INTERVAL = 10.0
SPOTIFY_REQUEST_TIMEOUT = 10
```

`SPOTIFY_POLL_INTERVAL` controls how frequently playback state is requested from Spotify. Progress is calculated locally between requests.

The default 10-second interval is recommended. Reducing it increases Spotify API traffic and can exhaust Spotify Development Mode quotas. Increasing it delays track and playback-state changes, while the progress bar remains smooth because it is calculated locally.

`SPOTIFY_REQUEST_TIMEOUT` applies to network downloads such as album artwork and Spotify Codes.

## Runtime cache

```python
RUNTIME_CACHE_DIR = "/tmp/nowframe"
ALBUM_CACHE_PATH = "/tmp/nowframe/album.jpg"
```

Album artwork and generated Spotify Codes are runtime data and are deliberately stored outside the Git repository.

The default cache is temporary and may be cleared during reboot.

## Spotify Codes

```python
SPOTIFY_CODE_ENABLED = True
SPOTIFY_CODE_WIDTH = 350
SPOTIFY_CODE_HEIGHT = 80
SPOTIFY_CODE_CACHE_LIMIT = 100
SPOTIFY_CODE_POSITION = "above_progress"
```

Available positions:

- `"above_progress"`
- `"bottom_center"`

Spotify Codes are cached by track URI. Old entries are removed when the configured limit is exceeded.

The renderer removes the downloaded black rectangle and draws the code transparently. It normally uses white artwork over NowFrame’s dark background and can switch to black over a bright background.

## Idle behavior

```python
PAUSE_GRACE_SECONDS = 10.0
IDLE_DISPLAY_MODE = "clock_album"
IDLE_BLACK_TIMEOUT = 600
```

`PAUSE_GRACE_SECONDS` controls how long the current album screen remains after playback pauses.

Available idle modes:

- `"clock_album"` shows the clock over the previous album background.
- `"clock_black"` shows the clock over black.
- `"black"` turns the display black.

`IDLE_BLACK_TIMEOUT` adds a second idle stage:

```python
IDLE_BLACK_TIMEOUT = None
```

never switches an idle clock to black.

```python
IDLE_BLACK_TIMEOUT = 600
```

switches to black after ten minutes.

## Clock

```python
CLOCK_ENABLED = True
CLOCK_FONT_SIZE = 120
CLOCK_DATE_FONT_SIZE = 34
CLOCK_BACKGROUND_DARKEN = 0.35
CLOCK_TIME_Y_OFFSET = -35
CLOCK_DATE_Y_OFFSET = 85
```

`CLOCK_BACKGROUND_DARKEN` ranges from `0.0` for unchanged to `1.0` for completely black.

Offsets adjust the clock elements relative to the center of the display.

## Transitions

```python
CROSSFADE_ENABLED = True
CROSSFADE_STEPS = 6
```

More steps produce a smoother transition but require more framebuffer writes.

The tested Pi Zero 2 W configuration uses six steps.

## Album artwork

```python
ALBUM_SIZE = 300
ALBUM_RADIUS = 28
ALBUM_Y = 110
```

These settings control artwork size, rounded-corner radius, and vertical position.

## Album glow

```python
GLOW_ENABLED = True
GLOW_TARGET_PEAK = 165
OUTER_GLOW_ALPHA = 35
OUTER_GLOW_BLUR = 80
INNER_GLOW_ALPHA = 52
INNER_GLOW_BLUR = 34
```

When enabled, NowFrame selects a saturated color from the current album palette.

Set:

```python
GLOW_ENABLED = False
```

to disable both colored glow layers while retaining the local artwork shadow.

## Typography

```python
TITLE_MAX_FONT_SIZE = 50
TITLE_MIN_FONT_SIZE = 30
TITLE_MAX_WIDTH = 1450
ARTIST_FONT_SIZE = 30
TITLE_Y = 465
ARTIST_Y = 525
```

Long titles automatically shrink and, if necessary, truncate with an ellipsis.

## Progress bar

```python
PROGRESS_WIDTH = 1100
PROGRESS_HEIGHT = 18
PROGRESS_BACKGROUND = (65, 65, 65)
PROGRESS_FOREGROUND = (255, 255, 255)
```

Colors use RGB tuples with values from `0` to `255`.

## Premium background

```python
BACKGROUND_WORK_SIZE = (640, 360)
BACKGROUND_BLUR = 32
BACKGROUND_SECOND_BLUR = 10
BACKGROUND_SATURATION = 1.25
BACKGROUND_CONTRAST = 1.08
BACKGROUND_BRIGHTNESS = 0.43
BACKGROUND_DITHER = True
```

The background is generated at a smaller working resolution and then enlarged. This reduces processing time on the Pi Zero 2 W.

Higher blur values soften the background. Saturation, contrast, and brightness use Pillow enhancement factors.

## Performance logging

```python
PERFORMANCE_LOGGING = True
PERFORMANCE_REPORT_SECONDS = 5.0
```

Disable performance reporting for quieter logs:

```python
PERFORMANCE_LOGGING = False
```

## Fonts

```python
FONT_REGULAR = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans.ttf"
)

FONT_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)
```

The installer installs DejaVu fonts automatically.

Custom fonts must exist on the Pi and be readable by the `nowframe` service account.
