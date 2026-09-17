#!/usr/bin/env python3
"""Build the Travel eSIM Rates static site from the region/country Markdown pages.

Source of truth = the `<Region>/<Country>.md` rate tables. This script parses every
country page's first Markdown table, normalizes it into structured rows (with numeric
fields derived for sorting/filtering), and emits a static site into `docs/`:

  docs/index.html          country picker -> best options across selected destinations
  docs/<Region>/<C>.html   per-country page with sortable columns
  docs/rates.json          all parsed data (for external use)
  docs/style.css           shared styles
  docs/.nojekyll           disable Jekyll (serve plain static)

Re-run after editing any .md file:  python3 build.py
Nothing here is provider-specific; new countries/regions are picked up automatically.
"""
import json
import re
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
REGIONS = ["Asia", "Europe", "Americas", "Oceania", "Middle-East", "Africa", "Global"]
GITHUB_REPO = "https://github.com/frindle/travel-esim-rates"

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _num(s):
    """First number in a string as float, else None. Handles $, ~, commas."""
    if s is None:
        return None
    m = re.search(r"[\d]+(?:[,\d]*\.\d+|[,\d]*)", s.replace(",", ""))
    return float(m.group(0)) if m else None


def _price(cell):
    """Price in USD -> float or None. Requires a $ sign to avoid grabbing stray nums."""
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", cell)
    return float(m.group(1).replace(",", "")) if m else None


def _per_gb(cell):
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", cell)
    return float(m.group(1).replace(",", "")) if m else None


def _rating(cell):
    m = re.search(r"(\d+(?:\.\d+)?)", cell)
    return float(m.group(1)) if m else None


def _plan_data_gb(plan):
    """Data allowance in GB. Unlimited -> None (flagged separately). Else first N GB."""
    if re.search(r"unlimited", plan, re.I):
        return None  # unlimited
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB", plan, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)\s*MB", plan, re.I)
    return round(float(m.group(1)) / 1024, 3) if m else None


def _plan_is_unlimited(plan):
    return bool(re.search(r"unlimited", plan, re.I))


def _plan_duration_days(plan):
    """Days from ' / N d' style. Avoids matching 'GB/day' (no digit after slash)."""
    m = re.search(r"/\s*(\d+)\s*d(?:ay)?s?\b", plan, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*d(?:ay)?s?\b", plan)
    return int(m.group(1)) if m else None


def _source(cell):
    """Markdown link -> {text,url}; plain text -> {text, url:None}."""
    m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", cell)
    if m:
        return {"text": m.group(1).strip(), "url": m.group(2).strip()}
    return {"text": cell.strip(), "url": None}


def _hotspot_ok(cell):
    return cell.strip().startswith("✅")  # leading green check


def _split_row(line):
    # strip leading/trailing pipe then split
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _find_col(headers, *names):
    for i, h in enumerate(headers):
        hl = h.lower()
        if any(n in hl for n in names):
            return i
    return None


def parse_country(md_path):
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # title: first "# ..." line
    title = md_path.stem.replace("-", " ")
    for ln in lines:
        if ln.startswith("# "):
            title = re.sub(r"\s*\(.*?\)\s*$", "", ln[2:]).strip()
            break

    # find the header row of the first table (must contain 'provider' + 'price')
    hdr_idx = None
    for i, ln in enumerate(lines):
        if "|" in ln and "provider" in ln.lower() and "price" in ln.lower():
            hdr_idx = i
            break
    if hdr_idx is None:
        return {"title": title, "rows": []}

    headers = _split_row(lines[hdr_idx])
    col = {
        "provider": _find_col(headers, "provider"),
        "plan": _find_col(headers, "plan"),
        "price": _find_col(headers, "price"),
        "pergb": _find_col(headers, "$/gb", "/gb", "per gb"),
        "hotspot": _find_col(headers, "hotspot"),
        "rating": _find_col(headers, "rating"),
        "confidence": _find_col(headers, "confidence"),
        "source": _find_col(headers, "source"),
        "seen": _find_col(headers, "seen"),
    }

    rows = []
    for ln in lines[hdr_idx + 2:]:  # skip header + separator
        if "|" not in ln:
            break  # table ended
        if re.match(r"^\s*\|?\s*:?-{2,}", ln):
            continue  # stray separator
        cells = _split_row(ln)
        if col["provider"] is None or col["provider"] >= len(cells):
            continue

        def g(key):
            idx = col[key]
            return cells[idx] if idx is not None and idx < len(cells) else ""

        plan = g("plan")
        price = _price(g("price"))
        data_gb = _plan_data_gb(plan)
        unlimited = _plan_is_unlimited(plan)
        duration = _plan_duration_days(plan)
        pergb = _per_gb(g("pergb"))
        if pergb is None and price is not None and data_gb:
            pergb = round(price / data_gb, 2)  # derive when omitted
        rows.append({
            "provider": g("provider"),
            "plan": plan,
            "data_gb": data_gb,
            "unlimited": unlimited,
            "duration_days": duration,
            "price": price,
            "per_gb": pergb,
            "hotspot": g("hotspot"),
            "hotspot_ok": _hotspot_ok(g("hotspot")),
            "rating": _rating(g("rating")),
            "confidence": g("confidence"),
            "source": _source(g("source")),
            "seen": g("seen"),
        })
    return {"title": title, "rows": rows}


def collect():
    data = []
    for region in REGIONS:
        rdir = ROOT / region
        if not rdir.is_dir():
            continue
        for md in sorted(rdir.glob("*.md")):
            if md.name.lower() == "readme.md":
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
            })
    return data


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

