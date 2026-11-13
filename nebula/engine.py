"""
NEBULA ASCII STUDIO — Core ASCII Engine (Version 3.0)
Converts image pixel matrices into high-density ASCII glyphs with 24-bit Truecolor mapping.
Uses vectorized Rec. 709 luminance calculations and scientifically ordered density ramps.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image

from .config import (
    CHARACTER_RAMPS,
    COLOR_MODE_GRAYSCALE,
    COLOR_MODE_MONO_AMBER,
    COLOR_MODE_MONO_GREEN,
    COLOR_MODE_TRUECOLOR,
    MODE_PORTRAIT_PRECISION,
    MODE_RGB_PHOTOREALISTIC,
    MODE_ULTRA_DETAIL,
    RAMP_PORTRAIT_64,
    RAMP_ULTRA_95,
    RENDERING_MODES,
)
from .image_processor import ImageProcessor


@dataclass
class AsciiFrame:
    """Represents a fully rendered ASCII frame with character matrix and truecolor data."""
    width: int
    height: int
    chars: List[List[str]]
    colors: np.ndarray  # Shape: (height, width, 3), dtype=uint8
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_characters(self) -> int:
        return self.width * self.height


class AsciiEngine:
    """High-performance vectorized ASCII rendering engine."""

    @staticmethod
    def map_luminance_to_chars(
        luminance: np.ndarray,
        ramp: str,
        invert: bool = False,
    ) -> List[List[str]]:
        """
        Maps continuous luminance values [0..255] to discrete characters from the ramp.
        On dark terminal backgrounds:
        0 (black shadows) -> ramp[0] (' ' space / micro-dot)
        255 (brightest highlight) -> ramp[-1] (dense glyph e.g. '@', '█')
        """
        ramp_len = len(ramp)
        if ramp_len == 0:
            raise ValueError("Character ramp cannot be empty.")

        norm_lum = np.clip(luminance / 255.0, 0.0, 1.0)
        if invert:
            norm_lum = 1.0 - norm_lum

        indices = np.clip(np.floor(norm_lum * ramp_len).astype(np.int32), 0, ramp_len - 1)
        char_lookup = np.array(list(ramp))
        char_matrix = char_lookup[indices]
        return [list(row) for row in char_matrix]

    @staticmethod
    def apply_color_palette(
        rgb_array: np.ndarray,
        luminance: np.ndarray,
        color_mode: str,
    ) -> np.ndarray:
        """Transforms RGB pixel colors according to the chosen color mode."""
        if color_mode == COLOR_MODE_TRUECOLOR:
            return np.clip(rgb_array, 0, 255).astype(np.uint8)

        lum_int = np.clip(luminance, 0, 255).astype(np.uint8)
        out = np.zeros_like(rgb_array, dtype=np.uint8)

        if color_mode == COLOR_MODE_GRAYSCALE:
            out[:, :, 0] = lum_int
            out[:, :, 1] = lum_int
            out[:, :, 2] = lum_int

        elif color_mode == COLOR_MODE_MONO_AMBER:
            out[:, :, 0] = lum_int
            out[:, :, 1] = (lum_int.astype(np.float32) * 0.72).astype(np.uint8)
            out[:, :, 2] = (lum_int.astype(np.float32) * 0.12).astype(np.uint8)

        elif color_mode == COLOR_MODE_MONO_GREEN:
            out[:, :, 0] = (lum_int.astype(np.float32) * 0.15).astype(np.uint8)
            out[:, :, 1] = lum_int
            out[:, :, 2] = (lum_int.astype(np.float32) * 0.25).astype(np.uint8)

        else:
            return np.clip(rgb_array, 0, 255).astype(np.uint8)

        return out

    @classmethod
    def render_frame(
        cls,
        image: Image.Image,
        mode: str = MODE_ULTRA_DETAIL,
        ramp: Optional[str] = None,
        color_mode: str = COLOR_MODE_TRUECOLOR,
        invert: bool = False,
    ) -> AsciiFrame:
        """
        Renders a PIL Image into a high-fidelity AsciiFrame.
        Expects the image to be resized to the target character grid dimensions.
        """
        start_time = time.perf_counter()

        rgb_array = np.array(image.convert("RGB"), dtype=np.uint8)
        height, width, _ = rgb_array.shape

        # Select character ramp based on mode if not explicitly provided
        if ramp is None:
            if mode == MODE_ULTRA_DETAIL:
                ramp = RAMP_ULTRA_95
            elif mode == MODE_PORTRAIT_PRECISION:
                ramp = RAMP_PORTRAIT_64
            elif mode == MODE_RGB_PHOTOREALISTIC:
                ramp = RAMP_PORTRAIT_64
            else:
                ramp = RAMP_ULTRA_95

        # 1. Accurate Rec. 709 Luminance
        luminance = ImageProcessor.calculate_luminance(rgb_array)

        # 2. Map luminance to optical character density
        char_matrix = cls.map_luminance_to_chars(luminance, ramp, invert=invert)

        # 3. Apply color palette
        processed_colors = cls.apply_color_palette(rgb_array, luminance, color_mode)

        # 4. Generate plain text
        raw_text_lines = ["".join(row) for row in char_matrix]
        raw_text = "\n".join(raw_text_lines)

        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        metadata = {
            "width": width,
            "height": height,
            "mode": mode,
            "ramp_length": len(ramp),
            "color_mode": color_mode,
            "invert": invert,
            "process_time_ms": process_time_ms,
        }

        return AsciiFrame(
            width=width,
            height=height,
            chars=char_matrix,
            colors=processed_colors,
            raw_text=raw_text,
            metadata=metadata,
        )
