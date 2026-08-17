import hashlib
import os

import requests

from PIL import Image

from config import (
    RUNTIME_CACHE_DIR,
    SPOTIFY_CODE_WIDTH,
    SPOTIFY_CODE_CACHE_LIMIT,
    SPOTIFY_REQUEST_TIMEOUT
)


CACHE_PREFIX = "spotify_code_"
CACHE_SUFFIX = ".png"


class SpotifyCodeGenerator:

    def __init__(self):

        os.makedirs(
            RUNTIME_CACHE_DIR,
            exist_ok=True
        )

        self.last_uri = None
        self.last_path = None


    def _cache_path(self, uri):

        # MD5 is used only for a short deterministic
        # cache filename, not for security.

        key = hashlib.md5(
            uri.encode()
        ).hexdigest()

        return os.path.join(
            RUNTIME_CACHE_DIR,
            (
                CACHE_PREFIX
                +
                key
                +
                CACHE_SUFFIX
            )
        )


    def _valid_image(self, path):

        try:

            with Image.open(path) as image:

                if image.format != "PNG":
                    return False

                image.verify()

            return True

        except Exception:

            return False


    def _cleanup_cache(self):

        try:

            paths = []

            for name in os.listdir(
                RUNTIME_CACHE_DIR
            ):

                if (
                    name.startswith(
                        CACHE_PREFIX
                    )
                    and
                    name.endswith(
                        CACHE_SUFFIX
                    )
                ):

                    path = os.path.join(
                        RUNTIME_CACHE_DIR,
                        name
                    )

                    if os.path.isfile(path):

                        paths.append(path)


            paths.sort(
                key=os.path.getmtime,
                reverse=True
            )

            limit = max(
                1,
                SPOTIFY_CODE_CACHE_LIMIT
            )

            for stale_path in paths[limit:]:

                try:

                    os.remove(
                        stale_path
                    )

                except OSError:

                    pass

        except OSError:

            pass


    def get_code(self, uri):

        if not uri:
            return None


        if uri.startswith("spotify:local:"):

            if uri != self.last_uri:

                print(
                    "Skipping Spotify Code for local track"
                )

            self.last_uri = uri
            self.last_path = None

            return None


        if (
            uri == self.last_uri
            and
            self.last_path
            and
            os.path.exists(
                self.last_path
            )
        ):

            return self.last_path


        path = self._cache_path(uri)


        if os.path.exists(path):

            if self._valid_image(path):

                os.utime(
                    path,
                    None
                )

                self.last_uri = uri
                self.last_path = path

                self._cleanup_cache()

                return path

            try:

                os.remove(path)

            except OSError:

                pass


        temp_path = (
            path
            +
            ".tmp"
        )

        print(
            "Generating Spotify Code..."
        )


        try:

            url = (
                "https://scannables.scdn.co/uri/plain/png/"
                "000000/"
                "white/"
                f"{SPOTIFY_CODE_WIDTH}/"
                f"{uri}"
            )

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


            if not self._valid_image(
                temp_path
            ):

                raise ValueError(
                    "Downloaded Spotify Code is not a valid PNG"
                )


            os.replace(
                temp_path,
                path
            )

            self.last_uri = uri
            self.last_path = path

            self._cleanup_cache()

            print(
                "Spotify Code generated"
            )

            return path


        except Exception as error:

            try:

                if os.path.exists(
                    temp_path
                ):

                    os.remove(
                        temp_path
                    )

            except OSError:

                pass

            print(
                "Spotify Code error:",
                error
            )

            return None
