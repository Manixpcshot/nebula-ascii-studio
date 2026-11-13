"""
NEBULA ASCII STUDIO — Quality Benchmark & Visual Verification Suite
Tests the rendering engine across all 5 mandatory categories:
1. Detailed Human Portrait
2. Black & White Monochromatic Photograph
3. Vibrant Colorful Photograph
4. Hair Strands & Micro-Textures
5. Complex Landscape Scenery

Generates side-by-side comparison images [Original vs ASCII] and computes
mathematical reconstruction fidelity metrics (PSNR, Structural Correlation).
"""

import math
import os
import sys
import time
import numpy as np
from PIL import Image

from nebula.config import (
    MODE_PORTRAIT_PRECISION,
    MODE_RGB_PHOTOREALISTIC,
    MODE_ULTRA_DETAIL,
)
from nebula.engine import AsciiEngine
from nebula.exporter import ArtworkExporter
from nebula.image_processor import ImageProcessor
from nebula.samples import SampleGenerator


def calculate_metrics(orig_img: Image.Image, ascii_png_path: str) -> dict:
    """
    Computes visual fidelity metrics by comparing the rasterized ASCII artwork
    against the original image:
    1. PSNR (Peak Signal-to-Noise Ratio in dB)
    2. Normalized Cross-Correlation (NCC in [0..1])
    3. Mean Absolute Error (MAE in [0..255])
    """
    with Image.open(ascii_png_path) as ascii_img:
        # Resize both to common evaluation grid (300 x 300)
        eval_size = (300, 300)
        orig_eval = np.array(orig_img.convert("RGB").resize(eval_size, Image.Resampling.LANCZOS), dtype=np.float32)
        ascii_eval = np.array(ascii_img.convert("RGB").resize(eval_size, Image.Resampling.LANCZOS), dtype=np.float32)

        # Mean Absolute Error
        mae = float(np.mean(np.abs(orig_eval - ascii_eval)))

        # Mean Squared Error & PSNR
        mse = float(np.mean((orig_eval - ascii_eval) ** 2))
        if mse == 0:
            psnr = 100.0
        else:
            psnr = float(20 * math.log10(255.0 / math.sqrt(mse)))

        # Normalized Cross-Correlation
        norm_orig = orig_eval - np.mean(orig_eval)
        norm_ascii = ascii_eval - np.mean(ascii_eval)
        denom = np.sqrt(np.sum(norm_orig ** 2) * np.sum(norm_ascii ** 2))
        ncc = float(np.sum(norm_orig * norm_ascii) / max(1e-8, denom))

        return {
            "psnr_db": round(psnr, 2),
            "ncc_correlation": round(ncc, 3),
            "mae": round(mae, 2),
        }


