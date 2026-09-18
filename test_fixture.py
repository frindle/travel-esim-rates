"""Adversarial fixture for: esim-global-v2

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)
"""
import os
import sys
import tempfile
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("target", 'build.py')
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)


def _global_rows():
    return target.parse_global(Path("Global/README.md"))["rows"]


def _country_page_html():
    data = target.collect()
    e = next(x for x in data if not x.get("global"))
    g = [r for x in data if x.get("global") for r in x["rows"]]
    return e, target.render_country_page(e, g)


def _no_table_parse():
    fd, name = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("# No table here\n\nJust prose, no rate table.\n")
    return target.parse_global(Path(name))["rows"]


CASES = [
    ("parse_global parses Global/README.md's first row with parse_country's fields + global flag",
     lambda: {k: _global_rows()[0][k] for k in ("provider", "plan", "price", "data_gb",
                                                "unlimited", "duration_days", "per_gb",
                                                "hotspot_ok", "rating", "global_coverage")},
     {"provider": "Maya Mobile", "plan": "Global unlimited / 3 d", "price": 9.99,
      "data_gb": None, "unlimited": True, "duration_days": 3, "per_gb": None,
      "hotspot_ok": True, "rating": 4.6, "global_coverage": True}),

    ("collect() surfaces a Global entry whose rows are ALL flagged global-coverage",
     lambda: any(e["region"] == "Global" and e.get("global") is True
                 and len(e["rows"]) >= 10
                 and all(r.get("global_coverage") is True for r in e["rows"])
                 for e in target.collect()),
     True),

    ("no regional README (Asia/Europe/...) leaks into the destination list",
     lambda: any(not e.get("global") and e["md_path"].lower().endswith("/readme.md")
                 for e in target.collect()),
     False),

    ("regression: country rows are NOT flagged global-coverage",
     lambda: all(not r.get("global_coverage") for e in target.collect()
                 if not e.get("global") for r in e["rows"]),
     True),

    ("index.html: 'Worldwide / Global' section, no Global checkbox, GLOBAL_ROWS + badge present",
     lambda: (lambda h: ("Worldwide / Global" in h)
              and ('value="Global::' not in h)
              and ('<span class="chip">Global</span>' in h)
              and ("GLOBAL_ROWS" in h)
              and ("Maya Mobile" in h))(target.render_index(target.collect())),
     True),

    ("per-country page merges global rows (badged) while keeping its own rows",
     lambda: (lambda e, h: ("Maya Mobile" in h)
             and ('<span class="chip">Global</span>' in h)
             and (e["rows"][0]["provider"] in h))(*_country_page_html()),
     True),

    ("boundary: parse_global on a table-less .md returns empty rows without raising",
     lambda: _no_table_parse() == [],
     True),

    ("regression: existing country pages still parse (Japan + Germany present with rows)",
     lambda: {e["country"] for e in target.collect() if not e.get("global") and len(e["rows"]) > 0} >= {"Japan", "Germany"},
     True),
]


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        print("  A generated scaffold is not a verify. Author the cases in "
              "test_fixture.py.")
        return 1
    fails = 0
    for desc, thunk, want in CASES:
        try:
            got = thunk()
        except Exception as e:
            print("  FAIL {} -- raised {}: {}".format(desc, type(e).__name__, e))
            fails += 1
            continue
        if got != want:
            print("  FAIL {} -- got {!r}, want {!r}".format(desc, got, want))
            fails += 1
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
