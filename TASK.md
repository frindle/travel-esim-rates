# TASK: esim-global-v2

## Confirmed defect (observed, not suspected)

Global-coverage eSIM plans never appear on the built site. Reproduced at baseline: `python3 build.py` builds only per-country pages; `collect()` skips every `README.md`, and the global plans live in `Global/README.md`, so no entry with `"region": "Global"` reaches `rates.json`; `docs/index.html` has no "Worldwide / Global" section, and no per-country table contains a global row (e.g. Maya Mobile's $9.99 unlimited / 3 d plan).

## Entry point

build.py:182 — `collect()` (the loop that skips `md.name.lower() == "readme.md"`); rendering in `render_index` (line 367) and `render_country_page` (line 286).

## Required change

Global-coverage eSIM plans (worldwide/multi-region) never appear on the built site: collect() in build.py iterates REGIONS (which includes 'Global') but skips every README.md (md.name.lower()=='readme.md'), and the global plans live in Global/README.md, so nothing parses them. FIX build.py so global plans surface everywhere: (1) parse Global/README.md's first rate table into global plan rows using the SAME row-parsing logic as parse_country (provider/plan/price/data_gb/etc.); (2) stop treating 'Global' as a country in the destination picker (it must NOT appear as a country checkbox/region grid); (3) flag every global row as global-coverage and render it BOTH as a dedicated 'Worldwide / Global' section on index.html AND merged into every selected country's ranked results and into each per-country page's table, each row visibly badged 'Global' so users know it is not country-specific; global rows must obey the same rank/filter controls (rankBy, minGB, topN, hotspot, unlimited). build.py must still build all existing country pages without error.

Behaviour that must NOT change:
- Every existing per-country page still builds without error and keeps exactly its own rows' values (country row dicts gain no new keys; parsing of non-README .md files is untouched).
- Regional index READMEs (Asia/README.md, Europe/README.md, ...) are still skipped — only Global/README.md is parsed.
- The destination picker still lists every real country grouped by region, and select-all/clear keep working.
- Existing rank/filter controls (rankBy, minGB, topN, hotspot-only, include-unlimited) keep their semantics for country rows; global rows are subject to the same controls when merged in.

## Must contain

- `def parse_global(md_path):`
- `row["global_coverage"] = True`
- `"Worldwide / Global"`
- `<span class="chip">Global</span>`
- `GLOBAL_ROWS`
- `def render_country_page(entry, global_rows=()):`

## Scope

Only edit `build.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and asks the verify to catch it. A changed line whose every mutant survives -- because no test asserts it -- FAILS the gate even when the fix is correct, and the review never runs. So do NOT emit an isolated, untested line:
- Fold an unavoidable constant onto a line the test already exercises. Put a `timeout=` / a `daemon=True` flag / a small tuning number on the SAME line as a header dict, URL, or argument the fixture checks -- never on its own line.
- Prefer falling through to an implicit `return None` over a standalone `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it is about not leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints `VERIFY_OK`.
