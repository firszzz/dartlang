#!/usr/bin/env python3
import re
from pathlib import Path

SPEC_DIR = Path(__file__).resolve().parents[1]
RU_FILE = SPEC_DIR / "dartLangSpec.ru.tex"

TOKEN_RE = re.compile(r"[<«]{2,3}P\d{6}[>»]{0,3}")

ARTIFACT_FIXES = [
    (re.compile(r"\{<+%>"), "%"),
    (re.compile(r"\{<+%"), "%"),
    (re.compile(r"%>"), "%"),
    (re.compile(r"<<+\s*>"), ""),
]

def main():
    text = RU_FILE.read_text(encoding="utf-8")
    text = TOKEN_RE.sub("", text)
    for pat, repl in ARTIFACT_FIXES:
        text = pat.sub(repl, text)
    RU_FILE.write_text(text, encoding="utf-8")
    print("Sanitized placeholder residues in", RU_FILE)

if __name__ == "__main__":
    main()