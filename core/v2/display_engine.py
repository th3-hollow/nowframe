import numpy as np


fb = open(
    "/dev/fb0",
    "r+b",
    buffering=0
)


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BYTES_PER_PIXEL = 2
STRIDE = 3840


def rgb888_to_rgb565(img):

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

    return rgb565.astype(
        "<u2",
        copy=False
    )


def show_frame(img):

    if img.size != (
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    ):
        raise ValueError(
            f"Expected {SCREEN_WIDTH}x{SCREEN_HEIGHT}, "
            f"got {img.size[0]}x{img.size[1]}"
        )

    rgb565 = rgb888_to_rgb565(
        img
    )

    fb.seek(0)

    fb.write(
        rgb565.tobytes()
    )


def show_region(img, x, y):

    width, height = img.size

    if (
        x < 0
        or y < 0
        or x + width > SCREEN_WIDTH
        or y + height > SCREEN_HEIGHT
    ):
        raise ValueError(
            "Region is outside framebuffer bounds"
        )

    rgb565 = rgb888_to_rgb565(
        img
    )

    row_bytes = width * BYTES_PER_PIXEL

    raw = rgb565.tobytes()

    for row in range(height):

        framebuffer_offset = (
            (y + row) * STRIDE
            +
            x * BYTES_PER_PIXEL
        )

        source_start = (
            row * row_bytes
        )

        source_end = (
            source_start + row_bytes
        )

        fb.seek(
            framebuffer_offset
        )

        fb.write(
            raw[
                source_start:
                source_end
            ]
        )
