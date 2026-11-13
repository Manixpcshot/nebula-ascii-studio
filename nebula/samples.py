"""
NEBULA ASCII STUDIO — Master Test Image Generator (Version 3.0)
Generates high-definition reference targets across all 5 mandatory test categories:
1. Detailed Human Portrait
2. Black & White Monochromatic Photograph
3. Vibrant Colorful Photograph
4. Hair Strands & Micro-Textures Target
5. Complex Landscape Scenery
"""

import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class SampleGenerator:
    """Procedurally generates pristine high-resolution test images."""

    @staticmethod
    def generate_portrait(output_path: str = "samples/portrait_hd.jpg", width: int = 800, height: int = 1000) -> str:
        """Category 1: Detailed Human Portrait with facial geometry, eyes, lips, skin shading."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        img = Image.new("RGB", (width, height), (16, 20, 28))
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2 - 30

        # Background studio rim light
        for r in range(400, 0, -10):
            glow = (1.0 - (r / 400.0)) * 50
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(int(20 + glow), int(26 + glow * 1.2), int(45 + glow * 2)))

        # Shoulders & Charcoal suit
        draw.polygon([(cx - 320, height), (cx - 200, cy + 280), (cx + 200, cy + 280), (cx + 320, height)], fill=(28, 34, 46))
        # Shirt collar
        draw.polygon([(cx - 70, cy + 280), (cx, cy + 340), (cx + 70, cy + 280)], fill=(235, 238, 245))
        # Neck
        draw.rectangle([cx - 55, cy + 160, cx + 55, cy + 290], fill=(215, 160, 130))

        # Face oval
        draw.ellipse([cx - 135, cy - 160, cx + 135, cy + 185], fill=(244, 198, 168))

        # Cheek shadows & blush
        draw.ellipse([cx - 110, cy + 20, cx - 40, cy + 70], fill=(240, 175, 150))
        draw.ellipse([cx + 40, cy + 20, cx + 110, cy + 70], fill=(240, 175, 150))

        # Eyebrows
        draw.arc([cx - 95, cy - 55, cx - 30, cy - 30], start=200, end=340, fill=(65, 38, 22), width=5)
        draw.arc([cx + 30, cy - 55, cx + 95, cy - 30], start=200, end=340, fill=(65, 38, 22), width=5)

        # Eyes: sclera, iris, pupil, glint, crease
        for side, eye_cx in [(-1, cx - 62), (1, cx + 62)]:
            draw.ellipse([eye_cx - 26, cy - 24, eye_cx + 26, cy - 4], fill=(252, 252, 255))
            draw.ellipse([eye_cx - 12, cy - 22, eye_cx + 12, cy - 4], fill=(42, 105, 80))
            draw.ellipse([eye_cx - 6, cy - 18, eye_cx + 6, cy - 8], fill=(12, 14, 18))
            draw.ellipse([eye_cx + 2, cy - 20, eye_cx + 7, cy - 14], fill=(255, 255, 255))
            draw.arc([eye_cx - 28, cy - 30, eye_cx + 28, cy - 14], start=190, end=350, fill=(110, 75, 60), width=3)

        # Nose bridge and nostrils
        draw.line([(cx, cy - 20), (cx, cy + 50)], fill=(205, 145, 115), width=4)
        draw.arc([cx - 16, cy + 38, cx + 16, cy + 58], start=20, end=160, fill=(175, 115, 90), width=3)
        draw.ellipse([cx - 12, cy + 50, cx - 6, cy + 56], fill=(120, 75, 60))
        draw.ellipse([cx + 6, cy + 50, cx + 12, cy + 56], fill=(120, 75, 60))

        # Lips
        draw.polygon([(cx - 44, cy + 96), (cx - 18, cy + 90), (cx, cy + 93), (cx + 18, cy + 90), (cx + 44, cy + 96), (cx, cy + 101)], fill=(190, 72, 72))
        draw.polygon([(cx - 44, cy + 96), (cx, cy + 101), (cx + 44, cy + 96), (cx, cy + 118)], fill=(220, 92, 92))
        draw.ellipse([cx - 12, cy + 104, cx + 12, cy + 110], fill=(245, 135, 135))

        # Hair
        draw.ellipse([cx - 150, cy - 205, cx + 150, cy - 40], fill=(44, 26, 18))
        draw.polygon([(cx - 155, cy - 50), (cx - 130, cy + 140), (cx - 100, cy + 20), (cx - 110, cy - 50)], fill=(44, 26, 18))
        draw.polygon([(cx + 155, cy - 50), (cx + 130, cy + 140), (cx + 100, cy + 20), (cx + 110, cy - 50)], fill=(44, 26, 18))
        draw.arc([cx - 85, cy - 180, cx + 85, cy - 130], start=210, end=330, fill=(90, 55, 40), width=8)

        img = img.filter(ImageFilter.SMOOTH)
        img.save(output_path, quality=95)
        return os.path.abspath(output_path)

    @staticmethod
    def generate_bw_classic(output_path: str = "samples/bw_classic.jpg", width: int = 800, height: int = 600) -> str:
        """Category 2: Black & White Monochromatic Photograph with deep chiaroscuro tones."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        x = np.linspace(-2.5, 2.5, width)
        y = np.linspace(-1.875, 1.875, height)
        xx, yy = np.meshgrid(x, y)

        r = np.sqrt(xx**2 + yy**2)
        # Vintage architecture arches / radial light falloff
        pattern = np.abs(np.cos(r * 4.0)) * np.exp(-0.35 * r) * 220 + 20
        pattern += np.abs(np.sin(xx * 5.0)) * 25

        gray = np.clip(pattern, 0, 255).astype(np.uint8)
        img = Image.fromarray(gray, mode="L").convert("RGB")
        img.save(output_path, quality=95)
        return os.path.abspath(output_path)

    @staticmethod
    def generate_colorful(output_path: str = "samples/vivid_colors.jpg", width: int = 800, height: int = 600) -> str:
        """Category 3: Vibrant Colorful Photograph with rich color gradients."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        xx, yy = np.meshgrid(x, y)

        red = (np.sin(xx * math.pi * 2.0) * 0.5 + 0.5) * 255.0
        green = (np.sin(yy * math.pi * 2.0) * 0.5 + 0.5) * 255.0
        blue = (np.sin((xx + yy) * math.pi * 2.0) * 0.5 + 0.5) * 255.0

        rgb = np.stack([red.astype(np.uint8), green.astype(np.uint8), blue.astype(np.uint8)], axis=2)
        img = Image.fromarray(rgb)
        img.save(output_path, quality=95)
        return os.path.abspath(output_path)

    @staticmethod
    def generate_hair_textures(output_path: str = "samples/textures_hair.jpg", width: int = 800, height: int = 600) -> str:
        """Category 4: Photograph with fine hair strands, fabric textures, and micro-gradients."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        img = Image.new("RGB", (width, height), (20, 22, 30))
        draw = ImageDraw.Draw(img)

        # Draw hundreds of overlapping delicate hair strands
        np.random.seed(99)
        for i in range(160):
            start_x = np.random.randint(100, width - 100)
            mid_x = start_x + np.random.randint(-40, 40)
            end_x = mid_x + np.random.randint(-50, 50)
            col_lum = np.random.randint(90, 220)
            color = (col_lum, int(col_lum * 0.8), int(col_lum * 0.55))
            draw.line([(start_x, 50), (mid_x, height // 2), (end_x, height - 50)], fill=color, width=2)

        img.save(output_path, quality=95)
        return os.path.abspath(output_path)

    @staticmethod
    def generate_landscape(output_path: str = "samples/landscape_sunset.jpg", width: int = 800, height: int = 600) -> str:
        """Category 5: Complex Landscape Scenery with sky gradient, mountains, and water reflections."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Sky sunset gradient
        for y in range(height // 2):
            t = y / (height / 2.0)
            r = int(255 * (1 - t) + 240 * t)
            g = int(80 * (1 - t) + 160 * t)
            b = int(120 * (1 - t) + 50 * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Mountain peaks silhouette
        mountains = [
            (0, height // 2),
            (150, height // 3),
            (300, height // 2 - 40),
            (480, height // 4),
            (650, height // 2 - 20),
            (width, height // 2),
        ]
        draw.polygon(mountains + [(width, height), (0, height)], fill=(30, 25, 45))

        # Water lake reflection
        for y in range(height // 2, height):
            t = (y - height / 2.0) / (height / 2.0)
            draw.line([(0, y), (width, y)], fill=(int(25 + 40 * t), int(35 + 60 * t), int(70 + 80 * t)))

        img.save(output_path, quality=95)
        return os.path.abspath(output_path)
