import time

from PIL import Image

from core.app import NowFrameApp

from core.v2.display_engine import (
    show_frame,
    show_region
)

from config import (
    CROSSFADE_ENABLED,
    CROSSFADE_STEPS,
    PERFORMANCE_LOGGING,
    PERFORMANCE_REPORT_SECONDS
)


print("NowFrame starting...")


app = NowFrameApp()


current_screen = None


last_report = time.monotonic()

full_frames = 0
region_frames = 0

full_time = 0.0
region_time = 0.0


def crossfade(
    old_frame,
    new_frame,
    steps=CROSSFADE_STEPS
):

    if old_frame is None:

        start = time.monotonic()

        show_frame(
            new_frame
        )

        print(
            f"Initial framebuffer write: "
            f"{time.monotonic() - start:.3f}s"
        )

        return


    print("Song crossfade")


    fade_start = time.monotonic()


    for step in range(
        1,
        steps + 1
    ):

        step_start = time.monotonic()


        t = (
            step / steps
        )


        alpha = (
            t
            * t
            * (
                3.0
                -
                2.0 * t
            )
        )


        blend_start = time.monotonic()


        blended = Image.blend(
            old_frame,
            new_frame,
            alpha
        )


        blend_time = (
            time.monotonic()
            -
            blend_start
        )


        display_start = time.monotonic()


        show_frame(
            blended
        )


        display_time = (
            time.monotonic()
            -
            display_start
        )


        step_time = (
            time.monotonic()
            -
            step_start
        )


        print(
            f"Fade {step}/{steps} | "
            f"blend: {blend_time:.3f}s | "
            f"display: {display_time:.3f}s | "
            f"total: {step_time:.3f}s"
        )


    print(
        f"Crossfade total: "
        f"{time.monotonic() - fade_start:.3f}s"
    )


while True:

    try:

        loop_start = time.monotonic()


        update_start = time.monotonic()


        update = app.create_update()


        update_time = (
            time.monotonic()
            -
            update_start
        )


        if update is None:

            time.sleep(
                0.05
            )

            continue


        if update["type"] == "full":

            print(
                f"Full render preparation: "
                f"{update_time:.3f}s"
            )


            new_frame = update["image"]


            display_start = time.monotonic()


            if (
                CROSSFADE_ENABLED
                and
                update.get("transition")
                in ("song", "mode")
                and
                current_screen is not None
            ):

                crossfade(
                    current_screen,
                    new_frame,
                    steps=CROSSFADE_STEPS
                )

            else:

                show_frame(
                    new_frame
                )


            display_time = (
                time.monotonic()
                -
                display_start
            )


            current_screen = (
                new_frame.copy()
            )


            total_full_time = (
                time.monotonic()
                -
                loop_start
            )


            print(
                f"Full update totals | "
                f"prepare: {update_time:.3f}s | "
                f"display/transition: {display_time:.3f}s | "
                f"overall: {total_full_time:.3f}s"
            )


            full_frames += 1

            full_time += (
                total_full_time
            )


        elif update["type"] == "region":

            region = update["image"]

            x = update["x"]
            y = update["y"]


            show_region(
                region,
                x,
                y
            )


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
                -
                loop_start
            )


        now = time.monotonic()


        if (
            PERFORMANCE_LOGGING
            and
            now - last_report
            >= PERFORMANCE_REPORT_SECONDS
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
