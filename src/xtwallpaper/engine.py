"""Image preparation and output quantization for e-paper targets."""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# Starter dimensions only; verify exact resolution for the particular device/firmware.
DEVICE_PROFILES = {
    "Xteink X3 (528×792)": (528, 792),
    "Xteink X4 Classic (480×800)": (480, 800),
    "Xteink X4 Pro (480×800)": (480, 800),
    "Custom": (528, 792),
}
OUTPUT_MODES = {
    "4 gray levels": ("gray", 4),
    "16 gray levels": ("gray", 16),
    "256 gray levels (8-bit PNG)": ("gray", 256),
    "Kaleido 4096 colors (12-bit RGB)": ("kaleido", 4096),
    "Spectra 6 palette": ("spectra6", 6),
    "Full-color RGB (Gallery 3 / generic)": ("rgb", 0),
}
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)
KERNELS = {
    "Floyd–Steinberg": [(1,0,7/16),(-1,1,3/16),(0,1,5/16),(1,1,1/16)],
    "Atkinson": [(1,0,1/8),(2,0,1/8),(-1,1,1/8),(0,1,1/8),(1,1,1/8),(0,2,1/8)],
    "Jarvis–Judice–Ninke": [(1,0,7/48),(2,0,5/48),(-2,1,3/48),(-1,1,5/48),(0,1,7/48),(1,1,5/48),(2,1,3/48),(-2,2,1/48),(-1,2,3/48),(0,2,5/48),(1,2,3/48),(2,2,1/48)],
    "Stucki": [(1,0,8/42),(2,0,4/42),(-2,1,2/42),(-1,1,4/42),(0,1,8/42),(1,1,4/42),(2,1,2/42),(-2,2,1/42),(-1,2,2/42),(0,2,4/42),(1,2,2/42),(2,2,1/42)],
    "Burkes": [(1,0,8/32),(2,0,4/32),(-2,1,2/32),(-1,1,4/32),(0,1,8/32),(1,1,4/32),(2,1,2/32)],
}
SPECTRA6 = np.array([[0,0,0],[255,255,255],[220,0,0],[255,230,0],[0,80,200],[0,150,70]], dtype=np.float32)

def _quantize_gray(image: Image.Image, levels: int, method: str) -> Image.Image:
    arr = np.asarray(image.convert("L"), dtype=np.float32).copy()
    if levels <= 1: return Image.fromarray(np.zeros(arr.shape, dtype=np.uint8), "L")
    step = 255.0 / (levels - 1)
    if method == "None":
        out = np.rint(arr / step) * step
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "L")
    if method == "Bayer 4×4":
        yy, xx = np.indices(arr.shape)
        arr = np.clip(arr + (BAYER4[yy % 4, xx % 4] - 7.5) * (step / 16), 0, 255)
        return Image.fromarray(np.clip(np.rint(arr / step) * step, 0, 255).astype(np.uint8), "L")
    kernel = KERNELS.get(method)
    if not kernel:
        return Image.fromarray(np.clip(np.rint(arr / step) * step, 0, 255).astype(np.uint8), "L")
    h, w = arr.shape
    for y in range(h):
        for x in range(w):
            old = float(arr[y, x]); new = round(old / step) * step
            arr[y, x] = new; error = old - new
            for dx, dy, weight in kernel:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and ny < h: arr[ny, nx] = np.clip(arr[ny, nx] + error * weight, 0, 255)
    return Image.fromarray(np.clip(np.rint(arr / step) * step, 0, 255).astype(np.uint8), "L")

def _adjust(img: Image.Image, settings: dict) -> Image.Image:
    img = ImageEnhance.Brightness(img).enhance(max(.01, 1 + settings.get("brightness", 0) / 100))
    img = ImageEnhance.Contrast(img).enhance(max(.01, 1 + settings.get("contrast", 0) / 100))
    gamma = max(.1, settings.get("gamma", 100) / 100)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    img = Image.fromarray(np.clip(np.power(arr, 1 / gamma) * 255, 0, 255).astype(np.uint8), img.mode)
    noise = settings.get("noise_reduction", 0)
    if noise: img = img.filter(ImageFilter.MedianFilter(3 if noise < 60 else 5))
    sharpness = settings.get("sharpness", 0)
    if sharpness: img = ImageEnhance.Sharpness(img).enhance(1 + sharpness / 50)
    return img

