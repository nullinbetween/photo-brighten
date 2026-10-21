# Photo Brighten — fix a folder of dim photos in one go

Brighten every JPEG/PNG in a folder and write the results to a `brighten/` folder next to them.
**Your originals are never modified, and the photos you choose are processed on your own computer — never uploaded.**

**Live demo:** <https://nullinbetween.github.io/photo-brighten/> — folder mode in Chrome/Edge; other browsers fall back to download mode (simulated in tests, not yet tried in real Safari/Firefox). Your photos are processed in the browser and never uploaded.

[繁體中文說明 → README.zh-TW.md](README.zh-TW.md)

![Before and after: a dim synthetic room scene brightened with factor 1.45](docs/images/before-after.jpg)

*The “after” half was produced by `brighten.py` itself from a synthetic test image (`docs/make_before_after.py`).*

Two ways to run it:

| | Browser — `batch-brighten.html` | Script — `brighten.py` / `batch-brighten.command` |
|---|---|---|
| Start | open the HTML file | `python3 brighten.py FOLDER`, or double-click the `.command` on macOS |
| Controls | brightness + contrast sliders with live preview | brightness only |
| Defaults | brightness 1.45, contrast 1.06 | brightness 1.45 |
| Subfolders | top level of the chosen folder only | up to 5 levels deep, structure preserved |
| Output | Chrome/Edge: writes to `brighten/`. Safari/Firefox: starts one download per file | always `brighten/` |
| Needs | a browser | Python 3.9+ and Pillow |

<img src="docs/images/browser-ui.png" alt="Browser version with live preview and brightness/contrast sliders" width="640">

---

## Design notes — how we thought about it

| Decision | Why | Trade-off we accepted |
|---|---|---|
| **Never touch the originals; write to `brighten/`** | Safe to run twice, easy to compare side by side, and “undo” is deleting one folder. The script also refuses to write through a symbolic link in `brighten/` that would lead back to an original. | Extra disk space. |
| **Ask for the brightness every run** | Each batch is shot in different light; one fixed value is wrong half the time. | One prompt per run. |
| **Two entry points** | The browser gives instant visual feedback with nothing to install; the script handles folders of folders without opening anything. | Two implementations; their differences are listed above instead of hidden. |
| **Output format follows the file name** | A `.png` must contain PNG and keep its transparency. The original browser version wrote JPEG bytes into `.png` files, and the script threw transparency away. | A mis-named input is converted to match its name. |
| **Brightness via a per-pixel lookup table, not the canvas `filter`** | Some browsers (Safari) silently ignore `ctx.filter`: the page said “done” while every file came out unchanged. A lookup table needs only standard pixel access and is the same multiply the script uses. Tested in Chromium (including a simulated Safari path); real Safari/Firefox not yet. | Slightly more code. |
| **Apply EXIF orientation, then drop EXIF** | Portrait photos stay upright, and location data (GPS) does not leak into copies you share. | Camera metadata is not kept. |
| **Report failures honestly** | A corrupt file used to count as a success (and could stall the browser version forever). Now every file is either written (in download mode: handed to the browser) or listed as failed with the reason. | — |
| **Say before overwriting** | Re-running overwrites files with the same name in `brighten/`; the count is shown before and after. | No per-file “keep both”. |
| **Never install anything silently** | The original script ran `pip install` on every launch. Installing is your decision; the tested version is pinned in `requirements.txt`. | One manual step the first time. |

## Tutorial

Practice images are in [`examples/sample-photos/`](examples/sample-photos/) — synthetic colour blocks and gradients
(no photographs), including a transparent PNG, a palette PNG, a JPEG with an EXIF rotation, nested folders and an
upper-case extension.

### A. In the browser (nothing to install)

1. Open `batch-brighten.html` in **Chrome or Edge**.
2. Click the dashed box and choose your photo folder (or drag the folder onto it).
3. Move the **Brightness** and **Contrast** sliders while watching the preview.
4. Press **Process & export**. The results appear in a new `brighten/` folder inside the folder you chose.
   The message lists how many succeeded and failed, and how many existing files were overwritten.

In **Safari or Firefox** (no folder access): click the box and choose the photo *files* (multi-select works), then press the
button; each result is handed to the browser as a download. Your browser may ask once whether to allow multiple downloads.
The page can only tell that it *started* each download, not that the file was saved, so check your Downloads folder.
(This mode is covered by a simulated test; it has not yet been tried in real Safari or Firefox.)

### B. With the script (any OS with Python) — verified on macOS

```bash
python3 -m pip install --user -r requirements.txt
python3 brighten.py examples/sample-photos --brightness 1.45
```

Output:

```
📂 Found 7 image(s) including subfolders → writing to …/examples/sample-photos/brighten/
Done: 7 succeeded / 0 failed / 7 total (0 overwritten) → …/examples/sample-photos/brighten/
```

Exit code `0` = all succeeded, `1` = some failed, `2` = bad arguments or Pillow missing. Brightness must be 0.1–5.0.

### C. Double-click on macOS

Double-click `batch-brighten.command`: it checks for Pillow (it tells you the install command instead of installing it),
asks for a folder and a brightness, and runs `brighten.py`.

If macOS refuses to open a `.command` file you downloaded from the internet, either run it from Terminal —

```bash
bash batch-brighten.command
```

— or allow it once under **System Settings → Privacy & Security → Open Anyway**. (This is standard macOS behaviour for
unsigned downloads; it was not reproduced on a downloaded copy during testing.)

## Rules both versions follow

- Only `.jpg`, `.jpeg`, `.png` (any letter case). Hidden files such as `._IMG_0001.JPG` and any folder named `brighten` are skipped.
- `.png` → PNG with transparency kept — an alpha channel, or a transparent colour (tRNS) in palette, RGB or greyscale PNGs; `.jpg`/`.jpeg` → JPEG at quality 95.
- Brightness multiplies each RGB value (1.0 = unchanged, capped at 255); alpha is never touched.
- The browser version applies contrast around mid-grey after brightness and outputs sRGB without an ICC profile; the
  script keeps the original RGB colour profile. Wide-gamut photos can therefore look slightly different between the two.

## Tests

```bash
python3 -m unittest discover -s tests -v          # 18 tests, script version
python3 -m http.server 8765 --bind 127.0.0.1      # then open /tests/core.test.html — 10 tests, browser version
```

The browser suite includes a simulated Safari run (folder access removed → file picker → downloads).

## From personal tool to open source

The original was a quick personal helper: an HTML page and a double-click script with the Python inlined. Preparing it
for release meant fixing what a careful read found — wrong output format for PNGs, transparency lost, a click that failed
in Safari, failures counted as successes, sideways portrait photos, unchanged output in Safari, a silent `pip install` —
then moving the processing into a testable `brighten.py`, documenting where the two versions differ, and replacing real
photos with generated test images. Known limits are in [`ISSUES.md`](ISSUES.md).

## How it was built

Designed by the author and written with AI coding assistants. The open-source preparation ran as a small multi-agent
workflow: **Codex** scoped the work and reviewed it independently, **Claude** made allowlisted copies, fixed defects and
wrote the tests and docs, and the author made the final calls.

## Licence

[MIT](LICENSE). The script uses [Pillow](https://pypi.org/project/pillow/) (MIT-CMU), installed by you, not bundled —
see [`ASSET_REGISTER.md`](ASSET_REGISTER.md).

---

Made by [@nullinbetween](https://x.com/nullinbetween) · apps by meredith · [appsbymeredith.carrd.co](https://appsbymeredith.carrd.co)
