# TASK: esim-global-s2-picker-exclude-global

## Confirmed defect (observed, not suspected)

`docs/index.html`'s destination picker renders a `Global` region group whose only
checkbox is "Global" itself (`value="Global::README"`), sourced from the
`Global/README.md` worldwide-plan table. Reproduced by running `python3 build.py`
and inspecting `docs/index.html`: the picker grid contains
`<div class="regionhdr">Global</div>` plus a Global checkbox, so "select all" /
"clear" also toggle a non-destination, and the header line ("N countries · M
regions") is inflated by one country and one region.

## Entry point

build.py: `render_index(data)` builds the picker grid (region groups + `.cpick`
checkboxes) and the "N countries · M regions" counts from the full `collect()`
output, which includes the Global entry (`region == "Global"`).

## Required change

Stop treating 'Global' as a country/region in the destination picker on index.html: it must NOT appear as a country checkbox nor as a region group in the picker grid. Every real country still appears, grouped by its real region, and select-all / clear still operate over exactly the real countries.

Contract (each clause is asserted by the fixture):
- `collect()` STILL returns the Global entry (`region == "Global"`, `country == "Global"`) with its parsed rows -- the worldwide table stays in `docs/rates.json` and keeps its own page; only the picker excludes it. Do NOT delete the Global branch from `collect()`.
- The rendered index.html contains no checkbox whose value starts with `Global::` and no `<div class="regionhdr">Global</div>` group header.
- Every non-Global entry from `collect()` appears exactly once as a `.cpick` checkbox, under its real region's group header (e.g. Asia/Japan stays in the Asia group). No other entries may appear.
- The "N countries · M regions" header counts only non-Global entries and their distinct regions.
- select-all / clear keep working over exactly the rendered checkboxes: they toggle every `.cpick`, so excluding Global from the grid is sufficient -- do not special-case ids in the JS.

Behaviour that must NOT change: per-country pages, `docs/rates.json` contents, index result sorting/filtering (rank by, min GB, top N, hotspot/unlimited filters), and localStorage selection restore.

## Must contain

- `def picker_entries(data):`
- `e["region"] != "Global"`
- `picker = picker_entries(data)`

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
