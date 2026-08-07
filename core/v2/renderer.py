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
            # Glow color
            # =========================

            palette = (
                self.cache.palette
                or
                [(100, 100, 100)]
            )


            glow_color = palette[0]


            max_channel = max(
                glow_color
            )


            if max_channel > 0:

                scale = min(
                    1.0,
                    180 / max_channel
                )

                glow_color = tuple(
                    int(channel * scale)
                    for channel in glow_color
                )


            # =========================
            # LOCAL glow
            #
            # Previously this was a
            # 1920x1080 blurred image.
            #
            # Now only ~540x540.
            # =========================

            glow_margin = 120

            glow_size = (
                size
                +
                glow_margin * 2
            )


            glow_layer = Image.new(
                "RGBA",
                (
                    glow_size,
                    glow_size
                ),
                (0, 0, 0, 0)
            )


            glow_draw = ImageDraw.Draw(
                glow_layer
            )


            glow_padding = 35


            glow_draw.rounded_rectangle(
                (
                    glow_margin - glow_padding,
                    glow_margin - glow_padding,
                    glow_margin + size + glow_padding,
                    glow_margin + size + glow_padding
                ),
                radius=55,
                fill=(
                    glow_color[0],
                    glow_color[1],
                    glow_color[2],
                    75
                )
            )


            glow_layer = glow_layer.filter(
                ImageFilter.GaussianBlur(
                    55
                )
            )


            frame.paste(
                glow_layer,
                (
                    x - glow_margin,
                    y - glow_margin
                ),
                glow_layer
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
            # Rounded album
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


        # Album art uses the SAME cached
        # image + palette as the background.

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