def render_image(source: Image.Image, settings: dict, *, preview: bool = False, pre_quantization: bool = False) -> Image.Image:
    """Render to the selected output profile. Set pre_quantization=True to return the adjusted image before dithering/palette quantization."""
    width, height = settings["size"]
    fit_mode = settings.get("fit_mode", "Cover")
    bg = (0, 0, 0) if fit_mode == "Fit (black bars)" else (255, 255, 255)
    canvas = Image.new("RGB", (width, height), bg)
    src = source.convert("RGB")
    if settings.get("rotation", 0): src = src.rotate(-int(settings["rotation"]), expand=True, resample=Image.Resampling.BICUBIC)
    sw, sh = src.size
    factor = (max if fit_mode == "Cover" else min)(width / sw, height / sh) * settings.get("zoom", 100) / 100
    rw, rh = max(1, round(sw * factor)), max(1, round(sh * factor))
    src = src.resize((rw, rh), Image.Resampling.LANCZOS)
    x = round((width - rw) / 2 + settings.get("offset_x", 0)); y = round((height - rh) / 2 + settings.get("offset_y", 0))
    canvas.paste(src, (x, y))
    mode = settings.get("output_mode", "4 gray levels")
    kind, _ = OUTPUT_MODES.get(mode, ("gray", 4))
    if kind == "gray":
        img = _adjust(ImageOps.grayscale(canvas), settings)
        if pre_quantization:
            return img.convert("L")
        levels = OUTPUT_MODES[mode][1]
        return _quantize_gray(img, levels, "None" if preview else settings.get("dither", "Atkinson")) if levels < 256 else img.convert("L")
    img = _adjust(canvas, settings)
    if pre_quantization:
        return img.convert("RGB")
    if kind == "kaleido":
        # 16 quantization steps per RGB channel => 16^3 = 4096 possible RGB values.
        arr = np.asarray(img, dtype=np.uint16)
        arr = np.clip(np.rint(arr / 17.0) * 17, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, "RGB")
    if kind == "spectra6":
        arr = np.asarray(img, dtype=np.float32).reshape(-1, 3)
        # Nearest color in a simple six-color palette; controller-specific palettes may differ.
        idx = np.sum((arr[:, None, :] - SPECTRA6[None, :, :]) ** 2, axis=2).argmin(axis=1)
        return Image.fromarray(SPECTRA6[idx].reshape(height, width, 3).astype(np.uint8), "RGB")
    return img.convert("RGB")


def histogram_data(image: Image.Image, plot_height: int) -> tuple[np.ndarray, np.ndarray]:
    """Return 256 luminance bins and display heights with square-root scaling.

    The square-root display scale keeps dominant bins from visually flattening
    less frequent tones. Raw counts remain available for validation/tooltips.
    The tallest non-empty bin always reaches ``plot_height``.
    """
    gray = np.asarray(image.convert("L"), dtype=np.uint8).ravel()
    counts = np.bincount(gray, minlength=256)[:256]
    peak = int(counts.max()) if counts.size else 0
    if peak <= 0 or plot_height <= 0:
        return counts, np.zeros(256, dtype=np.int32)
    normalized = np.sqrt(counts.astype(np.float64) / peak)
    heights = np.rint(normalized * int(plot_height)).astype(np.int32)
    heights[counts > 0] = np.maximum(1, heights[counts > 0])
    return counts, heights

def four_level_dither(image: Image.Image, method: str = "Atkinson") -> Image.Image:
    """Backward-compatible helper for classic four-level grayscale output."""
    return _quantize_gray(image, 4, method)
