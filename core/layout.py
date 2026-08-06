from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)


class Layout:

    def __init__(self):

        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT


    def album_position(self):

        size = int(self.height * 0.55)

        x = int(self.width * 0.05)

        y = int(
            (self.height - size) / 2
        )

        return x, y, size


    def title_position(self):

        x = int(self.width * 0.45)

        y = int(self.height * 0.25)

        return x, y


    def artist_position(self):

        x = int(self.width * 0.45)

        y = int(self.height * 0.35)

        return x, y


    def progress_position(self):

        x = int(self.width * 0.45)

        y = int(self.height * 0.55)

        width = int(self.width * 0.4)

        height = 10

        return x, y, width, height
