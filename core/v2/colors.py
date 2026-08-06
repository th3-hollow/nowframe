from PIL import Image
from collections import Counter


class ColorExtractor:


    def __init__(self):
        pass


    def get_colors(self, image_path, count=5):

        try:

            image = Image.open(
                image_path
            ).convert(
                "RGB"
            )


            image = image.resize(
                (100,100)
            )


            pixels = list(
                image.getdata()
            )


            colors = Counter(
                pixels
            )


            return [
                color
                for color, amount in colors.most_common(count)
            ]


        except Exception as e:

            print(
                "Color extraction error:",
                e
            )

            return [
                (0,0,0)
            ]