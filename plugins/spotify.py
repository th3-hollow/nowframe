import os
import time

import requests
import spotipy

from PIL import Image

from spotipy.oauth2 import SpotifyOAuth

from config import (
    SPOTIFY_POLL_INTERVAL,
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

        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=[
                    "user-read-playback-state",
                    "user-read-currently-playing"
                ],
                redirect_uri="http://127.0.0.1:8888/callback",
                cache_path="/root/.nowframe_spotify_cache",
                open_browser=False
            )
        )

        self.last_image = None
        self.last_track = None

        self.cached_data = None

        self.last_poll = 0.0

        self.poll_interval = (
            SPOTIFY_POLL_INTERVAL
        )

        self.progress_ms = 0
        self.duration_ms = 1

        self.progress_timestamp = (
            time.monotonic()
        )


    def download_album(
        self,
        url
    ):

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


            # Write new image to temporary file first.

            with open(
                temp_path,
                "wb"
            ) as f:

                f.write(
                    response.content
                )


            # Validate that Pillow can actually
            # open and understand the image.

            with Image.open(
                temp_path
            ) as image:

                image.verify()


            # Replace the old artwork only after
            # the new image has been validated.

            os.replace(
                temp_path,
                ALBUM_CACHE_PATH
            )


            self.last_image = url

            print(
                "Album art updated"
            )


        except Exception as e:

            print(
                "Album download error:",
                e
            )


            # Remove incomplete temporary file,
            # but preserve the last valid album.

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

        try:

            current = (
                self.spotify.current_playback()
            )


        except Exception as e:

            print(
                "Spotify API error:",
                e
            )

            return


        now = time.monotonic()


        if (
            not current
            or
            not current.get("item")
        ):

            self.cached_data = {
                "playing": False,
                "title": "",
                "artist": "",
                "album": "",
                "album_url": None
            }

            self.progress_ms = 0
            self.duration_ms = 1

            self.progress_timestamp = now

            return


        track = current["item"]


        images = (
            track["album"].get(
                "images",
                []
            )
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


        if (
            track["id"]
            !=
            self.last_track
        ):

            print(
                "Now playing:"
            )

            print(
                track["name"]
            )

            print(
                track["artists"][0]["name"]
            )

            self.last_track = (
                track["id"]
            )


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

            "title": (
                track["name"]
            ),

            "artist": (
                track["artists"][0]["name"]
            ),

            "album": (
                track["album"]["name"]
            ),

            "album_url": (
                image_url
            )
        }


    def get_data(self):

        now = time.monotonic()


        if (
            self.cached_data is None
            or
            now - self.last_poll
            >=
            self.poll_interval
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
                "progress": 0.0
            }


        data = (
            self.cached_data.copy()
        )


        progress_ms = (
            self.progress_ms
        )


        if data["playing"]:

            elapsed_ms = (
                now
                -
                self.progress_timestamp
            ) * 1000.0

            progress_ms += (
                elapsed_ms
            )


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
