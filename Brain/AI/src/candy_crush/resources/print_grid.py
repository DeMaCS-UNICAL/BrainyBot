#!/usr/bin/env python3
import sys
import re
from pathlib import Path

CELL_RE = re.compile(r"cell\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*\"(.*?)\"\s*\)\.")


def type_to_char(t: str) -> str:
    if t is None or t == "" or t.lower() == "empty":
        return '.'
    return t[0].upper()


def parse_cells(lines):
    cells = {}
    max_r = max_c = -1
    for line in lines:
        m = CELL_RE.search(line)
        if not m:
            continue
        # id_str = m.group(1)  # available if ever needed
        r = int(m.group(2))
        c = int(m.group(3))
        t = m.group(4)
        cells[(r, c)] = t
        if r > max_r:
            max_r = r
        if c > max_c:
            max_c = c
    return cells, max_r, max_c


def render_grid(cells, max_r, max_c):
    rows = []
    for r in range(max_r + 1):
        row_chars = []
        for c in range(max_c + 1):
            t = cells.get((r, c), "")
            row_chars.append(type_to_char(t))
        rows.append("".join(row_chars))
    return "\n".join(rows)


def main():
    # Determine input file
    if len(sys.argv) > 1:
        facts_path = Path(sys.argv[1])
    else:
        # default to examplefacts.asp in the same directory as this script
        facts_path = Path(__file__).with_name("examplefacts.asp")

    if not facts_path.exists():
        print(f"Facts file not found: {facts_path}", file=sys.stderr)
        sys.exit(1)

    with facts_path.open() as f:
        lines = f.readlines()

    cells, max_r, max_c = parse_cells(lines)
    if max_r < 0 or max_c < 0:
        print("No cell facts found.", file=sys.stderr)
        sys.exit(2)

    print(render_grid(cells, max_r, max_c))


if __name__ == "__main__":
    main()
