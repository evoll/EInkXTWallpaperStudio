import sys, tempfile, struct, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PIL import Image
from xtwallpaper.formats import save_pxc, save_indexed_bmp, save_png_for_mode

class ExportFormatTests(unittest.TestCase):
    def test_pxc_header_and_size_x4(self):
        image = Image.new("L", (480, 800), 255)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sleep.pxc"
            save_pxc(image, str(p), "None")
            data = p.read_bytes()
        self.assertEqual(struct.unpack("<HH", data[:4]), (480, 800))
        self.assertEqual(len(data), 4 + 480 * 800 // 4)
        self.assertTrue(all(b == 0xFF for b in data[4:]))

    def test_pxc_packs_four_levels_msb_first(self):
        image = Image.new("L", (4, 1))
        image.putdata([0, 85, 170, 255])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.pxc"
            save_pxc(image, str(p), "None")
            data = p.read_bytes()
        self.assertEqual(data[4], 0b00011011)

    def test_png_4_level_is_2bit_palette_and_16_level_is_4bit_palette(self):
        image = Image.new("L", (12, 5))
        image.putdata([int((i % 16) * 17) for i in range(60)])
        with tempfile.TemporaryDirectory() as td:
            p2 = Path(td) / "four.png"
            p4 = Path(td) / "sixteen.png"
            save_png_for_mode(image, str(p2), "4 gray levels")
            save_png_for_mode(image, str(p4), "16 gray levels")
            d2, d4 = p2.read_bytes(), p4.read_bytes()
        self.assertEqual(d2[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(d2[24], 2)  # IHDR bit depth
        self.assertEqual(d2[25], 3)  # indexed color
        self.assertEqual(d4[24], 4)
        self.assertEqual(d4[25], 3)

    def test_bmp_4bit_indexed_header(self):
        image = Image.new("L", (8, 2), 170)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.bmp"
            save_indexed_bmp(image, str(p), [(0,0,0),(85,85,85),(170,170,170),(255,255,255)])
            data = p.read_bytes()
        self.assertEqual(data[:2], b"BM")
        self.assertEqual(struct.unpack_from("<H", data, 28)[0], 4)
        self.assertEqual(struct.unpack_from("<I", data, 30)[0], 0)

if __name__ == "__main__": unittest.main()
