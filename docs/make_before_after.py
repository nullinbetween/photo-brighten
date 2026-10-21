#!/usr/bin/env python3
"""Render docs/images/before-after.jpg from the synthetic sample image.

The "after" half is produced by brighten.py itself (same code path as the
script version), so the picture shows real output, not a mock-up.

    python3 docs/make_before_after.py
"""
import os
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
import brighten  # noqa: E402

SRC = os.path.join(ROOT, "examples", "sample-photos", "dim-room.jpg")
BRIGHTNESS = 1.45


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 12 + 8 * len(text), 26], fill=(0, 0, 0))
    d.text((7, 7), text, fill=(255, 255, 255))
    return im


def main():
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "after.jpg")
        brighten.brighten_image(SRC, dst, BRIGHTNESS)
        with Image.open(SRC) as a, Image.open(dst) as b:
            before, after = a.convert("RGB"), b.convert("RGB")
    gap = 8
    out = Image.new("RGB", (before.width * 2 + gap, before.height), (255, 255, 255))
    out.paste(label(before, "Before"), (0, 0))
    out.paste(label(after, "After  (brightness %.2f)" % BRIGHTNESS), (before.width + gap, 0))
    path = os.path.join(HERE, "images", "before-after.jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path, quality=88)
    print("wrote", path)


if __name__ == "__main__":
    main()
