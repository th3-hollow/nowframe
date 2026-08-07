import numpy as np


fb = open(
    "/dev/fb0",
    "wb",
    buffering=0
)


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


def show_frame(img):

    if img.size != (
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    ):

        raise ValueError(
            f"Expected {SCREEN_WIDTH}x{SCREEN_HEIGHT}, "
            f"got {img.size[0]}x{img.size[1]}"
        )


    if img.mode != "RGB":
        img = img.convert("RGB")


    frame = np.asarray(
        img,
        dtype=np.uint8
    )


    r = frame[:, :, 0].astype(
        np.uint16
    )

    g = frame[:, :, 1].astype(
        np.uint16
    )

    b = frame[:, :, 2].astype(
        np.uint16
    )


    rgb565 = (
        ((r & 0xF8) << 8)
        |
        ((g & 0xFC) << 3)
        |
        (b >> 3)
    )


    fb.seek(0)

    fb.write(
        rgb565.astype(
            "<u2",
            copy=False
        ).tobytes()
    )
