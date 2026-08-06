import time


class Animation:

    def __init__(self):

        self.alpha = 0


    def fade_in(self, duration=1):

        steps = 20

        for i in range(steps + 1):

            self.alpha = i / steps

            time.sleep(
                duration / steps
            )

        return self.alpha


    def fade_out(self, duration=1):

        steps = 20

        for i in range(steps + 1):

            self.alpha = 1 - (i / steps)

            time.sleep(
                duration / steps
            )

        return self.alpha
