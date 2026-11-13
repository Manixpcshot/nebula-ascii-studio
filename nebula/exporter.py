"""
NEBULA ASCII STUDIO — Professional Export System (Version 3.0)
Exports rendered artwork into TXT, rich standalone HTML, high-resolution PNG,
and side-by-side [Original vs ASCII] comparison images.
"""

import html
import os
import sys
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .engine import AsciiFrame


class ArtworkExporter:
    """Handles professional multi-format artwork exporting."""

    @staticmethod
    def _ensure_dir(filepath: str) -> None:
        """Creates destination directory if needed."""
        dirname = os.path.dirname(os.path.abspath(filepath))
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    @staticmethod
    def export_txt(frame: AsciiFrame, output_path: str) -> str:
        """Exports raw ASCII text matrix with UTF-8 encoding."""
        ArtworkExporter._ensure_dir(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(frame.raw_text)
        return os.path.abspath(output_path)

    @staticmethod
    def export_html(
        frame: AsciiFrame,
        output_path: str,
        title: str = "NEBULA ASCII STUDIO Artwork",
    ) -> str:
        """
        Exports the artwork as a standalone, responsive, dark-mode HTML file.
        Preserves 24-bit Truecolor using run-length encoded color spans.
        Includes interactive zoom controls and copy-to-clipboard functionality.
        """
        ArtworkExporter._ensure_dir(output_path)

        rows_html = []
        for y in range(frame.height):
            line_parts = []
            current_color = None
            current_run = []

            for x in range(frame.width):
                char = frame.chars[y][x]
                escaped_char = html.escape(char)
                if escaped_char == " ":
                    escaped_char = "&nbsp;"

                color_tuple = (
                    int(frame.colors[y, x, 0]),
                    int(frame.colors[y, x, 1]),
                    int(frame.colors[y, x, 2]),
                )

                if color_tuple == current_color:
                    current_run.append(escaped_char)
                else:
                    if current_run:
                        r, g, b = current_color
                        line_parts.append(f'<span style="color:rgb({r},{g},{b})">{"".join(current_run)}</span>')
                    current_color = color_tuple
                    current_run = [escaped_char]

            if current_run:
                r, g, b = current_color
                line_parts.append(f'<span style="color:rgb({r},{g},{b})">{"".join(current_run)}</span>')

            rows_html.append("".join(line_parts))

        ascii_content = "\n".join(rows_html)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        :root {{
            --bg-color: #070a12;
            --panel-bg: rgba(14, 20, 32, 0.95);
            --border-color: #1e293b;
            --accent-cyan: #00f0ff;
            --accent-magenta: #ff007f;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: auto;
        }}
        header {{
            position: sticky;
            top: 0;
            z-index: 100;
            width: 100%;
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .brand {{ display: flex; align-items: center; gap: 10px; }}
        .brand-title {{
            font-weight: 800;
            font-size: 1.1rem;
            letter-spacing: 1px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-magenta));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .badge {{
            background: #1e293b;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        .controls {{ display: flex; align-items: center; gap: 10px; }}
        button {{
            background: #1e293b;
            border: 1px solid #334155;
            color: var(--text-main);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        button:hover {{
            background: #334155;
            border-color: var(--accent-cyan);
            color: #fff;
        }}
        .slider-group {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        input[type="range"] {{ accent-color: var(--accent-cyan); cursor: pointer; }}
        main {{
            padding: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            flex-grow: 1;
        }}
        #art-container {{
            background-color: #04060a;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.9);
            border: 1px solid #1e293b;
            display: inline-block;
        }}
        pre.ascii-canvas {{
            font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
            font-size: 11px;
            line-height: 0.92;
            letter-spacing: 0px;
            white-space: pre;
            user-select: text;
            text-rendering: geometricPrecision;
        }}
        footer {{
            padding: 16px;
            color: var(--text-muted);
            font-size: 0.8rem;
            text-align: center;
            border-top: 1px solid var(--border-color);
            width: 100%;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span class="brand-title">NEBULA ASCII STUDIO</span>
            <span class="badge">{frame.width} &times; {frame.height} | {frame.total_characters:,} characters</span>
        </div>
        <div class="controls">
            <div class="slider-group">
                <span>Font Size:</span>
                <input type="range" id="size-slider" min="6" max="22" value="11" oninput="changeFontSize(this.value)">
                <span id="size-label">11px</span>
            </div>
            <button onclick="toggleBackground()">Toggle Dark/Black</button>
            <button onclick="copyRawText()">Copy Text</button>
            <button onclick="window.print()">Print / PDF</button>
        </div>
    </header>

    <main>
        <div id="art-container">
            <pre class="ascii-canvas" id="canvas">{ascii_content}</pre>
        </div>
    </main>

    <footer>
        Rendered with NEBULA ASCII STUDIO v3.0 &bull; Mode: {html.escape(str(frame.metadata.get("mode", "ultra_detail")))} &bull; Truecolor ANSI Engine
    </footer>

    <script>
        function changeFontSize(val) {{
            document.getElementById('canvas').style.fontSize = val + 'px';
            document.getElementById('size-label').textContent = val + 'px';
        }}
        let isPureBlack = true;
        function toggleBackground() {{
            const container = document.getElementById('art-container');
            isPureBlack = !isPureBlack;
            container.style.backgroundColor = isPureBlack ? '#000000' : '#111827';
        }}
        function copyRawText() {{
            const text = document.getElementById('canvas').innerText;
            navigator.clipboard.writeText(text).then(() => {{
                alert('ASCII artwork copied to clipboard!');
            }}).catch(err => {{
                console.error('Could not copy text: ', err);
            }});
        }}
    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        return os.path.abspath(output_path)

    @staticmethod
    def _find_monospace_font(font_size: int = 14) -> ImageFont.ImageFont:
        """Loads system monospace font (Consolas / Courier) with fallback."""
        candidates = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
            "C:/Windows/Fonts/lucon.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/System/Library/Fonts/Monaco.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, font_size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @staticmethod
    def export_png(
        frame: AsciiFrame,
        output_path: str,
        font_size: int = 14,
        background_color: Tuple[int, int, int] = (6, 8, 14),
    ) -> str:
        """
        Renders the actual ASCII artwork as a high-resolution raster graphic.
        Paints each character glyph with its corresponding 24-bit RGB Truecolor.
        """
        ArtworkExporter._ensure_dir(output_path)

        font = ArtworkExporter._find_monospace_font(font_size)

        try:
            bbox = font.getbbox("M")
            char_width = max(6, int(bbox[2] - bbox[0]))
            ascent, descent = font.getmetrics()
            char_height = max(10, ascent + descent)
        except Exception:
            char_width = 8
            char_height = 14

        padding = 24
        canvas_width = (frame.width * char_width) + (2 * padding)
        canvas_height = (frame.height * char_height) + (2 * padding)

        canvas = Image.new("RGB", (canvas_width, canvas_height), background_color)
        draw = ImageDraw.Draw(canvas)

        for y in range(frame.height):
            y_pos = padding + (y * char_height)
            for x in range(frame.width):
                char = frame.chars[y][x]
                if char == " ":
                    continue
                x_pos = padding + (x * char_width)
                color = (
                    int(frame.colors[y, x, 0]),
                    int(frame.colors[y, x, 1]),
                    int(frame.colors[y, x, 2]),
                )
                draw.text((x_pos, y_pos), char, fill=color, font=font)

        canvas.save(output_path, format="PNG", optimize=True)
        return os.path.abspath(output_path)

    @staticmethod
    def export_side_by_side_comparison(
        original_img: Image.Image,
        ascii_png_path: str,
        output_path: str,
    ) -> str:
        """
        Creates a side-by-side comparison image:
        [ ORIGINAL PHOTOGRAPH | NEBULA ASCII RECONSTRUCTION ]
        """
        ArtworkExporter._ensure_dir(output_path)

        with Image.open(ascii_png_path) as ascii_img:
            target_h = ascii_img.height
            # Resize original to match ASCII image height while preserving aspect ratio
            orig_aspect = original_img.width / float(original_img.height)
            orig_target_w = int(target_h * orig_aspect)
            orig_resized = original_img.resize((orig_target_w, target_h), Image.Resampling.LANCZOS)

            margin = 30
            total_w = orig_target_w + ascii_img.width + (3 * margin)
            total_h = target_h + 70  # Space for title header

            comp = Image.new("RGB", (total_w, total_h), (10, 14, 22))
            draw = ImageDraw.Draw(comp)

            # Paste images
            comp.paste(orig_resized, (margin, 50))
            comp.paste(ascii_img, (orig_target_w + 2 * margin, 50))

            # Header text
            font = ArtworkExporter._find_monospace_font(18)
            draw.text((margin, 16), "ORIGINAL PHOTOGRAPH", fill=(100, 200, 255), font=font)
            draw.text((orig_target_w + 2 * margin, 16), "NEBULA HIGH-FIDELITY ASCII RECONSTRUCTION", fill=(255, 100, 200), font=font)

            comp.save(output_path, format="PNG", optimize=True)
            return os.path.abspath(output_path)
