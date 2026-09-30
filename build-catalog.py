#!/usr/bin/env python3
"""Build the Kestrelattice product catalog page (products/index.html).

Reads every live product (originals + pending-listings.jsonl via build-covers.products()),
renders a branded catalog grid with covers, and updates sitemap.xml.
Idempotent — safe to re-run as the catalog grows.
"""
import html, json, os, sys
from datetime import date

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "build_covers", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-covers.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
products = _mod.products

SITE = os.path.expanduser("~/workspace/kestrelattice")
BASE_URL = "https://koalstingkdelaney-gif.github.io/kestrelattice"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Product Catalog — Kestrelattice</title>
<meta name="description" content="Every Kestrelattice self-serve PDF: agent governance checklists, runbooks, worksheets and kits. Instant download.">
<style>
:root{--bg:#121212;--panel:#1c1a18;--panel2:#232019;--line:#332e26;--text:#e8e2d8;--muted:#9a917f;--accent:#e07a5f;--accent-dim:#b9634b;--ok:#7fbf7f}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.6}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
a{color:var(--accent);text-decoration:none}
header{border-bottom:1px solid var(--line);padding:14px 0;position:sticky;top:0;background:rgba(18,18,18,.94);z-index:100}
header .wrap{display:flex;align-items:center;justify-content:space-between}
.logo{font-weight:700;font-size:1.15rem;color:var(--text)}
nav a{margin-left:18px;color:var(--muted);font-size:.95rem}
nav a:hover{color:var(--text)}
.hero{padding:56px 0 24px;text-align:center}
.hero h1{font-size:2.2rem;margin-bottom:8px}
.lede{color:var(--muted);max-width:640px;margin:0 auto}
.filters{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:28px 0}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:999px;padding:6px 14px;font-size:.85rem;cursor:pointer}
.chip.active{background:var(--accent);border-color:var(--accent);color:#161210;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px;padding:8px 0 64px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:3/4;object-fit:cover;display:block;background:#0c0c0c}
.card .body{padding:16px;display:flex;flex-direction:column;gap:8px;flex:1}
.card h3{font-size:1.02rem;line-height:1.35}
.price{color:var(--accent);font-weight:700}
.card p.desc{color:var(--muted);font-size:.88rem;flex:1}
.btn{display:inline-block;background:var(--accent);color:#161210;font-weight:700;padding:10px 18px;border-radius:8px;text-align:center}
.btn:hover{background:var(--accent-dim);text-decoration:none}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.btn.ghost:hover{background:var(--panel)}
footer{border-top:1px solid var(--line);padding:28px 0;color:var(--muted);font-size:.85rem;text-align:center}
.hidden{display:none!important}
</style>
</head>
<body>
<header><div class="wrap">
<a class="logo" href="../">Kestrelattice</a>
<nav><a href="../">Home</a><a href="../articles/">Articles</a><a href="../#products">Products</a></nav>
</div></header>
<div class="wrap hero">
<h1>The Catalog</h1>
<p class="lede">Every self-serve PDF in the Kestrelattice library — checklists, runbooks, worksheets, and kits for governing AI agents. Buy once, download instantly, yours forever.</p>
</div>
<div class="wrap"><div class="filters" id="filters"></div></div>
<div class="wrap"><div class="grid" id="grid">
__CARDS__
</div></div>
<footer><div class="wrap">Kestrelattice · independent studio · secure checkout via Gumroad · instant delivery</div></footer>
<script>
const grid=document.getElementById('grid'),filters=document.getElementById('filters');
const tags=[...new Set([...grid.querySelectorAll('.card')].flatMap(c=>c.dataset.tags.split('|').filter(Boolean)))].sort();
const mk=(label,tag)=>{const b=document.createElement('button');b.className='chip'+(tag===''?' active':'');b.textContent=label;b.onclick=()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.card').forEach(c=>{c.classList.toggle('hidden',tag!==''&&!c.dataset.tags.split('|').includes(tag))})};return b};
filters.appendChild(mk('All',''));
tags.forEach(t=>filters.appendChild(mk(t.replace(/-/g,' '),t)));
</script>
</body>
</html>
"""

CARD = """<div class="card" data-tags="{tags}">
<a href="{slug}/" style="text-decoration:none;color:inherit;display:block"><img src="../assets/covers/{pid}.png" alt="{title} cover" loading="lazy">
<div class="body"><h3>{title}</h3><p class="desc">{tagline}</p><p class="price">${price} <span style="color:var(--muted);font-weight:400;font-size:.85rem">one-time</span></p></div></a>
<div class="body" style="padding-top:0;display:flex;gap:10px"><a class="btn" href="{url}">Get it</a><a class="btn ghost" href="{slug}/">Details</a></div>
</div>
"""

ORIGINAL_SLUGS = {
    "hdigmr": "the-playbook-studio-edition",
    "sahva": "ai-agent-risk-audit-kit",
    "jbngbu": "agent-incident-response-runbook",
    "slexhv": "100-agent-use-cases-pre-tiered",
    "cjdkuu": "prompt-injection-defense-field-guide",
    "ilxccs": "agent-cost-control-workbook",
    "fdtkdd": "quarterly-access-review-kit",
    "yzbumc": "complete-kestrelattice-library",
}

def slugify(t):
    import re as _re
    s = _re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return _re.sub(r"-+", "-", s)

def main():
    prods = products()
    # tag lookup from pending-listings for filtering
    tagmap = {}
    pj = os.path.expanduser("~/workspace/goals/kestrelattice-autonomous-growth/hidden_files/marketplace/pending-listings.jsonl")
    if os.path.exists(pj):
        with open(pj) as f:
            for line in f:
                try:
                    p = json.loads(line)
                    pid = p["gumroad_url"].rstrip("/").split("/")[-1]
                    tagmap[pid] = [t.lower().replace(" ", "-") for t in p.get("tags", [])[:6]]
                except Exception:
                    pass
    cards = []
    for p in sorted(prods, key=lambda x: (x["price"], x["title"])):
        pid = p["id"]
        tags = "|".join(tagmap.get(pid, ["governance"]))
        cards.append(CARD.format(
            pid=html.escape(pid),
            title=html.escape(p["title"]),
            tagline=html.escape(p.get("tagline", "")),
            price=p["price"],
            url=f"https://koalstin.gumroad.com/l/{html.escape(pid)}",
            tags=html.escape(tags),
            slug=ORIGINAL_SLUGS.get(pid, slugify(p["title"])),
        ))
    outdir = os.path.join(SITE, "products")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "index.html"), "w") as f:
        f.write(PAGE.replace("__CARDS__", "\n".join(cards)))

    # sitemap entry
    sm = os.path.join(SITE, "sitemap.xml")
    with open(sm) as f:
        content = f.read()
    entry = f"""  <url>
    <loc>{BASE_URL}/products/</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    if "/products/</loc>" not in content:
        content = content.replace("</urlset>", entry + "</urlset>")
        with open(sm, "w") as f:
            f.write(content)

    # homepage catalog link card (insert once)
    idx = os.path.join(SITE, "index.html")
    with open(idx) as f:
        h = f.read()
    marker = 'id="catalog-link-card"'
    if marker not in h:
        card = ('      <div class="card" id="catalog-link-card" style="border-color:var(--accent)">'
                '<h3>Browse the full catalog</h3>'
                f'<p class="price" style="margin:8px 0">{len(prods)} products <span style="font-size:.85rem;color:var(--muted);font-weight:400">and growing</span></p>'
                '<p>Every checklist, runbook, worksheet, and kit — filterable, with covers, in one place.</p>'
                '<p><a class="btn primary" href="products/">Open the catalog</a></p></div>\n')
        h = h.replace('<div class="grid">\n', '<div class="grid">\n' + card, 1)
        with open(idx, "w") as f:
            f.write(h)
    else:
        # keep the count fresh
        import re
        h = re.sub(r'<p class="price" style="margin:8px 0">\d+ products',
                   f'<p class="price" style="margin:8px 0">{len(prods)} products', h)
        with open(idx, "w") as f:
            f.write(h)

    # homepage bundle card (keep file count + savings math fresh, data-driven)
    import re as _re2
    indiv = [p for p in prods if p["id"] != "yzbumc"]
    _n, _val = len(indiv), int(sum(p["price"] for p in indiv))
    _save = _val - 79
    h = _re2.sub(r"one-time · \d+ (?:PDFs|files) · <s>\$\d+(?:\.\d+)?</s> save \$\d+(?:\.\d+)?",
                 f"one-time · {_n} files · <s>${_val}</s> save ${_save}", h)
    with open(idx, "w") as f:
        f.write(h)
    print(f"catalog: {len(prods)} products -> products/index.html")

if __name__ == "__main__":
    main()
