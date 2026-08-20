from io import BytesIO

import requests

from PIL import Image

import plugins.spotify as spotify_module


class Response:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None


def jpeg_bytes():
    output = BytesIO()

    Image.new(
        "RGB",
        (8, 8),
        (20, 40, 60),
    ).save(
        output,
        format="JPEG",
    )

    return output.getvalue()


def plugin_without_network():
    plugin = (
        spotify_module
        .SpotifyPlugin
        .__new__(
            spotify_module.SpotifyPlugin
        )
    )

    plugin.last_image = None
    plugin.album_revision = 0

    return plugin


def test_verified_artwork_increments_revision(
    monkeypatch,
    tmp_path,
):
    album_path = tmp_path / "album.jpg"

    monkeypatch.setattr(
        spotify_module,
        "ALBUM_CACHE_PATH",
        str(album_path),
    )

    monkeypatch.setattr(
        spotify_module.requests,
        "get",
        lambda *args, **kwargs: Response(
            jpeg_bytes()
        ),
    )

    plugin = plugin_without_network()

    assert plugin.download_album(
        "https://example.test/album.jpg"
    ) is True

    assert album_path.exists()
    assert plugin.album_revision == 1

    assert plugin.download_album(
        "https://example.test/album.jpg"
    ) is True

    assert plugin.album_revision == 1


def test_failed_artwork_keeps_revision(
    monkeypatch,
    tmp_path,
):
    album_path = tmp_path / "album.jpg"

    monkeypatch.setattr(
        spotify_module,
        "ALBUM_CACHE_PATH",
        str(album_path),
    )

    def timeout(*args, **kwargs):
        raise requests.Timeout(
            "simulated timeout"
        )

    monkeypatch.setattr(
        spotify_module.requests,
        "get",
        timeout,
    )

    plugin = plugin_without_network()

    assert plugin.download_album(
        "https://example.test/album.jpg"
    ) is None

    assert album_path.exists() is False
    assert plugin.album_revision == 0
    assert plugin.last_image is None


def test_spotify_refresh_runs_in_background():
    import time

    from concurrent.futures import (
        ThreadPoolExecutor,
    )

    from core.app import NowFrameApp

    class SlowSpotify:
        def refresh_if_due(self):
            time.sleep(0.2)

    app = NowFrameApp.__new__(
        NowFrameApp
    )

    app.spotify = SlowSpotify()

    app.spotify_executor = (
        ThreadPoolExecutor(
            max_workers=1
        )
    )

    app.spotify_future = None
    app.next_spotify_refresh_check = 0.0

    started = time.monotonic()

    app._refresh_spotify_async()

    elapsed = time.monotonic() - started

    assert elapsed < 0.1
    assert app.spotify_future is not None

    app.spotify_future.result(
        timeout=1
    )

    app.spotify_executor.shutdown(
        wait=True
    )


def test_new_artwork_revision_forces_full_render():
    from core.app import NowFrameApp

    data = {
        "playing": True,
        "title": "Same song",
        "artist": "Same artist",
        "album_url": "https://example.test/art.jpg",
        "album_ready": False,
        "album_revision": 2,
        "uri": "spotify:track:test",
        "progress": 0.5,
    }

    class Spotify:
        def get_cached_data(self):
            return data.copy()

    class Renderer:
        def __init__(self):
            self.full_rendered = False

        def create_frame(self):
            return "blank"

        def render(
            self,
            album_path,
            title,
            artist,
            progress,
            spotify_code_path=None,
        ):
            self.full_rendered = True
            return "rendered"

        def render_progress_region(self, progress):
            raise AssertionError(
                "Artwork change used progress-only render"
            )

    class SpotifyCode:
        def get_code(self, uri):
            raise AssertionError(
                "Code download should be skipped "
                "while artwork is unavailable"
            )

    app = NowFrameApp.__new__(
        NowFrameApp
    )

    app.away_mode = False
    app.spotify = Spotify()
    app.renderer = Renderer()
    app.spotify_code = SpotifyCode()

    app._refresh_spotify_async = (
        lambda: None
    )

    app.last_mode = "playing"

    app.last_track_key = (
        data["title"],
        data["artist"],
        data["album_url"],
        data["uri"],
    )

    app.last_artwork_revision = 1
    app.pause_started = None
    app.idle_started = None

    result = app.create_update()

    assert result["type"] == "full"
    assert result["image"] == "rendered"
    assert result["transition"] is None
    assert app.renderer.full_rendered is True
    assert app.last_artwork_revision == 2
