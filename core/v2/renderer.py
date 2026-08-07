from PIL import Image, ImageDraw, ImageFont, ImageOps

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
            45
        )

        self.artist_font = ImageFont.truetype(
            font_regular,
            28
        )

        self.clock_font = ImageFont.truetype(
            font_bold,
            120
        )


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

        draw = ImageDraw.Draw(frame)

        try:

            album = Image.open(
                album_path
            ).convert("RGB")

            size = 260

            album = ImageOps.fit(
                album,
                (
                    size,
                    size
                )
            )

            x, y = self.layout.album_position(
                size
            )

            frame.paste(
                album,
                (
                    x,
                    y
                )
            )

        except Exception as e:

            print(
                "Album render error:",
                e
            )

        draw.text(
            self.layout.title_position(),
            title,
            font=self.title_font,
            fill="white",
            anchor="mm"
        )

        draw.text(
            self.layout.artist_position(),
            artist,
            font=self.artist_font,
            fill=(190, 190, 190),
            anchor="mm"
        )

        bar_x, bar_y = self.layout.progress_position()

        bar_width = 1100
        bar_height = 18

        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width,
                bar_y + bar_height
            ),
            radius=9,
            fill=(80, 80, 80)
        )

        progress = max(
            0.0,
            min(
                1.0,
                progress
            )
        )

        filled_width = int(
            bar_width * progress
        )

        if filled_width > 0:

            draw.rounded_rectangle(
                (
                    bar_x,
                    bar_y,
                    bar_x + filled_width,
                    bar_y + bar_height
                ),
                radius=9,
                fill="white"
            )

        return frame