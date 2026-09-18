#!/usr/bin/env python3
"""Reference impl for: esim-global-v2

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Applies a set of exact anchored replacements to build.py so that:
  * Global/README.md's first rate table is parsed with parse_country's row logic,
    every row flagged global-coverage (parse_global);
  * collect() includes the Global entry but still skips other regions' READMEs;
  * render_index drops Global from the destination picker, adds a dedicated
    'Worldwide / Global' section and merges GLOBAL_ROWS into each selected
    country's ranked results (badged 'Global');
  * render_country_page merges global rows into its table (badged 'Global').
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / "build.py"
t = p.read_text()

EDITS = [
    # 1) parse_global: same row logic as parse_country, rows flagged global.
    ("""    return {"title": title, "rows": rows}


def collect():""",
     """    return {"title": title, "rows": rows}


def parse_global(md_path):
    # Parse Global/README.md's first rate table with the SAME row logic as
    # parse_country; every row is flagged global-coverage.
    parsed = parse_country(md_path)
    for row in parsed["rows"]:
        row["global_coverage"] = True
    return {"title": "Worldwide / Global", "rows": parsed["rows"]}


def collect():"""),

    # 2) collect(): parse Global/README.md, keep skipping other READMEs.
    ("""            if md.name.lower() == "readme.md":
                continue
            parsed = parse_country(md)
            if not parsed["rows"]:
                continue
            data.append({
                "region": region,
                "country": parsed["title"],
                "slug": md.stem,
                "md_path": f"{region}/{md.name}",
                "rows": parsed["rows"],
            })""",
     """            is_readme = md.name.lower() == "readme.md"
            if is_readme and region != "Global":
                continue  # regional index pages are not destinations
            parsed = parse_global(md) if is_readme else parse_country(md)
            if not parsed["rows"]:
                continue
            data.append({
                "region": region,
                "country": parsed["title"],
                "slug": md.stem,
                "md_path": f"{region}/{md.name}",
                "rows": parsed["rows"],
                "global": is_readme,
            })"""),

    # 3) render_country_page accepts the global rows to merge in.
    ("def render_country_page(entry):",
     "def render_country_page(entry, global_rows=()):"),

    # 4) country page ROWS = own rows + global rows.
    ('    rows_json = json.dumps(entry["rows"])',
     '    rows_json = json.dumps(list(entry["rows"]) + list(global_rows))'),

    # 5) badge global rows in the per-country table.
    ("""      '<td>'+esc(r.provider)+'</td>'+
      '<td>'+esc(r.plan)+'</td>+""",
     """      '<td>'+esc(r.provider)+(r.global_coverage?' <span class="chip">Global</span>':'')+'</td>'+
      '<td>'+esc(r.plan)+'</td>+"""),

    # 6) render_index: split countries vs global; picker sees countries only.
    ("""def render_index(data):
    # group for picker
    by_region = {}
    for e in data:
        by_region.setdefault(e["region"], []).append(e)
    all_json = json.dumps([
        {"region": e["region"], "country": e["country"], "slug": e["slug"],
         "href": f"{e['region']}/{e['slug']}.html", "rows": e["rows"]}
        for e in data
    ])""",
     """def render_index(data):
    countries = [e for e in data if not e.get("global")]
    global_rows = [r for g in data if g.get("global") for r in g["rows"]]
    # group for picker (Global is a coverage, not a destination)
    by_region = {}
    for e in countries:
        by_region.setdefault(e["region"], []).append(e)
    all_json = json.dumps([
        {"region": e["region"], "country": e["country"], "slug": e["slug"],
         "href": f"{e['region']}/{e['slug']}.html", "rows": e["rows"]}
        for e in countries
    ])"""),

    # 7) dedicated 'Worldwide / Global' section + GLOBAL_ROWS payload.
    ("""    n_countries = len(data)
    n_regions = len(by_region)""",
     """    n_countries = len(countries)
    n_regions = len(by_region)

    def _fmt(v, money=False):
        if v is None:
            return "—"
        return ("$" + format(v, ".2f")) if money else str(v)

    gtrs = []
    for r in global_rows:
        data_txt = "Unlimited" if r["unlimited"] else (str(r["data_gb"]) + " GB" if r["data_gb"] is not None else "—")
        dur = str(r["duration_days"]) + " d" if r["duration_days"] is not None else "—"
        rating = format(r["rating"], ".1f") if r["rating"] is not None else "—"
        gtrs.append(
            "<tr><td>" + html.escape(r["provider"]) + ' <span class="chip">Global</span></td>'
            "<td>" + html.escape(r["plan"]) + "</td>"
            '<td class="num">' + data_txt + '</td><td class="num">' + dur + "</td>"
            '<td class="num">' + _fmt(r["price"], money=True) + '</td><td class="num">' + _fmt(r["per_gb"], money=True) + "</td>"
            "<td>" + html.escape(r["hotspot"]) + "</td>"
            '<td class="num">' + rating + "</td><td>" + html.escape(r["confidence"]) + "</td></tr>")
    gtable = ""
    if global_rows:
        gtable = ('<div class="result-country">Worldwide / Global <span class="muted">(global coverage — not country-specific)</span></div>'
                  '<div class="panel tablewrap"><table><thead><tr>'
                  "<th>Provider</th><th>Plan</th><th class=\\"num\\">Data</th><th class=\\"num\\">Days</th>"
                  '<th class="num">Price</th><th class="num">$/GB</th><th>Hotspot</th><th class="num">Rating</th><th>Conf.</th>'
                  "</tr></thead><tbody>" + "".join(gtrs) + "</tbody></table></div>")
    global_rows_json = json.dumps(global_rows)"""),

    # 8) inject the section above the results box.
    ('<div id="results"></div>',
     '{gtable}\n<div id="results"></div>'),

    # 9) merge global rows into each selected country's ranked pool.
    ("    let rows=e.rows.filter(planMatches).filter(r=>rankKey(r,by)!=null);",
     "    let rows=e.rows.concat(GLOBAL_ROWS).filter(planMatches).filter(r=>rankKey(r,by)!=null);"),

    # 10) badge global rows in the index per-country tables.
    ("""        '<td>'+esc(r.provider)+'</td><td>'+esc(r.plan)+'</td>'+""",
     """        '<td>'+esc(r.provider)+(r.global_coverage?' <span class="chip">Global</span>':'')+'</td><td>'+esc(r.plan)+'</td>'+"""),

    # 11) expose GLOBAL_ROWS to the index JS.
    ('<script>const DATA={all_json};{SORT_JS}',
     '<script>const DATA={all_json};const GLOBAL_ROWS={global_rows_json};{SORT_JS}'),

    # 12) main(): pass global rows into country pages; no Global destination page.
    ("""    total_rows = 0
    for e in data:
        outdir = DOCS / e["region"]
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / f"{e['slug']}.html").write_text(render_country_page(e), encoding="utf-8")
        total_rows += len(e["rows"])""",
     """    global_rows = [r for g in data if g.get("global") for r in g["rows"]]
    total_rows = 0
    for e in data:
        if e.get("global"):
            continue  # Global is a coverage, not a destination page
        outdir = DOCS / e["region"]
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / f"{e['slug']}.html").write_text(render_country_page(e, global_rows), encoding="utf-8")
        total_rows += len(e["rows"])"""),
]

for old, new in EDITS:
    n = t.count(old)
    if n != 1:
        raise SystemExit("refimpl anchor not found/ambiguous ({}x): {!r}".format(n, old[:70]))
    t = t.replace(old, new, 1)

p.write_text(t)
print("refimpl applied")
