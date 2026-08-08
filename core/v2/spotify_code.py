import os
import hashlib
import requests

from config import (
    RUNTIME_CACHE_DIR,
    SPOTIFY_CODE_WIDTH
)


CACHE_DIR = RUNTIME_CACHE_DIR


class SpotifyCodeGenerator:

    def __init__(self):

        os.makedirs(
            CACHE_DIR,
            exist_ok=True
        )

        self.last_uri = None
        self.last_path = None


    def _cache_path(self, uri):

        key = hashlib.md5(
            uri.encode()
        ).hexdigest()

        return os.path.join(
            CACHE_DIR,
            f"spotify_code_{key}.png"
        )


    def get_code(self, uri):

        if not uri:
            return None


        if uri == self.last_uri:
            return self.last_path


        path = self._cache_path(uri)


        if os.path.exists(path):

            self.last_uri = uri
            self.last_path = path

            return path


        print(
            "Generating Spotify Code..."
        )


        try:

            # Spotify Code endpoint
            url = (
                "https://scannables.scdn.co/uri/plain/png/"
                "000000/"
                "white/"
                f"{SPOTIFY_CODE_WIDTH}/"
                f"{uri}"
            )


            response = requests.get(
                url,
                timeout=10
            )

            response.raise_for_status()


            with open(
                path,
                "wb"
            ) as f:

                f.write(
                    response.content
                )


            print(
                "Spotify Code generated"
            )


            self.last_uri = uri
            self.last_path = path


            return path


        except Exception as e:

            print(
                "Spotify Code error:",
                e
            )

            return None
