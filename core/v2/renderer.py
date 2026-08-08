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

from config import (
    ALBUM_SIZE,
    ALBUM_RADIUS,
    ALBUM_Y,
    GLOW_ENABLED,
    GLOW_TARGET_PEAK,
    OUTER_GLOW_ALPHA,
    OUTER_GLOW_BLUR,
    INNER_GLOW_ALPHA,
    INNER_GLOW_BLUR,
    TITLE_MAX_FONT_SIZE,
    TITLE_MIN_FONT_SIZE,
    TITLE_MAX_WIDTH,
    ARTIST_FONT_SIZE,
    TITLE_Y,
    ARTIST_Y,
    SPOTIFY_CODE_ENABLED,
    SPOTIFY_CODE_WIDTH,
    SPOTIFY_CODE_HEIGHT,
    SPOTIFY_CODE_POSITION,
    PROGRESS_WIDTH,
    PROGRESS_HEIGHT,
    PROGRESS_BACKGROUND,
    PROGRESS_FOREGROUND,
    CLOCK_FONT_SIZE,
    CLOCK_DATE_FONT_SIZE,
    CLOCK_BACKGROUND_DARKEN,
    CLOCK_TIME_Y_OFFSET,
    CLOCK_DATE_Y_OFFSET,
    IDLE_DISPLAY_MODE,
)


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

        self.font_regular_path = font_regular
        self.font_bold_path = font_bold

        self.title_font = ImageFont.truetype(
            font_bold,
            TITLE_MAX_FONT_SIZE
        )

        self.artist_font = ImageFont.truetype(
            font_regular,
            ARTIST_FONT_SIZE
        )

        self.clock_font = ImageFont.truetype(
            font_bold,
            CLOCK_FONT_SIZE
        )

        self.base_frame = None

        self.bar_width = PROGRESS_WIDTH
        self.bar_height = PROGRESS_HEIGHT

        self.album_size = ALBUM_SIZE
        self.album_radius = ALBUM_RADIUS


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

        # Reuse the last Spotify background
        # so idle mode visually matches NowFrame.

        if (
           IDLE_DISPLAY_MODE == "clock_album"
           and
           self.cache.background is not None
        ):

            clock_background = (
                self.cache.background.copy()
            )

            dark_overlay = Image.new(
                "RGB",
                clock_background.size,
                (0, 0, 0)
            )

            clock_background = Image.blend(
                clock_background,
                dark_overlay,
                CLOCK_BACKGROUND_DARKEN
            )

            image.paste(
                clock_background,
                (0, 0)
            )


        draw = ImageDraw.Draw(
            image
        )


        # Large centered time

        draw.text(
            (
                self.width // 2,
                self.height // 2 + CLOCK_TIME_Y_OFFSET
            ),
            data["time"],
            font=self.clock_font,
            fill=(
                255,
                255,
                255
            ),
            anchor="mm"
        )


        # Date underneath

        date_font = ImageFont.truetype(
            self.font_regular_path,
            CLOCK_DATE_FONT_SIZE
        )

        draw.text(
            (
                self.width // 2,
                self.height // 2 + CLOCK_DATE_Y_OFFSET
            ),
            data["date"],
            font=date_font,
            fill=(
                185,
                185,
                185
            ),
            anchor="mm"
        )


        return image


    def choose_glow_color(
        self,
        palette
    ):

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


            if value < 0.12:
                continue


            brightness_score = (
                1.0
                -
                abs(
                    value - 0.62
                )
            )


            score = (
                saturation * 2.5
                +
                brightness_score
            )


            if score > best_score:

                best_score = score
                best_color = color


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

        peak = max(
            r,
            g,
            b
        )

        target_peak = GLOW_TARGET_PEAK


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

            y = ALBUM_Y


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
            # Outer glow
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
                    OUTER_GLOW_ALPHA
                )
            )

            outer_glow = outer_glow.filter(
                ImageFilter.GaussianBlur(
                    OUTER_GLOW_BLUR
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
            # Inner glow
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
                    INNER_GLOW_ALPHA
                )
            )

            inner_glow = inner_glow.filter(
                ImageFilter.GaussianBlur(
                    INNER_GLOW_BLUR
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
            # Local shadow
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


    def fit_title_font(
        self,
        text,
        max_width=TITLE_MAX_WIDTH,
        max_size=TITLE_MAX_FONT_SIZE,
        min_size=TITLE_MIN_FONT_SIZE
    ):

        # Try progressively smaller fonts
        # until the title fits.

        for font_size in range(
            max_size,
            min_size - 1,
            -2
        ):

            font = ImageFont.truetype(
                self.font_bold_path,
                font_size
            )

            bbox = font.getbbox(
                text
            )

            text_width = (
                bbox[2] - bbox[0]
            )

            if text_width <= max_width:

                return (
                    font,
                    text
                )


        # Still too long at minimum size.
        # Truncate cleanly with an ellipsis.

        font = ImageFont.truetype(
            self.font_bold_path,
            min_size
        )

        display_text = text


        while len(display_text) > 1:

            candidate = (
                display_text
                +
                "…"
            )

            bbox = font.getbbox(
                candidate
            )

            text_width = (
                bbox[2] - bbox[0]
            )

            if text_width <= max_width:

                return (
                    font,
                    candidate
                )

            display_text = (
                display_text[:-1]
            )


        return (
            font,
            "…"
        )



    def draw_spotify_code(
        self,
        image,
        spotify_code_path
    ):

        if (
            not SPOTIFY_CODE_ENABLED
            or
            not spotify_code_path
        ):

            return


        try:

            with Image.open(
                spotify_code_path
            ) as source:

                spotify_code = (
                    source.convert("RGB")
                )


            spotify_code = ImageOps.contain(
                spotify_code,
                (
                    SPOTIFY_CODE_WIDTH,
                    SPOTIFY_CODE_HEIGHT
                ),
                method=Image.Resampling.LANCZOS
            )


            code_x = (
                self.width
                -
                spotify_code.width
            ) // 2


            if (
                SPOTIFY_CODE_POSITION
                ==
                "bottom_center"
            ):

                code_y = (
                    self.height
                    -
                    spotify_code.height
                    -
                    30
                )

            else:

                _, bar_y = (
                    self.layout.progress_position()
                )

                code_y = (
                    bar_y
                    -
                    spotify_code.height
                    -
                    15
                )


            image.paste(
                spotify_code,
                (
                    code_x,
                    code_y
                )
            )


        except Exception as e:

            print(
                "Spotify Code render error:",
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
            fill=PROGRESS_BACKGROUND
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
                fill=PROGRESS_FOREGROUND
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
        progress,
        spotify_code_path=None
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


        self.draw_album_art(
            frame
        )


        draw = ImageDraw.Draw(
            frame
        )


        # =========================
        # Adaptive title
        # =========================

        title_font, display_title = (
            self.fit_title_font(
                title
            )
        )

        draw.text(
            (
                self.width // 2,
                TITLE_Y
            ),
            display_title,
            font=title_font,
            fill=(
                255,
                255,
                255
            ),
            anchor="mm"
        )


        # =========================
        # Artist
        # =========================

        draw.text(
            (
                self.width // 2,
                ARTIST_Y
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


        self.draw_spotify_code(
            frame,
            spotify_code_path
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
