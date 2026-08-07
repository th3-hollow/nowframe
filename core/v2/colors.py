from PIL import Image
from collections import Counter
import colorsys


class ColorExtractor:

    def __init__(self):
        pass


    def get_colors(self, image_path, count=5):

        try:

            image = Image.open(
                image_path
            ).convert("RGB")


            image = image.resize(
                (100, 100)
            )


            pixels = list(
                image.getdata()
            )


            colors = Counter(
                pixels
            )


            candidates = []


            for color, amount in colors.most_common(200):

                r, g, b = color


                rf = r / 255.0
                gf = g / 255.0
                bf = b / 255.0


                hue, saturation, brightness = colorsys.rgb_to_hsv(
                    rf,
                    gf,
                    bf
                )


                if brightness < 0.035:

                    continue


                score = (
                    amount
                    * (1.0 + saturation * 2.0)
                    * (0.5 + brightness)
                )


                candidates.append(
                    (
                        score,
                        color
                    )
                )


            candidates.sort(
                reverse=True
            )


            palette = []


            for score, color in candidates:

                r, g, b = color


                too_similar = False


                for existing in palette:

                    er, eg, eb = existing


                    distance = (
                        abs(r - er)
                        + abs(g - eg)
                        + abs(b - eb)
                    )


                    if distance < 45:

                        too_similar = True

                        break


                if not too_similar:

                    palette.append(
                        color
                    )


                if len(palette) >= count:

                    break


            if not palette:

                palette = [
                    (20, 20, 20)
                ]


            while len(palette) < count:

                palette.append(
                    palette[-1]
                )


            return palette


        except Exception as e:

            print(
                "Color extraction error:",
                e
            )


            return [
                (20, 20, 20)
            ] * count