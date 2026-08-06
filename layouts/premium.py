class PremiumLayout:


    def __init__(self, width, height):

        self.width = width
        self.height = height



    def album_position(self, size):

        return (
            (self.width - size) // 2,
            140
        )



    def title_position(self):

        return (
            self.width // 2,
            470
        )



    def artist_position(self):

        return (
            self.width // 2,
            525
        )



    def progress_position(self):

        return (
            400,
            650
        )
