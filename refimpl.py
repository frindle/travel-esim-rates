#!/usr/bin/env python3
"""Reference impl for: esim-global-s3-global-section

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Strategy: restore build.py to its baseline bytes (git HEAD), then apply four
exact string replacements. Every anchor must occur exactly once in the
baseline file or this script fails loudly.
"""
import pathlib
import subprocess
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
p = wt / "build.py"


def baseline_text():
    try:
        out = subprocess.run(["git", "-C", str(wt), "show", "HEAD:build.py"],
                             capture_output=True, text=True, check=True)
        return out.stdout
    except Exception:
        return p.read_text(encoding="utf-8")


def replace_once(text, old, new, label):
    n = text.count(old)
    assert n == 1, f"anchor for {label} found {n} times (want exactly 1)"
    return text.replace(old, new, 1)


t = baseline_text()

# --- 1. shared pure rank/filter helper, right after parse_global -------------
A1_OLD = '''def collect():'''
A1_NEW = '''def _rank_rows(rows, rank_by="pergb", min_gb=None, top_n=3,
              hotspot_only=False, include_unlimited=False):
    """Rank + filter rows with the SAME controls as the index page's country
    results: hotspot-only, include-unlimited, min data GB (unlimited always
    passes), rank by pergb/price/rating (nulls last), then top-N."""
    out = [r for r in rows if not (hotspot_only and not r.get("hotspot_ok"))]
    if not include_unlimited:
        out = [r for r in out if not r.get("unlimited")]
    if min_gb is not None:
        out = [r for r in out if r.get("unlimited") or (r.get("data_gb") is not None and r["data_gb"] >= min_gb)]

    def key(r):
        if rank_by == "price":
            return r.get("price")
        if rank_by == "rating":
            v = r.get("rating")
            return -v if v is not None else None
        return r.get("per_gb")

    def skey(r):
        v = key(r)
        return (v is None, -v if isinstance(v, (int, float)) else 0, v)

    out.sort(key=skey)
    if top_n is not None:
        out = out[:max(1, int(top_n))]
    return out


def collect():'''
t = replace_once(t, A1_OLD, A1_NEW, "helper")

# --- 2. render_index: compute GLOBAL_ROWS + reuse the helper for countries ----
A2_OLD = '''def render_index(data):
    # group for picker
    by_region = {}'''
A2_NEW = '''def global_rows(data):
    """The parsed Global (worldwide) rows, in source order."""
    out = []
    for e in data:
        if e.get("region") == "Global":
            out.extend(e["rows"])
    return out


def render_index(data):
    # group for picker
    by_region = {}'''
t = replace_once(t, A2_OLD, A2_NEW, "global_rows fn")

A3_OLD = '''    n_countries = len(data)
    n_regions = len(by_region)'''
A3_NEW = '''    n_countries = len(data)
    n_regions = len(by_region)
    global_json = json.dumps(global_rows(data))'''
t = replace_once(t, A3_OLD, A3_NEW, "global_json")

# --- 3. dedicated 'Worldwide / Global' section on index.html ------------------
A4_OLD = '''<div id="results"></div>'''
A4_NEW = '''<h2 class="regionhdr">Worldwide / Global</h2>
<div id="globalResults" class="panel tablewrap"><table><thead><tr>
<th>Provider</th><th>Plan</th><th class="num">Data</th><th class="num">Days</th>
<th class="num">Price</th><th class="num">$/GB</th><th>Hotspot</th><th class="num">Rating</th><th>Conf.</th></tr></thead>
<tbody id="globalTb"></tbody></table></div>

<div id="results"></div>'''
t = replace_once(t, A4_OLD, A4_NEW, "section html")

# --- 4. JS: GLOBAL_ROWS constant + shared controls drive both sections --------
A5_OLD = '''<script>const DATA={all_json};{SORT_JS}'''
A5_NEW = '''<script>const DATA={all_json};const GLOBAL_ROWS={global_json};{SORT_JS}'''
t = replace_once(t, A5_OLD, A5_NEW, "GLOBAL_ROWS const")

A6_OLD = '''    let rows=e.rows.filter(planMatches).filter(r=>rankKey(r,by)!=null);
    rows.sort((a,b)=>rankKey(a,by)-rankKey(b,by));
    rows=rows.slice(0,topN);'''
A6_NEW = '''    let rows=_rank_rows(e.rows,by,mg,topN,$('fHot').checked,$('fUnlim').checked).filter(r=>rankKey(r,by)!=null);'''
t = replace_once(t, A6_OLD, A6_NEW, "country rank call")

A7_OLD = '''document.querySelectorAll('.cpick').forEach(c=>c.addEventListener('change',render));'''
A7_NEW = '''function renderGlobal(){{
  const by=$('rankBy').value;
  const mg=parseFloat($('minGB').value);
  const topN=Math.max(1,parseInt($('topN').value)||3);
  let rows=_rank_rows(GLOBAL_ROWS,by,isNaN(mg)?null:mg,topN,$('fHot').checked,$('fUnlim').checked).filter(r=>rankKey(r,by)!=null);
  const tb=document.getElementById('globalTb');
  if(!rows.length){{tb.innerHTML='<tr><td colspan="9" class="empty">No worldwide plans match your filters.</td></tr>';return;}}
  tb.innerHTML=rows.map((r,i)=>'<tr'+(i===0?' class="cheapest"':'')+'>'+
    '<td>'+esc(r.provider)+'</td><td>'+esc(r.plan)+'</td>'+
    '<td class="num">'+fmtGB(r)+'</td><td class="num">'+fmtDur(r)+'</td>'+
    '<td class="num">'+fmtUSD(r.price)+'</td><td class="num">'+fmtGBp(r.per_gb)+'</td>'+
    '<td>'+esc(r.hotspot)+'</td><td class="num">'+fmtRating(r.rating)+'</td><td>'+esc(r.confidence)+'</td></tr>').join('');
}}
function render(){{renderGlobal();'''
t = replace_once(t, A7_OLD, A7_NEW, "renderGlobal")

p.write_text(t, encoding="utf-8")
print("refimpl applied")
