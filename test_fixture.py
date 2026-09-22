"""Adversarial fixture for: esim-global-s4-badge-and-merge

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
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)

BADGE = '<span class="chip">Global</span>'


def _data():
    data = target.collect()
    ge = next(e for e in data if e["region"] == "Global")
    ce = next(e for e in data if e["country"] == "Cambodia")
    return data, ge, ce


def case1():
    """Per-country page: EVERY global row is merged into ROWS and flagged."""
    _, ge, ce = _data()
    html = target.render_country_page(ce, ge["rows"])
    return html.count('"is_global": true') == len(ge["rows"])


def case2():
    """Per-country page: global rows are badged; country rows are NOT flagged.

    Exact count -- a fix that flags the country's own rows too fails this."""
    _, ge, ce = _data()
    html = target.render_country_page(ce, ge["rows"])
    return (BADGE in html
            and html.count('"is_global": true') == len(ge["rows"]))


def case3():
    """Default call: render_country_page(entry) still works with no global rows
    and flags nothing (default arg + regression half)."""
    _, _, ce = _data()
    return target.render_country_page(ce).count('"is_global": true') == 0


def case4():
    """index.html: global rows are merged into EVERY selected country's ranked
    list and badged there too. A badge-only fix (no merge) fails the concat;
    a merge-without-badge fix fails the badge check."""
    data, _, _ = _data()
    idx = target.render_index(data)
    return ('e.rows.concat(gRows)' in idx and BADGE in idx)


def case5():
    """main() wiring: the built per-country page actually carries the global
    rows, while the Global page itself is not double-flagged. A fix that only
    changes render_country_page's signature but never passes the rows in fails."""
    data, ge, _ = _data()
    target.main()
    cambodia = open("docs/Asia/Cambodia.html").read()
    globalpage = open("docs/Global/global.html").read()
    return (cambodia.count('"is_global": true') == len(ge["rows"])
            and globalpage.count('"is_global": true') == 0)


CASES = [
    ("per-country page merges every global row with an is_global flag", case1, True),
    ("per-country page badges global rows and leaves country rows unflagged", case2, True),
    ("render_country_page(entry) default call renders with zero flagged rows", case3, True),
    ("index.html merges flagged global rows into each selected country's list", case4, True),
    ("main() passes global rows into country pages (and none into the Global page)", case5, True),
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
