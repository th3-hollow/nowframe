import os
import time

import requests
import spotipy

from urllib.parse import unquote

from PIL import Image
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from config import (
    SPOTIFY_POLL_INTERVAL,
    SPOTIFY_PAUSED_POLL_INTERVAL,
    SPOTIFY_IDLE_POLL_INTERVAL,
    SPOTIFY_DEVICE_FILTER_ENABLED,
    SPOTIFY_ALLOWED_DEVICES,
    SPOTIFY_UNAPPROVED_DEVICE_POLL_INTERVAL,
    SPOTIFY_USAGE_LOG_ENABLED,
    SPOTIFY_USAGE_LOG_PATH,
    SPOTIFY_USAGE_LOG_FLUSH_SECONDS,
    SPOTIFY_REQUEST_TIMEOUT,
    RUNTIME_CACHE_DIR,
    ALBUM_CACHE_PATH
)

from core.v2.spotify_usage import SpotifyUsageTracker


def environment_seconds(
    name,
    default
):

    value = os.environ.get(
        name
    )


    if value is None:
        return float(default)


    try:

        return max(
            float(value),
            1.0
        )


    except ValueError:

        print(
            f"Invalid {name}; using {default}"
        )

        return float(default)


class SpotifyPlugin:

    def __init__(self):

        os.makedirs(
            RUNTIME_CACHE_DIR,
            exist_ok=True
        )

        auth_cache_path = os.path.abspath(
            os.path.expanduser(
                os.environ.get(
                    "NOWFRAME_SPOTIFY_CACHE_PATH",
                    "~/.nowframe_spotify_cache"
                )
            )
        )

        os.makedirs(
            os.path.dirname(
                auth_cache_path
            ),
            exist_ok=True
        )

        redirect_uri = os.environ.get(
            "SPOTIPY_REDIRECT_URI",
            "http://127.0.0.1:8888/callback"
        )

        encoded_devices = os.environ.get(
            "NOWFRAME_ALLOWED_SPOTIFY_DEVICES_ENCODED"
        )

        private_devices = os.environ.get(
            "NOWFRAME_ALLOWED_SPOTIFY_DEVICES",
            ""
        )

        if encoded_devices is not None:

            self.allowed_devices = tuple(
                unquote(name).strip()
                for name in encoded_devices.split(",")
                if name.strip()
            )

        elif private_devices.strip():

            self.allowed_devices = tuple(
                name.strip()
                for name in private_devices.split(",")
                if name.strip()
            )

        else:

            self.allowed_devices = tuple(
                SPOTIFY_ALLOWED_DEVICES
            )

        private_filter_enabled = os.environ.get(
            "NOWFRAME_SPOTIFY_DEVICE_FILTER_ENABLED"
        )

        if private_filter_enabled is None:

            self.device_filter_enabled = bool(
                SPOTIFY_DEVICE_FILTER_ENABLED
            )

        else:

            self.device_filter_enabled = (
                private_filter_enabled.strip().lower()
                in
                (
                    "1",
                    "true",
                    "yes",
                    "on"
                )
            )

        self.allowed_device_keys = {
            name.casefold()
            for name in self.allowed_devices
        }

        self.usage = SpotifyUsageTracker(
            SPOTIFY_USAGE_LOG_ENABLED,
            SPOTIFY_USAGE_LOG_PATH,
            SPOTIFY_USAGE_LOG_FLUSH_SECONDS
        )

        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=[
                    "user-read-playback-state",
                    "user-read-currently-playing"
                ],
                redirect_uri=redirect_uri,
                cache_path=auth_cache_path,
                open_browser=False
            ),
            requests_timeout=SPOTIFY_REQUEST_TIMEOUT,
            retries=0,
            status_retries=0
        )

        self.last_image = None
        self.last_track = None
        self.last_device_name = None

        # Cached Spotify state
        self.cached_data = None

        # Last time Spotify API was queried
        self.last_poll = 0.0

        # Poll intervals, with optional private
        # environment overrides.

        self.poll_interval = environment_seconds(
            "NOWFRAME_SPOTIFY_POLL_INTERVAL",
            SPOTIFY_POLL_INTERVAL
        )

        self.paused_poll_interval = environment_seconds(
            "NOWFRAME_SPOTIFY_PAUSED_POLL_INTERVAL",
            SPOTIFY_PAUSED_POLL_INTERVAL
        )

        self.idle_poll_interval = environment_seconds(
            "NOWFRAME_SPOTIFY_IDLE_POLL_INTERVAL",
            SPOTIFY_IDLE_POLL_INTERVAL
        )

        self.unapproved_poll_interval = environment_seconds(
            "NOWFRAME_SPOTIFY_UNAPPROVED_POLL_INTERVAL",
            SPOTIFY_UNAPPROVED_DEVICE_POLL_INTERVAL
        )

        # Smooth local progress tracking
        self.progress_ms = 0
        self.duration_ms = 1
        self.progress_timestamp = time.monotonic()

        # Network recovery and quota state
        self.spotify_available = True
        self.retry_after_until = 0.0


    def download_album(self, url):

        if url == self.last_image:
            return

        temp_path = (
            ALBUM_CACHE_PATH
            +
            ".tmp"
        )

        try:

            response = requests.get(
                url,
                timeout=SPOTIFY_REQUEST_TIMEOUT
            )

            response.raise_for_status()

            with open(
                temp_path,
                "wb"
            ) as file:

                file.write(
                    response.content
                )

            with Image.open(
                temp_path
            ) as image:

                image.verify()

            os.replace(
                temp_path,
                ALBUM_CACHE_PATH
            )

            self.last_image = url

            print("Album art updated")

        except Exception as e:

            print(
                "Album download error:",
                e
            )

            try:

                if os.path.exists(
                    temp_path
                ):

                    os.remove(
                        temp_path
                    )

            except Exception:

                pass


    def _device_allowed(
        self,
        device_name
    ):

        if not self.device_filter_enabled:

            return True

        return (
            device_name.casefold()
            in
            self.allowed_device_keys
        )


    def _response_state(
        self,
        current,
        device_allowed
    ):

        if not current or not current.get("item"):
            return "idle"

        if not device_allowed:
            return "unapproved"

        if current.get("is_playing", False):
            return "playing"

        return "paused"


    def poll_spotify(self):

        now = time.monotonic()

        try:

            current = self.spotify.current_playback()

            device = (
                (current or {}).get("device")
                or
                {}
            )

            device_name = str(
                device.get("name")
                or
                ""
            )

            device_allowed = (
                self._device_allowed(
                    device_name
                )
            )

            if device_name != self.last_device_name:

                print(
                    "Spotify device:",
                    device_name or "none",
                    "| approved:",
                    device_allowed
                )

                self.last_device_name = device_name

            response_state = (
                self._response_state(
                    current,
                    device_allowed
                )
            )

            self.usage.record_success(
                response_state
            )

            if not self.spotify_available:
                print("Spotify connection restored")

            self.spotify_available = True
            self.retry_after_until = 0.0


        except SpotifyException as error:

            if error.http_status == 429:

                retry_header = (
                    error.headers.get(
                        "Retry-After"
                    )
                    or
                    error.headers.get(
                        "retry-after"
                    )
                    or
                    60
                )

                try:

                    retry_after = max(
                        60,
                        int(
                            float(
                                retry_header
                            )
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    retry_after = 60


                self.retry_after_until = (
                    now
                    +
                    retry_after
                )

                quota_exceeded = (
                    error.reason
                    ==
                    "QUOTA_EXCEEDED"
                )

                self.usage.record_error(
                    quota=quota_exceeded,
                    rate_limit=(
                        not quota_exceeded
                    ),
                    retry_after=retry_after
                )

                reason = (
                    f" ({error.reason})"
                    if error.reason
                    else
                    ""
                )

                print(
                    "Spotify quota/rate limit reached"
                    f"{reason}. "
                    "API polling paused for "
                    f"{retry_after} seconds."
                )

            elif self.spotify_available:

                print(
                    "Spotify unavailable:",
                    error
                )


            if error.http_status != 429:

                self.usage.record_error()


            self.spotify_available = False

            return


        except Exception as error:

            self.usage.record_error()

            if self.spotify_available:

                print(
                    "Spotify unavailable:",
                    error
                )

            self.spotify_available = False

            return


        if not current or not current.get("item"):

            self.cached_data = {
                "playing": False,
                "title": "",
                "artist": "",
                "album": "",
                "album_url": None,
                "uri": None,
                "source_playing": False,
                "device_name": "",
                "device_allowed": True
            }

            self.progress_ms = 0
            self.duration_ms = 1
            self.progress_timestamp = now

            return


        track = current["item"]


        images = track["album"].get(
            "images",
            []
        )


        image_url = (
            images[0]["url"]
            if images
            else None
        )


        if image_url and device_allowed:

            self.download_album(
                image_url
            )


        if (
            device_allowed
            and
            track["id"] != self.last_track
        ):

            print("Now playing:")
            print(track["name"])
            print(track["artists"][0]["name"])

            self.last_track = track["id"]


        self.progress_ms = (
            current.get(
                "progress_ms"
            )
            or 0
        )


        self.duration_ms = max(
            track.get(
                "duration_ms",
                1
            ),
            1
        )


        self.progress_timestamp = now


        self.cached_data = {

            "playing": (
                bool(
                    current.get(
                        "is_playing",
                        False
                    )
                )
                and
                device_allowed
            ),

            "title": track["name"],

            "artist": track["artists"][0]["name"],

            "album": track["album"]["name"],

            "album_url": image_url,

            # Spotify Code uses this
            "uri": track["uri"],

            "source_playing": bool(
                current.get(
                    "is_playing",
                    False
                )
            ),

            "device_name": device_name,
            "device_allowed": device_allowed
        }



    def _current_poll_interval(self):

        if self.cached_data is None:
            return self.poll_interval

        if self.cached_data.get("device_allowed") is False:
            return self.unapproved_poll_interval

        if self.cached_data.get("playing"):
            return self.poll_interval

        if self.cached_data.get("uri"):
            return self.paused_poll_interval

        return self.idle_poll_interval


    def get_data(self):

        now = time.monotonic()


        if (
            now >= self.retry_after_until
            and
            (
                self.cached_data is None
                or
                now - self.last_poll
                >=
                self._current_poll_interval()
            )
        ):

            self.poll_spotify()

            self.last_poll = now


        if self.cached_data is None:

            return {
                "playing": False,
                "title": "",
                "artist": "",
                "album": "",
                "album_url": None,
                "uri": None,
                "progress": 0.0
            }


        data = self.cached_data.copy()


        progress_ms = self.progress_ms


        if data["playing"]:

            elapsed_ms = (
                now - self.progress_timestamp
            ) * 1000.0

            progress_ms += elapsed_ms


        progress_ms = min(
            progress_ms,
            self.duration_ms
        )


        data["progress"] = (
            progress_ms
            /
            self.duration_ms
        )


        return data
