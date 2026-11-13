"""
NEBULA ASCII STUDIO — High-Fidelity Image Processing Engine (Version 3.0)
Implements Rec. 709 luminance, multi-scale detail decomposition, Lanczos resizing,
and aspect ratio compensation to preserve facial features, shadows, and textures.
"""

import os
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .config import DEFAULT_ASPECT_RATIO, SUPPORTED_EXTENSIONS


class ImageProcessor:
    """Provides high-performance, vectorized computer vision preprocessing."""

    @staticmethod
    def validate_path(image_path: str) -> Tuple[bool, str]:
        """Validates existence and format of local image path."""
        clean_path = image_path.strip().strip("'\"")
        if not clean_path:
            return False, "Image path cannot be empty."

        if not os.path.exists(clean_path):
            return False, f"File not found: '{clean_path}'"

        if not os.path.isfile(clean_path):
            return False, f"Path is a directory, not an image file: '{clean_path}'"

        ext = os.path.splitext(clean_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported image format '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"

        return True, clean_path

    @staticmethod
    def load_image(image_path: str) -> Image.Image:
        """
        Loads an image from disk, normalizes EXIF orientation,
        and composites transparency over a dark backdrop.
        """
        valid, result = ImageProcessor.validate_path(image_path)
        if not valid:
            raise FileNotFoundError(result)

        try:
            img = Image.open(result)
            img.load()
        except Exception as e:
            raise ValueError(f"Corrupted or unreadable image file: {e}")

        # Correct camera/phone EXIF orientation
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Handle alpha channel (transparency)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img_rgba = img.convert("RGBA")
            background = Image.new("RGBA", img_rgba.size, (10, 14, 22, 255))
            composite = Image.alpha_composite(background, img_rgba)
            return composite.convert("RGB")

        return img.convert("RGB")

    @staticmethod
    def calculate_luminance(rgb_array: np.ndarray) -> np.ndarray:
        """
        Computes accurate Rec. 709 perceptual luminance:
        Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
        """
        r = rgb_array[:, :, 0].astype(np.float32)
        g = rgb_array[:, :, 1].astype(np.float32)
        b = rgb_array[:, :, 2].astype(np.float32)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def resize_for_terminal(
        img: Image.Image,
        target_width: int,
        aspect_ratio_correction: float = DEFAULT_ASPECT_RATIO,
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """
        Resizes the image to the specified column width while compensating for the
        non-square rectangular dimensions of monospace terminal character cells.
        Uses Lanczos resampling for pristine anti-aliased sharpness.
        """
        orig_width, orig_height = img.size
        if orig_width <= 0 or orig_height <= 0:
            raise ValueError("Invalid image dimensions (0 width or height).")

        target_width = max(20, target_width)
        aspect_ratio = orig_height / float(orig_width)
        target_height = max(1, int(target_width * aspect_ratio * aspect_ratio_correction))

        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        return resized_img, (target_width, target_height)

    @staticmethod
    def enhance_for_ascii(
        img: Image.Image,
        sharpness: float = 1.4,
        detail_boost: float = 1.5,
        contrast: float = 1.2,
        brightness: float = 1.0,
        gamma: float = 1.0,
        saturation: float = 1.2,
    ) -> Image.Image:
        """
        High-Fidelity Feature & Shading Pipeline:
        1. Multi-scale Unsharp Masking:
           - Macro-scale unsharp mask (radius ~ 3.0px) for facial volumes, shadows, and contours.
           - Micro-scale unsharp mask (radius ~ 1.0px) for eyelashes, iris, lips, wrinkles, hair.
        2. Dynamic range expansion (1st to 99th percentile contrast stretch).
        3. Gamma tone mapping with deep shadow preservation.
        4. Color saturation enhancement for vibrant Truecolor output.
        """
        # 1. Multi-scale feature enhancement
        enhanced = img
        if detail_boost > 1.0:
            # Macro structural contrast
            enhanced = enhanced.filter(
                ImageFilter.UnsharpMask(radius=3.0, percent=int(detail_boost * 45), threshold=2)
            )
            # Fine micro-detail (eyes, eyelashes, lips, hair texture)
            enhanced = enhanced.filter(
                ImageFilter.UnsharpMask(radius=1.0, percent=int(detail_boost * 90), threshold=1)
            )

        if sharpness > 1.0:
            sharp_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharp_enhancer.enhance(min(sharpness, 2.5))

        # 2. Dynamic range calibration via NumPy
        arr = np.array(enhanced, dtype=np.float32)
        p1, p99 = np.percentile(arr, (1, 99))
        if p99 > p1 + 10:
            arr = np.clip((arr - p1) / (p99 - p1) * 255.0, 0.0, 255.0)

        # 3. Intelligent contrast and gamma adjustment
        if abs(contrast - 1.0) > 0.02:
            mean = np.mean(arr, axis=(0, 1), keepdims=True)
            arr = np.clip(mean + (arr - mean) * contrast, 0.0, 255.0)

        if abs(brightness - 1.0) > 0.02:
            arr = np.clip(arr * brightness, 0.0, 255.0)

        if abs(gamma - 1.0) > 0.02:
            inv_gamma = 1.0 / max(0.1, gamma)
            arr = 255.0 * np.power(np.clip(arr / 255.0, 0.0, 1.0), inv_gamma)

        enhanced = Image.fromarray(np.clip(arr, 0.0, 255.0).astype(np.uint8))

        # 4. Color saturation
        if abs(saturation - 1.0) > 0.02:
            sat_enhancer = ImageEnhance.Color(enhanced)
            enhanced = sat_enhancer.enhance(max(0.0, saturation))

        return enhanced

    @classmethod
    def enhance_image(
        cls,
        img: Image.Image,
        contrast: float = 1.0,
        brightness: float = 1.0,
        sharpness: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
        detail_boost: float = 1.0,
    ) -> Image.Image:
        """Backward-compatibility alias."""
        return cls.enhance_for_ascii(
            img,
            sharpness=sharpness,
            detail_boost=detail_boost,
            contrast=contrast,
            brightness=brightness,
            gamma=gamma,
            saturation=saturation,
        )
