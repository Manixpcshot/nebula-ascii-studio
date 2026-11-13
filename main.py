"""
NEBULA ASCII STUDIO — Advanced Image-to-ASCII Engine (Version 3.0)
High-Fidelity Terminal Graphics & Photographic ASCII Reconstruction.
"""

import argparse
import os
import sys
import time

from rich.prompt import Confirm

from nebula.config import (
    APP_NAME,
    APP_VERSION,
    COLOR_MODE_TRUECOLOR,
    MODE_PORTRAIT_PRECISION,
    MODE_RGB_PHOTOREALISTIC,
    MODE_ULTRA_DETAIL,
    RENDERING_MODES,
    THEME_CYAN,
    THEME_ERROR,
    THEME_MAGENTA,
    THEME_WARNING,
)
from nebula.engine import AsciiEngine
from nebula.exporter import ArtworkExporter
from nebula.image_processor import ImageProcessor
from nebula.renderer import LiveRenderer
from nebula.terminal import TerminalManager
from nebula.ui import TerminalUI, console


def run_pipeline(
    image_path: str,
    mode: str = MODE_ULTRA_DETAIL,
    target_width: int = 150,
    speed: str = "fast",
    color_mode: str = COLOR_MODE_TRUECOLOR,
    export_all: bool = True,
) -> bool:
    """Executes high-fidelity image-to-ASCII pipeline."""
    # 1. Validate and load image
    valid, result = ImageProcessor.validate_path(image_path)
    if not valid:
        console.print(f"[{THEME_ERROR}]Error: {result}[/{THEME_ERROR}]")
        return False

    resolved_path = result
    try:
        raw_img = ImageProcessor.load_image(resolved_path)
    except Exception as e:
        console.print(f"[{THEME_ERROR}]Failed to load image: {e}[/{THEME_ERROR}]")
        return False

    orig_dims = raw_img.size
    mode_config = RENDERING_MODES.get(mode, RENDERING_MODES[MODE_ULTRA_DETAIL])

    # 2. High-Quality Lanczos Resizing with Aspect Ratio Correction
    resized_img, target_dims = ImageProcessor.resize_for_terminal(
        raw_img,
        target_width=target_width,
        aspect_ratio_correction=0.485,
    )

    # 3. High-Fidelity Feature & Shading Enhancement (Rec. 709 Luminance & Multi-Scale Detail)
    enhanced_img = ImageProcessor.enhance_for_ascii(
        resized_img,
        sharpness=mode_config["sharpness"],
        detail_boost=mode_config["detail_boost"],
        contrast=mode_config["contrast"],
        gamma=mode_config["gamma"],
        saturation=mode_config["color_saturation"],
    )

    # 4. Display Pre-render Summary
    TerminalUI.display_pre_render_summary(
        image_name=resolved_path,
        orig_dims=orig_dims,
        target_dims=target_dims,
        mode_name=mode_config["name"],
        ramp_len=len(mode_config["ramp"]),
    )

    # 5. Render Frame
    frame = AsciiEngine.render_frame(
        image=enhanced_img,
        mode=mode,
        ramp=mode_config["ramp"],
        color_mode=color_mode,
        invert=False,
    )

    # 6. Live Stream in Terminal
    renderer = LiveRenderer()
    render_stats = renderer.render_live(frame, speed=speed)
    render_stats["cols"] = target_dims[0]
    render_stats["rows"] = target_dims[1]

    # 7. Exports (PNG, HTML, TXT, Comparison)
    base_name = os.path.splitext(os.path.basename(resolved_path))[0]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    export_prefix = os.path.join("exports", f"{base_name}_{mode}_{timestamp}")

    txt_path = ArtworkExporter.export_txt(frame, f"{export_prefix}.txt")
    html_path = ArtworkExporter.export_html(frame, f"{export_prefix}.html", title=f"NEBULA ART — {base_name}")
    png_path = ArtworkExporter.export_png(frame, f"{export_prefix}.png", font_size=13)
    comp_path = ArtworkExporter.export_side_by_side_comparison(
        raw_img,
        png_path,
        f"{export_prefix}_comparison.png",
    )

    # 8. Display Completion Summary Card
    TerminalUI.display_completion_card(
        stats=render_stats,
        txt_path=txt_path,
        html_path=html_path,
        png_path=png_path,
        comp_path=comp_path,
    )

    return True


def interactive_mode():
    """Main interactive studio workflow."""
    TerminalManager.enable_vt_mode()

    while True:
        TerminalUI.display_banner()

        # Step 1: Image Path
        image_path = TerminalUI.prompt_image_path()

        # Step 2: Select Mode (A: Ultra Detail, B: RGB Photo, C: Portrait Precision)
        mode = TerminalUI.choose_rendering_mode()

        # Step 3: Select Resolution (100, 150, 200, 250, 300, Custom)
        term_width, _ = TerminalManager.get_size()
        width = TerminalUI.choose_resolution(term_width)

        # Step 4: Execute Pipeline
        try:
            run_pipeline(
                image_path=image_path,
                mode=mode,
                target_width=width,
                speed="fast",
            )
        except Exception as e:
            console.print(f"[{THEME_ERROR}]An unexpected error occurred during rendering: {e}[/{THEME_ERROR}]")

        # Step 5: Loop prompt
        console.print()
        again = Confirm.ask(f"[{THEME_CYAN}]Transform another image?[/{THEME_CYAN}]", default=True)
        if not again:
            console.print(f"\n[{THEME_MAGENTA}]Thank you for using NEBULA ASCII STUDIO v3.0. Farewell![/{THEME_MAGENTA}]\n")
            break
        console.print("\n" + "=" * 70 + "\n")


def main():
    """CLI dispatcher."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{APP_VERSION} — Advanced High-Fidelity Image-to-ASCII Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("image", nargs="?", help="Path to local image file (JPG, PNG, WEBP, BMP, etc.)")
    parser.add_argument(
        "--mode",
        choices=[MODE_ULTRA_DETAIL, MODE_RGB_PHOTOREALISTIC, MODE_PORTRAIT_PRECISION],
        default=MODE_ULTRA_DETAIL,
        help="Rendering mode (ultra_detail, rgb_photo, portrait)",
    )
    parser.add_argument("--width", type=int, default=150, help="Output width in columns (100, 150, 200, 250, 300...)")
    parser.add_argument(
        "--speed",
        choices=["instant", "fast", "normal", "cinematic"],
        default="fast",
        help="Animation speed for line reveal",
    )
    parser.add_argument(
        "--color",
        choices=[COLOR_MODE_TRUECOLOR, "grayscale", "mono_amber", "mono_green"],
        default=COLOR_MODE_TRUECOLOR,
        help="Color mode pipeline",
    )

    args = parser.parse_args()

    if not args.image:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            console.print(f"\n[{THEME_WARNING}]Interrupted by user. Exiting cleanly.[/{THEME_WARNING}]")
            sys.exit(0)
    else:
        success = run_pipeline(
            image_path=args.image,
            mode=args.mode,
            target_width=args.width,
            speed=args.speed,
            color_mode=args.color,
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