STYLE = """
:root{--bg:#0f1115;--panel:#171a21;--line:#262b36;--fg:#e6e9ef;--mut:#9aa4b2;
--accent:#4da3ff;--good:#3fb950;--warn:#d29922;--bad:#f85149;--chip:#1f2430;}
@media(prefers-color-scheme:light){:root:not([data-theme=dark]){--bg:#f7f8fa;--panel:#fff;
--line:#e3e6 eb;--line:#e3e6eb;--fg:#1a1f29;--mut:#5b6472;--accent:#0969da;--chip:#eef1f5;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px 80px}
header h1{font-size:22px;margin:0 0 4px}
header .sub{color:var(--mut);margin:0 0 20px;font-size:14px}
.crumb{color:var(--mut);font-size:13px;margin-bottom:14px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:20px}
.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end}
.ctl{display:flex;flex-direction:column;gap:5px}
.ctl label{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
select,input[type=number]{background:var(--bg);color:var(--fg);border:1px solid var(--line);
border-radius:8px;padding:7px 9px;font-size:14px;min-width:120px}
.chk{display:flex;align-items:center;gap:6px;font-size:14px}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:14px;min-width:640px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{position:sticky;top:0;background:var(--panel);cursor:pointer;user-select:none;
font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mut)}
th:hover{color:var(--fg)}
th .arr{opacity:.4;font-size:11px}
th.sorted .arr{opacity:1;color:var(--accent)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:rgba(127,127,127,.06)}
.cheapest td{background:rgba(63,185,80,.10)}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:1px 8px;font-size:12px}
.regionhdr{margin:22px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
.pickgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px 14px}
.muted{color:var(--mut)}
.result-country{font-weight:600;margin:18px 0 6px;font-size:15px}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.pill{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:13px;cursor:pointer}
.pill.on{background:var(--accent);border-color:var(--accent);color:#fff}
footer{margin-top:40px;color:var(--mut);font-size:12px}
.empty{color:var(--mut);padding:12px 0}
"""

