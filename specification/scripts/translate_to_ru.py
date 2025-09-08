#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

# External deps: argostranslate
try:
    from argostranslate import package as argos_package
    from argostranslate import translate as argos_translate
except Exception as e:
    print(f"Failed to import argostranslate: {e}")
    sys.exit(1)

SPEC_DIR = Path(__file__).resolve().parents[1]
SRC_FILE = SPEC_DIR / "dartLangSpec.tex"
OUT_FILE = SPEC_DIR / "dartLangSpec.ru.tex"

# Environments whose entire contents must be preserved verbatim (no translation)
PROTECTED_ENVS = [
    "dartCode",
    "normativeDartCode",
    "verbatim",
    "lstlisting",
    "alltt",
    "syntax",
    "tabular",
    "array",
    "align",
    "align*",
    "equation",
    "equation*",
    "displaymath",
]

# Commands with arguments that must be preserved entirely (no translation)
PROTECTED_COMMANDS_FULL = [
    "ref",
    "label",
    "cite",
    "url",
    "href",
    "path",
    "index",
    "Index",
    "code",
    "texttt",
    "tt",
    "kw",
    "id",
    "LMHash",
    "LMLabel",
    "BlindDefineSymbol",
]

# Commands which we should keep, but we DO want to translate their {argument}
SECTIONING_COMMANDS = [
    "title",
    "section",
    "subsection",
    "subsubsection",
    "paragraph",
    "subparagraph",
]

# Simple technical term preprocessing and postprocessing
PRE_REPLACEMENTS = [
    # Mark terms to stabilize translation
    (r"\bIsolate\b", "IsolateTerm"),
    (r"\bIsolates\b", "IsolateTerm"),
    (r"\bisolate\b", "IsolateTerm"),
    (r"\bDeclaration\b", "DeclarationTerm"),
    (r"\bDeclarations\b", "DeclarationTerm"),
]

POST_REPLACEMENTS = [
    (r"IsolateTerm", "изолят"),
    (r"DeclarationTerm", "декларация"),
]

# Math patterns to protect
MATH_PATTERNS = [
    re.compile(r"\\\(.*?\\\)", re.DOTALL),  # \( ... \)
    re.compile(r"\\\[.*?\\\]", re.DOTALL),  # \[ ... \]
    re.compile(r"\$\$[\s\S]*?\$\$", re.DOTALL),  # $$ ... $$
    re.compile(r"\$[^\n$]*?\$", re.DOTALL),  # $ ... $
]

PLACEHOLDER_PREFIX = "<<<P"
PLACEHOLDER_SUFFIX = ">>>"


def ensure_argos_model():
    # Ensure en->ru model is installed
    argos_package.update_package_index()
    available = argos_package.get_available_packages()
    candidates = [p for p in available if p.from_code == "en" and p.to_code == "ru"]
    if not candidates:
        print("No Argos en->ru package available")
        sys.exit(1)
    # Prefer the first (usually latest)
    pkg = candidates[0]
    installed = argos_package.get_installed_packages()
    if not any(ip.from_code == "en" and ip.to_code == "ru" for ip in installed):
        download_path = pkg.download()
        argos_package.install_from_path(download_path)


def make_placeholders(text: str):
    placeholders = {}
    counter = 0

    def put(segment: str) -> str:
        nonlocal counter
        key = f"{PLACEHOLDER_PREFIX}{counter:06d}{PLACEHOLDER_SUFFIX}"
        placeholders[key] = segment
        counter += 1
        return key

    # 1) Protect multi-line environments fully
    for env in PROTECTED_ENVS:
        pattern = re.compile(rf"\\begin\{{{re.escape(env)}\}}[\s\S]*?\\end\{{{re.escape(env)}\}}", re.DOTALL)
        while True:
            m = pattern.search(text)
            if not m:
                break
            segment = m.group(0)
            token = put(segment)
            text = text[:m.start()] + token + text[m.end():]

    # 2) Protect math segments
    for math_re in MATH_PATTERNS:
        while True:
            m = math_re.search(text)
            if not m:
                break
            segment = m.group(0)
            token = put(segment)
            text = text[:m.start()] + token + text[m.end():]

    # 3) Protect \begin{...} and \end{...} tokens themselves (names should not be translated)
    for kw in ("begin", "end"):
        pattern = re.compile(rf"\\{kw}\{{[^}}]*\}}")
        while True:
            m = pattern.search(text)
            if not m:
                break
            segment = m.group(0)
            token = put(segment)
            text = text[:m.start()] + token + text[m.end():]

    # 4) Protect fully-argument commands like \ref{...}, \label{...}, etc.
    for cmd in PROTECTED_COMMANDS_FULL:
        pattern = re.compile(rf"\\{cmd} *\{{[^\n\r\{{\}}]*\}}")
        while True:
            m = pattern.search(text)
            if not m:
                break
            segment = m.group(0)
            token = put(segment)
            text = text[:m.start()] + token + text[m.end():]

    # 5) Protect all control sequences except sectioning commands (command token only)
    control_seq_re = re.compile(r"\\[a-zA-Z]+\*?")
    while True:
        m = control_seq_re.search(text)
        if not m:
            break
        cmd = m.group(0)
        name = cmd[1:].rstrip("*")
        if name in SECTIONING_COMMANDS:
            # Leave command token intact for later, do not protect
            # But protect the command token itself to avoid translation altering it
            token = put(cmd)
            text = text[:m.start()] + token + text[m.end():]
        else:
            token = put(cmd)
            text = text[:m.start()] + token + text[m.end():]

    # 6) Protect double backslash and other single-char control sequences
    single_ctrl_re = re.compile(r"\\[^a-zA-Z]")
    while True:
        m = single_ctrl_re.search(text)
        if not m:
            break
        segment = m.group(0)
        token = put(segment)
        text = text[:m.start()] + token + text[m.end():]

    return text, placeholders


