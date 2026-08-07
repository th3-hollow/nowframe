import sys
import time

sys.path.append(
    "/root/spotify-display"
)

from core.app import NowFrameApp

from core.v2.display_engine import (
    show_frame,
    show_region
)


print(
    "NowFrame starting..."
)


app = NowFrameApp()


last_report = time.monotonic()

full_frames = 0
region_frames = 0

full_time = 0.0
region_time = 0.0


while True:

    try:

        start = time.monotonic()


        update = app.create_update()


        if update is None:

            time.sleep(
                0.05
            )

            continue


        if update["type"] == "full":

            show_frame(
                update["image"]
            )

            full_frames += 1

            full_time += (
                time.monotonic()
                - start
            )


        elif update["type"] == "region":

            show_region(
                update["image"],
                update["x"],
                update["y"]
            )

            region_frames += 1

            region_time += (
                time.monotonic()
                - start
            )


        now = time.monotonic()


        if (
            now - last_report
            >= 5
        ):

            elapsed = (
                now - last_report
            )


            total_frames = (
                full_frames
                +
                region_frames
            )


            fps = (
                total_frames
                /
                elapsed
            )


            average_region = (
                region_time
                /
                region_frames
                if region_frames > 0
                else 0
            )


            average_full = (
                full_time
                /
                full_frames
                if full_frames > 0
                else 0
            )


            print(
                f"FPS: {fps:.2f} | "
                f"full: {full_frames} "
                f"({average_full:.3f}s) | "
                f"region: {region_frames} "
                f"({average_region:.4f}s)"
            )


            full_frames = 0
            region_frames = 0

            full_time = 0.0
            region_time = 0.0

            last_report = now


        time.sleep(
            0.05
        )


    except KeyboardInterrupt:

        print(
            "Stopping NowFrame..."
        )

        break
