"""
NEBULA ASCII STUDIO — Live Terminal Renderer
Renders ASCII artwork line-by-line with truecolor ANSI codes and smooth scan animation.
Includes consecutive color compression to optimize terminal I/O throughput.
"""

import sys
import time
from typing import Callable, Optional

from .config import (
    ANIMATION_SPEEDS,
    COLOR_MODE_ANSI_16,
)
from .engine import AsciiFrame
from .terminal import TerminalManager


class LiveRenderer:
    """Handles row-by-row live streaming animation with ANSI truecolor formatting."""

    def __init__(self, truecolor_supported: Optional[bool] = None):
        if truecolor_supported is None:
            self.truecolor_supported = TerminalManager.supports_truecolor()
        else:
            self.truecolor_supported = truecolor_supported

    def format_row(self, row_chars: list, row_colors, color_mode: str) -> str:
        """
        Builds an ANSI-colored string for a single row.
        Optimizes consecutive characters of identical color to minimize ANSI sequence overhead.
        """
        parts = []
        last_color = None
        use_ansi16 = (color_mode == COLOR_MODE_ANSI_16)

        for col_idx, char in enumerate(row_chars):
            r, g, b = int(row_colors[col_idx, 0]), int(row_colors[col_idx, 1]), int(row_colors[col_idx, 2])
            current_color = (r, g, b)

            # Change color escape code only if different from previous character
            if current_color != last_color:
                if self.truecolor_supported and not use_ansi16:
                    parts.append(TerminalManager.rgb_to_truecolor_fg(r, g, b))
                elif not use_ansi16:
                    parts.append(TerminalManager.rgb_to_256_fg(r, g, b))
                else:
                    parts.append(TerminalManager.rgb_to_ansi16_fg(r, g, b))
                last_color = current_color

            parts.append(char)

        # Reset colors at end of line
        parts.append(TerminalManager.reset_color())
        return "".join(parts)

    def render_live(
        self,
        frame: AsciiFrame,
        speed: str = "normal",
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> dict:
        """
        Streams the ASCII art line-by-line into the terminal with a smooth reveal animation.
        """
        delay = ANIMATION_SPEEDS.get(speed, ANIMATION_SPEEDS["normal"])
        total_rows = frame.height
        total_chars = frame.total_characters

        # Ensure terminal is configured
        TerminalManager.enable_vt_mode()
        TerminalManager.hide_cursor()

        start_time = time.perf_counter()

        try:
            for row_idx in range(total_rows):
                row_chars = frame.chars[row_idx]
                row_colors = frame.colors[row_idx]

                row_str = self.format_row(row_chars, row_colors, frame.metadata.get("color_mode", "truecolor"))

                # Write line to stdout
                sys.stdout.write(row_str + "\n")
                sys.stdout.flush()

                # Call progress callback if provided
                if progress_callback:
                    pct = ((row_idx + 1) / total_rows) * 100.0
                    progress_callback(row_idx + 1, total_rows, pct)

                # Delay for live animation
                if delay > 0:
                    time.sleep(delay)

        finally:
            TerminalManager.show_cursor()
            sys.stdout.write(TerminalManager.reset_color())
            sys.stdout.flush()

        elapsed_time = time.perf_counter() - start_time
        chars_per_sec = int(total_chars / max(0.0001, elapsed_time))

        return {
            "elapsed_seconds": round(elapsed_time, 3),
            "total_rows": total_rows,
            "total_chars": total_chars,
            "speed": speed,
            "chars_per_sec": chars_per_sec,
        }
