import sys
import time

sys.path.append(
    "/root/spotify-display"
)

from core.app import NowFrameApp
from display_engine import show_frame


print("NowFrame starting...")


app = NowFrameApp()


last_report = time.monotonic()

frame_count = 0

render_total = 0.0
display_total = 0.0


while True:

    try:

        start = time.monotonic()


        frame = app.create_frame()


        after_render = time.monotonic()


        show_frame(
            frame
        )


        after_display = time.monotonic()


        render_total += (
            after_render - start
        )

        display_total += (
            after_display - after_render
        )


        frame_count += 1


        if (
            after_display - last_report
            >= 5
        ):

            elapsed = (
                after_display - last_report
            )


            fps = (
                frame_count / elapsed
            )


            print(
                f"FPS: {fps:.2f} | "
                f"render: "
                f"{render_total / frame_count:.3f}s | "
                f"display: "
                f"{display_total / frame_count:.3f}s"
            )


            frame_count = 0

            render_total = 0.0
            display_total = 0.0

            last_report = after_display


        time.sleep(
            0.1
        )


    except KeyboardInterrupt:

        print(
            "Stopping NowFrame..."
        )

        break
