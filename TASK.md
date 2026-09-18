# TASK: esim-global-s1-parse-global

## Confirmed defect (observed, not suspected)

`Global/README.md` holds a 18-row rate table of global/multi-region eSIM plans, but
nothing in the built site or `docs/rates.json` ever includes it. Reproduced: running
`python3 -c "import build; d=build.collect(); print(len(d), sorted({e['region'] for e in d}))"`
yields 79 entries and regions `[Africa, Americas, Asia, Europe, Middle-East, Oceania]` —
no `Global`. Cause observed in code: `collect()` (build.py:182) unconditionally skips
every README.md at build.py:189 (`if md.name.lower() == "readme.md": continue`), so the
only file that carries global plans is dropped.

## Entry point

build.py:182 — `def collect():`, specifically the README skip at build.py:189; the new
parser belongs next to `parse_country` (build.py:109).

## Required change

Add a module-level `def parse_global(md_path):` that parses the FIRST markdown rate table
in Global/README.md into row dicts using the SAME row-parsing logic parse_country uses
(provider/plan/price/data_gb/duration/hotspot/unlimited/per_gb), and sets
`row["global_coverage"] = True` on every row it returns. `parse_global(md_path)` must
return the list of row dicts (empty list when the file has no rate table).

collect() must call it for Global/README.md ONLY, and append exactly one entry shaped like
the country entries:

    {"region": "Global", "country": "Global", "slug": "README",
     "md_path": "Global/README.md", "rows": <parse_global rows>}

— appended only when parse_global returns a non-empty list. Every other README.md
(Asia/README.md, Europe/README.md, ...) stays skipped exactly as today, and parsing of
non-README .md files is untouched. This slice adds the parser and its wiring into
collect(); rendering comes in later slices (main() may render the new entry; do not add
new rendering logic).

Behaviour that must NOT change:
- `parse_country` output is byte-for-byte unchanged: same rows, same keys, and NO
  `global_coverage` key on any row it returns.
- All 79 existing non-README entries in collect() keep their exact shape; none of their
  rows gains a `global_coverage` key (e.g. Asia/Cambodia still parses to 14 rows).
- Non-Global README.md files are still skipped entirely — after the change, exactly ONE
  entry in collect() has an md_path ending in readme.md: the Global one.
- A markdown file with no rate table passed to parse_global yields `[]` and does not raise.

## Must contain

- `def parse_global(md_path):`
- `"global_coverage"`
- `"Global"`

## Scope

Only edit `build.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and
asks the verify to catch it. A changed line whose every mutant survives --
because no test asserts it -- FAILS the gate even when the fix is correct, and
the review never runs. So do NOT emit an isolated, untested line:
- Fold an unavoidable constant onto a line the test already exercises. Put a
  `timeout=` / a `daemon=True` flag / a small tuning number on the SAME line as
  a header dict, URL, or argument the fixture checks -- never on its own line.
- Prefer falling through to an implicit `return None` over a standalone
  `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
