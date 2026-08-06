import sys
import time
from PIL import Image

sys.path.append("/root/spotify-display")

from core.app import NowFrameApp
from display_engine import show_frame


print("NowFrame starting...")


app = NowFrameApp()


last_update = 0


while True:

    try:

        frame = app.create_frame()

        frame = frame.resize(
            (960, 540),
            Image.LANCZOS
        )

        show_frame(frame)

        now = time.time()


        if now - last_update >= 1:

            print("Frame displayed")

            last_update = now


        time.sleep(0.1)


    except KeyboardInterrupt:

        print("Stopping NowFrame...")
        break
