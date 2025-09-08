#!/usr/bin/env python3
from pathlib import Path

RU_PATH = Path(__file__).resolve().parents[1] / "dartLangSpec.ru.tex"


def strip_macros(text: str) -> str:
    i = 0
    n = len(text)
    out = []

    def extract_brace(i0: int):
        assert text[i0] == '{'
        depth = 0
        j = i0
        while j < n:
            c = text[j]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[i0 + 1 : j], j + 1
            j += 1
        # unmatched, return until end
        return text[i0 + 1 :], n

    while i < n:
        if text[i] == '\\':
            # macro name
            j = i + 1
            while j < n and text[j].isalpha():
                j += 1
            name = text[i + 1 : j]
            if name in ("Index", "NoIndex"):
                # Expect one argument
                # skip spaces
                k = j
                while k < n and text[k].isspace():
                    out.append(text[i:k])  # preserve whitespace exactly
                    i = k
                    break
                # After optional spaces, must see '{'
                if k < n and text[k] == '{':
                    content, next_pos = extract_brace(k)
                    # Replace with content only
                    out.append(content)
                    i = next_pos
                    continue
                else:
                    # Fallback: drop macro token
                    i = j
                    continue
            elif name == "IndexCustom":
                # two arguments
                k = j
                # first arg
                while k < n and text[k].isspace():
                    k += 1
                if k < n and text[k] == '{':
                    arg1, pos1 = extract_brace(k)
                else:
                    arg1, pos1 = "", k
                # second arg
                while pos1 < n and text[pos1].isspace():
                    pos1 += 1
                if pos1 < n and text[pos1] == '{':
                    arg2, pos2 = extract_brace(pos1)
                else:
                    arg2, pos2 = "", pos1
                out.append(arg1)
                i = pos2
                continue
            else:
                out.append(text[i])
                i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def main():
    text = RU_PATH.read_text(encoding="utf-8")
    new_text = strip_macros(text)
    RU_PATH.write_text(new_text, encoding="utf-8")
    print("Stripped index macros in", RU_PATH)


if __name__ == "__main__":
    main()