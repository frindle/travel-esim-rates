#!/usr/bin/env python3
"""Reference impl for: esim-global-s4-badge-and-merge

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'build.py'
t = p.read_text()


def sub(old, new):
    global t
    assert old in t, "refimpl anchor not found -- did the target change?\n" + old[:200]
    assert t.count(old) == 1, "refimpl anchor is ambiguous: " + old[:80]
    t = t.replace(old, new, 1)


# 1) New signature with default.
sub(
    r"""def render_country_page(entry):""",
    r"""def render_country_page(entry, global_rows=()):""",
)

# 2) Per-country page: merge the global rows into ROWS (flagged is_global).
sub(
    r"""    title = entry["country"]
    region = entry["region"]
    rows_json = json.dumps(entry["rows"])""",
    r"""    title = entry["country"]
    region = entry["region"]
    merged = list(entry["rows"]) + [dict(r, is_global=True) for r in global_rows]
    rows_json = json.dumps(merged)""",
)

# 3) Per-country page: badge each merged global row in the provider cell.
sub(
    r"""      '<td>'+esc(r.provider)+'</td>'+
      '<td>'+esc(r.plan)+'</td>'+""",
    r"""      '<td>'+esc(r.provider)+(r.is_global?' <span class="chip">Global</span>':'')+'</td>'+
      '<td>'+esc(r.plan)+'</td>'+""",
)

# 4) index.html: merge the global rows into EVERY selected country's ranked list.
sub(
    r"""    let rows=e.rows.filter(planMatches).filter(r=>rankKey(r,by)!=null);
    rows.sort((a,b)=>rankKey(a,by)-rankKey(b,by));""",
    r"""    const ge=DATA.find(d=>d.region==='Global');
    const gRows=(ge?ge.rows:[]).map(r=>Object.assign({{}},r,{{is_global:true}})).filter(planMatches);
    let rows=e.rows.concat(gRows).filter(r=>rankKey(r,by)!=null);
    rows.sort((a,b)=>rankKey(a,by)-rankKey(b,by));""",
)

# 5) index.html: badge each merged global row in the provider cell.
sub(
    r"""      out+='<tr'+(i===0?' class="cheapest"':'')+'>'+
        '<td>'+esc(r.provider)+'</td><td>'+esc(r.plan)+'</td>'""",
    r"""      out+='<tr'+(i===0?' class="cheapest"':'')+'>'+
        '<td>'+esc(r.provider)+(r.is_global?' <span class="chip">Global</span>':'')+'</td><td>'+esc(r.plan)+'</td>'""",
)

# 6) main(): pass the global rows into every non-global country page.
sub(
    r"""def main():
    data = collect()""",
    r"""def main():
    data = collect()
    ge = _global_entry(data)
    g_rows = list(ge["rows"]) if ge else []""",
)

sub(
    r"""        (outdir / f"{e['slug']}.html").write_text(render_country_page(e), encoding="utf-8")""",
    r"""        (outdir / f"{e['slug']}.html").write_text(render_country_page(e, g_rows if e["region"] != "Global" else ()), encoding="utf-8")""",
)

p.write_text(t)
print("refimpl applied")
