#!/usr/bin/env python3

from pathlib import Path
import re

SPEC_DIR = Path(__file__).resolve().parents[1]
SRC_FILE = SPEC_DIR / "dartLangSpec.tex"
OUT_FILE = SPEC_DIR / "dartLangSpec.ru.tex"
CHUNKS_DIR = SPEC_DIR / ".ru_chunks"


def adjust_preamble_for_cyrillic(preamble: str) -> str:
    lines = preamble.splitlines(keepends=True)
    result = []
    inserted_after_fontenc = False
    has_inputenc = any("usepackage[utf8]{inputenc}" in ln for ln in lines)
    has_babel_ru = any("usepackage[russian]" in ln for ln in lines)

    for ln in lines:
        if "\\usepackage[T1]{fontenc}" in ln:
            ln = ln.replace("\\usepackage[T1]{fontenc}", "\\usepackage[T2A]{fontenc}")
            result.append(ln)
            if not has_inputenc:
                result.append("\\usepackage[utf8]{inputenc}\n")
            if not has_babel_ru:
                result.append("\\usepackage[russian]{babel}\n")
            inserted_after_fontenc = True
            continue
        result.append(ln)

    if not inserted_after_fontenc:
        # Insert after first \usepackage line if fontenc not found
        new_result = []
        inserted = False
        for ln in result:
            new_result.append(ln)
            if not inserted and ln.lstrip().startswith("\\usepackage"):
                if not has_inputenc:
                    new_result.append("\\usepackage[utf8]{inputenc}\n")
                if not has_babel_ru:
                    new_result.append("\\usepackage[russian]{babel}\n")
                inserted = True
        result = new_result

    return "".join(result)


def main():
    src = SRC_FILE.read_text(encoding="utf-8")
    m_begin = re.search(r"\\begin\{document\}", src)
    m_end = re.search(r"\\end\{document\}", src)
    if not m_begin or not m_end:
        raise SystemExit("Could not find document boundaries in source")

    preamble = src[: m_begin.start()]
    preamble = adjust_preamble_for_cyrillic(preamble)

    # Read translated chunks
    pre_ru = (CHUNKS_DIR / "preamble.ru.tex").read_text(encoding="utf-8")  # unused, we prefer original preamble
    body_parts = []
    i = 0
    while True:
        path = CHUNKS_DIR / f"body.{i:03d}.ru.tex"
        if not path.exists():
            break
        body_parts.append(path.read_text(encoding="utf-8"))
        i += 1
    if not body_parts:
        raise SystemExit("No translated body chunks found")

    body_ru = "".join(body_parts)
    out = preamble + "\\begin{document}\n" + body_ru + "\n\\end{document}\n"
    OUT_FILE.write_text(out, encoding="utf-8")
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()