"""Adversarial fixture for: esim-global-s1-parse-global

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
import sys
import importlib.util
import pathlib
import tempfile

spec = importlib.util.spec_from_file_location("target", 'build.py')
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)

P = target.ROOT / "Global" / "README.md"


def _g():
    return target.parse_global(P)


def _no_table_md():
    d = pathlib.Path(tempfile.mkdtemp(prefix="esim-fixture-"))
    f = d / "empty.md"
    f.write_text("# Some page\n\nNo rate table on this page at all.\n", encoding="utf-8")
    return f


CASES = [
    # --- parse_global: the new parser -------------------------------------
    ("parse_global returns all 18 rows of Global/README.md's first table",
     lambda: len(_g()), 18),

    ("every parse_global row is flagged global_coverage=True (not missing, not False)",
     lambda: all(r.get("global_coverage") is True for r in _g()), True),

    ("row values match parse_country logic -- Maya Mobile unlimited / 3 d",
     lambda: {k: _g()[0][k] for k in ("provider", "plan", "price", "data_gb",
                                      "unlimited", "duration_days", "per_gb", "hotspot_ok")},
     {"provider": "Maya Mobile", "plan": "Global unlimited / 3 d", "price": 9.99,
      "data_gb": None, "unlimited": True, "duration_days": 3, "per_gb": None,
      "hotspot_ok": True}),

    ("MB plan converts to GB and keeps duration -- StaffTraveler 100 MB / 365 d",
     lambda: {k: _g()[13][k] for k in ("provider", "data_gb", "duration_days",
                                       "price", "per_gb")},
     {"provider": "StaffTraveler", "data_gb": 0.098, "duration_days": 365,
      "price": 0.99, "per_gb": 9.9}),

    ("file with no rate table yields [] without raising (degenerate input)",
     lambda: target.parse_global(_no_table_md()), []),

    # --- collect(): wiring --------------------------------------------------
    ("collect() adds exactly one README-derived entry: the Global one",
     lambda: [e for e in target.collect() if e["md_path"].lower().endswith("readme.md")],
     [{"region": "Global", "country": "Global", "slug": "README",
       "md_path": "Global/README.md",
       "rows": [{**r, "global_coverage": True} for r in target.parse_country(P)["rows"]]}]),

    ("collect() now has 80 entries (79 country pages + Global)",
     lambda: len(target.collect()), 80),

    # --- regressions --------------------------------------------------------
    ("parse_country rows are untouched -- no global_coverage key leaks into them",
     lambda: all("global_coverage" not in r for r in target.parse_country(P)["rows"]), True),

    ("non-Global entries keep their exact row shape (no global_coverage anywhere)",
     lambda: all("global_coverage" not in r
                 for e in target.collect() if e["region"] != "Global"
                 for r in e["rows"]), True),

    ("Asia country pages still parse with rows (e.g. Cambodia has 14)",
     lambda: [len(e["rows"]) for e in target.collect()
              if e["region"] == "Asia" and e["country"] == "Cambodia"], [14]),
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
