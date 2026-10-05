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

_ospec = importlib.util.spec_from_file_location(
    "slug_overrides", os.path.join(os.path.dirname(os.path.abspath(__file__)), "slug_overrides.py"))
_omod = importlib.util.module_from_spec(_ospec)
_ospec.loader.exec_module(_omod)
SLUG_OVERRIDES = _omod.SLUG_OVERRIDES

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
    # Trim lone trailing fragments from mid-word cuts ("...protocols for h")
    t = _re.sub(r"\s[a-zA-Z0-9]$", "\u2026", t)
    return t.replace(" -- ", " \u2014 ")

def fmt_price(p):
    f = float(p)
    return str(int(f)) if f.is_integer() else str(f)

PAGE = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI Agent Governance Products — Catalog | ghostcorpnet</title>
<meta name="description" content="Every ghostcorpnet self-serve product: agent governance playbooks, checklists, runbooks, kits, and working code. Instant download.">
<meta name="theme-color" content="#0f0e0d">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://koalstingkdelaney-gif.github.io/kestrelattice/products/">
<link rel="preconnect" href="https://koalstin.gumroad.com">
<link rel="dns-prefetch" href="https://koalstin.gumroad.com">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-541TCHWW98"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  if (!window.__klExcludeSelf) {
    gtag('js', new Date());
    gtag('config', 'G-541TCHWW98');
  }
