#!/usr/bin/env python3
"""Reference impl for: esim-global-s2-picker-exclude-global

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Change made to build.py: render_index() builds its picker grid and header
counts from `picker_entries(data)` -- every entry except the 'Global' one. The
Global worldwide table stays in collect()/rates.json; only the index.html
destination picker stops treating it as a country/region.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / "build.py"
t = p.read_text()

OLD_FN = "def render_index(data):"
NEW_FN = (
    'def picker_entries(data):\n'
    '    return [e for e in data if e["region"] != "Global"\n'
    '            and e["country"].lower() != "global"]\n'
    "\n\n"
    "def render_index(data):"
)

OLD_LOOP = (
    "    by_region = {}\n"
    "    for e in data:\n"
    "        by_region.setdefault(e[\"region\"], []).append(e)\n"
)
NEW_LOOP = (
    "    picker = picker_entries(data)\n"
    "    by_region = {}\n"
    "    for e in picker:\n"
    "        by_region.setdefault(e[\"region\"], []).append(e)\n"
)

OLD_COUNT = "    n_countries = len(data)\n"
NEW_COUNT = "    n_countries = len(picker)\n"

assert OLD_FN in t, "render_index anchor not found -- did the target change?"
t = t.replace(OLD_FN, NEW_FN, 1)
assert OLD_LOOP in t, "picker by_region loop anchor not found"
t = t.replace(OLD_LOOP, NEW_LOOP, 1)
assert OLD_COUNT in t, "n_countries anchor not found"
t = t.replace(OLD_COUNT, NEW_COUNT, 1)

p.write_text(t)
print("refimpl applied")
