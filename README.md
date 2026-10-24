# EInkXT Wallpaper Studio

A cross-platform desktop and browser-based image preparation tool for E-Ink displays. The desktop app is built with Python, PySide6, Pillow and NumPy. The website is a static site with a client-side editor: images are processed locally in the browser and are not uploaded to a server. The web editor is an independent implementation; the original generator is used as an interaction reference, not copied as a codebase.

- **Project website:** https://evoll.github.io/EInkXTWallpaperStudio/
- **Repository:** https://github.com/evoll/EInkXTWallpaperStudio
- **Latest desktop release:** https://github.com/evoll/EInkXTWallpaperStudio/releases/latest

## Features

- Device presets for Xteink X3 and X4 variants, custom dimensions, portrait/landscape orientation and crop framing.
- Image adjustment presets, brightness, contrast, gamma, sharpening and dithering (Atkinson default, Floyd–Steinberg, Bayer, Jarvis–Judice–Ninke, Stucki, Burkes and none).
- Grayscale, Kaleido-like 4096 RGB-value quantization, Spectra 6 palette approximation and full RGB preparation modes.
- PNG, BMP and CrossPoint PXC export in the desktop application. Check compatibility with your device and firmware before use; color profile names do not guarantee that a physical panel supports that file format.
- Batch processing and `.xtws` project settings in the desktop application.
- Russian and English desktop UI, with additional translations loaded from `lang/<code>.json`.
- Static Jekyll website is maintained separately in the `site-app` branch; the desktop application and release workflow live in `main`.

## Run desktop app from source

Python 3.12 is used in CI. Python 3.12 or newer is recommended.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python main.py
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=src python main.py
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Build executable locally

Install requirements first, then run:

```bash
pyinstaller --noconfirm --clean EInkXTWallpaperStudio.spec
```

Build separately on each target OS. GitHub Actions does not cross-compile these desktop binaries.

## Add a translation

Create `lang/<language-code>.json`. The keys should be canonical English UI strings, matching `lang/en.json`; set `__language_name__` to the language name. Missing keys fall back to English. For packaged builds, the `lang` folder is included by the PyInstaller spec.

## Web editor

The browser editor is in `[EInkXT Wallpaper Studio](https://evoll.github.io/EInkXTWallpaperStudio/editor.html)` and is served through GitHub Pages. It supports image loading, framing, device dimensions, presets, Atkinson/Floyd/Bayer/Jarvis/Stucki dithering, grayscale and approximate color modes, PNG/BMP/PXC downloads. Export is rendered at full selected dimensions and can take longer for very large custom resolutions. The web editor is an independent implementation; byte-for-byte parity with the desktop engine or original third-party generator is not claimed.

## Reference

The editor layout and workflow were informed by the public [Xteink X3 / X4 Wallpaper Generator](https://xtwallgen.madebybaker.dev/)/.

## License

See [LICENSE](LICENSE).
