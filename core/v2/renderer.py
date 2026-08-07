from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageOps,
    ImageFilter
)

from layouts.premium import PremiumLayout
from core.v2.cache import BackgroundCache
from core.v2.colors import ColorExtractor


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
        self.colors = ColorExtractor()

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


    def draw_clock(self, image, data):

        draw = ImageDraw.Draw(image)

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
        frame,
        album_path
    ):

        try:

            album = Image.open(
                album_path
            ).convert("RGB")

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
            # Album glow color
            # =========================

            palette = self.colors.get_colors(
                album_path,
                count=3
            )

            glow_color = palette[0]

            # Prevent very bright album colors
            # from producing an overpowering halo.

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
            # Soft colored glow
            # =========================

            glow_layer = Image.new(
                "RGBA",
                frame.size,
                (0, 0, 0, 0)
            )

            glow_draw = ImageDraw.Draw(
                glow_layer
            )

            glow_padding = 35

            glow_draw.rounded_rectangle(
                (
                    x - glow_padding,
                    y - glow_padding,
                    x + size + glow_padding,
                    y + size + glow_padding
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
                (0, 0),
                glow_layer
            )


            # =========================
            # Dark shadow
            # =========================

            shadow_layer = Image.new(
                "RGBA",
                frame.size,
                (0, 0, 0, 0)
            )

            shadow_draw = ImageDraw.Draw(
                shadow_layer
            )

            shadow_draw.rounded_rectangle(
                (
                    x + 10,
                    y + 14,
                    x + size + 10,
                    y + size + 14
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
                (0, 0),
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
            self.bar_width * progress
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


        # Album artwork

        self.draw_album_art(
            frame,
            album_path
        )


        draw = ImageDraw.Draw(
            frame
        )


        # =========================
        # Title
        # =========================

        draw.text(
            (
                self.width // 2,
                465
            ),
            title,
            font=self.title_font,
            fill=(255, 255, 255),
            anchor="mm"
        )


        # =========================
        # Artist
        # =========================

        draw.text(
            (
                self.width // 2,
                525
            ),
            artist,
            font=self.artist_font,
            fill=(205, 205, 205),
            anchor="mm"
        )


        # Save screen without progress

        self.base_frame = frame.copy()


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
