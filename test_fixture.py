"""Adversarial fixture for: esim-global-s2-picker-exclude-global

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
import re
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


def _data():
    return target.collect()


def _real(data):
    """Entries that are real destinations (not the Global plan category)."""
    return [e for e in data if e["region"] != "Global"]


def _html(data=None):
    if data is None:
        data = _data()
    return target.render_index(data)


def _picker_values(html):
    """The exact set of destination ids the picker renders as checkboxes --
    select-all/clear toggle precisely this set."""
    return set(re.findall(r'class="cpick" value="([^"]+)"', html))


CASES = [
    # --- regression half: the Global table is DATA, not a destination -------
    ("Global worldwide table still parsed into data (fix must not delete it)",
     lambda: any(e["region"] == "Global" and e["country"] == "Global"
                 and len(e["rows"]) > 0 for e in _data()),
     True),

    # --- the defect itself ---------------------------------------------------
    ("picker renders no Global country checkbox",
     lambda: re.search(r'class="cpick" value="Global::', _html()) is None,
     True),

    ("picker renders no Global region group header",
     lambda: '<div class="regionhdr">Global</div>' not in _html(),
     True),

    # --- select-all/clear scope: exactly the real countries, none missing ----
    ("checkbox set is EXACTLY the real countries (no extras, none dropped)",
     lambda: _picker_values(_html()) == {f"{e['region']}::{e['slug']}" for e in _real(_data())},
     True),

    # --- header counts must not be inflated by Global ------------------------
    ("'N countries · M regions' counts only real countries and regions",
     lambda: "{} countries \u00b7 {} regions".format(
         len(_real(_data())),
         len({e["region"] for e in _real(_data())})) in _html(),
     True),

    # --- boundary: a dataset whose only entry is Global ----------------------
    ("dataset containing ONLY the Global entry renders an empty picker",
     lambda: (lambda g, h: "0 countries \u00b7 0 regions" in h
              and 'class="cpick"' not in h)([e for e in _data() if e["region"] == "Global"],
                                            target.render_index([e for e in _data() if e["region"] == "Global"])),
     True),

    # --- degenerate input must not raise -------------------------------------
    ("empty dataset renders without crashing and reports 0/0",
     lambda: "0 countries \u00b7 0 regions" in target.render_index([]),
     True),

    # --- regression half: real countries keep their real region group --------
    ("real country stays grouped under its real region (Asia/Japan)",
     lambda: ('<div class="regionhdr">Asia</div>' in _html())
             and ('value="Asia::Japan"' in _html()),
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
