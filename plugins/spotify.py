import os
import time

import requests
import spotipy

from PIL import Image
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from config import (
    SPOTIFY_POLL_INTERVAL,
    SPOTIFY_PAUSED_POLL_INTERVAL,
    SPOTIFY_IDLE_POLL_INTERVAL,
    SPOTIFY_REQUEST_TIMEOUT,
    RUNTIME_CACHE_DIR,
    ALBUM_CACHE_PATH
)


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

        # Cached Spotify state
        self.cached_data = None

        # Last time Spotify API was queried
        self.last_poll = 0.0

        # Poll interval
        self.poll_interval = SPOTIFY_POLL_INTERVAL

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


    def poll_spotify(self):

        now = time.monotonic()

        try:

            current = self.spotify.current_playback()

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


            self.spotify_available = False

            return


        except Exception as error:

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
                "uri": None
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


        if image_url:

            self.download_album(
                image_url
            )


        if track["id"] != self.last_track:

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

            "playing": bool(
                current.get(
                    "is_playing",
                    False
                )
            ),

            "title": track["name"],

            "artist": track["artists"][0]["name"],

            "album": track["album"]["name"],

            "album_url": image_url,

            # Spotify Code uses this
            "uri": track["uri"]
        }



    def _current_poll_interval(self):

        if self.cached_data is None:
            return self.poll_interval

        if self.cached_data.get("playing"):
            return self.poll_interval

        if self.cached_data.get("uri"):
            return SPOTIFY_PAUSED_POLL_INTERVAL

        return SPOTIFY_IDLE_POLL_INTERVAL


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
