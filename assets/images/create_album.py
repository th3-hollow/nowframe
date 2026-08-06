from PIL import Image, ImageDraw, ImageFont


size = 500

img = Image.new(
    "RGB",
    (size, size),
    (40, 40, 40)
)

draw = ImageDraw.Draw(img)


# simple artwork
draw.ellipse(
    (100, 100, 400, 400),
    fill=(30, 180, 100)
)


draw.rectangle(
    (180, 180, 320, 320),
    fill=(255, 255, 255)
)


try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        50
    )
except:
    font = None


draw.text(
    (250, 430),
    "NOW",
    fill=(255,255,255),
    font=font,
    anchor="mm"
)


img.save(
    "album.jpg"
)

print("Album created")
