"""
NEBULA ASCII STUDIO — Automated Comprehensive Test Suite (Version 3.0)
Validates image processing, Rec. 709 luminance calculations, multi-scale detail,
all core rendering modes, multi-resolution export formats, and error handling.
"""

import os
import sys
import tempfile
import unittest
import numpy as np
from PIL import Image

from nebula.config import (
    CHARACTER_RAMPS,
    COLOR_MODES,
    MODE_PORTRAIT_PRECISION,
    MODE_RGB_PHOTOREALISTIC,
    MODE_ULTRA_DETAIL,
    RENDERING_MODES,
    SUPPORTED_EXTENSIONS,
)
from nebula.engine import AsciiEngine
from nebula.exporter import ArtworkExporter
from nebula.image_processor import ImageProcessor
from nebula.renderer import LiveRenderer
from nebula.samples import SampleGenerator
from nebula.terminal import TerminalManager


class TestNebulaAsciiStudioV3(unittest.TestCase):
    """Full test suite for NEBULA ASCII STUDIO v3.0."""

    @classmethod
    def setUpClass(cls):
        """Create sample images for testing."""
        os.makedirs("samples", exist_ok=True)
        os.makedirs("exports", exist_ok=True)
        cls.portrait_path = SampleGenerator.generate_portrait("samples/test_portrait.jpg", width=200, height=250)
        cls.bw_path = SampleGenerator.generate_bw_classic("samples/test_bw.jpg", width=200, height=150)
        cls.color_path = SampleGenerator.generate_colorful("samples/test_color.jpg", width=200, height=150)

    def test_path_validation_with_spaces_and_quotes(self):
        """Test sanitizing paths with whitespace and surrounding quotes."""
        valid, clean = ImageProcessor.validate_path(f'  "{self.portrait_path}"  ')
        self.assertTrue(valid)
        self.assertEqual(clean, self.portrait_path)

        valid, clean = ImageProcessor.validate_path(f"  '{self.portrait_path}'  ")
        self.assertTrue(valid)
        self.assertEqual(clean, self.portrait_path)

        valid, err = ImageProcessor.validate_path("non_existent_file_99999.jpg")
        self.assertFalse(valid)
        self.assertIn("File not found", err)

    def test_alpha_compositing(self):
        """Test RGBA transparent image compositing cleanly over dark backdrop."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            rgba_img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
            rgba_img.save(tmp_path)
            loaded = ImageProcessor.load_image(tmp_path)
            self.assertEqual(loaded.mode, "RGB")
            self.assertEqual(loaded.size, (100, 100))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_aspect_ratio_correction(self):
        """Test that monospace cell height-to-width ratio compensates correctly."""
        img = Image.new("RGB", (100, 100), (200, 200, 200))
        resized, (w, h) = ImageProcessor.resize_for_terminal(img, target_width=100, aspect_ratio_correction=0.50)
        self.assertEqual(w, 100)
        self.assertEqual(h, 50)

    def test_rec709_luminance_calculation(self):
        """Test Rec. 709 luminance formula: Y = 0.2126*R + 0.7152*G + 0.0722*B."""
        red = np.zeros((1, 1, 3), dtype=np.uint8)
        red[0, 0, 0] = 255
        lum_red = ImageProcessor.calculate_luminance(red)[0, 0]
        self.assertAlmostEqual(lum_red, 0.2126 * 255, places=2)

        green = np.zeros((1, 1, 3), dtype=np.uint8)
        green[0, 0, 1] = 255
        lum_green = ImageProcessor.calculate_luminance(green)[0, 0]
        self.assertAlmostEqual(lum_green, 0.7152 * 255, places=2)

        blue = np.zeros((1, 1, 3), dtype=np.uint8)
        blue[0, 0, 2] = 255
        lum_blue = ImageProcessor.calculate_luminance(blue)[0, 0]
        self.assertAlmostEqual(lum_blue, 0.0722 * 255, places=2)

    def test_all_rendering_modes(self):
        """Verify Mode A, Mode B, and Mode C render without errors."""
        raw_img = ImageProcessor.load_image(self.portrait_path)
        resized_img, (w, h) = ImageProcessor.resize_for_terminal(raw_img, target_width=80)

        for mode_key in [MODE_ULTRA_DETAIL, MODE_RGB_PHOTOREALISTIC, MODE_PORTRAIT_PRECISION]:
            m_cfg = RENDERING_MODES[mode_key]
            enhanced = ImageProcessor.enhance_for_ascii(
                resized_img,
                sharpness=m_cfg["sharpness"],
                detail_boost=m_cfg["detail_boost"],
                contrast=m_cfg["contrast"],
                gamma=m_cfg["gamma"],
                saturation=m_cfg["color_saturation"],
            )
            frame = AsciiEngine.render_frame(
                enhanced,
                mode=mode_key,
                ramp=m_cfg["ramp"],
                color_mode="truecolor",
            )
            self.assertEqual(frame.width, 80)
            self.assertEqual(frame.height, h)
            self.assertEqual(len(frame.chars), h)
            self.assertEqual(len(frame.chars[0]), 80)
            self.assertEqual(frame.colors.shape, (h, 80, 3))

    def test_artwork_exports_and_comparison(self):
        """Verify TXT, HTML, PNG, and side-by-side comparison files are generated."""
        raw_img = ImageProcessor.load_image(self.portrait_path)
        resized, (w, h) = ImageProcessor.resize_for_terminal(raw_img, target_width=60)
        frame = AsciiEngine.render_frame(resized, mode=MODE_ULTRA_DETAIL)

        with tempfile.TemporaryDirectory() as tmp_dir:
            txt_path = os.path.join(tmp_dir, "test.txt")
            ArtworkExporter.export_txt(frame, txt_path)
            self.assertTrue(os.path.exists(txt_path))
            self.assertGreater(os.path.getsize(txt_path), 0)

            html_path = os.path.join(tmp_dir, "test.html")
            ArtworkExporter.export_html(frame, html_path, title="Test HTML")
            self.assertTrue(os.path.exists(html_path))
            self.assertGreater(os.path.getsize(html_path), 500)

            png_path = os.path.join(tmp_dir, "test.png")
            ArtworkExporter.export_png(frame, png_path, font_size=12)
            self.assertTrue(os.path.exists(png_path))
            self.assertGreater(os.path.getsize(png_path), 1000)

            comp_path = os.path.join(tmp_dir, "comp.png")
            ArtworkExporter.export_side_by_side_comparison(raw_img, png_path, comp_path)
            self.assertTrue(os.path.exists(comp_path))
            self.assertGreater(os.path.getsize(comp_path), 1000)

            with Image.open(png_path) as p_img:
                self.assertEqual(p_img.format, "PNG")

    def test_live_renderer(self):
        """Test renderer execution with line reveal."""
        raw_img = ImageProcessor.load_image(self.portrait_path)
        resized, _ = ImageProcessor.resize_for_terminal(raw_img, target_width=40)
        frame = AsciiEngine.render_frame(resized)

        renderer = LiveRenderer()
        stats = renderer.render_live(frame, speed="instant")
        self.assertEqual(stats["total_rows"], frame.height)
        self.assertEqual(stats["total_chars"], frame.total_characters)


if __name__ == "__main__":
    unittest.main()
