#!/usr/bin/env python3
"""Batch-brighten JPEG/PNG images into a brighten/ subfolder. Local only.

Usage:
    python3 brighten.py FOLDER [--brightness 1.45]

Behaviour (kept identical to README):
- Looks for .jpg/.jpeg/.png (any letter case) in FOLDER and up to 5 levels of
  subfolders. Hidden files (names starting with ".") and any folder named
  "brighten" are skipped.
- Writes to FOLDER/brighten/, keeping the subfolder structure and file names.
  Existing files with the same name in brighten/ are overwritten; the count is
  printed before and after processing. Originals are never modified: nothing is
  written if brighten/ is a symbolic link, or through a link that leads out of it.
- Output format follows the file extension: .png -> PNG (transparency kept, including
  palette/RGB/greyscale PNGs with a tRNS transparent colour),
  .jpg/.jpeg -> JPEG quality 95. EXIF orientation is applied to the pixels and
  the EXIF block (including any GPS data) is not copied. An RGB ICC colour
  profile is kept; CMYK/greyscale sources are converted to RGB without one.
- Brightness multiplies every RGB value (1.0 = unchanged). Alpha is untouched.
- Exit code 0 when every image succeeded, 1 when any failed, 2 on bad input.

Requires Pillow (see requirements.txt). This script never installs packages.
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageEnhance, ImageOps
except ImportError:  # pragma: no cover - exercised manually
    sys.stderr.write(
        "Pillow is not installed for this python3.\n"
        "Install it yourself, then run again:\n"
        "  python3 -m pip install --user -r requirements.txt\n"
    )
    sys.exit(2)

IMAGE_EXTS = (".jpg", ".jpeg", ".png")
OUT_DIRNAME = "brighten"
MAX_DEPTH = 5
BRIGHTNESS_MIN, BRIGHTNESS_MAX = 0.1, 5.0


def find_images(src):
    """Return sorted absolute paths of images under src (max depth 5)."""
    found = []
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        parts = [] if rel == "." else rel.split(os.sep)
        dirs[:] = sorted(d for d in dirs if d != OUT_DIRNAME and not d.startswith("."))
        if len(parts) >= MAX_DEPTH:
            dirs[:] = []
        for fn in files:
            if fn.startswith("."):
                continue
            if fn.lower().endswith(IMAGE_EXTS):
                found.append(os.path.join(root, fn))
    return sorted(found)


def output_format(path):
    return "PNG" if path.lower().endswith(".png") else "JPEG"


def has_transparency(im):
    """True for an alpha channel, and for palette/RGB/greyscale PNGs that mark a colour as transparent (tRNS)."""
    return im.mode in ("RGBA", "LA", "PA", "RGBa", "La") or "transparency" in im.info


def brighten_image(src_path, dst_path, brightness):
    """Brighten one image and save it; raises on any failure."""
    with Image.open(src_path) as im:
        im.load()
        # Keep an RGB colour profile only; a CMYK/grey profile would be wrong on RGB output.
        icc = im.info.get("icc_profile") if im.mode in ("RGB", "RGBA", "P", "PA") else None
        fmt = output_format(dst_path)
        keep_alpha = fmt == "PNG" and has_transparency(im)
        # Convert before rotating so a tRNS colour key becomes a real alpha channel first.
        im = im.convert("RGBA") if keep_alpha else im
        im = ImageOps.exif_transpose(im)
        if keep_alpha:
            alpha = im.getchannel("A")
            out = ImageEnhance.Brightness(im.convert("RGB")).enhance(brightness).convert("RGBA")
            out.putalpha(alpha)
        else:
            out = ImageEnhance.Brightness(im.convert("RGB")).enhance(brightness)
        kwargs = {"icc_profile": icc} if icc else {}
        if fmt == "JPEG":
            kwargs["quality"] = 95
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        out.save(dst_path, format=fmt, **kwargs)


class UnsafeOutput(Exception):
    """Writing here could touch an original (for example through a symbolic link)."""


def check_output_root(out_root):
    """brighten/ must be a real folder inside the source folder, never a link to somewhere else."""
    if os.path.islink(out_root):
        raise UnsafeOutput("brighten/ is a symbolic link; refusing to write through it")
    if os.path.exists(out_root) and not os.path.isdir(out_root):
        raise UnsafeOutput("brighten exists but is not a folder")


def check_target(src_path, dst, out_real):
    """Refuse a target that is a link, resolves outside brighten/, or is the original itself."""
    if os.path.islink(dst):
        raise UnsafeOutput("the output file is a symbolic link; refusing to write through it")
    parent = os.path.realpath(os.path.dirname(dst))
    if parent != out_real and not parent.startswith(out_real + os.sep):
        raise UnsafeOutput("the output path leads outside brighten/ (a symbolic link inside it?)")
    if os.path.exists(dst) and os.path.samefile(dst, src_path):
        raise UnsafeOutput("the output would overwrite the original")


def run(src, brightness, log=print):
    """Process a folder. Returns (ok, failed, overwritten, total)."""
    src = os.path.abspath(src)
    out_root = os.path.join(src, OUT_DIRNAME)
    files = find_images(src)
    if not files:
        log(f"⚠ No JPG/PNG found in this folder (including {MAX_DEPTH} levels of subfolders).")
        return 0, 0, 0, 0
    try:
        check_output_root(out_root)
    except UnsafeOutput as e:
        log(f"❌ {e}. Nothing was written; your originals are untouched.")
        return 0, len(files), 0, len(files)
    out_real = os.path.join(os.path.realpath(src), OUT_DIRNAME)
    targets = [(f, os.path.join(out_root, os.path.relpath(f, src))) for f in files]
    existing = sum(1 for _, d in targets if os.path.exists(d))
    log(f"📂 Found {len(files)} image(s) including subfolders → writing to {out_root}/")
    if existing:
        log(f"⚠ brighten/ already has {existing} file(s) with the same name; they will be overwritten.")
    ok = failed = overwritten = 0
    for i, (f, dst) in enumerate(targets, 1):
        rel = os.path.relpath(f, src)
        existed = os.path.exists(dst)
        try:
            check_target(f, dst, out_real)
            brighten_image(f, dst, brightness)
            ok += 1
            overwritten += 1 if existed else 0
        except Exception as e:  # noqa: BLE001 - report every failure and continue
            failed += 1
            log(f"  ❌ {rel}: {e}")
        if i % 20 == 0 or i == len(targets):
            log(f"  …{i}/{len(targets)}")
    log(f"\nDone: {ok} succeeded / {failed} failed / {len(files)} total ({overwritten} overwritten) → {out_root}/")
    return ok, failed, overwritten, len(files)


def parse_args(argv):
    p = argparse.ArgumentParser(description="Batch-brighten JPEG/PNG into FOLDER/brighten/.")
    p.add_argument("folder")
    p.add_argument("--brightness", default="1.45",
                   help=f"multiplier {BRIGHTNESS_MIN}–{BRIGHTNESS_MAX}, 1.0 = unchanged (default 1.45)")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        b = float(a.brightness)
    except ValueError:
        b = float("nan")
    if not (BRIGHTNESS_MIN <= b <= BRIGHTNESS_MAX):
        print(f"❌ Brightness must be a number from {BRIGHTNESS_MIN} to {BRIGHTNESS_MAX} (got: {a.brightness}).", file=sys.stderr)
        return 2
    if not os.path.isdir(a.folder):
        print(f"❌ Folder not found: {a.folder}", file=sys.stderr)
        return 2
    print(f"Brightness: {b}")
    ok, failed, _, total = run(a.folder, b)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
