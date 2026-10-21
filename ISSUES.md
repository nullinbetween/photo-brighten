# Known limitations — photo-brighten

## Limitations

1. **The browser version only processes the top level of a folder**; the script goes 5 levels deep. This difference is
   deliberate and listed in the README.
2. **Only the browser version has contrast**, and the defaults differ (browser contrast 1.06). The same photo processed
   both ways will not come out identical.
3. **Colour profiles**: the browser version writes sRGB without an ICC profile; the script keeps the original RGB ICC profile.
4. **Not supported**: HEIC, WebP, TIFF, GIF, RAW.
5. **Overwriting is not asked about**: same-name files in `brighten/` are overwritten (the count is shown before processing).
6. **Download mode** (Safari/Firefox): one download per photo; the page only knows it started each download, not that
   the file was saved, and how same-name files are named is up to the browser.
7. **Brightness dialog in the script version**: an empty answer uses the default 1.45; a value outside 0.1–5.0, or not a
   number, ends with an error.

## Test coverage

- `tests/test_brighten.py`: 18 tests (JPEG/PNG format, alpha channel, palette, RGB and greyscale tRNS transparency,
  EXIF orientation, subfolder depth, skipped hidden files, failure count, overwrite count, originals untouched,
  symbolic links in `brighten/` that point back at the originals, argument checks). Passing on Python 3.9.6 with Pillow 11.3.0.
- `.command` end to end: run in Terminal with a stand-in `osascript` that returns a test folder and a brightness; all
  synthetic images succeeded, exit code 0. **The real macOS dialogs are not tested automatically.**
- `tests/core.test.html`: 10 tests, passing in a Chromium-based browser, including a simulated Safari run
  (`showDirectoryPicker` removed → file picker → downloads).
- **Real Safari and Firefox: not tested.**
- **Symbolic links inside `brighten/` in the browser version: not tested.** The script refuses to write through them;
  the browser version writes through the folder handle the browser gives it.
- **Chrome “choose a folder and write back to brighten/”** needs a permission prompt from the user and is **not tested
  automatically**; the write function is only tested with a stand-in.
- Performance and memory with many or very large photos: **not tested**.
