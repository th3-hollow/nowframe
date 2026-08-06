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


    def create_frame(self):

        return Image.new(
            "RGB",
            (
                self.width,
                self.height
            ),
            (0,0,0)
        )
      


    def render(
        self,
        album_path,
        title,
        artist,
        progress
    ):

        frame = Image.new(
            "RGB",
            (
                self.width,
                self.height
            ),
            (0,0,0)
        )


        background = self.cache.generate(
            album_path,
            (
                self.width,
                self.height
            )
        )


        if background:

            frame.paste(
                background,
                (0,0)
            )


        draw = ImageDraw.Draw(frame)


        album = Image.open(
            album_path
        ).convert(
            "RGB"
        )


        size = 260


        album = ImageOps.fit(
            album,
            (
                size,
                size
            )
        )


        x,y = self.layout.album_position(
            size
        )


        frame.paste(
            album,
            (
                x,
                y
            )
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
            fill=(190,190,190),
            anchor="mm"
        )


        bar_x, bar_y = self.layout.progress_position()


        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + 1100,
                bar_y + 18
            ),
            radius=9,
            fill=(80,80,80)
        )


        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + int(1100 * progress),
                bar_y + 18
            ),
            radius=9,
            fill="white"
        )


        return frame
