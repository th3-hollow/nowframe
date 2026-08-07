import sys
import time

from PIL import Image

sys.path.append(
    "/root/spotify-display"
)

from core.app import NowFrameApp

from core.v2.display_engine import (
    show_frame,
    show_region
)


print("NowFrame starting...")


app = NowFrameApp()


# Current image that is actually visible
# on the physical display.

current_screen = None


# Performance counters

last_report = time.monotonic()

full_frames = 0
region_frames = 0

full_time = 0.0
region_time = 0.0


# =====================================
# Song transition
# =====================================

def crossfade(
    old_frame,
    new_frame,
    steps=6
):

    if old_frame is None:

        show_frame(
            new_frame
        )

        return


    print("Song crossfade")


    for step in range(
        1,
        steps + 1
    ):

        t = (
            step / steps
        )


        # Smoothstep easing.
        #
        # Less mechanical than a
        # completely linear fade.

        alpha = (
            t
            * t
            * (
                3.0
                -
                2.0 * t
            )
        )


        blended = Image.blend(
            old_frame,
            new_frame,
            alpha
        )


        show_frame(
            blended
        )


# =====================================
# Main loop
# =====================================

while True:

    try:

        start = time.monotonic()


        update = app.create_update()


        if update is None:

            time.sleep(
                0.05
            )

            continue


        # =================================
        # FULL FRAME
        # =================================

        if update["type"] == "full":

            new_frame = update["image"]


            if (
                update.get("transition")
                == "song"
                and
                current_screen is not None
            ):

                crossfade(
                    current_screen,
                    new_frame,
                    steps=6
                )

            else:

                show_frame(
                    new_frame
                )


            current_screen = (
                new_frame.copy()
            )


            full_frames += 1

            full_time += (
                time.monotonic()
                - start
            )


        # =================================
        # PARTIAL REGION
        # =================================

        elif update["type"] == "region":

            region = update["image"]

            x = update["x"]
            y = update["y"]


            show_region(
                region,
                x,
                y
            )


            # Keep our in-memory copy in
            # sync with the real display.

            if current_screen is not None:

                current_screen.paste(
                    region,
                    (
                        x,
                        y
                    )
                )


            region_frames += 1

            region_time += (
                time.monotonic()
                - start
            )


        # =================================
        # Performance report
        # =================================

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