def run_benchmark():
    """Executes the full test across all 5 image categories."""
    os.makedirs("samples", exist_ok=True)
    os.makedirs("exports/comparisons", exist_ok=True)

    test_cases = [
        {
            "category": "1. Detailed Human Portrait",
            "generator": SampleGenerator.generate_portrait,
            "sample_path": "samples/portrait_hd.jpg",
            "mode": MODE_PORTRAIT_PRECISION,
            "width": 150,
            "target_filename": "cat1_portrait",
        },
        {
            "category": "2. Black & White Monochromatic",
            "generator": SampleGenerator.generate_bw_classic,
            "sample_path": "samples/bw_classic.jpg",
            "mode": MODE_ULTRA_DETAIL,
            "width": 150,
            "target_filename": "cat2_bw_classic",
        },
        {
            "category": "3. Vibrant Colorful Photograph",
            "generator": SampleGenerator.generate_colorful,
            "sample_path": "samples/vivid_colors.jpg",
            "mode": MODE_RGB_PHOTOREALISTIC,
            "width": 150,
            "target_filename": "cat3_colorful",
        },
        {
            "category": "4. Hair Strands & Fine Textures",
            "generator": SampleGenerator.generate_hair_textures,
            "sample_path": "samples/textures_hair.jpg",
            "mode": MODE_ULTRA_DETAIL,
            "width": 160,
            "target_filename": "cat4_hair_textures",
        },
        {
            "category": "5. Complex Landscape Scenery",
            "generator": SampleGenerator.generate_landscape,
            "sample_path": "samples/landscape_sunset.jpg",
            "mode": MODE_RGB_PHOTOREALISTIC,
            "width": 160,
            "target_filename": "cat5_landscape",
        },
    ]

    print("=" * 80)
    print("NEBULA ASCII STUDIO v3.0 — QUALITY VERIFICATION & BENCHMARK SUITE")
    print("Testing 5 Mandatory Image Categories across Ultra Detail, Photo & Portrait Modes")
    print("=" * 80)

    results = []

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[{idx}/5] Testing {tc['category']}...")

        # 1. Generate or verify sample image
        sample_path = tc["sample_path"]
        if not os.path.exists(sample_path):
            tc["generator"](sample_path)

        orig_img = ImageProcessor.load_image(sample_path)
        start_time = time.perf_counter()

        # 2. Resize with aspect ratio correction
        resized_img, dims = ImageProcessor.resize_for_terminal(
            orig_img,
            target_width=tc["width"],
            aspect_ratio_correction=0.485,
        )

        # 3. Enhance
        from nebula.config import RENDERING_MODES
        m_cfg = RENDERING_MODES[tc["mode"]]
        enhanced_img = ImageProcessor.enhance_for_ascii(
            resized_img,
            sharpness=m_cfg["sharpness"],
            detail_boost=m_cfg["detail_boost"],
            contrast=m_cfg["contrast"],
            gamma=m_cfg["gamma"],
            saturation=m_cfg["color_saturation"],
        )

        # 4. Render Frame
        frame = AsciiEngine.render_frame(
            enhanced_img,
            mode=tc["mode"],
            ramp=m_cfg["ramp"],
            color_mode="truecolor",
        )

        render_time = time.perf_counter() - start_time

        # 5. Export PNG and Side-by-Side Comparison
        png_out = f"exports/comparisons/{tc['target_filename']}_ascii.png"
        comp_out = f"exports/comparisons/{tc['target_filename']}_comparison.png"

        ArtworkExporter.export_png(frame, png_out, font_size=13)
        ArtworkExporter.export_side_by_side_comparison(orig_img, png_out, comp_out)

        # 6. Calculate Metrics
        metrics = calculate_metrics(orig_img, png_out)

        res_entry = {
            "category": tc["category"],
            "grid": f"{dims[0]}x{dims[1]}",
            "total_chars": frame.total_characters,
            "mode": tc["mode"],
            "render_time_s": round(render_time, 3),
            "psnr": metrics["psnr_db"],
            "correlation": metrics["ncc_correlation"],
            "comp_path": comp_out,
        }
        results.append(res_entry)

        print(f"    ✔ Grid: {dims[0]}×{dims[1]} ({frame.total_characters:,} characters)")
        print(f"    ✔ Duration: {res_entry['render_time_s']}s")
        print(f"    ✔ Correlation to Original: {metrics['ncc_correlation']} (Scale 0..1)")
        print(f"    ✔ PSNR Fidelity: {metrics['psnr_db']} dB")
        print(f"    ✔ Comparison image saved: {os.path.abspath(comp_out)}")

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY RESULTS TABLE")
    print("=" * 80)
    header = f"{'Category':<32} | {'Grid':<10} | {'Chars':<8} | {'Corr':<6} | {'PSNR (dB)':<10} | {'Time (s)':<8}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['category']:<32} | {r['grid']:<10} | {r['total_chars']:<8} | {r['correlation']:<6} | {r['psnr']:<10} | {r['render_time_s']:<8}")
    print("=" * 80)
    print("All comparison images successfully generated in exports/comparisons/")


if __name__ == "__main__":
    run_benchmark()