SORT_JS = """
function fmtGB(r){ if(r.unlimited) return 'Unlimited'; if(r.data_gb==null) return '—'; return r.data_gb+' GB'; }
function fmtDur(r){ return r.duration_days==null?'—':r.duration_days+' d'; }
function fmtUSD(v){ return v==null?'—':'$'+v.toFixed(2); }
function fmtGBp(v){ return v==null?'—':'$'+v.toFixed(2); }
function fmtRating(v){ return v==null?'—':v.toFixed(1); }
function srcCell(s){ if(!s) return ''; if(s.url) return '<a href="'+s.url+'" target="_blank" rel="noopener">'+esc(s.text)+'</a>'; return esc(s.text); }
function esc(s){ return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
// sort key: unlimited data sorts high; nulls always last
function keyer(col){
  return {
    provider:r=>r.provider.toLowerCase(),
    data:r=>r.unlimited?Number.POSITIVE_INFINITY:(r.data_gb==null?null:r.data_gb),
    duration:r=>r.duration_days,
    price:r=>r.price,
    pergb:r=>r.per_gb,
    hotspot:r=>r.hotspot_ok?0:1,
    rating:r=>r.rating,
    confidence:r=>r.confidence,
    seen:r=>r.seen,
  }[col];
}
function sortRows(rows,col,dir){
  const k=keyer(col);
  return rows.slice().sort((a,b)=>{
    let x=k(a),y=k(b);
    const xn=(x==null||Number.isNaN(x)), yn=(y==null||Number.isNaN(y));
    if(xn&&yn) return 0; if(xn) return 1; if(yn) return -1; // nulls last both dirs
    if(typeof x==='string') return dir*x.localeCompare(y);
    return dir*(x-y);
  });
}
"""


def render_country_page(entry):
    title = entry["country"]
    region = entry["region"]
    rows_json = json.dumps(entry["rows"])
    md_link = f"{GITHUB_REPO}/blob/main/{entry['md_path']}"
    body = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} eSIM rates</title>
