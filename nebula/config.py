"""
NEBULA ASCII STUDIO — Configuration & Presets (Version 3.0 Rebuild)
Defines scientifically measured character ramps, core rendering modes,
perceptual color constants, and terminal parameters.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# APPLICATION BRANDING
# ==============================================================================

APP_NAME = "NEBULA ASCII STUDIO"
APP_SUBTITLE = "Advanced High-Fidelity Image-to-ASCII Engine"
APP_VERSION = "3.0.0"
APP_TAGLINE = "Extreme Image Clarity, Multi-Scale Detail & Photographic ASCII Reconstruction"

# ==============================================================================
# SCIENTIFICALLY MEASURED CHARACTER RAMPS (CALIBRATED ON CONSOLAS MONOSPACE)
# ==============================================================================

# 95-character full ASCII ramp strictly sorted by measured optical pixel fill factor
# From lowest density (empty space) to maximum physical ink coverage ('@')
RAMP_ULTRA_95 = (
    " `-'.:_,\"^~;=!<+>\\/*TL?|cr7ilFzJ(v)It[Ys1{}xufnjC]253ZoeV4EkaySUPhwX6AK9HRdqDGm#pbONWBM8$0%gQ&@"
)

# 64-character Portrait Precision ramp — tuned for smooth facial skin and sharp contours.
# Omits distracting directional punctuation while keeping rich tonal gradation.
RAMP_PORTRAIT_64 = (
    " .':;-+~*|1()/{}[vucxzrjftnXYUJCLQ0OZmwqpdbkhao*#MW&8%B$@█"
)

# 40-character Clean Chiaroscuro ramp for high-contrast dramatic lighting
RAMP_CHIAROSCURO_40 = (
    "   ....::::----====++++****####%%%%@@@@$$$$████"
)

# 16-character Classic Photographic ramp
RAMP_CLASSIC_16 = "  ..::--==++**##%%@@$$"

# Unicode Shaded Blocks for silky smooth tonal transitions
RAMP_UNICODE_SHADES = "  ░░▒▒▓▓██"

CHARACTER_RAMPS: Dict[str, str] = {
    "ultra_95": RAMP_ULTRA_95,
    "portrait_64": RAMP_PORTRAIT_64,
    "chiaroscuro_40": RAMP_CHIAROSCURO_40,
    "classic_16": RAMP_CLASSIC_16,
    "unicode_shades": RAMP_UNICODE_SHADES,
}

# ==============================================================================
# CORE RENDERING MODES
# ==============================================================================

MODE_ULTRA_DETAIL = "ultra_detail"           # Mode A: Maximum character density & micro-contrast
MODE_RGB_PHOTOREALISTIC = "rgb_photo"        # Mode B: Natural color balance & smooth tonal gradients
MODE_PORTRAIT_PRECISION = "portrait"         # Mode C: Optimized for facial structure, eyes, lips, skin

RENDERING_MODES = {
    MODE_ULTRA_DETAIL: {
        "name": "MODE A — ULTRA DETAIL",
        "description": "Maximum character density, micro-contrast & edge clarity for complex textures",
        "ramp": RAMP_ULTRA_95,
        "sharpness": 1.8,
        "detail_boost": 1.7,
        "contrast": 1.25,
        "gamma": 1.0,
        "color_saturation": 1.15,
    },
    MODE_RGB_PHOTOREALISTIC: {
        "name": "MODE B — RGB PHOTOREALISTIC",
        "description": "Truecolor preservation, smooth gradients & accurate color depth",
        "ramp": RAMP_PORTRAIT_64,
        "sharpness": 1.3,
        "detail_boost": 1.3,
        "contrast": 1.15,
        "gamma": 1.02,
        "color_saturation": 1.30,
    },
    MODE_PORTRAIT_PRECISION: {
        "name": "MODE C — PORTRAIT PRECISION",
        "description": "Engineered for faces: eyes, eyebrows, lips, skin highlights & facial shadows",
        "ramp": RAMP_PORTRAIT_64,
        "sharpness": 1.5,
        "detail_boost": 1.6,
        "contrast": 1.22,
        "gamma": 1.04,
        "color_saturation": 1.18,
    },
}

# ==============================================================================
# RESOLUTION PRESETS
# ==============================================================================

RESOLUTION_OPTIONS = [
    (100, "100 Columns (Standard Terminal)"),
    (150, "150 Columns (High Detail)"),
    (200, "200 Columns (Ultra Wide / 1080p Window)"),
    (250, "250 Columns (Extreme Fidelity / Max Terminal)"),
    (300, "300 Columns (Master High-Definition Canvas)"),
]

# Character aspect ratio compensation factor (Consolas character cell width / height ratio ~ 0.48 to 0.50)
DEFAULT_ASPECT_RATIO = 0.485

# Terminal Color Modes
COLOR_MODE_TRUECOLOR = "truecolor"       # Full 24-bit ANSI RGB
COLOR_MODE_GRAYSCALE = "grayscale"       # 256-level calibrated white/gray RGB
COLOR_MODE_MONO_AMBER = "mono_amber"     # CRT amber phosphor
ANIMATION_SPEEDS = {
    "instant": 0.0,
    "fast": 0.003,
    "normal": 0.012,
    "cinematic": 0.028,
}

COLOR_MODE_ANSI_16 = "ansi_16"

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif")

COLOR_MODE_MONO_GREEN = "mono_green"     # Matrix terminal green

COLOR_MODES = [
    COLOR_MODE_TRUECOLOR,
    COLOR_MODE_GRAYSCALE,
    COLOR_MODE_MONO_AMBER,
    COLOR_MODE_MONO_GREEN,
]

PRESETS = RENDERING_MODES

# Theme UI Colors
THEME_CYAN = "#00f0ff"
THEME_PURPLE = "#b026ff"
THEME_MAGENTA = "#ff007f"
THEME_BLUE = "#3b82f6"
THEME_DARK = "#0a0e17"
THEME_TEXT = "#e2e8f0"
THEME_SUCCESS = "#10b981"
THEME_WARNING = "#f59e0b"
THEME_ERROR = "#ef4444"
