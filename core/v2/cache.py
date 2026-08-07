import os
import numpy as np

from PIL import (
    Image,
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


    def add_rgb565_dither(self, image):

        """
        Add extremely subtle noise before RGB565 conversion.

        RGB565 has relatively large color steps:
        R = 5 bits
        G = 6 bits
        B = 5 bits

        Tiny noise helps break visible gradient bands
        without making the image look grainy.
        """

        array = np.asarray(
            image,
            dtype=np.int16
        ).copy()

        height, width, channels = array.shape

        rng = np.random.default_rng(
            12345
        )

        # Red and blue have larger RGB565 steps,
        # so they receive slightly stronger dithering.

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


    def generate(self, album_path, size):

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


            # =====================================
            # Read album palette
            # =====================================

            palette = self.colors.get_colors(
                album_path,
                count=5
            )

            print(
                "Album palette:",
                palette
            )


            # =====================================
            # Work at medium resolution
            #
            # 320x180 was contributing to the
            # large contour-like shapes.
            #
            # 640x360 is still inexpensive because
            # this runs only when the album changes.
            # =====================================

            work_size = (
                640,
                360
            )


            album = Image.open(
                album_path
            ).convert(
                "RGB"
            )


            # Fill the entire 16:9 frame naturally
            # using the actual album artwork.

            background = ImageOps.fit(
                album,
                work_size,
                method=Image.Resampling.LANCZOS
            )


            # =====================================
            # Blur the actual artwork
            # =====================================

            background = background.filter(
                ImageFilter.GaussianBlur(
                    32
                )
            )


            # =====================================
            # Slightly enrich album colors
            # =====================================

            background = ImageEnhance.Color(
                background
            ).enhance(
                1.25
            )


            # Slight contrast boost keeps the
            # blurred background from looking flat.

            background = ImageEnhance.Contrast(
                background
            ).enhance(
                1.08
            )


            # =====================================
            # Darken
            #
            # We want atmosphere, not competition
            # with the album art and text.
            # =====================================

            background = ImageEnhance.Brightness(
                background
            ).enhance(
                0.43
            )


            # =====================================
            # Soft second blur
            #
            # Helps remove remaining structures
            # after contrast/color processing.
            # =====================================

            background = background.filter(
                ImageFilter.GaussianBlur(
                    10
                )
            )


            # =====================================
            # Upscale cleanly to 1920x1080
            # =====================================

            background = background.resize(
                size,
                Image.Resampling.BICUBIC
            )


            # =====================================
            # RGB565-friendly dithering
            #
            # Do this AFTER upscaling so the dither
            # exists at the physical pixel level.
            # =====================================

            background = self.add_rgb565_dither(
                background
            )


            # =====================================
            # Cache
            # =====================================

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
