#!/usr/bin/env python3
"""Reference impl for: esim-global-s1-parse-global

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Patches build.py in place with two anchored replacements:
  1. adds module-level parse_global() right after parse_country();
  2. wires collect() to call it for Global/README.md only (other READMEs stay skipped).
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'build.py'
t = p.read_text()

# --- anchor 1: end of parse_country ---------------------------------------
OLD1 = """            "seen": g("seen"),
        })
    return {"title": title, "rows": rows}


def collect():"""
NEW1 = """            "seen": g("seen"),
        })
    return {"title": title, "rows": rows}


def parse_global(md_path):
    \"\"\"Parse the first rate table of Global/README.md with parse_country's row logic.

    Every returned row is additionally flagged global_coverage=True so later
    slices can render it as a multi-region plan rather than a country page.\"\"\"
    rows = parse_country(md_path)["rows"]
    for row in rows:
        row["global_coverage"] = True
    return rows


def collect():"""

# --- anchor 2: the README skip inside collect() ----------------------------
OLD2 = """            if md.name.lower() == "readme.md":
                continue"""
NEW2 = """            if md.name.lower() == "readme.md":
                if region == "Global":
                    g_rows = parse_global(md)
                    if g_rows:
                        data.append({
                            "region": "Global",
                            "country": "Global",
                            "slug": "README",
                            "md_path": f"{region}/README.md",
                            "rows": g_rows,
                        })
                continue"""

assert OLD1 in t, "refimpl anchor 1 not found -- did build.py change?"
assert OLD2 in t, "refimpl anchor 2 not found -- did build.py change?"
t = t.replace(OLD1, NEW1, 1).replace(OLD2, NEW2, 1)
p.write_text(t)
print("refimpl applied")
