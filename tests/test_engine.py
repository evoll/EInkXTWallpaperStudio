import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PIL import Image
import numpy as np
from xtwallpaper.engine import four_level_dither, render_image, histogram_data

class EngineTests(unittest.TestCase):
    def test_all_dither_modes_have_four_levels(self):
        src = Image.fromarray(np.tile(np.arange(32, dtype=np.uint8) * 8, (24, 1)))
        for mode in ["None", "Bayer 4×4", "Floyd–Steinberg", "Atkinson", "Jarvis–Judice–Ninke", "Stucki", "Burkes"]:
            out = four_level_dither(src, mode)
            self.assertEqual(out.mode, "L")
            self.assertEqual(out.size, src.size)
            self.assertTrue(set(np.unique(np.asarray(out))).issubset({0, 85, 170, 255}), mode)

    def test_render_output_dimensions_and_levels(self):
        src = Image.new("RGB", (40, 60), (120, 80, 200))
        settings = {"size": (64, 96), "fit_mode": "Cover", "rotation": 0, "zoom": 100,
                    "offset_x": 0, "offset_y": 0, "brightness": 0, "contrast": 0,
                    "gamma": 100, "sharpness": 0, "noise_reduction": 0, "dither": "Atkinson"}
        out = render_image(src, settings)
        self.assertEqual(out.size, (64, 96))
        self.assertTrue(set(np.unique(np.asarray(out))).issubset({0, 85, 170, 255}))

    def test_pre_quantization_image_keeps_tonal_levels_for_histogram(self):
        src = Image.fromarray(np.tile(np.arange(32, dtype=np.uint8) * 8, (24, 1))).convert("RGB")
        settings = {"size": (32, 24), "fit_mode": "Cover", "rotation": 0, "zoom": 100,
                    "offset_x": 0, "offset_y": 0, "brightness": 0, "contrast": 0,
                    "gamma": 100, "sharpness": 0, "noise_reduction": 0, "dither": "Atkinson",
                    "output_mode": "4 gray levels"}
        output = render_image(src, settings, preview=True)
        histogram_source = render_image(src, settings, preview=True, pre_quantization=True)
        self.assertEqual(output.mode, "L")
        self.assertLessEqual(len(np.unique(np.asarray(output))), 4)
        self.assertEqual(histogram_source.mode, "L")
        self.assertGreater(len(np.unique(np.asarray(histogram_source))), 4)

    def test_histogram_counts_and_display_scaling(self):
        # A dominant black bin should not make all other tones visually vanish.
        values = np.array([0] * 900 + list(range(1, 101)), dtype=np.uint8)
        image = Image.fromarray(values.reshape(10, 100), mode="L")
        counts, heights = histogram_data(image, 65)
        self.assertEqual(len(counts), 256)
        self.assertEqual(int(counts.sum()), image.width * image.height)
        self.assertEqual(int(heights.max()), 65)
        self.assertGreater(int(heights[50]), 0)
        self.assertEqual(int(counts[0]), 900)
        self.assertEqual(int(counts[50]), 1)

    def test_grayscale_and_color_output_profiles(self):
        src = Image.new("RGB", (32, 24), (137, 83, 211))
        base = {"size": (32, 24), "fit_mode": "Cover", "rotation": 0, "zoom": 100,
                "offset_x": 0, "offset_y": 0, "brightness": 0, "contrast": 0,
                "gamma": 100, "sharpness": 0, "noise_reduction": 0, "dither": "None"}
        out16 = render_image(src, {**base, "output_mode": "16 gray levels"})
        self.assertEqual(out16.mode, "L")
        self.assertLessEqual(len(np.unique(np.asarray(out16))), 16)
        out256 = render_image(src, {**base, "output_mode": "256 gray levels (8-bit PNG)"})
        self.assertEqual(out256.mode, "L")
        kaleido = render_image(src, {**base, "output_mode": "Kaleido 4096 colors (12-bit RGB)"})
        self.assertEqual(kaleido.mode, "RGB")
        self.assertTrue(np.all(np.asarray(kaleido) % 17 == 0))
        spectra = render_image(src, {**base, "output_mode": "Spectra 6 palette"})
        self.assertEqual(spectra.mode, "RGB")
        self.assertLessEqual(len(np.unique(np.asarray(spectra).reshape(-1, 3), axis=0)), 6)

if __name__ == "__main__": unittest.main()
