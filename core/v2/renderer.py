import colorsys

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageOps,
    ImageFilter
)

from layouts.premium import PremiumLayout
from core.v2.cache import BackgroundCache


class PremiumRenderer:

    def __init__(
        self,
        width,
        height,
        font_regular,
        font_bold
    ):

        self.width = width
        self.height = height

        self.layout = PremiumLayout(
            width,
            height
        )

        self.cache = BackgroundCache()

        self.title_font = ImageFont.truetype(
            font_bold,
            50
        )

        self.artist_font = ImageFont.truetype(
            font_regular,
            30
        )

        self.clock_font = ImageFont.truetype(
            font_bold,
            120
        )

        self.base_frame = None

        self.bar_width = 1100
        self.bar_height = 18

        self.album_size = 300
        self.album_radius = 28


    def create_frame(self):

        return Image.new(
            "RGB",
            (
                self.width,
                self.height
            ),
            (0, 0, 0)
        )


    def draw_clock(
        self,
        image,
        data
    ):

        draw = ImageDraw.Draw(
            image
        )

        draw.text(
            (
                self.width // 2,
                self.height // 2
            ),
            data["time"],
            font=self.clock_font,
            fill="white",
            anchor="mm"
        )

        return image


    def choose_glow_color(
        self,
        palette
    ):

        """
        Choose an adaptive glow color.

        Strongly prefers useful album accent
        colors while rejecting near-black,
        white and dull grey colors.
        """

        best_color = None
        best_score = -1.0


        for color in palette:

            r, g, b = color

            rf = r / 255.0
            gf = g / 255.0
            bf = b / 255.0

            hue, saturation, value = (
                colorsys.rgb_to_hsv(
                    rf,
                    gf,
                    bf
                )
            )


            # Too dark to make a useful glow.

            if value < 0.12:
                continue


            # Prefer colors around medium
            # brightness instead of pure white.

            brightness_score = (
                1.0
                -
                abs(
                    value - 0.62
                )
            )


            # Saturation is deliberately weighted
            # heavily so a real album accent beats
            # white/grey background colors.

            score = (
                saturation * 2.5
                +
                brightness_score
            )


            if score > best_score:

                best_score = score
                best_color = color


        # Mostly monochrome album.
        #
        # Use a restrained neutral glow instead
        # of forcing an arbitrary color.

        if (
            best_color is None
            or
            best_score < 1.15
        ):

            return (
                115,
                115,
                115
            )


        r, g, b = best_color


        # Normalize perceived intensity.
        #
        # This prevents bright orange/red covers
        # from producing dramatically stronger
        # glows than dark blue/green covers.

        peak = max(
            r,
            g,
            b
        )

        target_peak = 165


        if peak > 0:

            scale = (
                target_peak
                /
                peak
            )

            r = int(
                min(
                    255,
                    r * scale
                )
            )

            g = int(
                min(
                    255,
                    g * scale
                )
            )

            b = int(
                min(
                    255,
                    b * scale
                )
            )


        return (
            r,
            g,
            b
        )


    def draw_album_art(
        self,
        frame
    ):

        try:

            if self.cache.album_image is None:
                return


            album = (
                self.cache.album_image.copy()
            )

            size = self.album_size

            album = ImageOps.fit(
                album,
                (
                    size,
                    size
                ),
                method=Image.Resampling.LANCZOS
            )

            x = (
                self.width - size
            ) // 2

            y = 110


            # =========================
            # Adaptive album glow
            # =========================

            palette = (
                self.cache.palette
                or
                [(100, 100, 100)]
            )

            glow_color = (
                self.choose_glow_color(
                    palette
                )
            )

            print(
                "Album glow:",
                glow_color
            )


            # =========================
            # OUTER GLOW
            #
            # Wide and subtle.
            # Gives the album atmosphere
            # without looking like a blob.
            # =========================

            glow_margin = 130

            glow_size = (
                size
                +
                glow_margin * 2
            )

            outer_glow = Image.new(
                "RGBA",
                (
                    glow_size,
                    glow_size
                ),
                (0, 0, 0, 0)
            )

            outer_draw = ImageDraw.Draw(
                outer_glow
            )

            outer_padding = 38

            outer_draw.rounded_rectangle(
                (
                    glow_margin - outer_padding,
                    glow_margin - outer_padding,
                    glow_margin + size + outer_padding,
                    glow_margin + size + outer_padding
                ),
                radius=60,
                fill=(
                    glow_color[0],
                    glow_color[1],
                    glow_color[2],
                    35
                )
            )

            outer_glow = outer_glow.filter(
                ImageFilter.GaussianBlur(
                    80
                )
            )

            frame.paste(
                outer_glow,
                (
                    x - glow_margin,
                    y - glow_margin
                ),
                outer_glow
            )


            # =========================
            # INNER GLOW
            #
            # Smaller and slightly stronger.
            # Makes the light appear to originate
            # from the album itself.
            # =========================

            inner_margin = 70

            inner_size = (
                size
                +
                inner_margin * 2
            )

            inner_glow = Image.new(
                "RGBA",
                (
                    inner_size,
                    inner_size
                ),
                (0, 0, 0, 0)
            )

            inner_draw = ImageDraw.Draw(
                inner_glow
            )

            inner_padding = 18

            inner_draw.rounded_rectangle(
                (
                    inner_margin - inner_padding,
                    inner_margin - inner_padding,
                    inner_margin + size + inner_padding,
                    inner_margin + size + inner_padding
                ),
                radius=48,
                fill=(
                    glow_color[0],
                    glow_color[1],
                    glow_color[2],
                    52
                )
            )

            inner_glow = inner_glow.filter(
                ImageFilter.GaussianBlur(
                    34
                )
            )

            frame.paste(
                inner_glow,
                (
                    x - inner_margin,
                    y - inner_margin
                ),
                inner_glow
            )


            # =========================
            # LOCAL shadow
            # =========================

            shadow_margin = 55

            shadow_size = (
                size
                +
                shadow_margin * 2
            )

            shadow_layer = Image.new(
                "RGBA",
                (
                    shadow_size,
                    shadow_size
                ),
                (0, 0, 0, 0)
            )

            shadow_draw = ImageDraw.Draw(
                shadow_layer
            )

            shadow_draw.rounded_rectangle(
                (
                    shadow_margin + 10,
                    shadow_margin + 14,
                    shadow_margin + size + 10,
                    shadow_margin + size + 14
                ),
                radius=self.album_radius,
                fill=(
                    0,
                    0,
                    0,
                    170
                )
            )

            shadow_layer = shadow_layer.filter(
                ImageFilter.GaussianBlur(
                    20
                )
            )

            frame.paste(
                shadow_layer,
                (
                    x - shadow_margin,
                    y - shadow_margin
                ),
                shadow_layer
            )


            # =========================
            # Rounded album corners
            # =========================

            mask = Image.new(
                "L",
                (
                    size,
                    size
                ),
                0
            )

            mask_draw = ImageDraw.Draw(
                mask
            )

            mask_draw.rounded_rectangle(
                (
                    0,
                    0,
                    size,
                    size
                ),
                radius=self.album_radius,
                fill=255
            )

            frame.paste(
                album,
                (
                    x,
                    y
                ),
                mask
            )


        except Exception as e:

            print(
                "Album render error:",
                e
            )


    def draw_progress(
        self,
        image,
        progress,
        x,
        y
    ):

        draw = ImageDraw.Draw(
            image
        )

        progress = max(
            0.0,
            min(
                1.0,
                progress
            )
        )

        draw.rounded_rectangle(
            (
                x,
                y,
                x + self.bar_width,
                y + self.bar_height
            ),
            radius=9,
            fill=(65, 65, 65)
        )

        filled_width = int(
            self.bar_width
            *
            progress
        )

        if filled_width > 0:

            draw.rounded_rectangle(
                (
                    x,
                    y,
                    x + filled_width,
                    y + self.bar_height
                ),
                radius=9,
                fill="white"
            )


    def render_progress_region(
        self,
        progress
    ):

        if self.base_frame is None:

            return None

        bar_x, bar_y = (
            self.layout.progress_position()
        )

        region = self.base_frame.crop(
            (
                bar_x,
                bar_y,
                bar_x + self.bar_width,
                bar_y + self.bar_height
            )
        )

        self.draw_progress(
            region,
            progress,
            0,
            0
        )

        return region


    def render(
        self,
        album_path,
        title,
        artist,
        progress
    ):

        frame = self.create_frame()

        background = self.cache.generate(
            album_path,
            (
                self.width,
                self.height
            )
        )

        if background is not None:

            frame.paste(
                background,
                (0, 0)
            )


        # Album art uses the same cached
        # image and palette as the background.

        self.draw_album_art(
            frame
        )


        draw = ImageDraw.Draw(
            frame
        )

        draw.text(
            (
                self.width // 2,
                465
            ),
            title,
            font=self.title_font,
            fill=(
                255,
                255,
                255
            ),
            anchor="mm"
        )

        draw.text(
            (
                self.width // 2,
                525
            ),
            artist,
            font=self.artist_font,
            fill=(
                205,
                205,
                205
            ),
            anchor="mm"
        )


        self.base_frame = (
            frame.copy()
        )


        bar_x, bar_y = (
            self.layout.progress_position()
        )

        self.draw_progress(
            frame,
            progress,
            bar_x,
            bar_y
        )

        return frame
