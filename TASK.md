# TASK: esim-global-s4-badge-and-merge

## Confirmed defect (observed, not suspected)

On the built site (`docs/`), selecting a country on `index.html` shows ONLY that
country's own plans — the Global rows parsed from `Global/README.md` appear in
no per-country ranked list. Likewise each per-country page
(`docs/<Region>/<C>.html`) renders only its own table; the global plans are
reachable only via the separate "Worldwide / Global" section on index.html.
Reproduced by building (`python3 build.py`) and inspecting `docs/Asia/Cambodia.html`
and `docs/index.html`: neither contains any of the 18 parsed Global rows in a
country's ranked results, so users cannot compare global plans against a
destination's own plans or tell them apart.

## Entry point

build.py:302 (`def render_country_page(entry):`) and build.py:600 (the `main()`
call site that renders each country page), plus the per-country ranked-list loop
inside `render_index`'s inline JS.

## Required change

Merge global rows into EVERY selected country's ranked results on index.html and
into each per-country page's table, with each global row visibly badged
`<span class="chip">Global</span>` so users can tell it is not country-specific.
Change render_country_page's signature to `def render_country_page(entry, global_rows=()):`
and pass the global rows in (from `main()`, using `_global_entry(data)`). Merged
global rows obey the same rank/filter controls as the country's own rows;
country rows are never badged and their values are unchanged.

Concretely:
- `render_country_page(entry, global_rows=())`: merge `global_rows` into the page's
  ROWS payload (e.g. flag each merged row with an `is_global` key) so the existing
  sort/filter JS applies to them; render a `<span class="chip">Global</span>` badge
  in the provider cell of every flagged row only.
- index.html: for each selected country, merge the Global entry's rows (flagged
  `is_global`) into that country's ranked list before ranking/slicing, and badge
  flagged rows with `<span class="chip">Global</span>`; unflagged country rows are
  rendered exactly as before.
- `main()`: resolve the global entry once (`_global_entry(data)`) and pass its rows
  to every non-global country page's `render_country_page` call (the Global page
  itself gets none, so it is not double-flagged).

Behaviour that must NOT change:
- Country rows keep their exact values; they are never flagged or badged.
- The existing rank/filter controls (rankBy, minGB, topN, hotspot-only,
  include-unlimited on index.html; fHot/fCap on country pages) apply to merged
  global rows exactly as they do to the country's own rows.
- `render_country_page(entry)` with no second argument still works and renders
  only the entry's own rows (default `global_rows=()`).
- The Global page (`docs/Global/global.html`) is unchanged in content: it shows
  its own table, unflagged.
- Everything else already built by earlier slices (parsing, rates.json, style.css,
  the Worldwide/Global section) keeps working.

## Must contain

- `def render_country_page(entry, global_rows=()):`
- `<span class="chip">Global</span>`
- `is_global`
- `_global_entry(data)`

## Scope

Only edit `build.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and
asks the verify to catch it. A changed line whose every mutant survives --
because no test asserts it -- FAILS the gate even when the fix is correct, and
the review never runs. So do NOT emit an isolated, untested line:
- Fold an unavoidable constant onto a line the test already exercises. Put a
  `timeout=` / a `daemon=True` flag / a small tuning number on the SAME line as a
  header dict, URL, or argument the fixture checks -- never on its own line.
- Prefer falling through to an implicit `return None` over a standalone
  `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it's about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
