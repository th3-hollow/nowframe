import time
import requests
import spotipy

from spotipy.oauth2 import SpotifyOAuth

from config import (
    SPOTIFY_POLL_INTERVAL,
    SPOTIFY_REQUEST_TIMEOUT
)


ALBUM_PATH = "assets/images/album.jpg"


class SpotifyPlugin:

    def __init__(self):

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

        # Network recovery state
        self.spotify_available = True


    def download_album(self, url):

        if url == self.last_image:
            return

        try:

            response = requests.get(
                url,
                timeout=SPOTIFY_REQUEST_TIMEOUT
            )

            response.raise_for_status()

            with open(
                ALBUM_PATH,
                "wb"
            ) as f:
                f.write(response.content)

            self.last_image = url

            print("Album art updated")

        except Exception as e:

            print(
                "Album download error:",
                e
            )


    def poll_spotify(self):

        try:

            current = self.spotify.current_playback()

            if not self.spotify_available:
                print("Spotify connection restored")

            self.spotify_available = True


        except Exception as e:

            if self.spotify_available:
                print(
                    "Spotify unavailable:",
                    e
                )

            self.spotify_available = False

            return


        now = time.monotonic()


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



    def get_data(self):

        now = time.monotonic()


        if (
            self.cached_data is None
            or
            now - self.last_poll >= self.poll_interval
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
