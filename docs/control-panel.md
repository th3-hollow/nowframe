# NowFrame Control Panel

NowFrame Control is an optional local web interface for
configuring and monitoring NowFrame from a phone or computer
on the same trusted network.

Default address: http://nowframe.local:8080

## Pages

### Status

Shows service health, Spotify API requests, failures,
rate-limit events, playback-state counts, and seven days
of usage history.

### Devices

Discovers devices available through Spotify Connect.
Checked devices are shown by NowFrame. Unchecked devices
can still play music, but their playback is hidden.

Spotify may only report a device while its app is open
or after it was used recently. Previously discovered
devices remain listed when offline.

### Display

Controls Away mode, idle behavior, clock visibility,
pause grace time, idle-to-black timeout, and clock
background darkening.

### Background

Selects Current, Vivid, Soft, or Dark rendering and
controls the album-art glow.

### Polling

Provides Responsive, Balanced, and Low API Usage presets,
plus custom playing, paused, idle, and blocked-device
intervals. Balanced (4 / 10 / 15 / 30) is the tested default.

### Plugins

Controls Spotify Code display and provides space for future
plugin settings. Local spotify:local tracks automatically
skip Spotify Code generation.

## Storage

- Settings: /etc/nowframe/control.env
- Device history: /etc/nowframe/devices.json
- Private credentials: /etc/nowframe/spotify.env
- Token cache: /var/lib/nowframe-control/spotify-cache
- Usage statistics: /var/lib/nowframe/spotify_api_usage.csv

## Security model

The web service runs as the dedicated nowframe-control
account. Application code and its virtual environment are
installed beneath /opt/nowframe-control.

The service can write only its settings and state directories.
It cannot run arbitrary root commands. Only the exact validate
and restart helper actions are permitted.

New settings are validated before activation. If NowFrame
fails to restart, the previous settings are restored.

The panel listens on the LAN and does not currently provide
TLS. Use it only on a trusted local network.

## Development

Install requirements-dev.txt, then run: python -m pytest

Tests use temporary files and mocked restarts. They do not
modify the live /etc/nowframe configuration.
