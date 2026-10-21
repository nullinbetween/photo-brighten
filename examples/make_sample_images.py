#!/usr/bin/env python3
"""Generate neutral synthetic sample images (colour blocks / patterns) for trying
batch-brighten. No photographs are used. Output: examples/sample-photos/

    python3 examples/make_sample_images.py
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sample-photos")


def gradient(w, h, dark=0.45):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (int(255 * dark * x / (w - 1)), int(255 * dark * y / (h - 1)), int(255 * dark * 0.6))
    return im


def blocks(w, h):
    im = Image.new("RGB", (w, h), (40, 44, 52))
    d = ImageDraw.Draw(im)
    colours = [(90, 60, 50), (50, 80, 60), (50, 60, 95), (85, 80, 45)]
    for i, c in enumerate(colours):
        d.rectangle([10 + i * (w - 20) // 4, 20, 5 + (i + 1) * (w - 20) // 4, h - 20], fill=c)
    return im


def dim_room(w=640, h=420):
    """An under-exposed 'room' drawn from flat shapes: wall, window, table, mug, plant."""
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):              # wall: dark vertical gradient
        for x in range(w):
            v = 38 + int(22 * (1 - y / h)) + int(6 * x / w)
            px[x, y] = (v + 6, v + 2, v - 4)
    d = ImageDraw.Draw(im)
    d.rectangle([60, 50, 250, 230], fill=(70, 78, 92))           # window
    d.line([155, 50, 155, 230], fill=(46, 44, 42), width=6)
    d.line([60, 140, 250, 140], fill=(46, 44, 42), width=6)
    d.rectangle([0, 300, w, h], fill=(52, 40, 30))               # table
    d.rectangle([0, 296, w, 304], fill=(66, 52, 40))
    d.rounded_rectangle([380, 230, 440, 300], radius=8, fill=(92, 60, 52))   # mug
    d.ellipse([432, 248, 462, 280], outline=(92, 60, 52), width=7)
    d.polygon([(520, 300), (540, 240), (560, 300)], fill=(40, 62, 44))       # plant
    d.ellipse([500, 170, 580, 250], fill=(44, 70, 48))
    d.rectangle([515, 262, 565, 300], fill=(70, 50, 40))
    return im


def main():
    os.makedirs(os.path.join(OUT, "nested", "level-2"), exist_ok=True)
    dim_room().save(os.path.join(OUT, "dim-room.jpg"), quality=90)
    gradient(320, 200).save(os.path.join(OUT, "gradient-dark.jpg"), quality=90)

    # PNG with a transparent hole: transparency must survive brightening.
    rgba = Image.new("RGBA", (240, 160), (60, 70, 90, 255))
    ImageDraw.Draw(rgba).ellipse([70, 30, 170, 130], fill=(0, 0, 0, 0))
    rgba.save(os.path.join(OUT, "checker-alpha.png"))

    # Palette PNG with one transparent palette entry.
    pal = blocks(200, 120).convert("P", palette=Image.ADAPTIVE, colors=8)
    pal.info["transparency"] = 0
    pal.save(os.path.join(OUT, "palette-transparent.png"), transparency=0)

    # JPEG stored landscape with EXIF Orientation=6: viewers show it portrait.
    exif = Image.Exif()
    exif[0x0112] = 6
    rot = blocks(200, 120)
    ImageDraw.Draw(rot).rectangle([0, 0, 30, 30], fill=(200, 200, 200))  # marker in stored top-left
    rot.save(os.path.join(OUT, "rotated-exif6.jpg"), quality=90, exif=exif.tobytes())

    blocks(160, 100).save(os.path.join(OUT, "nested", "blocks-level1.jpg"), quality=90)
    gradient(120, 80, 0.3).save(os.path.join(OUT, "nested", "level-2", "UPPER-CASE.JPG"), quality=90)
    print("wrote samples to", OUT)


if __name__ == "__main__":
    main()
