#!/usr/bin/env python3
"""Build the ghostcorpnet product catalog page (products/index.html).

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

_BOILER = ("A complete, zero-placeholder template for teams governing AI agents in production: "
           "policy gates, audit trails, cost controls.")

def fix_tagline(t):
    """Repair truncated boilerplate taglines (micro-forge sometimes cuts them mid-word)."""
    import re as _re
    t = t or ""
    if "A complete, zero-placeholder" in t and "cost controls." not in t:
        t = _re.sub(r"A complete, zero-placeholder.*$", _BOILER, t)
    t = t.replace(
        "A complete, zero-placeholder draft for teams governing AI agents in production: policy gates, audit trails, cost controls.",
        _BOILER)
    return t.replace(" -- ", " \u2014 ")

def fmt_price(p):
    f = float(p)
    return str(int(f)) if f.is_integer() else str(f)

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Product Catalog — ghostcorpnet</title>
<meta name="description" content="Every ghostcorpnet self-serve product: agent governance playbooks, checklists, runbooks, kits, and working code. Instant download.">
<meta name="theme-color" content="#1a1f2e">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://koalstingkdelaney-gif.github.io/kestrelattice/products/">
<link rel="preconnect" href="https://koalstin.gumroad.com">
<link rel="dns-prefetch" href="https://koalstin.gumroad.com">
<meta property="og:type" content="website">
<meta property="og:title" content="Product Catalog — ghostcorpnet">
<meta property="og:description" content="Every ghostcorpnet self-serve product: agent governance playbooks, checklists, runbooks, kits, and working code. Instant download.">
<meta property="og:url" content="https://koalstingkdelaney-gif.github.io/kestrelattice/products/">
<meta property="og:image" content="https://koalstingkdelaney-gif.github.io/kestrelattice/assets/studio-edition-cover.jpg">
<meta property="og:image:alt" content="ghostcorpnet product catalog — governed agent mesh playbooks and kits">
<meta property="og:image:width" content="1600">
<meta property="og:image:height" content="1600">
<meta property="og:site_name" content="ghostcorpnet by GhostCorp">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Product Catalog — ghostcorpnet">
<meta name="twitter:description" content="Every ghostcorpnet self-serve product: agent governance playbooks, checklists, runbooks, kits, and working code. Instant download.">
<meta name="twitter:image" content="https://koalstingkdelaney-gif.github.io/kestrelattice/assets/studio-edition-cover.jpg">
<script type="application/ld+json">
__ITEMLIST__
</script>
<style>
:root{color-scheme:dark;--bg:#0f0e0d;--bg-soft:#141210;--panel:#1a1714;--panel2:#211c17;--line:#2c261e;--text:#f1ebdd;--muted:#a89d89;--faint:#7d7461;--accent:#e07a5f;--accent-bright:#f09474;--accent-dim:#c06a4e;--accent-ink:#1a0f08;--accent-soft:rgba(224,122,95,.1);--radius:12px;--radius-sm:8px;--ease:cubic-bezier(.2,.7,.25,1)}
*{margin:0;padding:0;box-sizing:border-box}
body{background:radial-gradient(900px 420px at 50% -6%, rgba(224,122,95,.06), transparent 62%),var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
a{color:var(--accent);text-decoration:none;transition:color .16s var(--ease)}
a:hover{text-decoration:underline}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent-bright);outline-offset:3px;border-radius:4px}
header.site{border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(15,14,13,.92);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);z-index:100}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;min-height:58px}
.logo{display:flex;align-items:center;gap:9px;font-weight:700;font-size:1.05rem;color:var(--text)}
.logo:hover{text-decoration:none;color:var(--accent-bright)}
nav.main{display:flex;align-items:center;gap:20px}
nav.main a{color:var(--muted);font-size:.88rem;font-weight:500}
nav.main a:hover{color:var(--accent-bright)}
.hero{padding:44px 0 8px;text-align:center}
.hero h1{font-size:clamp(1.7rem,3.4vw + .8rem,2.4rem);font-weight:800;letter-spacing:-.02em;margin-bottom:10px}
.lede{color:var(--muted);max-width:620px;margin:0 auto;font-size:.98rem}
.filters{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:26px 0}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:999px;padding:7px 15px;font-size:.84rem;letter-spacing:.1em;cursor:pointer;font-family:inherit;transition:all .16s var(--ease)}
.chip:hover{border-color:var(--accent-dim);color:var(--text)}
.chip.active{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:18px;padding:8px 0 64px}
.card{background:linear-gradient(180deg,var(--panel),var(--bg-soft));border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;display:flex;flex-direction:column;transition:border-color .18s var(--ease),transform .18s var(--ease),box-shadow .18s var(--ease)}
.card:hover{border-color:var(--accent-dim);transform:translateY(-3px);box-shadow:0 14px 34px rgba(0,0,0,.4)}
.card img{transition:transform .3s ease}
.card:hover img{transform:scale(1.05)}
@media (prefers-reduced-motion:reduce){.card:hover img{transform:none}}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#0b0a09}
.card .body{padding:16px;display:flex;flex-direction:column;gap:7px;flex:1}
.codebadge{display:inline-block;align-self:flex-start;background:var(--accent-soft);border:1px solid var(--accent-dim);color:var(--accent-bright);font-size:.68rem;font-weight:700;letter-spacing:.08em;padding:2px 8px;border-radius:999px}
.card h2{font-size:.98rem;line-height:1.35;font-weight:700;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.price{color:var(--text);font-weight:800;font-variant-numeric:tabular-nums}
.card p.desc{color:var(--muted);font-size:.85rem;flex:1}
.card .row{display:flex;gap:10px;padding:0 16px 16px}
.btn{display:inline-block;background:linear-gradient(180deg,var(--accent-bright),var(--accent));color:var(--accent-ink);font-weight:700;padding:10px 18px;border-radius:var(--radius-sm);text-align:center;font-size:.88rem;flex:1;transition:transform .16s var(--ease)}
.btn:hover{transform:translateY(-1px);text-decoration:none}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--line)}
.btn.ghost:hover{border-color:var(--accent-dim);color:var(--accent-bright)}
footer.site{border-top:1px solid var(--line);background:var(--bg-soft);padding:24px 0;color:var(--muted);font-size:.82rem}
footer.site .wrap{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px 16px}
footer.site a{color:var(--faint);margin-left:14px}
footer.site a:hover{color:var(--accent-bright)}
.skip{position:absolute;left:-9999px;top:0;background:var(--accent);color:var(--accent-ink);padding:10px 18px;font-weight:700;z-index:200;border-radius:0 0 8px 0}
.skip:focus{left:0}
.trust{color:var(--faint);font-size:.78rem;text-align:center;margin:-8px 0 14px}
.result-count{color:var(--muted);font-size:.86rem;text-align:center;margin:4px 0 0}
.hidden{display:none!important}
#backtop{position:fixed;right:22px;bottom:22px;width:46px;height:46px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--accent);font-size:1.3rem;cursor:pointer;opacity:0;pointer-events:none;transition:opacity .2s var(--ease);z-index:150}
#backtop.show{opacity:1;pointer-events:auto}
#backtop:hover{border-color:var(--accent-dim)}
@media(prefers-reduced-motion:reduce){#backtop{display:none}}
@media(max-width:640px){.filters{overflow-x:auto;flex-wrap:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.filters::-webkit-scrollbar{display:none}
nav.main a:not(:last-child){display:none}footer.site .wrap{justify-content:center;text-align:center}footer.site a{margin:0 7px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important;animation:none!important}}

  h1,h2{text-wrap:balance}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
<a class="logo" href="../">
<svg width="24" height="24" viewBox="0 0 26 26" fill="none" aria-hidden="true"><circle cx="5" cy="6" r="2.4" fill="#e07a5f"/><circle cx="21" cy="6" r="2.4" fill="#e07a5f"/><circle cx="13" cy="13" r="2.4" fill="#e07a5f"/><circle cx="5" cy="20" r="2.4" fill="#e07a5f"/><circle cx="21" cy="20" r="2.4" fill="#e07a5f"/><path d="M6.6 7.4L11.2 11.8M19.4 7.4L14.8 11.8M6.6 18.6L11.2 14.2M19.4 18.6L14.8 14.2" stroke="#e07a5f" stroke-width="1.4"/></svg>
ghostcorpnet</a>
<nav class="main" aria-label="Primary"><a href="../">Home</a><a href="../brands/">Stores</a><a href="../ecosystem/">Ecosystem</a><a href="../directory/">Directory</a><a href="../build/">Build</a><a href="../articles/">Articles</a><a href="../#faq">FAQ</a></nav>
</div></header>
<main id="main">
<div class="wrap hero">
<h1>The Catalog</h1>
<p class="lede">Every self-serve product in the ghostcorpnet library — playbooks, checklists, runbooks, kits, and working code for governing AI agents. Buy once, download instantly, yours forever.</p>
</div>
<div class="wrap"><p class="result-count" id="result-count" aria-live="polite">__COUNT__</p><div class="filters" id="filters"></div></div>
<div class="wrap"><div class="grid" id="grid">
__CARDS__
</div></div>
<button id="backtop" aria-label="Back to top">↑</button>
</main>
<footer class="site"><div class="wrap">
<span>© 2026 GhostCorp · ghostcorpnet · An independent studio</span>
<span><a href="mailto:koalstin.g.k.delaney@gmail.com">Contact</a><a href="../articles/">Articles</a><a href="../brands/">Stores</a><a href="../ecosystem/">Ecosystem</a><a href="../directory/">Directory</a><a href="../build/">Build</a><a href="../sitemap.xml">Sitemap</a><a href="../admin-login.html">Admin</a></span>
</div></footer>
<script>
const grid=document.getElementById('grid'),filters=document.getElementById('filters'),rc=document.getElementById('result-count');
const updateCount=()=>{const v=[...grid.querySelectorAll('.card')].filter(c=>!c.classList.contains('hidden')).length;rc.textContent=v===0?'No products match':(v===1?'1 product':v+' products')};
const tags=[...new Set([...grid.querySelectorAll('.card')].flatMap(c=>c.dataset.tags.split('|').filter(Boolean)))].sort();
const mk=(label,tag)=>{const b=document.createElement('button');b.className='chip'+(tag===''?' active':'');b.textContent=label;b.setAttribute('aria-pressed',String(tag===''));b.onclick=()=>{document.querySelectorAll('.chip').forEach(x=>{x.classList.remove('active');x.setAttribute('aria-pressed','false')});b.classList.add('active');b.setAttribute('aria-pressed','true');document.querySelectorAll('.card').forEach(c=>{c.classList.toggle('hidden',tag!==''&&!c.dataset.tags.split('|').includes(tag))});updateCount()};return b};
filters.appendChild(mk('All',''));
tags.forEach(t=>filters.appendChild(mk(t.replace(/-/g,' '),t)));

<script>
(function(){var b=document.getElementById('backtop');if(!b)return;
function onScroll(){b.classList.toggle('show',window.scrollY>1200)}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
b.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});})();
</script>
</script>
</body>
</html>
"""

