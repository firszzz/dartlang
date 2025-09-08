#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
import argparse

try:
    from argostranslate import package as argos_package
    from argostranslate import translate as argos_translate
except Exception as e:
    print(f"Failed to import argostranslate: {e}")
    sys.exit(1)

from translate_to_ru import (
    make_placeholders,
    restore_placeholders,
    apply_pre_replacements,
    apply_post_replacements,
    tweak_preamble_for_cyrillic,
)

SPEC_DIR = Path(__file__).resolve().parents[1]
SRC_FILE = SPEC_DIR / "dartLangSpec.tex"
CHUNKS_DIR = SPEC_DIR / ".ru_chunks"


def ensure_argos_model():
    argos_package.update_package_index()
    available = argos_package.get_available_packages()
    candidates = [p for p in available if p.from_code == "en" and p.to_code == "ru"]
    if not candidates:
        print("No Argos en->ru package available")
        sys.exit(1)
    pkg = candidates[0]
    installed = argos_package.get_installed_packages()
    if not any(ip.from_code == "en" and ip.to_code == "ru" for ip in installed):
        download_path = pkg.download()
        argos_package.install_from_path(download_path)


def split_body_into_chunks(body: str, chunks: int) -> list[tuple[int, int]]:
    # Split on paragraph boundaries (double newline) into nearly equal sized chunks
    boundaries = [0]
    for m in re.finditer(r"\n\s*\n", body):
        boundaries.append(m.end())
    boundaries.append(len(body))

    # If too few boundaries, fall back to fixed-size chunks
    if len(boundaries) < chunks + 2:
        size = len(body) // chunks + 1
        return [(i * size, min(len(body), (i + 1) * size)) for i in range(chunks)]

    # Target size per chunk
    target = len(body) / chunks
    ranges = []
    start = 0
    acc = 0.0
    last_idx = 0
    for i in range(1, len(boundaries)):
        acc += boundaries[i] - boundaries[i - 1]
        if acc >= target and len(ranges) < chunks - 1:
            ranges.append((start, boundaries[i]))
            start = boundaries[i]
            acc = 0.0
            last_idx = i
    ranges.append((start, len(body)))
    return ranges


def translate_text(text: str) -> str:
    masked, placeholders = make_placeholders(text)
    masked = apply_pre_replacements(masked)

    # Translate by manageable subchunks to avoid model slowdowns
    out_parts = []
    max_len = 4000
    start = 0
    while start < len(masked):
        end = min(len(masked), start + max_len)
        sub = masked[start:end]
        if end < len(masked):
            nl = sub.rfind("\n")
            if nl > 0:
                end = start + nl
                sub = masked[start:end]
        translated_sub = argos_translate.translate(sub, "en", "ru")
        translated_sub = apply_post_replacements(translated_sub)
        out_parts.append(translated_sub)
        start = end

    restored = restore_placeholders("".join(out_parts), placeholders)
    return restored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["preamble", "body"], required=True)
    parser.add_argument("--chunks", type=int, default=12)
    parser.add_argument("--index", type=int, default=0)
    args = parser.parse_args()

    if not SRC_FILE.exists():
        print(f"Source file not found: {SRC_FILE}")
        sys.exit(1)

    ensure_argos_model()
    src = SRC_FILE.read_text(encoding="utf-8")

    # Extract preamble and body
    m_begin = re.search(r"\\begin\{document\}", src)
    m_end = re.search(r"\\end\{document\}", src)
    if not m_begin or not m_end:
        print("Could not find document boundaries")
        sys.exit(1)

    preamble = src[: m_begin.start()]
    body = src[m_begin.end() : m_end.start()]

    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "preamble":
        translated = translate_text(preamble)
        translated = tweak_preamble_for_cyrillic(translated)
        (CHUNKS_DIR / "preamble.ru.tex").write_text(translated, encoding="utf-8")
        print("Wrote preamble chunk")
        return

    ranges = split_body_into_chunks(body, args.chunks)
    if not (0 <= args.index < len(ranges)):
        print(f"Index out of range: {args.index} of {len(ranges)}")
        sys.exit(1)

    start, end = ranges[args.index]
    segment = body[start:end]
    translated = translate_text(segment)
    out_path = CHUNKS_DIR / f"body.{args.index:03d}.ru.tex"
    out_path.write_text(translated, encoding="utf-8")
    print(f"Wrote body chunk {args.index} of {len(ranges)} -> {out_path}")


if __name__ == "__main__":
    main()