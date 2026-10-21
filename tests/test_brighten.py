"""Tests for brighten.py using synthetic images generated in a temp folder.

    python3 -m unittest discover -s tests -v
"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import brighten  # noqa: E402


def quiet_run(folder, b):
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = brighten.run(folder, b, log=print)
    return r, buf.getvalue()


class BrightenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, *p):
        full = os.path.join(self.d, *p)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return full

    def test_jpeg_brightness_multiplies(self):
        Image.new("RGB", (40, 30), (100, 50, 20)).save(self.path("a.jpg"), quality=100)
        (ok, failed, _, total), _ = quiet_run(self.d, 1.5)
        self.assertEqual((ok, failed, total), (1, 0, 1))
        with Image.open(self.path("brighten", "a.jpg")) as out:
            self.assertEqual(out.format, "JPEG")
            r, g, b = out.getpixel((20, 15))
            self.assertAlmostEqual(r, 150, delta=3)
            self.assertAlmostEqual(g, 75, delta=3)
            self.assertAlmostEqual(b, 30, delta=3)

    def test_png_keeps_alpha_and_format(self):
        im = Image.new("RGBA", (20, 20), (100, 100, 100, 255))
        ImageDraw.Draw(im).rectangle([0, 0, 9, 19], fill=(0, 0, 0, 0))
        im.putpixel((15, 5), (100, 100, 100, 128))
        im.save(self.path("t.png"))
        quiet_run(self.d, 1.5)
        with Image.open(self.path("brighten", "t.png")) as out:
            self.assertEqual(out.format, "PNG")
            self.assertEqual(out.mode, "RGBA")
            self.assertEqual(out.getpixel((2, 2))[3], 0)
            self.assertEqual(out.getpixel((15, 5))[3], 128)
            self.assertEqual(out.getpixel((15, 15)), (150, 150, 150, 255))

    def test_palette_png_transparency_kept(self):
        im = Image.new("P", (10, 10), 1)
        im.putpalette([0, 0, 0, 80, 80, 80] + [0] * 762)
        im.putpixel((0, 0), 0)
        im.save(self.path("p.png"), transparency=0)
        quiet_run(self.d, 2.0)
        with Image.open(self.path("brighten", "p.png")) as out:
            out = out.convert("RGBA")
            self.assertEqual(out.getpixel((0, 0))[3], 0)
            self.assertEqual(out.getpixel((5, 5)), (160, 160, 160, 255))

    def test_rgb_png_with_trns_colour_key_keeps_transparency(self):
        im = Image.new("RGB", (10, 10), (80, 80, 80))
        im.putpixel((0, 0), (0, 0, 0))
        im.save(self.path("key.png"), transparency=(0, 0, 0))
        quiet_run(self.d, 2.0)
        with Image.open(self.path("brighten", "key.png")) as out:
            out = out.convert("RGBA")
            self.assertEqual(out.getpixel((0, 0))[3], 0)
            self.assertEqual(out.getpixel((5, 5)), (160, 160, 160, 255))

    def test_greyscale_png_with_trns_keeps_transparency(self):
        im = Image.new("L", (10, 10), 60)
        im.putpixel((0, 0), 0)
        im.save(self.path("grey.png"), transparency=0)
        quiet_run(self.d, 2.0)
        with Image.open(self.path("brighten", "grey.png")) as out:
            out = out.convert("RGBA")
            self.assertEqual(out.getpixel((0, 0))[3], 0)
            self.assertEqual(out.getpixel((5, 5)), (120, 120, 120, 255))

    def test_png_content_named_jpg_becomes_jpeg(self):
        Image.new("RGB", (8, 8), (10, 20, 30)).save(self.path("really-png.jpg"), format="PNG")
        quiet_run(self.d, 1.2)
        with Image.open(self.path("brighten", "really-png.jpg")) as out:
            self.assertEqual(out.format, "JPEG")

    def test_exif_orientation_applied_and_exif_dropped(self):
        exif = Image.Exif()
        exif[0x0112] = 6
        exif[0x010F] = "SyntheticCam"
        Image.new("RGB", (60, 20), (50, 50, 50)).save(self.path("r.jpg"), exif=exif.tobytes())
        quiet_run(self.d, 1.1)
        with Image.open(self.path("brighten", "r.jpg")) as out:
            self.assertEqual(out.size, (20, 60))
            self.assertEqual(len(out.getexif()), 0)

    def test_subfolders_depth_limit_and_structure(self):
        for depth in range(0, 7):
            parts = ["d%d" % i for i in range(depth)]
            Image.new("RGB", (4, 4)).save(self.path(*parts, "img%d.jpg" % depth))
        (ok, failed, _, total), _ = quiet_run(self.d, 1.2)
        self.assertEqual(total, 6)  # depths 0..5; depth 6 is beyond the limit
        self.assertTrue(os.path.exists(self.path("brighten", "d0", "d1", "img2.jpg")))
        self.assertFalse(os.path.exists(self.path("brighten", "d0", "d1", "d2", "d3", "d4", "d5", "img6.jpg")))

    def test_skips_output_folder_hidden_files_and_non_images(self):
        Image.new("RGB", (4, 4)).save(self.path("a.JPG"))
        Image.new("RGB", (4, 4)).save(self.path("brighten", "old.jpg"))
        with open(self.path("._a.jpg"), "wb") as f:
            f.write(b"\x00\x05\x16\x07AppleDouble")
        with open(self.path("notes.txt"), "w") as f:
            f.write("x")
        (ok, failed, _, total), _ = quiet_run(self.d, 1.2)
        self.assertEqual((ok, failed, total), (1, 0, 1))
        self.assertTrue(os.path.exists(self.path("brighten", "a.JPG")))

    def test_corrupt_file_counted_as_failure(self):
        Image.new("RGB", (4, 4)).save(self.path("good.jpg"))
        with open(self.path("broken.jpg"), "wb") as f:
            f.write(b"not an image")
        (ok, failed, _, total), log = quiet_run(self.d, 1.2)
        self.assertEqual((ok, failed, total), (1, 1, 2))
        self.assertIn("broken.jpg", log)
        self.assertIn("1 failed", log)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(brighten.main([self.d, "--brightness", "1.2"]), 1)

    def test_overwrite_is_reported(self):
        Image.new("RGB", (4, 4)).save(self.path("a.jpg"))
        quiet_run(self.d, 1.2)
        (ok, failed, overwritten, total), log = quiet_run(self.d, 1.3)
        self.assertEqual(overwritten, 1)
        self.assertIn("will be overwritten", log)

    def test_originals_untouched(self):
        p = self.path("a.png")
        Image.new("RGB", (4, 4), (10, 10, 10)).save(p)
        with open(p, "rb") as f:
            before = f.read()
        quiet_run(self.d, 2.0)
        with open(p, "rb") as f:
            self.assertEqual(f.read(), before)

    def _orig_bytes(self, *p):
        with open(self.path(*p), "rb") as f:
            return f.read()

    def test_brighten_symlink_to_source_is_refused(self):
        Image.new("RGB", (8, 8), (40, 40, 40)).save(self.path("a.jpg"))
        before = self._orig_bytes("a.jpg")
        os.symlink(self.d, os.path.join(self.d, "brighten"))          # brighten -> the source folder itself
        (ok, failed, _, total), log = quiet_run(self.d, 2.0)
        self.assertEqual((ok, failed), (0, total))
        self.assertIn("symbolic link", log)
        self.assertEqual(self._orig_bytes("a.jpg"), before)

    def test_link_inside_brighten_is_refused_for_that_file(self):
        Image.new("RGB", (8, 8), (40, 40, 40)).save(self.path("top.jpg"))
        Image.new("RGB", (8, 8), (40, 40, 40)).save(self.path("sub", "deep.jpg"))
        before = self._orig_bytes("sub", "deep.jpg")
        os.makedirs(self.path("brighten"), exist_ok=True)
        os.symlink(os.path.join(self.d, "sub"), os.path.join(self.d, "brighten", "sub"))   # brighten/sub -> ../sub
        (ok, failed, _, total), log = quiet_run(self.d, 2.0)
        self.assertEqual((ok, failed, total), (1, 1, 2))
        self.assertIn("outside brighten/", log)
        self.assertEqual(self._orig_bytes("sub", "deep.jpg"), before)

    def test_output_file_linked_to_original_is_refused(self):
        Image.new("RGB", (8, 8), (40, 40, 40)).save(self.path("a.jpg"))
        before = self._orig_bytes("a.jpg")
        os.makedirs(self.path("brighten"), exist_ok=True)
        os.symlink(os.path.join(self.d, "a.jpg"), os.path.join(self.d, "brighten", "a.jpg"))
        (ok, failed, _, total), log = quiet_run(self.d, 2.0)
        self.assertEqual((ok, failed), (0, 1))
        self.assertEqual(self._orig_bytes("a.jpg"), before)

    def test_invalid_brightness_rejected(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(brighten.main([self.d, "--brightness", "abc"]), 2)
            self.assertEqual(brighten.main([self.d, "--brightness", "0"]), 2)
            self.assertEqual(brighten.main([self.d, "--brightness", "9"]), 2)

    def test_missing_folder_rejected(self):
        self.assertEqual(brighten.main([os.path.join(self.d, "nope")]), 2)

    def test_empty_folder(self):
        (ok, failed, _, total), log = quiet_run(self.d, 1.2)
        self.assertEqual(total, 0)
        self.assertIn("No JPG/PNG", log)


if __name__ == "__main__":
    unittest.main()