CARD = """<div class="card" data-tags="{tags}">
<a href="{slug}/" style="text-decoration:none;color:inherit;display:block"><img src="../assets/covers/{pid}.png" alt="{title} cover" loading="lazy" decoding="async" sizes="(max-width:640px) 100vw, (max-width:1100px) 50vw, 320px">
<div class="body">{badge}<h2 translate="no">{title}</h2><p class="desc">{tagline}</p><p class="price"><span translate="no">${price}</span> <span style="color:var(--muted);font-weight:400;font-size:.85rem">one-time</span></p></div></a>
<div class="row"><a class="btn" href="{url}">Get it</a><a class="btn ghost" href="{slug}/">Details</a></div>
<p class="trust">Instant delivery via Gumroad</p>
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
        ptaglist = tagmap.get(pid, ["governance"])
        tags = "|".join(ptaglist)
        badge = '<span class="codebadge">CODE</span>' if "code" in ptaglist else ""
        cards.append(CARD.format(
            pid=html.escape(pid),
            title=html.escape(p["title"]),
            tagline=html.escape(fix_tagline(p.get("tagline", ""))),
            price=fmt_price(p["price"]),
            url=f"https://koalstin.gumroad.com/l/{html.escape(pid)}",
            tags=html.escape(tags),
            slug=ORIGINAL_SLUGS.get(pid, slugify(p["title"])),
            badge=badge,
        ))
    outdir = os.path.join(SITE, "products")
    os.makedirs(outdir, exist_ok=True)
    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "ghostcorpnet product catalog",
        "itemListElement": [
            {"@type": "ListItem", "position": n, "item": {
                "@type": "Product",
                "name": p["title"],
                "url": f"{BASE_URL}/products/{ORIGINAL_SLUGS.get(p['id'], slugify(p['title']))}/",
                "offers": {"@type": "Offer", "price": fmt_price(p["price"]), "priceCurrency": "USD"},
            }} for n, p in enumerate(sorted(prods, key=lambda x: (x["price"], x["title"])), 1)
        ],
    }
    page = PAGE.replace("__ITEMLIST__", json.dumps(itemlist, ensure_ascii=False, indent=2))
    with open(os.path.join(outdir, "index.html"), "w") as f:
        f.write(page.replace("__CARDS__", "\n".join(cards)).replace("__COUNT__", f"{len(prods)} products"))

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
                '<p>Every playbook, checklist, runbook, kit, and code tool — filterable, with covers, in one place.</p>'
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
    _n, _val = len(indiv), int(sum(float(p["price"]) for p in indiv))
    _save = _val - 79
    h = _re2.sub(r"one-time · \d+ (?:PDFs|files) · <s>\$[\d,.]+</s> save \$[\d,.]+",
                 f"one-time · {_n} files · <s>${_val:,}</s> save ${_save:,}", h)
    with open(idx, "w") as f:
        f.write(h)
    print(f"catalog: {len(prods)} products -> products/index.html")

if __name__ == "__main__":
    main()
