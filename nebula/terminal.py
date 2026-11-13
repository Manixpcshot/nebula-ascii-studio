"""
NEBULA ASCII STUDIO — Terminal Control & Color Management
Handles Windows console VT100 mode, terminal dimensions, truecolor formatting, and fallbacks.
"""

import atexit
import ctypes
import os
import shutil
import sys
from typing import Tuple


class TerminalManager:
    """Manages terminal state, ANSI VT processing, and truecolor output."""

    _vt_enabled = False
    _cursor_hidden = False

    @classmethod
    def enable_vt_mode(cls) -> bool:
        """
        Enables Virtual Terminal Processing in Windows 10/11 Command Prompt.
        This allows 24-bit Truecolor (ANSI escape codes) to render natively.
        """
        if sys.platform != "win32":
            cls._vt_enabled = True
            return True

        try:
            # Import colorama as secondary wrapper
            try:
                import colorama
                colorama.init(convert=True, autoreset=False)
            except ImportError:
                pass

            # Win32 API handles
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            ENABLE_PROCESSED_OUTPUT = 0x0001
            ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002

            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            if handle == 0 or handle == -1:
                return False

            mode = ctypes.c_ulong()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # Might be redirected or subshell, still return True if terminal supports ANSI
                cls._vt_enabled = True
                return True

            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING | ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT
            if kernel32.SetConsoleMode(handle, new_mode):
                cls._vt_enabled = True
                return True

            cls._vt_enabled = True
            return True
        except Exception:
            cls._vt_enabled = False
            return False

    @staticmethod
    def get_size(default_width: int = 100, default_height: int = 30) -> Tuple[int, int]:
        """Returns the current terminal width and height safely."""
        try:
            size = shutil.get_terminal_size(fallback=(default_width, default_height))
            # Protect against 0 or negative values in weird subshell environments
            width = max(size.columns, 40)
            height = max(size.lines, 15)
            return width, height
        except Exception:
            return default_width, default_height

    @staticmethod
    def supports_truecolor() -> bool:
        """
        Detects if current terminal environment supports 24-bit Truecolor.
        Windows Terminal, modern CMD (Win 10 build 14931+), VS Code, ConEmu, Mintty, etc.
        """
        if os.environ.get("COLORTERM") in ("truecolor", "24bit"):
            return True
        if "WT_SESSION" in os.environ:  # Windows Terminal
            return True
        if "VSCODE_PID" in os.environ or "VSCODE_INJECTION" in os.environ:
            return True
        if sys.platform == "win32":
            # Windows 10 build 14931+ supports truecolor out of the box in cmd.exe
            try:
                build = sys.getwindowsversion().build
                if build >= 14931:
                    return True
            except Exception:
                pass
        return True  # Modern terminals generally support truecolor

    @classmethod
    def hide_cursor(cls) -> None:
        """Hides the terminal cursor during live rendering."""
        if not cls._cursor_hidden:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
            cls._cursor_hidden = True

    @classmethod
    def show_cursor(cls) -> None:
        """Restores the terminal cursor."""
        if cls._cursor_hidden:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
            cls._cursor_hidden = False

    @staticmethod
    def clear_screen() -> None:
        """Clears the terminal screen."""
        if sys.platform == "win32":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    @staticmethod
    def reset_color() -> str:
        """ANSI escape sequence to reset colors."""
        return "\033[0m"

    @staticmethod
    def rgb_to_truecolor_fg(r: int, g: int, b: int) -> str:
        """Generates ANSI 24-bit Truecolor foreground code."""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def rgb_to_truecolor_bg(r: int, g: int, b: int) -> str:
        """Generates ANSI 24-bit Truecolor background code."""
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def rgb_to_256_fg(r: int, g: int, b: int) -> str:
        """Graceful fallback: Converts RGB to 256-color ANSI code."""
        # Check for grayscale
        if abs(r - g) < 8 and abs(g - b) < 8:
            gray = int((r + g + b) / 3)
            if gray < 8:
                code = 16
            elif gray > 248:
                code = 231
            else:
                code = int(((gray - 8) / 247) * 24) + 232
        else:
            # 6x6x6 color cube
            r_idx = int(r / 255.0 * 5.0 + 0.5)
            g_idx = int(g / 255.0 * 5.0 + 0.5)
            b_idx = int(b / 255.0 * 5.0 + 0.5)
            code = 16 + (36 * r_idx) + (6 * g_idx) + b_idx
        return f"\033[38;5;{code}m"

    @staticmethod
    def rgb_to_ansi16_fg(r: int, g: int, b: int) -> str:
        """Graceful fallback: Converts RGB to standard 16-color ANSI code."""
        # Simple brightness check
        brightness = (r + g + b) / 3.0
        bold = 1 if brightness > 128 else 0
        r_b = 1 if r > 80 else 0
        g_b = 1 if g > 80 else 0
        b_b = 1 if b > 80 else 0
        color_index = (r_b * 1) + (g_b * 2) + (b_b * 4)
        ansi_codes = [30, 31, 32, 33, 34, 35, 36, 37]
        return f"\033[{bold};{ansi_codes[color_index % 8]}m"


# Register atexit handler so terminal cursor and color are always safely restored
@atexit.register
def _cleanup_terminal() -> None:
    try:
        sys.stdout.write("\033[0m\033[?25h")
        sys.stdout.flush()
    except Exception:
        pass