<link rel="stylesheet" href="../style.css">
</head><body><div class="wrap">
<div class="crumb"><a href="../index.html">← All destinations</a></div>
<header><h1>{html.escape(title)} <span class="chip">{html.escape(region)}</span></h1>
<p class="sub">Travel eSIM rates · click any column header to sort ·
<a href="{md_link}" target="_blank" rel="noopener">source .md</a></p></header>
<div class="panel"><div class="controls">
<label class="chk"><input type="checkbox" id="fHot"> Hotspot-capable only</label>
<label class="chk"><input type="checkbox" id="fCap"> Capped plans only (hide unlimited)</label>
</div></div>
<div class="tablewrap"><table id="t"><thead><tr>
<th data-c="provider">Provider <span class="arr">↕</span></th>
<th data-c="plan">Plan</th>
<th data-c="data" class="num">Data <span class="arr">↕</span></th>
<th data-c="duration" class="num">Days <span class="arr">↕</span></th>
<th data-c="price" class="num">Price <span class="arr">↕</span></th>
<th data-c="pergb" class="num">$/GB <span class="arr">↕</span></th>
<th data-c="hotspot">Hotspot <span class="arr">↕</span></th>
<th data-c="rating" class="num">Rating <span class="arr">↕</span></th>
<th data-c="confidence">Conf.</th>
<th data-c="source">Source</th>
<th data-c="seen">Seen</th>
</tr></thead><tbody id="tb"></tbody></table></div>
<footer>Ratings are provider-level Trustpilot approximations. Confidence:
✅ sourced · ⚠️ approx/range · ❓ unverified.
Cheapest $/GB row highlighted. Data from
<a href="{GITHUB_REPO}" target="_blank" rel="noopener">frindle/travel-esim-rates</a>.</footer>
</div>
<script>const ROWS={rows_json};{SORT_JS}
let cur={{col:'pergb',dir:1}};
function filtered(){{
  let r=ROWS;
  if(document.getElementById('fHot').checked) r=r.filter(x=>x.hotspot_ok);
  if(document.getElementById('fCap').checked) r=r.filter(x=>!x.unlimited);
  return r;
}}
function draw(){{
  const rows=sortRows(filtered(),cur.col,cur.dir);
  // find cheapest per_gb for highlight
  let best=null; rows.forEach(r=>{{if(r.per_gb!=null&&(best==null||r.per_gb<best))best=r.per_gb;}});
  const tb=document.getElementById('tb');
  tb.innerHTML = rows.length? rows.map(r=>{{
    const hi=(r.per_gb!=null&&r.per_gb===best)?' class="cheapest"':'';
    return '<tr'+hi+'>'+
      '<td>'+esc(r.provider)+'</td>'+
      '<td>'+esc(r.plan)+'</td>'+
      '<td class="num">'+fmtGB(r)+'</td>'+
      '<td class="num">'+fmtDur(r)+'</td>'+
      '<td class="num">'+fmtUSD(r.price)+'</td>'+
      '<td class="num">'+fmtGBp(r.per_gb)+'</td>'+
      '<td>'+esc(r.hotspot)+'</td>'+
      '<td class="num">'+fmtRating(r.rating)+'</td>'+
      '<td>'+esc(r.confidence)+'</td>'+
      '<td>'+srcCell(r.source)+'</td>'+
      '<td>'+esc(r.seen)+'</td></tr>';
  }}).join(''):'<tr><td colspan="11" class="empty">No plans match these filters.</td></tr>';
  document.querySelectorAll('th[data-c]').forEach(th=>{{
    th.classList.toggle('sorted',th.dataset.c===cur.col);
    const a=th.querySelector('.arr'); if(a) a.textContent=th.dataset.c===cur.col?(cur.dir>0?'▲':'▼'):'↕';
  }});
}}
document.querySelectorAll('th[data-c]').forEach(th=>th.addEventListener('click',()=>{{
  const c=th.dataset.c; if(c==='plan')return;
  if(cur.col===c) cur.dir*=-1; else {{cur.col=c;cur.dir=(c==='provider'||c==='rating'||c==='data')?(c==='provider'?1:-1):1;}}
  draw();
}}));
document.getElementById('fHot').addEventListener('change',draw);
document.getElementById('fCap').addEventListener('change',draw);
draw();
</script></body></html>"""
    return body


def render_index(data):
    # group for picker
    by_region = {}
    for e in data:
        by_region.setdefault(e["region"], []).append(e)
    all_json = json.dumps([
        {"region": e["region"], "country": e["country"], "slug": e["slug"],
         "href": f"{e['region']}/{e['slug']}.html", "rows": e["rows"]}
        for e in data
    ])

    pick_html = []
    for region in REGIONS:
        if region not in by_region:
            continue
        pick_html.append(f'<div class="regionhdr">{html.escape(region)}</div><div class="pickgrid">')
        for e in sorted(by_region[region], key=lambda x: x["country"]):
            cid = f"{e['region']}::{e['slug']}"
            pick_html.append(
                f'<label class="chk"><input type="checkbox" class="cpick" value="{html.escape(cid)}"> '
                f'<a href="{e["region"]}/{e["slug"]}.html">{html.escape(e["country"])}</a></label>'
            )
        pick_html.append("</div>")
    pick_html = "\n".join(pick_html)

    n_countries = len(data)
    n_regions = len(by_region)

    body = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Travel eSIM Rates</title>
<link rel="stylesheet" href="style.css">
</head><body><div class="wrap">
<header><h1>Travel eSIM Rates</h1>
<p class="sub">Pick where you're going — get the best-value eSIM per destination.
{n_countries} countries · {n_regions} regions ·
<a href="{GITHUB_REPO}" target="_blank" rel="noopener">source repo</a></p></header>

<div class="panel">
<div class="controls">
<div class="ctl"><label>Rank by</label>
<select id="rankBy">
<option value="pergb">Best $/GB (value)</option>
<option value="price">Cheapest plan (total $)</option>
<option value="rating">Highest rated</option>
</select></div>
<div class="ctl"><label>Min data (GB)</label>
<input type="number" id="minGB" min="0" step="1" placeholder="any"></div>
<div class="ctl"><label>Options per country</label>
<input type="number" id="topN" min="1" step="1" value="3"></div>
<label class="chk"><input type="checkbox" id="fHot"> Hotspot only</label>
<label class="chk"><input type="checkbox" id="fUnlim"> Include unlimited</label>
</div>
</div>

<div class="panel">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
<strong>Choose destinations</strong>
<span><a href="#" id="selAll">select all</a> · <a href="#" id="selNone">clear</a></span>
</div>
{pick_html}
</div>

<div id="results"></div>

<footer>Ratings are provider-level Trustpilot approximations. Confidence:
✅ sourced · ⚠️ approx/range · ❓ unverified. "Best" ranks by your chosen
metric among plans matching your filters; verify live before buying.
Data from <a href="{GITHUB_REPO}" target="_blank" rel="noopener">frindle/travel-esim-rates</a>.</footer>
</div>
<script>const DATA={all_json};{SORT_JS}
const $=id=>document.getElementById(id);
function picked(){{return [...document.querySelectorAll('.cpick:checked')].map(c=>c.value);}}
function restore(){{try{{return JSON.parse(localStorage.getItem('esim.pick')||'[]');}}catch(e){{return[];}}}}
function save(){{try{{localStorage.setItem('esim.pick',JSON.stringify(picked()));}}catch(e){{}}}}
function planMatches(r){{
  if($('fHot').checked && !r.hotspot_ok) return false;
  if(!$('fUnlim').checked && r.unlimited) return false;
  const mg=parseFloat($('minGB').value);
  if(!isNaN(mg)){{ if(r.unlimited) return true; if(r.data_gb==null||r.data_gb<mg) return false; }}
  return true;
}}
function rankKey(r,by){{
  if(by==='pergb') return r.per_gb;
  if(by==='price') return r.price;
  if(by==='rating') return r.rating==null?null:-r.rating; // higher first
  return r.per_gb;
}}
function render(){{
  save();
  const sel=picked(), by=$('rankBy').value, topN=Math.max(1,parseInt($('topN').value)||3);
  const box=$('results');
  if(!sel.length){{box.innerHTML='<div class="panel empty">Select one or more destinations above to see the best options.</div>';return;}}
  let out='';
  sel.forEach(cid=>{{
    const e=DATA.find(d=>d.region+'::'+d.slug===cid); if(!e)return;
    let rows=e.rows.filter(planMatches).filter(r=>rankKey(r,by)!=null);
    rows.sort((a,b)=>rankKey(a,by)-rankKey(b,by));
    rows=rows.slice(0,topN);
    out+='<div class="result-country">'+esc(e.country)+' <span class="muted">('+esc(e.region)+')</span> '+
         '<a class="muted" href="'+e.href+'" style="font-weight:400;font-size:13px">full table →</a></div>';
    if(!rows.length){{out+='<div class="panel empty">No plans match your filters.</div>';return;}}
    out+='<div class="panel tablewrap"><table><thead><tr>'+
      '<th>Provider</th><th>Plan</th><th class="num">Data</th><th class="num">Days</th>'+
      '<th class="num">Price</th><th class="num">$/GB</th><th>Hotspot</th><th class="num">Rating</th><th>Conf.</th></tr></thead><tbody>';
    rows.forEach((r,i)=>{{
      out+='<tr'+(i===0?' class="cheapest"':'')+'>'+
        '<td>'+esc(r.provider)+'</td><td>'+esc(r.plan)+'</td>'+
        '<td class="num">'+fmtGB(r)+'</td><td class="num">'+fmtDur(r)+'</td>'+
        '<td class="num">'+fmtUSD(r.price)+'</td><td class="num">'+fmtGBp(r.per_gb)+'</td>'+
        '<td>'+esc(r.hotspot)+'</td><td class="num">'+fmtRating(r.rating)+'</td><td>'+esc(r.confidence)+'</td></tr>';
    }});
    out+='</tbody></table></div>';
  }});
  box.innerHTML=out;
}}
document.querySelectorAll('.cpick').forEach(c=>c.addEventListener('change',render));
['rankBy','minGB','topN','fHot','fUnlim'].forEach(id=>$(id).addEventListener('input',render));
$('selAll').addEventListener('click',e=>{{e.preventDefault();document.querySelectorAll('.cpick').forEach(c=>c.checked=true);render();}});
$('selNone').addEventListener('click',e=>{{e.preventDefault();document.querySelectorAll('.cpick').forEach(c=>c.checked=false);render();}});
// restore prior selection
const prev=restore(); if(prev.length){{document.querySelectorAll('.cpick').forEach(c=>{{if(prev.includes(c.value))c.checked=true;}});}}
render();
</script></body></html>"""
    return body


def main():
    data = collect()
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "style.css").write_text(STYLE, encoding="utf-8")
    (DOCS / "rates.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    (DOCS / "index.html").write_text(render_index(data), encoding="utf-8")

    total_rows = 0
    for e in data:
        outdir = DOCS / e["region"]
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / f"{e['slug']}.html").write_text(render_country_page(e), encoding="utf-8")
        total_rows += len(e["rows"])

    print(f"built {len(data)} country pages, {total_rows} rate rows -> {DOCS}")


if __name__ == "__main__":
    main()
