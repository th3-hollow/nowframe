import os

from PIL import Image, ImageFilter, ImageEnhance


class BackgroundCache:

    def __init__(self):
        self.last_album = None
        self.last_modified = None
        self.background = None


    def generate(self, album_path, size):

        try:
            modified = os.path.getmtime(album_path)

            if (
                album_path == self.last_album
                and modified == self.last_modified
            ):
                return self.background

            album = Image.open(album_path).convert("RGB")

            album = album.resize(size)

            background = album.filter(
                ImageFilter.GaussianBlur(60)
            )

            background = ImageEnhance.Brightness(
                background
            ).enhance(0.25)

            self.background = background
            self.last_album = album_path
            self.last_modified = modified

            print("Premium background updated")

            return background

        except Exception as e:
            print("Background error:", e)
            return None
