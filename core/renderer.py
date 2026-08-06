from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FONT_REGULAR,
    FONT_BOLD
)


class Renderer:

    def __init__(self):

        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        self.cached_album = None
        self.cached_background = None
        self.last_album_url = None


        self.title_font = ImageFont.truetype(
            FONT_BOLD,
            45
        )

        self.artist_font = ImageFont.truetype(
            FONT_REGULAR,
            28
        )

        self.clock_font = ImageFont.truetype(
            FONT_BOLD,
            80
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


    def fit_text(self, text, font, max_width):

        while font.getbbox(text)[2] > max_width and len(text) > 1:
            text = text[:-1]

        return text



    def load_album(self):

        try:

            return Image.open(
                "assets/images/album.jpg"
            ).convert("RGB")


        except Exception as e:

            print(
                "Album load error:",
                e
            )

            return None



    def update_album_cache(self):

        album = self.load_album()

        if album is None:
            return


        self.cached_album = ImageOps.fit(
            album,
            (
                260,
                260
            )
        )


        background = ImageOps.fit(
            album,
            (
                self.width,
                self.height
            )
        )


        background = background.filter(
            ImageFilter.GaussianBlur(
                40
            )
        )


        background = ImageEnhance.Brightness(
            background
        ).enhance(
            0.25
        )


        self.cached_background = background



    def draw_album(self, image):

        if self.cached_album is None:
            return


        size = 260

        x = (self.width - size) // 2
        y = 150


        mask = Image.new(
            "L",
            (
                size,
                size
            ),
            0
        )


        ImageDraw.Draw(mask).rounded_rectangle(
            (
                0,
                0,
                size,
                size
            ),
            radius=25,
            fill=255
        )


        image.paste(
            self.cached_album,
            (
                x,
                y
            ),
            mask
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



    def draw_spotify(self, image, data):

        draw = ImageDraw.Draw(image)


        # Detect new album

        album_url = data.get(
            "album_url"
        )


        if album_url != self.last_album_url:

            print(
                "Updating album background"
            )

            self.last_album_url = album_url

            self.update_album_cache()



        # Background

        if self.cached_background:

            image.paste(
                self.cached_background,
                (
                    0,
                    0
                )
            )



        # Album

        self.draw_album(
            image
        )



        # Title

        title = self.fit_text(
            data["title"],
            self.title_font,
            800
        )


        draw.text(
            (
                self.width // 2,
                470
            ),
            title,
            font=self.title_font,
            fill="white",
            anchor="mm"
        )



        # Artist

        draw.text(
            (
                self.width // 2,
                520
            ),
            data["artist"],
            font=self.artist_font,
            fill=(190,190,190),
            anchor="mm"
        )



        # Progress bar

        bar_width = 500
        bar_height = 12


        bar_x = (
            self.width - bar_width
        ) // 2


        bar_y = 600



        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width,
                bar_y + bar_height
            ),
            radius=6,
            fill=(70,70,70)
        )


        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + int(
                    bar_width * data["progress"]
                ),
                bar_y + bar_height
            ),
            radius=6,
            fill="white"
        )


        return image
