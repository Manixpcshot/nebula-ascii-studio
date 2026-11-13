"""
NEBULA ASCII STUDIO — Professional Terminal UI (Version 3.0)
Interactive Rich interface supporting modes A/B/C, resolution selection
(100-300+ columns), and comprehensive rendering summaries.
"""

import os
import sys
from typing import Any, Dict, Optional, Tuple

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_TAGLINE,
    APP_VERSION,
    MODE_PORTRAIT_PRECISION,
    MODE_RGB_PHOTOREALISTIC,
    MODE_ULTRA_DETAIL,
    RENDERING_MODES,
    RESOLUTION_OPTIONS,
    SUPPORTED_EXTENSIONS,
    THEME_BLUE,
    THEME_CYAN,
    THEME_ERROR,
    THEME_MAGENTA,
    THEME_PURPLE,
    THEME_SUCCESS,
    THEME_TEXT,
    THEME_WARNING,
)
from .terminal import TerminalManager

console = Console(highlight=False)


class TerminalUI:
    """Manages all Rich-based terminal presentation."""

    BANNER_ASCII = r"""
 ███╗   ██╗███████╗██████╗ ██╗   ██╗██╗      █████╗ 
 ████╗  ██║██╔════╝██╔══██╗██║   ██║██║     ██╔══██╗
 ██╔██╗ ██║█████╗  ██████╔╝██║   ██║██║     ███████║
 ██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║██║     ██╔══██║
 ██║ ╚████║███████╗██████╔╝╚██████╔╝███████╗██║  ██║
 ╚═╝  ╚═══╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
   ───  A S C I I   S T U D I O   v{version}  ───
"""

    @classmethod
    def display_banner(cls) -> None:
        """Displays glowing startup header."""
        TerminalManager.enable_vt_mode()

        banner_text = cls.BANNER_ASCII.format(version=APP_VERSION)
        styled_banner = Text(banner_text, style=f"bold {THEME_CYAN}")

        subtitle_text = Text()
        subtitle_text.append(f"{APP_SUBTITLE}\n", style=f"bold {THEME_MAGENTA}")
        subtitle_text.append(f"{APP_TAGLINE}\n", style=f"italic {THEME_BLUE}")
        subtitle_text.append("Windows 10/11 CMD Certified • 24-bit Truecolor • Rec. 709 Luminance", style="dim")

        panel = Panel(
            Align.center(Text.assemble(styled_banner, "\n", subtitle_text)),
            box=ROUNDED,
            border_style=f"bold {THEME_PURPLE}",
            padding=(1, 2),
        )
        console.print(panel)

    @classmethod
    def prompt_image_path(cls) -> str:
        """Prompts for image path with quote sanitization and demo shortcuts."""
        console.print()
        console.print(f"[{THEME_CYAN}]➤ Enter image path[/{THEME_CYAN}] [dim](e.g. C:\\Users\\User\\photo.jpg or drag & drop)[/dim]")
        console.print(f"  [dim]Quick Demos: [white]'portrait'[/white], [white]'bw'[/white], [white]'colorful'[/white], [white]'hair'[/white], [white]'landscape'[/white], [white]'demo'[/white][/dim]")

        while True:
            try:
                user_input = Prompt.ask(f"[{THEME_MAGENTA}]Image Path[/{THEME_MAGENTA}]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n[{THEME_WARNING}]Exiting.[/{THEME_WARNING}]")
                sys.exit(0)

            clean = user_input.strip("'\"")

            # Check demo shortcuts
            if clean.lower() in ("portrait", "face"):
                from .samples import SampleGenerator
                return SampleGenerator.generate_portrait()
            if clean.lower() in ("bw", "blackandwhite", "mono"):
                from .samples import SampleGenerator
                return SampleGenerator.generate_bw_classic()
            if clean.lower() in ("colorful", "vivid", "demo"):
                from .samples import SampleGenerator
                return SampleGenerator.generate_colorful()
            if clean.lower() in ("hair", "texture", "textures"):
                from .samples import SampleGenerator
                return SampleGenerator.generate_hair_textures()
            if clean.lower() in ("landscape", "scenery"):
                from .samples import SampleGenerator
                return SampleGenerator.generate_landscape()

            if clean.lower() in ("q", "quit", "exit"):
                console.print(f"[{THEME_CYAN}]Farewell![/{THEME_CYAN}]")
                sys.exit(0)

            if not clean:
                console.print(f"[{THEME_WARNING}]Path cannot be empty.[/{THEME_WARNING}]")
                continue

            if not os.path.exists(clean):
                console.print(f"[{THEME_ERROR}]File not found: '{clean}'[/{THEME_ERROR}]")
                continue

            if not os.path.isfile(clean):
                console.print(f"[{THEME_ERROR}]Path is a directory, not a file.[/{THEME_ERROR}]")
                continue

            ext = os.path.splitext(clean)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                console.print(f"[{THEME_ERROR}]Unsupported format '{ext}'.[/{THEME_ERROR}]")
                continue

            return clean

    @classmethod
    def choose_rendering_mode(cls) -> str:
        """Presents Mode A, Mode B, Mode C selection."""
        table = Table(
            title="[bold #00f0ff]SELECT RENDERING MODE[/bold #00f0ff]",
            box=ROUNDED,
            border_style=THEME_PURPLE,
            header_style=f"bold {THEME_MAGENTA}",
            title_justify="center",
            padding=(0, 1),
        )
        table.add_column("#", justify="center", style="bold cyan", width=4)
        table.add_column("Mode", style="bold white", width=28)
        table.add_column("Description", style=THEME_TEXT)

        modes = [
            (MODE_ULTRA_DETAIL, RENDERING_MODES[MODE_ULTRA_DETAIL]),
            (MODE_RGB_PHOTOREALISTIC, RENDERING_MODES[MODE_RGB_PHOTOREALISTIC]),
            (MODE_PORTRAIT_PRECISION, RENDERING_MODES[MODE_PORTRAIT_PRECISION]),
        ]

        for idx, (k, m) in enumerate(modes, 1):
            table.add_row(str(idx), m["name"], m["description"])

        console.print()
        console.print(table)
        console.print(f"[dim]Press [bold white]Enter[/bold white] for [bold cyan]MODE A — ULTRA DETAIL[/bold cyan] (Default)[/dim]")

        choice = Prompt.ask(f"[{THEME_CYAN}]Select Mode [1-3][/{THEME_CYAN}]", default="1").strip()
        mode_keys = [MODE_ULTRA_DETAIL, MODE_RGB_PHOTOREALISTIC, MODE_PORTRAIT_PRECISION]

        try:
            c_idx = int(choice) - 1
            if 0 <= c_idx < len(mode_keys):
                return mode_keys[c_idx]
        except ValueError:
            pass

        return MODE_ULTRA_DETAIL

    @classmethod
    def choose_resolution(cls, term_width: int) -> int:
        """Presents resolution width options (100, 150, 200, 250, 300, Custom)."""
        table = Table(
            title="[bold #00f0ff]OUTPUT RESOLUTION (COLUMNS)[/bold #00f0ff]",
            box=ROUNDED,
            border_style=THEME_PURPLE,
            header_style=f"bold {THEME_MAGENTA}",
            title_justify="center",
            padding=(0, 1),
        )
        table.add_column("#", justify="center", style="bold cyan", width=4)
        table.add_column("Width Preset", style="bold white", width=20)
        table.add_column("Best For", style=THEME_TEXT)

        table.add_row("1", "100 Columns", "Standard CMD / Compact Terminal window")
        table.add_row("2", "150 Columns", "High Detail / Recommended for Portraits (Default)")
        table.add_row("3", "200 Columns", "Ultra Wide / 1080p full-width terminal")
        table.add_row("4", "250 Columns", "Extreme Fidelity / High character density")
        table.add_row("5", "300 Columns", "Master Studio Canvas / Maximum resolution")
        table.add_row("6", "Custom Width", "Enter any width between 40 and 500 columns")

        console.print()
        console.print(table)
        console.print(f"[dim]Press [bold white]Enter[/bold white] for [bold cyan]150 Columns[/bold cyan] (Recommended)[/dim]")

        choice = Prompt.ask(f"[{THEME_CYAN}]Select Resolution [1-6][/{THEME_CYAN}]", default="2").strip()

        preset_map = {"1": 100, "2": 150, "3": 200, "4": 250, "5": 300}
        if choice in preset_map:
            return preset_map[choice]

        if choice == "6":
            custom_str = Prompt.ask(f"[{THEME_MAGENTA}]Enter custom column width (40 to 500)[/{THEME_MAGENTA}]", default="150").strip()
            try:
                return max(40, min(int(custom_str), 500))
            except ValueError:
                return 150

        return 150

    @classmethod
    def display_pre_render_summary(
        cls,
        image_name: str,
        orig_dims: Tuple[int, int],
        target_dims: Tuple[int, int],
        mode_name: str,
        ramp_len: int,
    ) -> None:
        """Displays technical briefing card before rendering."""
        total_cells = target_dims[0] * target_dims[1]

        table = Table(box=ROUNDED, border_style=THEME_CYAN, show_header=False, padding=(0, 1))
        table.add_column("Property", style=f"bold {THEME_MAGENTA}", width=22)
        table.add_column("Value", style="bold white")

        table.add_row("Source Image", os.path.basename(image_name))
        table.add_row("Original Resolution", f"{orig_dims[0]} × {orig_dims[1]} px")
        table.add_row("ASCII Reconstruction", f"{target_dims[0]} cols × {target_dims[1]} rows")
        table.add_row("Total Mapped Glyphs", f"{total_cells:,} characters")
        table.add_row("Active Mode", mode_name)
        table.add_row("Optical Ramp Levels", f"{ramp_len} calibrated density tiers")
        table.add_row("Color Pipeline", "24-bit Truecolor (Rec. 709 Luminance)")

        panel = Panel(
            table,
            title=f"[bold {THEME_CYAN}]✦ HIGH-FIDELITY RENDER SPECIFICATIONS ✦[/bold {THEME_CYAN}]",
            border_style=THEME_BLUE,
            padding=(0, 1),
        )
        console.print()
        console.print(panel)
        console.print(f"[{THEME_SUCCESS}]Streaming live Truecolor ASCII reconstruction...[/{THEME_SUCCESS}]\n")

    @classmethod
    def display_completion_card(
        cls,
        stats: Dict[str, Any],
        txt_path: str,
        html_path: str,
        png_path: str,
        comp_path: Optional[str] = None,
    ) -> None:
        """Displays completion metrics and generated export paths."""
        card = Text()
        card.append("🎉 ASCII RECONSTRUCTION COMPLETED SUCCESSFULLY!\n\n", style=f"bold {THEME_SUCCESS}")
        card.append(f"Grid Dimensions : ", style=f"bold {THEME_CYAN}")
        card.append(f"{stats['cols']} cols × {stats['rows']} rows ({stats['total_chars']:,} characters)\n", style="white")
        card.append(f"Render Duration : ", style=f"bold {THEME_CYAN}")
        card.append(f"{stats['elapsed_seconds']}s ({stats['chars_per_sec']:,} glyphs/sec)\n", style="white")
        card.append(f"Color Fidelity  : ", style=f"bold {THEME_CYAN}")
        card.append("24-bit ANSI Truecolor (Exact Color Preservation)\n\n", style="white")

        card.append("📁 Generated Export Files:\n", style=f"bold {THEME_MAGENTA}")
        card.append(f"  🖼️  High-Res PNG Art : {os.path.abspath(png_path)}\n", style="bold white")
        card.append(f"  🌐  Interactive HTML : {os.path.abspath(html_path)}\n", style="bold white")
        card.append(f"  📄  Clean Monospace  : {os.path.abspath(txt_path)}\n", style="bold white")
        if comp_path:
            card.append(f"  🔍  Side-by-Side Comp: {os.path.abspath(comp_path)}\n", style="bold cyan")

        panel = Panel(
            card,
            title=f"[bold {THEME_PURPLE}]✦ NEBULA ASCII STUDIO v3.0 — COMPLETE ✦[/bold {THEME_PURPLE}]",
            border_style=THEME_CYAN,
            padding=(1, 2),
        )
        console.print()
        console.print(panel)
