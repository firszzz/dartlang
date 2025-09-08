#!/usr/bin/env python3
from pathlib import Path
import re

SPEC_DIR = Path(__file__).resolve().parents[1]
RU_FILE = SPEC_DIR / "dartLangSpec.ru.tex"

FONT_SPEC = r"""
% XeLaTeX Unicode fonts for Cyrillic
\usepackage{fontspec}
\setmainfont{Noto Serif}
\setsansfont{Noto Sans}
\setmonofont{DejaVu Sans Mono}
""".strip() + "\n"

COLOR_ALIASES = r"""
% Russian color aliases to match translated identifiers
\providecolor{комментарийЦвет}{rgb}{0.5,0.5,0.5}
\providecolor{обоснованиеЦвет}{rgb}{0.5,0.5,0.5}
\providecolor{метаЦвет}{rgb}{0,0,1}
\providecolor{нормативныйЦвет}{rgb}{0,0,0}
""".strip() + "\n"


def main():
    text = RU_FILE.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    out_lines = []
    inserted_fontspec = False
    inserted_color_aliases = False

    for ln in lines:
        # Drop legacy encoding/font packages
        if "\\usepackage[T2A]{fontenc}" in ln:
            continue
        if "\\usepackage[utf8]{inputenc}" in ln:
            continue
        if re.match(r"\\usepackage\{lmodern\}", ln):
            continue
        # Replace babel russian with polyglossia is optional; keep babel or drop
        # We can keep babel, XeLaTeX + fontspec works fine without babel for glyphs.
        if re.match(r"\\usepackage\[russian\]\{babel\}", ln):
            # Drop babel to avoid conflicts
            continue
        out_lines.append(ln)
        # After hyperref or dart.sty lines, inject FONT_SPEC and COLOR_ALIASES once
        if not inserted_fontspec and ("{hyperref}" in ln or "{dart}" in ln):
            out_lines.append(FONT_SPEC)
            inserted_fontspec = True
        if not inserted_color_aliases and ("{xcolor}" in ln):
            out_lines.append(COLOR_ALIASES)
            inserted_color_aliases = True

    # Fallback: if not inserted, add near top after \documentclass
    if not inserted_fontspec:
        for i, ln in enumerate(out_lines):
            if ln.startswith("\\usepackage"):
                out_lines.insert(i + 1, FONT_SPEC)
                inserted_fontspec = True
                break
    if not inserted_color_aliases:
        for i, ln in enumerate(out_lines):
            if "{xcolor}" in ln:
                out_lines.insert(i + 1, COLOR_ALIASES)
                inserted_color_aliases = True
                break

    RU_FILE.write_text("".join(out_lines), encoding="utf-8")
    print("Patched preamble and color aliases in", RU_FILE)


if __name__ == "__main__":
    main()