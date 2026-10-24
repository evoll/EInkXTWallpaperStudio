"""Explicit e-paper export encoders: indexed BMP3 and CrossPoint PXC."""
from __future__ import annotations
import struct
import numpy as np
from PIL import Image
from .engine import four_level_dither


def save_indexed_bmp(image: Image.Image, path: str, colors: list[tuple[int, int, int]], color_distance: bool = False) -> None:
    """Write uncompressed BMP3 indexed image with explicit 4-bit or 8-bit palette."""
    if not colors or len(colors) > 256:
        raise ValueError("Indexed BMP palette must contain between 1 and 256 colors")
    if color_distance:
        pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
        palette_rgb = np.asarray(colors, dtype=np.float32)
        idx = np.sum((pixels[..., None, :] - palette_rgb[None, None, :, :]) ** 2, axis=3).argmin(axis=2).astype(np.uint8)
    else:
        gray = np.asarray(image.convert("L"), dtype=np.uint8)
        palette_luma = np.asarray([round(0.299*r + 0.587*g + 0.114*b) for r,g,b in colors], dtype=np.float32)
        idx = np.abs(gray[..., None].astype(np.float32) - palette_luma).argmin(axis=2).astype(np.uint8)
    h, w = idx.shape
    bpp = 4 if len(colors) <= 16 else 8
    row_bytes = ((w * bpp + 31) // 32) * 4
    palette_entries = 1 << bpp
    palette_bytes = b"".join(bytes((b, g, r, 0)) for r,g,b in colors)
    palette_bytes += bytes(max(0, palette_entries - len(colors)) * 4)
    pixel_bytes = bytearray()
    for row in idx[::-1]:
        packed = bytearray()
        if bpp == 4:
            for x in range(0, w, 2):
                hi = int(row[x]) & 0x0F
                lo = int(row[x+1]) & 0x0F if x+1 < w else 0
                packed.append((hi << 4) | lo)
        else:
            packed.extend(row.tobytes())
        packed.extend(b"\x00" * (row_bytes - len(packed)))
        pixel_bytes.extend(packed)
    offset = 14 + 40 + len(palette_bytes)
    file_size = offset + len(pixel_bytes)
    with open(path, "wb") as f:
        f.write(b"BM" + struct.pack("<IHHI", file_size, 0, 0, offset))
        f.write(struct.pack("<IiiHHIIiiII", 40, w, h, 1, bpp, 0, len(pixel_bytes), 2835, 2835, len(colors), len(colors)))
        f.write(palette_bytes)
        f.write(pixel_bytes)


def save_pxc(image: Image.Image, path: str, dither: str = "Floyd–Steinberg") -> None:
    """CrossPoint PXC: uint16 LE width/height + row-aligned packed 2bpp, MSB first."""
    gray4 = four_level_dither(image.convert("L"), dither)
    arr = np.asarray(gray4, dtype=np.uint8)
    h, w = arr.shape
    if w > 65535 or h > 65535:
        raise ValueError("PXC dimensions must fit into unsigned 16-bit values")
    levels = np.rint(arr.astype(np.float32) / 85.0).astype(np.uint8)
    row_bytes = (w + 3) // 4
    payload = bytearray()
    for row in levels:
        for x in range(row_bytes):
            p = row[x*4:x*4+4]
            byte = 0
            for j, val in enumerate(p):
                byte |= (int(val) & 3) << (6 - 2*j)
            payload.append(byte)
    with open(path, "wb") as f:
        f.write(struct.pack("<HH", w, h))
        f.write(payload)


def save_png_for_mode(image: Image.Image, path: str, mode: str) -> None:
    """Save PNG with a bit depth/palette appropriate for the selected output profile."""
    if mode == "4 gray levels":
        colors = [(0,0,0),(85,85,85),(170,170,170),(255,255,255)]
        _save_palette_png(image, path, colors, bits=2, color_distance=False)
    elif mode == "16 gray levels":
        colors = [(v,v,v) for v in range(0,256,17)]
        _save_palette_png(image, path, colors, bits=4, color_distance=False)
    elif mode == "Spectra 6 palette":
        colors = [(0,0,0),(255,255,255),(220,0,0),(255,230,0),(0,80,200),(0,150,70)]
        _save_palette_png(image, path, colors, bits=4, color_distance=True)
    elif mode == "256 gray levels (8-bit PNG)":
        image.convert("L").save(path, format="PNG", optimize=True, bits=8)
    else:
        image.convert("RGB").save(path, format="PNG", optimize=True)


def _save_palette_png(image: Image.Image, path: str, colors: list[tuple[int,int,int]], bits: int, color_distance: bool) -> None:
    if color_distance:
        pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
        palette = np.asarray(colors, dtype=np.float32)
        indices = np.sum((pixels[..., None, :] - palette[None, None, :, :]) ** 2, axis=3).argmin(axis=2).astype(np.uint8)
    else:
        gray = np.asarray(image.convert("L"), dtype=np.uint8)
        luminance = np.asarray([round(0.299*r + 0.587*g + 0.114*b) for r,g,b in colors], dtype=np.float32)
        indices = np.abs(gray[..., None].astype(np.float32) - luminance).argmin(axis=2).astype(np.uint8)
    out = Image.fromarray(indices, mode="P")
    palette = []
    for r,g,b in colors: palette.extend((r,g,b))
    palette.extend([0] * (768-len(palette)))
    out.putpalette(palette)
    out.save(path, format="PNG", optimize=True, bits=bits)