def restore_placeholders(text: str, placeholders: dict) -> str:
    # Replace tokens back in insertion order (keys are unique, order doesn't matter)
    for token, segment in placeholders.items():
        text = text.replace(token, segment)
    return text


def apply_pre_replacements(text: str) -> str:
    for pattern, repl in PRE_REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    return text


def apply_post_replacements(text: str) -> str:
    for pattern, repl in POST_REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    return text


def translate_blocks(text: str) -> str:
    # Split into blocks separated by blank lines to keep structure
    blocks = re.split(r"(\n\s*\n)", text)
    translated_parts = []
    for i, block in enumerate(blocks):
        # Keep pure separators as-is
        if re.fullmatch(r"\n\s*\n", block or ""):
            translated_parts.append(block)
            continue
        if not block.strip():
            translated_parts.append(block)
            continue
        # Argos translate per chunk smaller than ~5000 chars
        chunk = block
        chunk_translated = []
        max_len = 4000
        start = 0
        while start < len(chunk):
            end = min(len(chunk), start + max_len)
            sub = chunk[start:end]
            # Try to avoid splitting in the middle of a line
            if end < len(chunk):
                nl = sub.rfind("\n")
                if nl > 0:
                    end = start + nl
                    sub = chunk[start:end]
            translated_sub = argos_translate.translate(sub, "en", "ru")
            translated_sub = apply_post_replacements(translated_sub)
            chunk_translated.append(translated_sub)
            start = end
        translated_parts.append("".join(chunk_translated))
    return "".join(translated_parts)


def tweak_preamble_for_cyrillic(text: str) -> str:
    # Replace fontenc T1 -> T2A and add utf8 inputenc and russian babel if not present
    text_lines = text.splitlines(keepends=True)
    result = []
    inserted_after_fontenc = False
    has_inputenc = any("usepackage[utf8]{inputenc}" in ln for ln in text_lines)
    has_babel = any("usepackage[russian]" in ln or "usepackage[english,russian]" in ln or "usepackage[russian,english]" in ln for ln in text_lines)

    for ln in text_lines:
        if "\\usepackage[T1]{fontenc}" in ln:
            ln = ln.replace("\\usepackage[T1]{fontenc}", "\\usepackage[T2A]{fontenc}")
            result.append(ln)
            if not has_inputenc:
                result.append("\\usepackage[utf8]{inputenc}\n")
            if not has_babel:
                result.append("\\usepackage[russian]{babel}\n")
            inserted_after_fontenc = True
            continue
        result.append(ln)

    # If no fontenc line existed, add necessary lines near the top after \documentclass
    if not inserted_after_fontenc:
        new_result = []
        inserted = False
        for ln in result:
            new_result.append(ln)
            if not inserted and ln.lstrip().startswith("\\usepackage"):
                # Insert right after the first usepackage occurrence
                if not has_inputenc:
                    new_result.append("\\usepackage[utf8]{inputenc}\n")
                if not has_babel:
                    new_result.append("\\usepackage[russian]{babel}\n")
                inserted = True
        result = new_result

    return "".join(result)


def main():
    if not SRC_FILE.exists():
        print(f"Source file not found: {SRC_FILE}")
        sys.exit(1)

    ensure_argos_model()

    src = SRC_FILE.read_text(encoding="utf-8")

    # Protect comments: we won't translate pure comment lines, but they'll remain in place
    # For simplicity we keep them as part of the text, protection will cover commands.

    # Protect LaTeX structures with placeholders
    masked, placeholders = make_placeholders(src)

    # Preprocess terms (in unmasked text only)
    masked = apply_pre_replacements(masked)

    # Translate
    translated = translate_blocks(masked)

    # Restore placeholders
    restored = restore_placeholders(translated, placeholders)

    # Tweak preamble for Cyrillic
    restored = tweak_preamble_for_cyrillic(restored)

    OUT_FILE.write_text(restored, encoding="utf-8")
    print(f"Written: {OUT_FILE}")


if __name__ == "__main__":
    main()