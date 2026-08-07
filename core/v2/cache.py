import os

from PIL import (
    Image,
    ImageDraw,
    ImageFilter,
    ImageEnhance,
    ImageOps
)

from core.v2.colors import ColorExtractor


class BackgroundCache:

    def __init__(self):
        self.last_album = None
        self.last_modified = None
        self.background = None

        self.colors = ColorExtractor()


    def generate(self, album_path, size):

        try:
            modified = os.path.getmtime(album_path)

            if (
                album_path == self.last_album
                and modified == self.last_modified
            ):
                return self.background


            print("Generating premium background...")


            # Extract colors from album art

            palette = self.colors.get_colors(
                album_path,
                count=5
            )

            primary = palette[0]
            secondary = palette[1]
            accent = palette[2]

            print(
                "Album palette:",
                palette
            )


            # Render background at low resolution.
            # Much faster on Pi Zero 2 W.

            work_width = 320
            work_height = 180

            work_size = (
                work_width,
                work_height
            )


            # Blurred album layer

            album = Image.open(
                album_path
            ).convert("RGB")

            album_background = ImageOps.fit(
                album,
                work_size
            )

            album_background = album_background.filter(
                ImageFilter.GaussianBlur(18)
            )

            album_background = ImageEnhance.Brightness(
                album_background
            ).enhance(0.32)


            # Dynamic album-color glow

            glow = Image.new(
                "RGBA",
                work_size,
                (5, 5, 8, 255)
            )

            glow_draw = ImageDraw.Draw(
                glow,
                "RGBA"
            )


            # Primary color

            glow_draw.ellipse(
                (
                    -100,
                    -80,
                    260,
                    260
                ),
                fill=(
                    primary[0],
                    primary[1],
                    primary[2],
                    210
                )
            )


            # Secondary color

            glow_draw.ellipse(
                (
                    120,
                    -100,
                    430,
                    240
                ),
                fill=(
                    secondary[0],
                    secondary[1],
                    secondary[2],
                    180
                )
            )


            # Accent color

            glow_draw.ellipse(
                (
                    70,
                    70,
                    370,
                    280
                ),
                fill=(
                    accent[0],
                    accent[1],
                    accent[2],
                    150
                )
            )


            glow = glow.filter(
                ImageFilter.GaussianBlur(45)
            )

            glow = glow.convert("RGB")


            # Combine album blur and colors

            background = Image.blend(
                album_background,
                glow,
                0.55
            )


            # Darken for text readability

            dark_overlay = Image.new(
                "RGB",
                work_size,
                (0, 0, 0)
            )

            background = Image.blend(
                background,
                dark_overlay,
                0.28
            )


            # Upscale to display resolution

            background = background.resize(
                size,
                Image.Resampling.BILINEAR
            )


            # Cache completed background

            self.background = background
            self.last_album = album_path
            self.last_modified = modified

            print(
                "Premium dynamic background updated"
            )

            return background


        except Exception as e:

            print(
                "Background error:",
                e
            )

            return self.background
