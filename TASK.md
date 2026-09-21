# TASK: esim-global-s3-global-section

## Confirmed defect (observed, not suspected)

The index page (`docs/index.html`) only shows rows for countries the user ticks in
the destination picker. The parsed worldwide plans from `Global/README.md` are
collected by `collect()` but never surfaced on the index: there is no dedicated
section listing them and no JS variable exposing them. Verified by building with
`python3 build.py` and grepping `docs/index.html`: it contains neither a
"Worldwide / Global" section nor any global-rows data (the only place the rows
appear is `rates.json`).

## Entry point

build.py: `render_index(data)` — builds the index page; its `<script>` block
defines `DATA`, `planMatches`, `rankKey` and `render()`. The shared rank/filter
logic currently lives inline in the per-country loop inside `render()`'s JS.

## Required change

Expose the parsed global rows to the index page's JS as `GLOBAL_ROWS`, and render
a dedicated 'Worldwide / Global' section on index.html listing them. The
section's rows must obey the SAME rank/filter controls as country rows (rankBy,
minGB, topN, hotspot-only, include-unlimited).

Contract:

- Add a pure Python helper `_rank_rows(rows, rank_by="pergb", min_gb=None,
  top_n=3, hotspot_only=False, include_unlimited=False)` in build.py that applies,
  in order: (1) drop rows where `hotspot_ok` is falsy when `hotspot_only`;
  (2) drop unlimited rows unless `include_unlimited`; (3) if `min_gb` is not
  None, keep only unlimited rows or rows with `data_gb >= min_gb`; (4) sort by the
  rank key — `pergb` -> `per_gb`, `price` -> `price`, `rating` -> highest first —
  with null keys last in every case; (5) truncate to at least 1 and at most
  `top_n` rows. It must not raise on rows missing any of these keys.
- Add a `global_rows(data)` helper returning the parsed Global region's rows, in
  source order (empty list when data has no Global entry).
- In `render_index`, compute `global_json = json.dumps(global_rows(data))` and
  emit `const GLOBAL_ROWS={global_json};` immediately after `const DATA=...;`.
- Render a dedicated section before the `<div id="results"></div>` container: an
  `<h2 class="regionhdr">Worldwide / Global</h2>` heading, then a panel with a
  table whose `<tbody>` has `id="globalTb"`, using the same column set as the
  country result tables (Provider, Plan, Data, Days, Price, $/GB, Hotspot,
  Rating, Conf.).
- The section must be driven by the SAME controls: a JS function `renderGlobal()`
  that calls `_rank_rows(GLOBAL_ROWS, ...)` with the current rankBy / minGB /
  topN / fHot / fUnlim values (minGB empty -> null), filters out rows whose rank
  key is null exactly like country rows do, highlights row 0 as `cheapest`, and
  shows an `.empty` message when nothing matches. `render()` must call
  `renderGlobal()` first so every control change re-renders both sections.
- The per-country loop in `render()` should use the same `_rank_rows` helper for
  its rows (same controls, same null-key filtering) instead of duplicating the
  filter/sort/slice logic inline.

Behaviour that must NOT change:
- Country pages (`docs/<Region>/<C>.html`) are byte-for-byte unchanged in
  structure and behaviour; `render_country_page` is untouched.
- The destination picker, select-all/clear links, localStorage restore, and the
  per-country result tables keep working exactly as before (same columns, same
  cheapest-row highlight, same empty message).
- `collect()` still returns one entry per country plus the Global entry;
  `rates.json` output is unchanged.
- Rows with a null rank key for the selected metric are excluded from both the
  global section and country results (e.g. rating ranking excludes unrated rows).

## Must contain

- `_rank_rows(rows, rank_by="pergb", min_gb=None, top_n=3, hotspot_only=False, include_unlimited=False)`
- `def global_rows(data):`
- `const GLOBAL_ROWS=`
- `Worldwide / Global`
- `id="globalTb"`
- `renderGlobal()`

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
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
