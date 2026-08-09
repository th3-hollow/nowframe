# Troubleshooting

## Check the service first

```bash
sudo systemctl status nowframe.service --no-pager
```

View recent logs:

```bash
sudo journalctl -u nowframe.service -n 100 --no-pager
```

Follow live logs:

```bash
sudo journalctl -u nowframe.service -f
```

Restart NowFrame:

```bash
sudo systemctl restart nowframe.service
```

## Service does not start

Verify that the environment file exists:

```bash
sudo ls -l /etc/nowframe.env
```

Verify that the application and virtual environment exist:

```bash
sudo ls -l /opt/nowframe/nowframe.py
sudo ls -l /opt/nowframe/.venv/bin/python
```

Check Python files:

```bash
sudo -u nowframe \
    /opt/nowframe/.venv/bin/python \
    -m py_compile \
    /opt/nowframe/nowframe.py \
    /opt/nowframe/config.py
```

Check installed Python packages:

```bash
sudo -u nowframe \
    /opt/nowframe/.venv/bin/pip \
    check
```

## Display remains blank

Confirm the framebuffer exists:

```bash
ls -l /dev/fb0
```

Confirm its resolution:

```bash
cat /sys/class/graphics/fb0/virtual_size
```

Confirm its color depth:

```bash
cat /sys/class/graphics/fb0/bits_per_pixel
```

NowFrame currently expects:

```text
1920,1080
16
```

Other resolutions can be configured in `config.py`, but the framebuffer must use 16-bit RGB565 output.

Confirm the service account belongs to the `video` group:

```bash
id nowframe
```

The output should include:

```text
video
```

If needed:

```bash
sudo usermod -aG video nowframe
sudo systemctl restart nowframe.service
```

## Spotify authorization fails

Confirm that `/etc/nowframe.env` contains:

```text
SPOTIPY_CLIENT_ID
SPOTIPY_CLIENT_SECRET
SPOTIPY_REDIRECT_URI
```

Do not post the values publicly.

The redirect URI must exactly match the Spotify developer application:

```text
http://127.0.0.1:8888/callback
```

Use `127.0.0.1`, not `localhost`.

Run authorization again:

```bash
sudo runuser -u nowframe -- sh -c '
    set -a
    . /etc/nowframe.env
    set +a
    cd /opt/nowframe
    HOME=/var/lib/nowframe \
        .venv/bin/python \
        scripts/authorize_spotify.py
'
```

If Spotify redirects the browser to a page that cannot load, copy the complete URL from the browser address bar and paste it into the terminal prompt.

## Spotify login needs to be reset

Stop the service:

```bash
sudo systemctl stop nowframe.service
```

Remove only the dedicated service account’s Spotify token cache:

```bash
sudo rm -f \
    /var/lib/nowframe/.nowframe_spotify_cache
```

Run the authorization helper again, then start the service:

```bash
sudo systemctl start nowframe.service
```

## No song appears

NowFrame displays the active Spotify playback session. Start playback on a phone, computer, speaker, or another Spotify device.

Check the logs for:

```text
Now playing:
```

If playback is paused, NowFrame waits for the configured grace period and then enters its selected idle mode.

## Album artwork does not change

Check the runtime artwork timestamp:

```bash
stat /tmp/nowframe/album.jpg
```

Change songs and check it again. The modification time should change.

Check recent logs for:

```text
Album art updated
```

The runtime artwork belongs in `/tmp/nowframe`. It should not modify the Git working tree.

Restarting the service forces the current artwork to be downloaded again:

```bash
sudo systemctl restart nowframe.service
```

## Spotify Code does not appear

Confirm it is enabled:

```python
SPOTIFY_CODE_ENABLED = True
```

Check generated files:

```bash
find /tmp/nowframe \
    -maxdepth 1 \
    -type f \
    -name 'spotify_code_*.png'
```

Check logs for:

```text
Generating Spotify Code...
Spotify Code generated
```

If generation fails, NowFrame continues rendering without the code. Confirm internet access and inspect the logged error.

Spotify Codes are downloaded from Spotify’s hosted scannables service.

## Spotify Code does not scan

Try the following:

- Hold the phone parallel to the display.
- Reduce reflections and glare.
- Keep the complete code visible.
- Try a slightly greater scanning distance.
- Confirm the code has strong contrast with the background.
- Increase `SPOTIFY_CODE_WIDTH` and `SPOTIFY_CODE_HEIGHT` if needed.

The transparent renderer normally uses white over dark backgrounds and black over bright backgrounds.

## Background or glow does not update

Check for:

```text
Generating premium background...
Premium smooth background updated
Album glow:
```

Confirm:

```python
RENDERER_MODE = "premium"
GLOW_ENABLED = True
```

Classic mode does not use the Premium renderer’s adaptive glow or Spotify Code layout.

## Performance is slow

The tested Pi Zero 2 W normally performs progress-region updates at approximately 16–17 FPS.

Potential adjustments:

```python
CROSSFADE_STEPS = 4
BACKGROUND_WORK_SIZE = (480, 270)
GLOW_ENABLED = False
PERFORMANCE_LOGGING = False
```

Lower crossfade steps reduce framebuffer writes. A smaller background working size reduces image-processing cost.

Do not reduce `SPOTIFY_POLL_INTERVAL` aggressively because that increases Spotify API traffic.

## Network disconnects

NowFrame retains its last valid playback data during temporary Spotify or network failures and retries automatically.

Check logs for:

```text
Spotify unavailable:
Spotify connection restored
```

If recovery does not occur, test network access and restart:

```bash
sudo systemctl restart nowframe.service
```

## Git reports changing album artwork

Current versions store album artwork under:

```text
/tmp/nowframe/album.jpg
```

If an older installation still modifies `assets/images/album.jpg`, update NowFrame and rerun the installer.

## Show the installed service

```bash
sudo systemctl cat nowframe.service
```

The public installation uses:

```text
Application: /opt/nowframe
Credentials: /etc/nowframe.env
Service home: /var/lib/nowframe
Service account: nowframe
```

Older manual installations may use different paths.

## Restore from an SD-card image

A full SD-card image can be written to a replacement card using an imaging utility.

The replacement card must contain at least as many actual bytes as the original card. Two cards with the same advertised capacity can differ slightly, so an identical model or larger card is safest.

SD-card images contain credentials and authentication data. Keep them private.

## Spotify quota or rate limit reached

When NowFrame reports that a Spotify quota or rate limit was reached, Spotify has temporarily refused further Web API requests. NowFrame automatically honors the Retry-After response and pauses API polling for the required period.

Do not repeatedly restart the service or create another client ID to evade the limit. Spotify Development Mode quotas are shared at the developer-account level. Wait for the reported cooldown to expire and keep SPOTIFY_POLL_INTERVAL at the recommended 10.0 seconds or higher.

The progress bar is calculated locally, so the longer polling interval does not make its animation less smooth.
