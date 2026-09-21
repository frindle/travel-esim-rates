"""Adversarial fixture for: esim-global-s3-global-section

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

spec = importlib.util.spec_from_file_location("target", 'build.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with the
# task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)


def _row(provider="P", plan="5 GB / 30 d", data_gb=5.0, unlimited=False,
         price=25.0, per_gb=5.0, hotspot_ok=True, rating=4.0):
    return {
        "provider": provider, "plan": plan, "data_gb": data_gb,
        "unlimited": unlimited, "duration_days": 30, "price": price,
        "per_gb": per_gb, "hotspot": "✅" if hotspot_ok else "❌",
        "hotspot_ok": hotspot_ok, "rating": rating, "confidence": "✅",
        "source": {"text": "x", "url": None}, "seen": "2026-01-01",
    }


ROWS = [
    _row("A", per_gb=9.0, price=45.0, rating=3.0),          # worst value
    _row("B", data_gb=10.0, per_gb=2.0, price=20.0, rating=4.5),  # best value
    _row("C", unlimited=True, data_gb=None, per_gb=None, price=9.99, rating=4.6),
    _row("D", hotspot_ok=False, per_gb=1.0, price=10.0, rating=2.0),  # no hotspot
    _row("E", per_gb=None, price=None, rating=None),          # null rank keys
]


def _names(rows):
    return [r["provider"] for r in rows]


CASES = [
    ("pergb ranking: best $/GB first, nulls last, topN=3 truncates",
     lambda: _names(target._rank_rows(ROWS, rank_by="pergb", top_n=3)),
     ["B", "D", "A"]),

    ("hotspot_only drops non-hotspot rows before ranking",
     lambda: _names(target._rank_rows(ROWS, hotspot_only=True, top_n=None)),
     ["B", "C", "A"]),

    ("include_unlimited=False hides unlimited; True keeps them ranked by price",
     lambda: (_names(target._rank_rows(ROWS, rank_by="price", include_unlimited=False, top_n=None)),
              _names(target._rank_rows(ROWS, rank_by="price", include_unlimited=True, top_n=None))),
     (["D", "A", "B"], ["C", "D", "A"])),

    ("min_gb boundary: data_gb == min kept, below dropped, unlimited always passes",
     lambda: _names(target._rank_rows(ROWS, min_gb=5.0, top_n=None)),
     ["B", "C"]),

    ("rating ranking is highest-first with unrated rows last (nulls never first)",
     lambda: _names(target._rank_rows(ROWS, rank_by="rating", top_n=None)),
     ["C", "B", "A", "D", "E"]),

    ("top_n floors at 1 even when asked for 0; missing keys do not raise",
     lambda: (_names(target._rank_rows([_row("X")], top_n=0)),
              _names(target._rank_rows([{"provider": "Z"}])),
              target.global_rows([])),
     (["X"], ["Z"], [])),

    ("global_rows returns the Global region's rows in source order",
     lambda: [r["provider"] for r in target.global_rows(
         [{"region": "Asia", "country": "Japan", "slug": "japan", "rows": [_row("J")]},
          {"region": "Global", "country": "Global", "slug": "global",
           "rows": [_row("G1"), _row("G2")]}])],
     ["G1", "G2"]),

    ("render_index exposes GLOBAL_ROWS and the Worldwide / Global section wired to globalTb",
     lambda: (lambda h: (
         "const GLOBAL_ROWS=" in h,
         'Worldwide / Global' in h,
         'id="globalTb"' in h,
         '"provider": "G1"' in h and '"provider": "J"' not in h.split('const GLOBAL_ROWS=')[1].split(";")[0],
     ))(target.render_index([{"region": "Global", "country": "Global", "slug": "global",
                              "rows": [_row("G1")]}])),
     (True, True, True, True)),

    ("render_index still emits the country DATA payload and results container",
     lambda: (lambda h: (
         "const DATA=" in h,
         '<div id="results"></div>' in h,
         '"country": "Japan"' in h,
     ))(target.render_index([{"region": "Asia", "country": "Japan", "slug": "japan",
                              "rows": [_row("J")]}])),
     (True, True, True)),
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
