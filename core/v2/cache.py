import os
import numpy as np

from PIL import (
    Image,
    ImageFilter,
    ImageEnhance,
    ImageOps
)

from core.v2.colors import ColorExtractor

from config import (
    BACKGROUND_WORK_SIZE,
    BACKGROUND_BLUR,
    BACKGROUND_SECOND_BLUR,
    BACKGROUND_SATURATION,
    BACKGROUND_CONTRAST,
    BACKGROUND_BRIGHTNESS,
    BACKGROUND_DITHER
)


class BackgroundCache:

    def __init__(self):

        self.last_album = None
        self.last_modified = None

        self.background = None
        self.album_image = None
        self.palette = None

        self.colors = ColorExtractor()


    def add_rgb565_dither(
        self,
        image
    ):

        array = np.asarray(
            image,
            dtype=np.int16
        ).copy()

        height, width, channels = (
            array.shape
        )

        rng = np.random.default_rng(
            12345
        )

        red_noise = rng.integers(
            -4,
            5,
            size=(height, width)
        )

        green_noise = rng.integers(
            -2,
            3,
            size=(height, width)
        )

        blue_noise = rng.integers(
            -4,
            5,
            size=(height, width)
        )

        array[:, :, 0] += red_noise
        array[:, :, 1] += green_noise
        array[:, :, 2] += blue_noise

        array = np.clip(
            array,
            0,
            255
        ).astype(
            np.uint8
        )

        return Image.fromarray(
            array,
            "RGB"
        )


    def generate(
        self,
        album_path,
        size
    ):

        try:

            modified = os.path.getmtime(
                album_path
            )


            if (
                album_path == self.last_album
                and
                modified == self.last_modified
            ):

                return self.background


            print(
                "Generating premium background..."
            )


            # =========================
            # Load album ONCE
            # =========================

            album = Image.open(
                album_path
            ).convert("RGB")

            self.album_image = (
                album.copy()
            )


            # =========================
            # Extract palette ONCE
            # =========================

            self.palette = (
                self.colors.get_colors_from_image(
                    album,
                    count=5
                )
            )

            print(
                "Album palette:",
                self.palette
            )


            # =========================
            # Background
            # =========================

            work_size = BACKGROUND_WORK_SIZE


            background = ImageOps.fit(
                album,
                work_size,
                method=Image.Resampling.LANCZOS
            )


            background = background.filter(
                ImageFilter.GaussianBlur(
                    BACKGROUND_BLUR
                )
            )


            background = ImageEnhance.Color(
                background
            ).enhance(
                BACKGROUND_SATURATION
            )


            background = ImageEnhance.Contrast(
                background
            ).enhance(
                BACKGROUND_CONTRAST
            )


            background = ImageEnhance.Brightness(
                background
            ).enhance(
                BACKGROUND_BRIGHTNESS
            )


            background = background.filter(
                ImageFilter.GaussianBlur(
                    BACKGROUND_SECOND_BLUR
                )
            )


            # Bilinear is plenty after such
            # a heavy blur and is cheaper
            # than bicubic.

            background = background.resize(
                size,
                Image.Resampling.BILINEAR
            )


            if BACKGROUND_DITHER:

                background = (
                    self.add_rgb565_dither(
                        background
                    )
                )


            self.background = background

            self.last_album = album_path
            self.last_modified = modified


            print(
                "Premium smooth background updated"
            )


            return background


        except Exception as e:

            print(
                "Background error:",
                e
            )

            return self.background