</script>
__PRELOAD__
<meta property="og:type" content="website">
<meta property="og:title" content="AI Agent Governance Products — Catalog | ghostcorpnet">
<meta property="og:description" content="Every ghostcorpnet self-serve product: agent governance playbooks, checklists, runbooks, kits, and working code. Instant download.">
<meta property="og:url" content="https://koalstingkdelaney-gif.github.io/kestrelattice/products/">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="https://koalstingkdelaney-gif.github.io/kestrelattice/assets/studio-edition-cover.jpg">
<meta property="og:image:alt" content="ghostcorpnet product catalog — governed agent mesh playbooks and kits">
<meta property="og:image:width" content="1600">
<meta property="og:image:height" content="1600">
<meta property="og:site_name" content="ghostcorpnet by GhostCorp">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AI Agent Governance Products — Catalog | ghostcorpnet">
<meta name="twitter:description" content="Every ghostcorpnet self-serve product: agent governance playbooks, checklists, runbooks, kits, and working code. Instant download.">
<meta name="twitter:image" content="https://koalstingkdelaney-gif.github.io/kestrelattice/assets/studio-edition-cover.jpg">
<meta name="twitter:image:alt" content="ghostcorpnet product catalog — AI agent governance playbooks and kits">
<script type="application/ld+json">
__ITEMLIST__
</script>
<style>
:root{color-scheme:dark;--bg:#0f0e0d;--bg-soft:#141210;--panel:#1a1714;--panel2:#211c17;--line:#2c261e;--text:#f1ebdd;--muted:#a89d89;--faint:#978b74;--accent:#e07a5f;--accent-bright:#f09474;--accent-dim:#c06a4e;--accent-ink:#1a0f08;--accent-soft:rgba(224,122,95,.1);--radius:12px;--radius-sm:8px;--ease:cubic-bezier(.2,.7,.25,1)}@media (prefers-contrast:more){:root{--muted:#d8cfbc;--faint:#c0b59e}}
*{margin:0;padding:0;box-sizing:border-box}
html,body{overflow-x:clip}
::selection{background:var(--accent);color:var(--accent-ink)}
html{scroll-behavior:smooth}
body{background:radial-gradient(900px 420px at 50% -6%, rgba(224,122,95,.06), transparent 62%),var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
a{color:var(--accent);text-decoration:none;transition:color .16s var(--ease)}
a:hover{text-decoration:underline}
a:focus-visible,button:focus-visible{outline:3px solid var(--accent-bright);outline-offset:3px;border-radius:4px}@media (prefers-reduced-motion:no-preference){a:focus-visible,button:focus-visible{transition:transform .15s ease}a:focus-visible{transform:scale(1.03)}.btn:focus-visible,.chip:focus-visible,nav.main a:focus-visible{transform:scale(1.02)}.btn:active{transform:scale(.98)}}
header.site{border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(15,14,13,.92);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);z-index:100}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;min-height:58px}
.logo{display:flex;align-items:center;gap:9px;font-weight:700;font-size:1.05rem;color:var(--text)}
.logo:hover{text-decoration:none;color:var(--accent-bright)}
nav.main{display:flex;align-items:center;gap:20px}
nav.main a{color:var(--muted);font-size:.88rem;font-weight:500}
nav.main a:hover{color:var(--accent-bright)}
nav.main a[aria-current="page"]{color:var(--accent-bright)}
nav.main a[aria-current="page"]::after{transform:scaleX(1)}
.hero{padding:44px 0 8px;text-align:center}
.hero h1{font-size:clamp(1.7rem,3.4vw + .8rem,2.4rem);font-weight:800;letter-spacing:-.02em;margin-bottom:10px}
.lede{color:var(--muted);max-width:620px;margin:0 auto;font-size:.98rem}
.secure-checkout{font-size:.72rem;color:var(--faint);margin-top:6px}
.filters{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:26px 0;position:sticky;top:58px;z-index:40;background:var(--bg);padding:10px 4px}
#filters{scroll-margin-top:76px}.filters-toggle{display:none}@media(max-width:640px){.filters{flex-direction:column;align-items:stretch;overflow:visible}.filters-toggle{display:inline-flex;align-items:center;justify-content:space-between;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:8px;color:var(--text);padding:10px 14px;font:inherit;font-size:.9rem;font-weight:600;cursor:pointer}.filters-toggle .ft-chev{transition:transform .18s var(--ease);color:var(--accent)}#filters[data-collapsed="true"] .filters-list{display:none}#filters[data-collapsed="true"] .ft-chev{transform:rotate(-90deg)}.filters-list{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}}
.tier-legend{color:var(--muted);font-size:.85rem;text-align:center;margin:0 0 14px}
.visually-hidden{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.catalog-search-row{display:flex;justify-content:center;align-items:center;gap:8px;margin:0 0 4px}
#catalog-search{width:min(440px,92%);padding:12px 18px;min-height:48px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--text);font-size:1rem}
.search-kbd{display:inline-flex;align-items:center;justify-content:center;min-width:26px;height:26px;padding:0 7px;border:1px solid var(--line);border-bottom-width:2px;border-radius:6px;background:var(--panel2);color:var(--muted);font-size:.78rem;font-family:inherit;flex:none}
#catalog-search:focus{border-color:var(--accent);outline:none}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:999px;padding:7px 15px;min-height:44px;display:inline-flex;align-items:center;justify-content:center;font-size:.84rem;letter-spacing:.1em;cursor:pointer;font-family:inherit;transition:all .16s var(--ease)}
.chip:hover{border-color:var(--accent-dim);color:var(--text)}
.chip.active{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700}.chip:active{transform:scale(.96)}\n.chip-count{font-size:.72em;color:var(--muted);opacity:.85;margin-left:2px;font-weight:400;letter-spacing:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:24px;padding:8px 0 64px;list-style:none;margin:0}
.card{background:linear-gradient(180deg,var(--panel),var(--bg-soft));border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;display:flex;flex-direction:column;content-visibility:auto;contain-intrinsic-size:auto 480px;transition:border-color .18s var(--ease),transform .18s var(--ease),box-shadow .18s var(--ease)}.card{position:relative}.card>a:first-of-type::after{content:"";position:absolute;inset:0}.card .row .btn{position:relative;z-index:1}
@media (hover:hover) and (pointer:fine){
.card:hover{border-color:var(--accent-dim);transform:translateY(-3px);box-shadow:0 14px 34px rgba(0,0,0,.4)}
}
.card img{transition:transform .3s ease}
@media (hover:hover) and (pointer:fine){
.card:hover img{transform:scale(1.05)}
}
@media (prefers-reduced-motion:reduce){.card:hover img{transform:none}}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#0b0a09}
.card .body{padding:16px;display:flex;flex-direction:column;gap:7px;flex:1}
.codebadge{display:inline-block;align-self:flex-start;background:var(--accent-soft);border:1px solid var(--accent-dim);color:var(--accent-bright);font-size:.68rem;font-weight:700;letter-spacing:.08em;padding:2px 8px;border-radius:999px}
.badge-new{display:inline-block;background:var(--accent);color:var(--accent-ink);font-size:.68rem;font-weight:700;letter-spacing:.08em;padding:2px 8px;border-radius:999px}
.dlbadge{display:inline-block;background:transparent;border:1px solid var(--line);color:var(--muted);font-size:.66rem;font-weight:700;letter-spacing:.08em;padding:2px 8px;border-radius:999px}
.badge-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 2px;min-height:22px}
.chip-group{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center}
.chip-group-label{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);font-weight:700;margin-right:2px}
.filters-list{display:flex;flex-wrap:wrap;gap:14px 10px;justify-content:center;align-items:center}
.catalog .wrap{max-width:1200px}
.sort-row{display:flex;justify-content:center;align-items:center;margin:0 0 10px}.sort-label{font-size:.86rem;color:var(--muted);margin-right:8px;font-weight:600}
#catalog-sort{padding:9px 14px;min-height:44px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--text);font-size:.86rem;font-family:inherit;cursor:pointer}
#catalog-sort:focus{border-color:var(--accent);outline:none}
#no-results{display:none;text-align:center;padding:48px 16px;color:var(--muted)}
#no-results.show{display:block}
#no-results p{margin-bottom:6px}
#no-results .sug-grid{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:14px}
#no-results .sug{display:block;border:1px solid var(--line);border-radius:12px;padding:12px 16px;background:var(--panel);min-width:200px;max-width:260px;text-decoration:none}
#no-results .sug:hover{border-color:var(--accent)}
#no-results .sug strong{display:block;color:var(--text);font-size:.9rem;line-height:1.35}
#no-results .sug span{display:block;color:var(--muted);font-size:.78rem;margin-top:6px}
.card picture{display:block}
.card h2{font-size:.98rem;line-height:1.35;font-weight:700;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.card a h2{text-decoration-thickness:1px;text-underline-offset:3px}
.price{color:var(--text);font-weight:800;font-variant-numeric:tabular-nums}
.card p.desc{color:var(--muted);font-size:.85rem;flex:0 1 auto;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card p.price{margin-top:auto;padding-top:6px}
.card .row{display:flex;gap:10px;padding:0 16px 16px}
.btn{display:inline-block;background:linear-gradient(180deg,var(--accent-bright),var(--accent));color:var(--accent-ink);font-weight:700;padding:10px 18px;border-radius:var(--radius-sm);text-align:center;font-size:.88rem;flex:1;transition:transform .16s var(--ease)}
.btn:hover{transform:translateY(-1px);text-decoration:none}.card .row .btn{min-height:44px;display:inline-flex;align-items:center;justify-content:center}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--line)}
.btn.ghost:hover{border-color:var(--accent-dim);color:var(--accent-bright)}
footer.site{border-top:1px solid var(--line);background:var(--bg-soft);padding:24px 0;color:var(--muted);font-size:.82rem}
footer.site .wrap{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px 16px}
footer.site a{color:var(--muted);margin-left:14px}
footer.site a:hover{color:var(--accent-bright)}
.skip{position:absolute;left:-9999px;top:0;background:var(--accent);color:var(--accent-ink);padding:10px 18px;font-weight:700;z-index:200;border-radius:0 0 8px 0}
.skip:focus{left:0}
.result-count{color:var(--muted);font-size:.86rem;text-align:center;margin:4px 0 0}
.hidden{display:none!important}
.reveal-row{display:flex;justify-content:center;margin:26px 0 8px}
#backtop{position:fixed;right:22px;bottom:calc(22px + env(safe-area-inset-bottom, 0px));width:46px;height:46px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--accent);font-size:1.3rem;cursor:pointer;opacity:0;pointer-events:none;transition:opacity .2s var(--ease);z-index:150}
#backtop.show{opacity:1;pointer-events:auto}
#backtop:hover{border-color:var(--accent-dim)}
@media(prefers-reduced-motion:reduce){#backtop{display:none}}
@media(max-width:640px){.filters{overflow-x:auto;flex-wrap:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none;-webkit-mask-image:linear-gradient(90deg,#000 92%,transparent);mask-image:linear-gradient(90deg,#000 92%,transparent)}
.filters::-webkit-scrollbar{display:none}
nav.main a:not(:last-child){display:none}footer.site .wrap{justify-content:center;text-align:center}footer.site a{margin:0 7px}.desc{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{transition:none!important;animation:none!important}a:focus-visible,.btn:focus-visible,.chip:focus-visible,nav.main a:focus-visible{transform:none!important}}

  h1,h2{text-wrap:balance}
@media print{
header.site,footer.site,nav,.nav-toggle,#backtop,.sticky-buy,.filters,.proof-strip,.sort,.search{display:none!important}
:root{--bg:#fff;--bg-soft:#fff;--panel:#fff;--panel2:#fff;--text:#141414;--muted:#333;--faint:#555;--line:#d4d4d4;--line-soft:#e8e8e8}
body{background:#fff!important;color:#141414!important}
.wrap{max-width:none!important}
a{color:#8a3a20!important;text-decoration:underline!important}}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<a class="skip" href="#filters" id="skip-filters">Skip to filters</a>
<header class="site"><div class="wrap">
<a class="logo" href="../">
<svg width="24" height="24" viewBox="0 0 26 26" fill="none" aria-hidden="true" focusable="false"><circle cx="5" cy="6" r="2.4" fill="#e07a5f"/><circle cx="21" cy="6" r="2.4" fill="#e07a5f"/><circle cx="13" cy="13" r="2.4" fill="#e07a5f"/><circle cx="5" cy="20" r="2.4" fill="#e07a5f"/><circle cx="21" cy="20" r="2.4" fill="#e07a5f"/><path d="M6.6 7.4L11.2 11.8M19.4 7.4L14.8 11.8M6.6 18.6L11.2 14.2M19.4 18.6L14.8 14.2" stroke="#e07a5f" stroke-width="1.4"/></svg>
ghostcorpnet</a>
<nav class="main" aria-label="Primary"><a href="./" aria-current="page">Catalog</a><a href="../">Home</a><a href="../brands/">Stores</a><a href="../ecosystem/">Ecosystem</a><a href="../directory/">Directory</a><a href="../build/">Build</a><a href="../articles/">Articles</a><a href="../changelog.html">Changelog</a><a href="../#faq">FAQ</a></nav>
</div></header>
<main id="main" class="catalog" tabindex="-1">
<div class="wrap hero">
<h1>Catalog</h1>
<p class="lede">Every self-serve product in the ghostcorpnet library — playbooks, checklists, runbooks, kits, and working code for governing AI agents. Buy once, download instantly.</p>
<p class="secure-checkout">Secure checkout via Gumroad · Instant delivery</p>
</div>
<div class="wrap"><p class="result-count" id="result-count" aria-live="polite">__COUNT__</p><search class="catalog-search-row"><label for="catalog-search" class="visually-hidden">Search products</label><input id="catalog-search" type="search" autocomplete="off" spellcheck="false" enterkeyhint="search" aria-keyshortcuts="/" placeholder="Search products… ( / )"><kbd class="search-kbd" aria-hidden="true">/</kbd></search><div class="sort-row"><label for="catalog-sort" class="sort-label">Sort:</label><select id="catalog-sort" aria-label="Sort products"><option value="new">Newest</option><option value="az">Title: A to Z</option><option value="lo">Price: low to high</option><option value="hi">Price: high to low</option></select></div><noscript><style>.catalog-search-row,.sort-row{display:none}</style><p class="lede sub">The full catalog is listed below — search and sort need JavaScript.</p></noscript><p class="tier-legend">9 Starter · 9 Core · 9–99 Premium</p><div class="filters" id="filters" role="region" tabindex="-1" aria-label="Filter products" aria-describedby="filters-note" data-collapsed="false"><button type="button" class="filters-toggle" aria-expanded="true" aria-controls="filters-list"><span>Filter products</span><span class="ft-chev" aria-hidden="true">▾</span></button><div class="filters-list" id="filters-list"></div></div><p class="visually-hidden" id="filters-note">Choosing filters updates the product count announced by the results region.</p></div>
<div class="wrap"><ul class="grid" id="grid">
__CARDS__
</ul><div class="reveal-row"><button class="btn ghost" id="show-more" type="button">Show more</button></div><div id="no-results" role="status"><p>Nothing matches that combination — try fewer filters or different keywords.</p><p><button class="chip" id="clear-filters" type="button" style="margin-top:12px">Clear filters</button></p><div class="sug-grid" id="no-results-sug"></div></div></div>
<button id="backtop" aria-label="Back to top">↑</button>
</main>
<footer class="site"><div class="wrap">
<span>© <span id="yr">2026</span> GhostCorp · ghostcorpnet · An independent studio</span>
<span><a href="mailto:corpghost420@gmail.com">Contact</a><a href="../articles/">Articles</a><a href="../changelog.html">Changelog · Oct 2026</a><a href="../brands/">Stores</a><a href="../ecosystem/">Ecosystem</a><a href="../directory/">Directory</a><a href="../build/">Build</a><a href="../sitemap.xml">Sitemap</a><a href="../admin-login.html" rel="nofollow">Admin</a></span>
</div></footer>
<script>
const grid=document.getElementById('grid'),filters=document.getElementById('filters'),rc=document.getElementById('result-count');const filtersList=document.getElementById('filters-list');
const noResults=document.getElementById('no-results');
const noResultsSug=document.getElementById('no-results-sug');
const POPULAR_SUGS=[['The Playbook — Studio Edition','the-playbook-studio-edition/','$29 · the flagship playbook'],['AI Agent Risk Audit Kit','ai-agent-risk-audit-kit/','$19 · audit any agent deployment'],['Agent Incident Response Runbook','agent-incident-response-runbook/','$19 · respond to agent incidents']];
const renderNoResultsSug=()=>{if(!noResultsSug||noResultsSug.childNodes.length)return;noResultsSug.innerHTML=POPULAR_SUGS.map(s=>'<a class="sug" href="'+s[1]+'"><strong>'+s[0]+'</strong><span>'+s[2]+'</span></a>').join('')};
const updateCount=()=>{const total=[...grid.querySelectorAll('.card')].length;const v=[...grid.querySelectorAll('.card')].filter(c=>!c.classList.contains('hidden')).length;rc.textContent=v===0?'No products match':(v===1?'1 of '+total+' product':v+' of '+total+' products');if(noResults){noResults.classList.toggle('show',v===0);if(v===0)renderNoResultsSug()}};
const tags=[...new Set([...grid.querySelectorAll('.card')].flatMap(c=>(c.dataset.tags||'').split('|').filter(Boolean)))].sort();
let activeTag='',searchQ='',activePrice=null;
try{var _hp=new URLSearchParams(location.hash.slice(1));activeTag=_hp.get('tag')||'';searchQ=_hp.get('q')||'';if(!searchQ){try{searchQ=new URLSearchParams(location.search).get('q')||''}catch(_e){}}}catch(e){}
// Sync filter/search/sort state to the URL hash so catalog views are shareable.
const syncHash=()=>{try{const p=new URLSearchParams();if(activeTag)p.set('tag',activeTag);if(searchQ)p.set('q',searchQ);if(activePrice)p.set('pr',PRICE_RANGES.indexOf(activePrice));const ss=document.getElementById('catalog-sort');if(ss&&ss.value&&ss.value!=='new')p.set('sort',ss.value);const s=p.toString();history.replaceState(null,'',s?('#'+s):location.pathname+location.search);}catch(e){}};
const REVEAL_STEP=40;let revealed=40;
const isFiltering=()=>activeTag!==''||searchQ!==''||activePrice!==null;
const updateShowMore=()=>{const sm=document.getElementById('show-more');if(!sm)return;const total=[...grid.querySelectorAll('.card')].length;const rest=total-revealed;const show=!isFiltering()&&rest>0;sm.classList.toggle('hidden',!show);if(show)sm.textContent='Show more ('+rest+' more)';};
const applyFilters=()=>{const cards=[...grid.querySelectorAll('.card')];let vis=0;cards.forEach(c=>{const t=(c.dataset.tags||'').split('|').filter(Boolean);const okT=activeTag===''||t.includes(activeTag);const h2=c.querySelector('h2');const dsc=c.querySelector('.desc');const hay=((h2&&h2.textContent)||'')+' '+((dsc&&dsc.textContent)||'');const okQ=searchQ===''||hay.toLowerCase().includes(searchQ);const pr=parseFloat(c.dataset.price||'0');const okP=!activePrice||(pr>=activePrice.min&&pr<=activePrice.max);let show=okT&&okQ&&okP;if(show&&!isFiltering()){vis++;show=vis<=revealed;}c.classList.toggle('hidden',!show)});updateCount();updateShowMore();syncHash()};
const tagCounts={};[...grid.querySelectorAll('.card')].forEach(c=>{(c.dataset.tags||'').split('|').filter(Boolean).forEach(t=>{tagCounts[t]=(tagCounts[t]||0)+1})});
const mk=(label,tag)=>{const b=document.createElement('button');b.className='chip'+(tag===activeTag?' active':'');b.textContent=label;b.setAttribute('aria-pressed',String(tag===activeTag));const n=tag===''?grid.querySelectorAll('.card').length:(tagCounts[tag]||0);if(tag===''){b.setAttribute('aria-label','Show all '+n+' products')}else{b.setAttribute('aria-label','Show '+n+' '+label+(n===1?'':'s'))}const badge=document.createElement('span');badge.className='chip-count';badge.setAttribute('aria-hidden','true');badge.textContent=' · '+n;b.appendChild(badge);b.onclick=()=>{activeTag=tag;document.querySelectorAll('.chip').forEach(x=>{x.classList.remove('active');x.setAttribute('aria-pressed','false')});b.classList.add('active');b.setAttribute('aria-pressed','true');applyFilters()};return b};
filtersList.appendChild(mk('All',''));
const FORMAT_TAGS=new Set(['playbook','runbook','kit','checklist','template','templates','policy-template','code','tool','interactive-tool','bundle','pack','collection','quiz','assessment','readiness-assessment','prompts','prompt-pack','dataset','csv','spreadsheet','worksheet','worksheets','audiobook','audio','audio-briefing','powerpoint','presentation','board-deck','compliance-kit','policy-generator','cost-calculator']);
const PRICE_RANGES=[{label:'$19 and under',min:0,max:19},{label:'$29 \u2013 $49',min:29,max:49},{label:'$50 and up',min:50,max:Infinity}];
const fmt=tags.filter(t=>FORMAT_TAGS.has(t));
const top=tags.filter(t=>!FORMAT_TAGS.has(t));
const grp=(label,list)=>{const s=document.createElement('span');s.className='chip-group';const h=document.createElement('span');h.className='chip-group-label';h.textContent=label;s.appendChild(h);list.forEach(t=>s.appendChild(mk(t.replace(/-/g,' '),t)));return s};
if(fmt.length)filtersList.appendChild(grp('Format',fmt));
if(top.length)filtersList.appendChild(grp('Topic',top));
const priceRow=document.createElement('span');priceRow.className='chip-group';priceRow.id='price-row';
const pLab=document.createElement('span');pLab.className='chip-group-label';pLab.textContent='Price';priceRow.appendChild(pLab);
const mkp=(r)=>{const b=document.createElement('button');b.className='chip';b.textContent=r.label;b.setAttribute('aria-pressed','false');const cnt=[...grid.querySelectorAll('.card')].filter(c=>{const p=parseFloat(c.dataset.price||'0');return p>=r.min&&p<=r.max}).length;const cb=document.createElement('span');cb.className='chip-count';cb.setAttribute('aria-hidden','true');cb.textContent=' \u00b7 '+cnt;b.appendChild(cb);b.onclick=()=>{activePrice=(activePrice===r)?null:r;priceRow.querySelectorAll('.chip').forEach(x=>{x.classList.remove('active');x.setAttribute('aria-pressed','false')});if(activePrice){b.classList.add('active');b.setAttribute('aria-pressed','true')}applyFilters()};return b};
PRICE_RANGES.forEach(r=>priceRow.appendChild(mkp(r)));
try{var _pr=new URLSearchParams(location.hash.slice(1)).get('pr');if(_pr!==null&&PRICE_RANGES[+_pr]){activePrice=PRICE_RANGES[+_pr];priceRow.querySelectorAll('.chip').forEach((x,i)=>{if(PRICE_RANGES[i]===activePrice){x.classList.add('active');x.setAttribute('aria-pressed','true')}})}}catch(e){}
filtersList.appendChild(priceRow);
const fToggle=filters.querySelector('.filters-toggle');
if(fToggle){fToggle.addEventListener('click',()=>{const c=filters.dataset.collapsed!=='true';filters.dataset.collapsed=String(c);fToggle.setAttribute('aria-expanded',String(!c));});}
const skipF=document.getElementById('skip-filters');if(skipF){skipF.addEventListener('click',()=>{filters.focus({preventScroll:true})});}
const sq=document.getElementById('catalog-search');
if(sq&&searchQ)sq.value=searchQ;
const smBtn=document.getElementById('show-more');
if(smBtn)smBtn.addEventListener('click',()=>{revealed+=REVEAL_STEP;applyFilters();});
if(sq){sq.addEventListener('input',()=>{searchQ=sq.value.trim().toLowerCase();applyFilters()});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==sq&&!/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)){e.preventDefault();sq.focus()}});
sq.addEventListener('keydown',e=>{if(e.key==='Escape')sq.blur()});}
applyFilters();

// Sort control: re-order cards by data-price / data-date.
const sortSel=document.getElementById('catalog-sort');
const applySort=()=>{if(!sortSel)return;const v=sortSel.value;const cards=[...grid.querySelectorAll('.card')];
cards.sort((a,b)=>{const pa=parseFloat(a.dataset.price||'0'),pb=parseFloat(b.dataset.price||'0');
if(v==='lo')return pa-pb;if(v==='hi')return pb-pa;if(v==='az')return (a.querySelector('h2').textContent||'').localeCompare(b.querySelector('h2').textContent||'');
const da=a.dataset.date||'',db=b.dataset.date||'';
if(da&&!db)return -1;if(!da&&db)return 1;return db.localeCompare(da)});
cards.forEach(c=>grid.appendChild(c));applyFilters();syncHash()};
if(sortSel){try{var _hs=new URLSearchParams(location.hash.slice(1)).get('sort');if(_hs&&['new','az','lo','hi'].indexOf(_hs)>=0)sortSel.value=_hs;}catch(e){}
sortSel.addEventListener('change',applySort);applySort()}

// Clear filters button in the empty state.
const clearBtn=document.getElementById('clear-filters');
if(clearBtn){clearBtn.addEventListener('click',()=>{activeTag='';searchQ='';activePrice=null;sq.value='';
if(sortSel){sortSel.value='new';applySort()}
document.querySelectorAll('#filters .chip').forEach(x=>{x.classList.remove('active');x.setAttribute('aria-pressed','false')});
const all=document.querySelector('#filters .chip');if(all){all.classList.add('active');all.setAttribute('aria-pressed','true')}
applyFilters();sq.focus()})};

// Back-to-top button.
(function(){var b=document.getElementById('backtop');if(!b)return;
function onScroll(){b.classList.toggle('show',window.scrollY>1200)}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
b.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});})();
</script>
<script>document.getElementById('yr').textContent=new Date().getFullYear();</script>
<script>try{{fetch("https://kestrelattice-approvals.koalstin-g-k-delaney.workers.dev/pv?p="+encodeURIComponent(location.pathname),{{mode:"no-cors",keepalive:true}}).catch(function(){{}})}}catch(e){{}}</script>
</body>
</html>
"""

CARD = """<li class="card{reveal}" data-tags="{tags}" data-price="{price_num}" data-date="{pdate}">
<a href="{slug}/" style="text-decoration:none;color:inherit;display:block" aria-label="{title} — {price_label}"><picture><source type="image/webp" srcset="../assets/covers/{pid}.webp"><img src="../assets/covers/{pid}.png" alt="{title} cover" {img_attrs} sizes="(max-width:640px) 100vw, (max-width:1100px) 50vw, 320px"></picture>
<div class="body"><p class="badge-row">{badge_row}</p><h2 translate="no">{title}</h2><p class="desc">{tagline}</p><p class="price"><span class="visually-hidden">USD </span>{price_html}</p></div></a>
<div class="row"><a class="btn" href="{url}" target="_blank" rel="noopener">Get it<span class="visually-hidden">(opens in new tab)</span></a><a class="btn ghost" href="{slug}/" aria-label="Details: {title}">Details</a></div>
</li>
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

ORIGINALS_DATE = "2026-09-29"  # flagship launch date (publish records); micros carry created_at per listing

NEW_BADGE_DAYS = 2  # "New" badge window. The whole catalog launched within
                    # days, so a 14-day window would badge every card and make
                    # the badge meaningless. 2 days (last 48h of launches) keeps
                    # it selective and truthful (real publish dates only, never
                    # fake). As the catalog ages, the badge naturally thins out.

def pdate(p, datemap):
    """Product publish date (YYYY-MM-DD) from listing created_at, or ORIGINALS_DATE
    for the 8 flagships, or '' when unknown."""
    if p["id"] in datemap:
        return datemap[p["id"]]
    if p["id"] in ORIGINALS_SLUGS:
        return ORIGINALS_DATE
    return ""

def is_new(p, datemap):
    """True when the product published <NEW_BADGE_DAYS days ago (real date field only)."""
    d = pdate(p, datemap)
    if not d:
        return False
    try:
        return (date.today() - date.fromisoformat(d)).days < NEW_BADGE_DAYS
    except ValueError:
        return False

def main():
    prods = products()
    # tag lookup from pending-listings for filtering
    tagmap = {}
    datemap = {}
    formatmap = {}
    # Deliverable-format badge labels keyed by the extension of the actual file
    # uploaded at publish time (pending-listings pdf_path). The Gumroad API
    # product scan carries NO format field (file_info empty for 327/335 live
    # products as of 2026-10-04), so the publish ledger's recorded upload file
    # is the real per-product source. Same keyed-by-pid pattern as tagmap /
    # datamap. NEVER infer format from titles/taglines — no ledger entry or
    # unknown extension means the generic badge stays.
    FORMAT_BADGE = {".pdf": "PDF DOWNLOAD", ".pptx": "PPTX DOWNLOAD",
                    ".mp3": "AUDIO DOWNLOAD", ".html": "HTML TOOL",
                    ".csv": "CSV DATASET", ".zip": "ZIP DOWNLOAD",
                    ".docx": "DOCX DOWNLOAD", ".xlsx": "XLSX DOWNLOAD",
                    ".md": "MD DOWNLOAD"}
    pj = os.path.expanduser("~/workspace/goals/kestrelattice-autonomous-growth/hidden_files/marketplace/pending-listings.jsonl")
    if os.path.exists(pj):
        with open(pj) as f:
            for line in f:
                try:
                    p = json.loads(line)
                    pid = p["gumroad_url"].rstrip("/").split("/")[-1]
                    tagmap[pid] = [t.lower().replace(" ", "-") for t in p.get("tags", [])[:6]]
                    datemap[pid] = str(p.get("created_at", ""))[:10]
                    ext = os.path.splitext(str(p.get("pdf_path") or p.get("file_path") or "").lower())[1]
                    if ext in FORMAT_BADGE:
                        formatmap[pid] = FORMAT_BADGE[ext]
                except Exception:
                    pass
    # default card order = newest first (matches the sort control's default)
    ordered = sorted(sorted(prods, key=lambda x: (float(x["price"]), x["title"])),
                     key=lambda x: pdate(x, datemap), reverse=True)
    cards = []
    for n, p in enumerate(ordered, 1):
        pid = p["id"]
        # LCP: only the first (above-the-fold) card image loads eagerly with high
        # priority; the rest stay lazy per the one-high-priority-image standard.
        img_attrs = ' fetchpriority="high"' if n == 1 else ' loading="lazy" fetchpriority="low" decoding="async"'
        ptaglist = tagmap.get(pid, ["governance"])
        tags = "|".join(ptaglist)
        badges = []
        if is_new(p, datemap):
            badges.append('<span class="badge-new">New</span>')
        if "code" in ptaglist:
            badges.append('<span class="codebadge">CODE</span>')
        _fmt_badge = formatmap.get(pid, "DIGITAL DOWNLOAD")
        badges.append('<span class="dlbadge">' + _fmt_badge + '</span>')
        badge_row = "".join(badges)
        reveal = "" if n <= 40 else " hidden reveal-capped"
        _fmt = fmt_price(p["price"])
        _is_free = float(p["price"]) == 0
        cards.append(CARD.format(
            reveal=reveal,
            pid=html.escape(pid),
            title=html.escape(p["title"]),
            tagline=html.escape(fix_tagline(p.get("tagline", ""))),
            price_label="Free" if _is_free else "$" + _fmt,
            price_html='<span translate="no">Free</span>' if _is_free else (
                '<span translate="no"><span aria-hidden="true">$</span>' + html.escape(_fmt) +
                '</span> <span style="color:var(--muted);font-weight:400;font-size:.85rem">one-time · instant delivery</span>'),
            price_num=float(p["price"]),
            pdate=html.escape(pdate(p, datemap)),
            url=f"https://koalstin.gumroad.com/l/{html.escape(pid)}",
            tags=html.escape(tags),
            slug=SLUG_OVERRIDES.get(pid, ORIGINAL_SLUGS.get(pid, slugify(p["title"]))),
            img_attrs=img_attrs,
            badge_row=badge_row,
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
            }} for n, p in enumerate(ordered, 1)
        ],
    }
    first_pid = ordered[0]["id"] if ordered else ""
    preload = (f'<link rel="preload" as="image" href="../assets/covers/{html.escape(first_pid)}.webp" '
               f'imagesrcset="../assets/covers/{html.escape(first_pid)}.webp" '
               f'imagesizes="(max-width:640px) 100vw, (max-width:1100px) 50vw, 320px">') if first_pid else ""
    page = PAGE.replace("__PRELOAD__", preload).replace("__ITEMLIST__", json.dumps(itemlist, ensure_ascii=False, indent=2))
    # tier legend computed from live product data — never hardcoded
    n_free = sum(1 for p in prods if float(p["price"]) == 0)
    n_mini = sum(1 for p in prods if 0 < float(p["price"]) < 19)
    n_starter = sum(1 for p in prods if 19 <= float(p["price"]) <= 29)
    n_core = sum(1 for p in prods if 30 <= float(p["price"]) <= 49)
    n_premium = sum(1 for p in prods if float(p["price"]) >= 50)
    tier_legend = f"Full catalog: {n_starter} Starter · {n_core} Core · {n_premium} Premium"
    if n_mini:
        tier_legend += f" · {n_mini} Mini"
    if n_free:
        tier_legend += f" · {n_free} Free"
    import re as _re
    page = _re.sub(r'<p class="tier-legend">.*?</p>',
                  f'<p class="tier-legend">{tier_legend}</p>', page, count=1)
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

    # ecosystems index entry (idempotent)
    eco_entry = f"""  <url>
    <loc>{BASE_URL}/ecosystems/</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    if "/ecosystems/</loc>" not in content:
        content = content.replace("</urlset>", eco_entry + "</urlset>")
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
