import requests
import spotipy

from spotipy.oauth2 import SpotifyOAuth


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


    def download_album(self, url):

        if url == self.last_image:
            return


        try:

            image = requests.get(
                url,
                timeout=10
            ).content


            with open(
                ALBUM_PATH,
                "wb"
            ) as f:

                f.write(image)


            self.last_image = url

            print("Album art updated")


        except Exception as e:

            print(
                "Album download error:",
                e
            )



    def get_data(self):

        current = self.spotify.current_playback()


        if not current or not current.get("item"):

            return {
                "playing": False,
                "title": "",
                "artist": "",
                "album": "",
                "progress": 0
            }



        track = current["item"]


        image_url = track["album"]["images"][0]["url"]


        self.download_album(
            image_url
        )


        if track["id"] != self.last_track:

            print("Now playing:")
            print(track["name"])
            print(track["artists"][0]["name"])

            self.last_track = track["id"]



        return {

            "playing": current["is_playing"],

            "title": track["name"],

            "artist": track["artists"][0]["name"],

            "album": track["album"]["name"],

            "album_url": image_url,

            "progress": (
                current["progress_ms"]
                /
                track["duration_ms"]
       )

  }
