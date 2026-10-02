#!/usr/bin/env python3
"""Generate one SEO product detail page per live product at products/<slug>/.

Reads marketplace/pending-listings.jsonl (micros) + ORIGINALS (flagships),
extracts "What's inside" from the matching manuscript's ## headings,
renders a branded page with Product JSON-LD, buy CTA, related products,
and registers every page in sitemap.xml. Idempotent.
"""
import datetime
import html, json, os, re, struct, subprocess


def png_dims(path):
    """Return (width, height) of a PNG via its IHDR chunk; None on failure."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        return struct.unpack(">II", head[16:24])
    except OSError:
        return None


def page_lastmod(path):
    """Last-mod date (YYYY-MM-DD) for a site file: real git commit date, mtime fallback."""
    try:
        d = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path],
                           cwd=SITE, capture_output=True, text=True,
                           timeout=20).stdout.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return d
    except Exception:
        pass
    try:
        return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    except OSError:
        return datetime.date.today().isoformat()


GOAL_DIR = os.path.expanduser("~/workspace/goals/kestrelattice-autonomous-growth")
_ASSET_EXTS = {".pdf", ".xlsx", ".docx", ".mp3", ".html", ".zip", ".pptx", ".md", ".txt", ".csv"}


def pdf_page_count(path):
    """Real page count parsed from the PDF's own page tree; None when unreadable. Never invented."""
    try:
        with open(path, "rb") as f:
            d = f.read(4000000)
    except OSError:
        return None
    try:
        # Primary: Catalog object -> its /Pages reference -> that object's /Count.
        m = re.search(rb"(\d+)\s+0\s+obj\b.{0,600}?/Type\s*/Catalog", d, re.S)
        if m:
            seg = d[m.start():m.start() + 1500]
            pm = re.search(rb"/Pages\s+(\d+)\s+0\s+R", seg)
            if pm:
                pn = pm.group(1)
                om = re.search(rb"(?<![0-9])" + pn + rb"\s+0\s+obj\b", d)
                if om:
                    cm = re.search(rb"/Count\s+(\d+)", d[om.start():om.start() + 3000])
                    if cm:
                        return int(cm.group(1))
        # Fallback: largest /Count on any /Pages (not /Page) node = root total.
        counts = [int(x) for x in re.findall(rb"/Type\s*/Pages\b.{0,400}?/Count\s+(\d+)", d, re.S)]
        return max(counts) if counts else None
    except Exception:
        return None


def build_asset_index():
    """Map filename stem -> full path for every deliverable asset under the goal. First hit wins.

    Two passes: PDFs first (the actual Gumroad deliverable), then other formats fill
    gaps — a stem with both a .md manuscript and a .pdf resolves to the PDF."""
    idx = {}
    roots = (os.path.join(GOAL_DIR, "hidden_files", "approvals"),
             os.path.join(GOAL_DIR, "hidden_files", "products"))
    for pass_exts in ((".pdf",), tuple(e for e in _ASSET_EXTS if e != ".pdf")):
        for root in roots:
            for dirpath, _dirnames, filenames in os.walk(root):
                for fn in filenames:
                    stem, ext = os.path.splitext(fn)
                    if ext.lower() in pass_exts and stem not in idx:
                        idx[stem] = os.path.join(dirpath, fn)
    return idx


def file_facts_line(pr, pack_file_path, asset_idx):
    """Small 'FORMAT · size · pages' line from the real asset; '' when no asset found (never guess)."""
    path = None
    if pack_file_path:
        cand = pack_file_path if os.path.isabs(pack_file_path) else os.path.join(GOAL_DIR, pack_file_path)
        if os.path.isfile(cand):
            path = cand
    if not path:
        for key in (pr.get("slug", ""), pr.get("gid", "")):
            if key and key in asset_idx:
                path = asset_idx[key]
                break
    if not path:
        return ""
    try:
        size = os.path.getsize(path)
    except OSError:
        return ""
    ext = os.path.splitext(path)[1].lower().lstrip(".").upper() or "FILE"
    size_s = f"{size / 1048576:.1f} MB" if size >= 1048576 else f"{max(1, round(size / 1024))} KB"
    if ext == "PDF":
        pages = pdf_page_count(path)
        pages_s = f" · {pages} pages" if pages else ""
        return f'<p class="file-facts">{ext} · {size_s}{pages_s}</p>'
    return f'<p class="file-facts">{ext} · {size_s}</p>'


def loc_to_file(loc):
    """Map a sitemap <loc> to its local file path; None if unknown."""
    if not loc.startswith(BASE_URL):
        return None
    rel = loc[len(BASE_URL):].lstrip("/")
    if not rel:
        return os.path.join(SITE, "index.html")
    if rel.endswith("/"):
        return os.path.join(SITE, rel, "index.html")
    return os.path.join(SITE, rel)


def refresh_sitemap_lastmods():
    """Rewrite every <lastmod> in sitemap.xml from real git/mtime dates. Never touches <loc>."""
    sm_path = os.path.join(SITE, "sitemap.xml")
    sm = open(sm_path).read()
    def repl(m):
        loc = m.group(1)
        f = loc_to_file(loc)
        if f and os.path.exists(f):
            return f"<loc>{loc}</loc><lastmod>{page_lastmod(f)}</lastmod>"
        return m.group(0)
    new = re.sub(r"<loc>([^<]+)</loc>\s*<lastmod>[^<]*</lastmod>",
                 lambda m: repl(m), sm)
    if new != sm:
        open(sm_path, "w").write(new)
        print("sitemap: lastmod refreshed from real file dates")
    return new != sm

SITE = os.path.expanduser("~/workspace/kestrelattice")
HIDDEN = os.path.expanduser("~/workspace/goals/kestrelattice-autonomous-growth/hidden_files")
BASE_URL = "https://koalstingkdelaney-gif.github.io/kestrelattice"

_BOILER = ("A complete, zero-placeholder template for teams governing AI agents in production: "
           "policy gates, audit trails, cost controls.")

def fix_tagline(t):
    """Repair truncated boilerplate taglines (micro-forge sometimes cuts them mid-word)."""
    t = t or ""
    if "A complete, zero-placeholder" in t and "cost controls." not in t:
        t = re.sub(r"A complete, zero-placeholder.*$", _BOILER, t)
    t = t.replace(
        "A complete, zero-placeholder draft for teams governing AI agents in production: policy gates, audit trails, cost controls.",
        _BOILER)
    return t.replace(" -- ", " \u2014 ")

def fmt_price(p):
    f = float(p)
    return str(int(f)) if f.is_integer() else str(f)

def trunc_meta(text, limit=160):
    """Truncate a meta description at a word boundary so it never cuts mid-word."""
    text = text or ""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "\u2026"

ORIGINALS = [
    ("hdigmr", "the-playbook-studio-edition", "The Playbook \u2014 Studio Edition", 29,
     "The governed-agent playbook: policies, schemas, and rollout in one PDF.",
     ["The 9-chapter governed agent mesh system", "Fill-in policy templates (6)", "JSON schemas for grants, tiers, and audit events",
      "Vendor/model matrix", "14-day rollout plan", "Final acceptance checklist"]),
    ("sahva", "ai-agent-risk-audit-kit", "AI Agent Risk Audit Kit", 19,
     "Scored risk-tier self-assessment and 40-point audit checklist.",
     ["Risk-tier self-assessment scoring", "40-point audit checklist", "Tier assignment worksheet", "Remediation planner"]),
    ("jbngbu", "agent-incident-response-runbook", "Agent Incident Response Runbook", 19,
     "Severity levels, triage procedures, kill-switch checklists.",
     ["Severity level definitions", "Triage procedures", "Kill-switch checklists", "Post-incident review template"]),
    ("slexhv", "100-agent-use-cases-pre-tiered", "100 Agent Use Cases, Pre-Tiered", 19,
     "100 concrete use cases, each pre-tiered with key controls.",
     ["100 concrete agent use cases", "Pre-assigned risk tiers", "Key controls per use case", "Adoption prioritization guide"]),
    ("cjdkuu", "prompt-injection-defense-field-guide", "Prompt Injection Defense Field Guide", 19,
     "15 attack scenarios, 6 layered defenses, 20 test prompts.",
     ["15 attack scenarios", "6 layered defenses", "20 test prompts", "Detection checklist"]),
    ("ilxccs", "agent-cost-control-workbook", "Agent Cost Control Workbook", 19,
     "Budget worksheets, metering setup, kill-on-overspend rules.",
     ["Budget worksheets", "Metering setup guide", "Kill-on-overspend rules", "Cost attribution templates"]),
    ("fdtkdd", "quarterly-access-review-kit", "Quarterly Access Review Kit", 19,
     "Re-tier every agent against what it can actually touch today.",
     ["Access review runbook", "Re-tiering worksheet", "Grant inventory template", "Review sign-off pack"]),
    ("yzbumc", "complete-kestrelattice-library", "The Complete ghostcorpnet Library", 79,
     "Every ghostcorpnet PDF in one bundle.",
     ["The Playbook \u2014 Studio Edition ($29)", "All the $19 kits and guides", "Every micro-product released to date", "Free updates as the library grows"]),
]

def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return re.sub(r"-+", "-", s)

def load_packs():
    """Micro-product records: pending-listings.jsonl + pending-packs.jsonl (merged,
    same as build-covers.products()). pending-packs.jsonl may not exist yet."""
    packs = []
    for fname in ("pending-listings.jsonl", "pending-packs.jsonl"):
        path = os.path.join(HIDDEN, "marketplace", fname)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    packs.append(json.loads(line))
    return packs

def manuscripts():
    d = os.path.join(HIDDEN, "products", "micro", "2026-09-29")
    out = {}
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".md"):
                out[fn[:-3]] = os.path.join(d, fn)
    return out

def pack_slug_by_title():
    """pack.json title -> manifest name (matches directory site_path)."""
    d = os.path.join(HIDDEN, "products", "packs-2026-09-30")
    out = {}
    if os.path.isdir(d):
        for slug in os.listdir(d):
            pj = os.path.join(d, slug, "pack.json")
            if os.path.isfile(pj):
                try:
                    m = json.load(open(pj))
                    out[m.get("title", "")] = m.get("name", slug)
                except Exception:
                    pass
    return out


def pack_manuscripts():
    """manifest name slug -> manuscript.md path for the pack-builder wave."""
    d = os.path.join(HIDDEN, "products", "packs-2026-09-30")
    out = {}
    if os.path.isdir(d):
        for slug in os.listdir(d):
            mp = os.path.join(d, slug, "manuscript.md")
            if os.path.isfile(mp):
                out[slug] = mp
    return out


def best_manuscript(title, mans):
    tw = set(re.findall(r"[a-z0-9]+", title.lower())) - {"the", "a", "an", "for", "and", "of", "to"}
    best, best_score = None, 0
    for slug, path in mans.items():
        sw = set(slug.replace("-", " ").split())
        score = len(tw & sw)
        if score > best_score:
            best, best_score = path, score
    return best if best_score >= 2 else None

def headings_of(path):
    heads = []
    with open(path) as f:
        for line in f:
            m = re.match(r"##\s+\**(.+?)\**\s*$", line.strip())
            if m:
                h = re.sub(r"\*+", "", m.group(1)).strip()
                h = re.sub(r"^\d+[\.\)]\s*", "", h)
                if h and len(heads) < 12:
                    heads.append(h)
    return heads

def esc(s):
    return html.escape(s or "")


def load_brand_title_map():
    """Exact launch-title (lowercased) -> brand dict, from brands.json.

    Same rule as admin panel v2: exact-title match only, no guessing."""
    path = os.path.join(HIDDEN, "brands", "brands.json")
    if not os.path.exists(path):
        return {}
    m = {}
    for b in json.load(open(path)):
        for p in b.get("products", []):
            m[str(p.get("title", "")).strip().lower()] = b
    return m


def studio_block(pr, title_map):
    """'More from this studio' cross-link to the brand's store page.

    Only when the product title exactly matches a brand launch title.
    No match -> no block, never guess."""
    b = title_map.get((pr["title"] or "").strip().lower()) if title_map else None
    if not b:
        return ""
    return (
        '  <section style="border:1px solid var(--line);border-radius:12px;'
        'padding:24px;background:#1c1a18">\n'
        '    <h2 style="margin-top:0">More from this studio</h2>\n'
        f'    <p>This product is part of <strong>{esc(b["display"])}</strong> — '
        f'{esc(b["tagline"])} A bot-run micro-brand of the ghostcorpnet fleet.</p>\n'
        f'    <p><a class="btn" href="../../brands/{b["name"]}/">'
        f'Browse the {esc(b["display"])} store</a></p>\n'
        '  </section>')


def load_ladder():
    """gumroad_id -> {title, tier, site_page, gumroad_url, next_step_up{...}|None, note}"""
    path = os.path.expanduser(
        "~/workspace/goals/kestrelattice-autonomous-growth/ecosystem/ladder-map.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        m = json.load(f)
    return {p["gumroad_id"]: p for p in m.get("products", [])}


def next_step_block(pr, ladder):
    """HTML for the 'Next step up the ladder' cross-sell block (ecosystem layer 1).
    Reads from ladder-map.json. Never alters buy links, prices, or checkout."""
    info = ladder.get(pr["gid"]) if ladder else None
    if not info:
        return ""  # not in the ladder map: render nothing rather than guess
    nxt = info.get("next_step_up")
    if nxt:
        title, gurl = esc(nxt["title"]), nxt.get("gumroad_url")
        up_slug = nxt["site_page"].rstrip("/").split("/")[-1]
        price = nxt["price_usd"]
        ptxt = f"${int(price)}" if float(price).is_integer() else f"${price}"
        checkout = (f'    <p style="color:var(--muted);font-size:.9rem">Or go straight to checkout: '
                    f'<a style="color:var(--accent)" href="{gurl}" target="_blank" rel="noopener" aria-label="Buy {esc(title)} on Gumroad (opens in new tab)">Buy {title} on Gumroad</a></p>\n'
                    if gurl else
                    f'    <p style="color:var(--muted);font-size:.9rem">{title} is publishing now — check back shortly.</p>\n')
        return (
            '  <section style="border:1px solid var(--line);border-radius:12px;'
            'padding:24px;background:#1b1916">\n'
            '    <h2 style="margin-top:0">Next step up the ladder</h2>\n'
            f'    <p>Done with this one? <strong>{title}</strong> ({ptxt}) takes '
            'it one rung further — the next step up in the ghostcorpnet ladder.</p>\n'
            f'    <p><a class="btn" href="../{up_slug}/">'
            f'See {title} — {ptxt}</a></p>\n'
            f'{checkout}'
            '  </section>')
    # top rung ($299): point to the ecosystem ladder + Layer 3 preview
    return (
        '  <section style="border:1px solid var(--accent);border-radius:12px;'
        'padding:24px;background:#1e1a16">\n'
        '    <h2 style="margin-top:0">You\'re at the top of the ladder</h2>\n'
        '    <p>This is the top rung of the ghostcorpnet product ladder. Coming next: '
        'the "Built on ghostcorpnet" certification and the third-party pack directory — '
        '<a style="color:var(--accent)" href="../../ecosystem/">see the whole ecosystem</a>.</p>\n'
        '  </section>')

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} — ghostcorpnet</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="product">
<meta property="og:title" content="{title} — ghostcorpnet">
<meta property="og:description" content="{meta}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="https://koalstingkdelaney-gif.github.io/kestrelattice/assets/covers/{gid}.png">
{og_dims}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} — ghostcorpnet">
<meta name="twitter:description" content="{meta}">
<meta name="twitter:image" content="https://koalstingkdelaney-gif.github.io/kestrelattice/assets/covers/{gid}.png">
<meta name="twitter:image:alt" content="{title} — cover art">
<script type="application/ld+json">
{jsonld}
</script>
<script type="application/ld+json">
{breadcrumblist}
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-541TCHWW98"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-541TCHWW98');
</script>
<style>
  :root{{color-scheme:dark;--bg:#121212; --panel:#1c1a18; --line:#332e26; --text:#e8e2d8;
        --muted:#9a917f; --accent:#e07a5f; --accent-dim:#b9634b;}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg);color:var(--text);
       font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
       line-height:1.7}}
  .wrap{{max-width:960px;margin:0 auto;padding:40px 24px 64px}}
  .brand{{display:flex;align-items:center;gap:10px;font-weight:700;margin-bottom:8px;
         color:var(--text);text-decoration:none}}
  .crumb{{color:var(--muted);font-size:.85rem;margin-bottom:24px}}
  .crumb a{{color:var(--accent);text-decoration:none}}
  .crumb ol{{list-style:none;display:flex;gap:8px;flex-wrap:wrap;margin:0;padding:0}}
  .crumb li+li::before{{content:"·";margin-right:8px;color:var(--muted)}}
  .crumb li[aria-current="page"]{{color:var(--muted)}}
  .crumb .esc-hint{{color:var(--muted);opacity:.65;font-size:.72rem;border:1px solid var(--line);border-radius:4px;padding:0 5px;margin-left:4px;font-family:inherit}}
  .hero{{display:grid;grid-template-columns:280px 1fr;gap:32px;margin:8px 0 40px}}
  @media(max-width:640px){{.hero{{grid-template-columns:1fr}}}}
  .hero img{{width:100%;border-radius:12px;border:1px solid var(--line)}}
  h1{{font-size:1.9rem;line-height:1.25;margin-bottom:8px;text-wrap:balance}}
  p[itemprop="description"]{{text-wrap:pretty}}
  .tagline{{color:var(--muted);font-size:1.05rem;margin-bottom:20px}}
  .price{{font-size:1.6rem;color:var(--accent);font-weight:700;margin-bottom:6px}}
  .instant{{color:var(--muted);font-size:.85rem;margin-bottom:20px}}
  .file-facts{{color:var(--muted);font-size:.85rem;margin:-12px 0 20px}}
  .facts{{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 4px}}
  .fact{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 14px;font-size:.86rem;color:var(--muted)}}
  .fact b{{color:var(--text)}}
  a:focus-visible,button:focus-visible{{outline:3px solid var(--accent);outline-offset:3px;border-radius:4px}}
  .pdp-sticky{{display:none}}
  .pdp-sticky span{{font-size:.85rem;color:var(--muted)}}
  .pdp-sticky span b{{color:var(--text)}}
  .pdp-sticky .btn{{padding:10px 20px;font-size:.88rem}}
  .pdp-sticky .soon{{color:var(--muted);font-size:.85rem}}
  @media(max-width:640px){{.pdp-sticky{{display:flex;position:sticky;bottom:0;z-index:120;background:rgba(26,23,20,.97);border-top:1px solid var(--line);padding:10px 16px calc(10px + env(safe-area-inset-bottom));align-items:center;justify-content:space-between;gap:12px}}}}
  @media (prefers-reduced-motion:reduce){{.pdp-sticky{{transition:none}}}}@media (prefers-reduced-motion:no-preference){{a:focus-visible,button:focus-visible{{transition:transform .15s ease}}a:focus-visible{{transform:scale(1.03)}}.btn:active{{transform:scale(.98)}}}}
  @media (prefers-reduced-motion:reduce){{*,*::before,*::after{{transition:none!important;animation:none!important}}}}
  .btn{{display:inline-block;background:var(--accent);color:#121212;font-weight:700;
       padding:14px 32px;border-radius:8px;text-decoration:none;font-size:1.05rem}}
  .btn:hover{{background:var(--accent-dim)}}
  section{{margin:36px 0}}
  h2{{font-size:1.35rem;margin-bottom:14px}}
  .inside{{columns:2;column-gap:32px}}
  @media(max-width:480px){{.btn{{width:100%;text-align:center;box-sizing:border-box}}}}
  @media(max-width:640px){{.inside{{columns:1}}}}
  .inside li{{margin:8px 0;break-inside:avoid;color:var(--text)}}
  ul.clean{{list-style:none}}
  ul.clean li{{padding-left:24px;position:relative}}
  ul.clean li:before{{content:"✓";color:var(--accent);position:absolute;left:0;font-weight:700}}
  .rel{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}}
  .rel a{{background:var(--panel);border:1px solid var(--line);border-radius:10px;
          padding:18px;color:var(--text);text-decoration:none;display:block}}
  .rel a:hover{{border-color:var(--accent)}}
  .rel .rp{{color:var(--accent);font-weight:700;margin-top:8px}}
  .faq p{{color:var(--muted);margin-bottom:16px}}
  .faq strong{{color:var(--text)}}
  footer{{border-top:1px solid var(--line);margin-top:48px;padding-top:20px;
         color:var(--muted);font-size:.82rem;display:flex;justify-content:space-between;
         flex-wrap:wrap;gap:8px}}
  footer a{{color:var(--muted);text-decoration:none}}
  footer a:hover{{color:var(--accent)}}

.currency-note{{font-size:.72rem;font-weight:400;color:var(--muted, #a89d89);margin-left:6px;vertical-align:middle}}</style>
</head>
<body>
<div class="wrap">
  <a class="brand" href="../../">
    <svg width="24" height="24" viewBox="0 0 26 26" fill="none" aria-hidden="true"><circle cx="5" cy="6" r="2.4" fill="#e07a5f"/><circle cx="21" cy="6" r="2.4" fill="#e07a5f"/><circle cx="13" cy="13" r="2.4" fill="#e07a5f"/><circle cx="5" cy="20" r="2.4" fill="#e07a5f"/><circle cx="21" cy="20" r="2.4" fill="#e07a5f"/><path d="M6.6 7.4L11.2 11.8M19.4 7.4L14.8 11.8M6.6 18.6L11.2 14.2M19.4 18.6L14.8 14.2" stroke="#e07a5f" stroke-width="1.4"/></svg>
    ghostcorpnet
  </a>
  <nav aria-label="Breadcrumb" class="crumb"><ol><li><a href="../../">Home</a></li><li><a id="pdp-back" href="../../products/" aria-keyshortcuts="Escape" aria-label="Back to all {n_products} products">Catalog</a><kbd class="esc-hint">Esc</kbd></li><li aria-current="page">{title}</li></ol></nav>

  <div class="hero" itemscope itemtype="https://schema.org/Product">
    {cover_img}
    <div>
      <h1 itemprop="name">{title}</h1>
      <p class="tagline">{tagline}</p>
      <p class="price">${price} <span class="currency-note">Prices in USD</span></p>
      {buy_html}
      {file_facts}
      <div class="facts">{facts_row}</div>
    </div>
  </div>

  <section aria-labelledby="pdp-what">
    <h2 id="pdp-what">What it does</h2>
    <p itemprop="description">{description}</p>
  </section>

  <section aria-labelledby="pdp-inside">
    <h2 id="pdp-inside">What's inside</h2>
    <ul class="clean inside">
{inside_items}
    </ul>
  </section>

  <section class="faq">
    <h2>How it works</h2>
    <p><strong>How do I receive it?</strong><br>Checkout is handled by Gumroad. The PDF is available for instant download the moment you pay — no account setup on our side, no waiting.</p>
    <p><strong>Is it really ready to use?</strong><br>Yes. Every ghostcorpnet product is written with zero placeholders — adopt it as-is, no "insert your policy here" gaps.</p>
    <p><strong>Who is it for?</strong><br>Teams shipping AI agents to production — founders, platform engineers, and anyone whose agents touch money, data, or external systems.</p>
  </section>
  <script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{{"@type":"Question","name":"How do I receive it?","acceptedAnswer":{{"@type":"Answer","text":"Checkout is handled by Gumroad. The PDF is available for instant download the moment you pay — no account setup on our side, no waiting."}}}},
{{"@type":"Question","name":"Is it really ready to use?","acceptedAnswer":{{"@type":"Answer","text":"Every ghostcorpnet product is written with zero placeholders — adopt it as-is, no \\"insert your policy here\\" gaps."}}}},
{{"@type":"Question","name":"Who is it for?","acceptedAnswer":{{"@type":"Answer","text":"Teams shipping AI agents to production — founders, platform engineers, and anyone whose agents touch money, data, or external systems."}}}}]}}
  </script>

  <section>
    <h2>Pairs well with</h2>
    <div class="rel">
{related}
    </div>
  </section>

{bundle_upsell}
{fbt}
{studio}
{next_step}
  <footer>
    <span>© 2026 ghostcorpnet · An independent studio</span>
    <span><a href="../../">Home</a> · <a href="../">Catalog</a> · <a href="../../changelog.html">Changelog</a> · <a href="mailto:ghostcorpnetai@gmail.com">Contact</a></span>
  </footer>
</div>
{sticky_bar}
<script>
document.addEventListener('keydown',function(e){{if(e.key==='Escape'&&!e.defaultPrevented&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){{var b=document.getElementById('pdp-back');if(b&&b.href){{location.href=b.href;}}}}}});
</script>
</body>
</html>
"""


def fbt_block(pr, products):
    """'Frequently bought together' block: up to 3 real bundle products.

    Bundles are identified from the actual product list (title keywords);
    links are internal site links with real prices. Never invents products.
    Empty when no bundles exist (never guess)."""
    kw = ("bundle", "library", "collection", "mega-kit", "complete", "vault")
    seen, picks = set(), []
    cands = [x for x in products
             if x["gid"] != pr["gid"] and x.get("slug")
             and any(k in (x.get("title") or "").lower() for k in kw)]
    def price_num(x):
        try: return float(x.get("price") or 0)
        except (TypeError, ValueError): return 0
    for x in sorted(cands, key=price_num, reverse=True):
        if x["slug"] not in seen:
            seen.add(x["slug"]); picks.append(x)
        if len(picks) == 3: break
    if not picks: return ""
    items = "".join(
        '<a href="../' + x["slug"] + '/"><strong>' + esc(x["title"]) + '</strong>'
        '<div class="rp">$' + x["price"] + '</div></a>' for x in picks)
    return ('  <section>\n    <h2>Frequently bought together</h2>\n'
            '    <div class="rel">\n' + items + '\n    </div>\n  </section>\n')


def main():
    packs = load_packs()
    ladder = load_ladder()
    title_map = load_brand_title_map()
    mans = manuscripts()
    products = []
    for gid, slug, title, price, tagline, inside in ORIGINALS:
        products.append(dict(gid=gid, slug=slug, title=title, price=fmt_price(price),
                             tagline=fix_tagline(tagline), description=fix_tagline(tagline), inside=inside,
                             gumroad_url=f"https://koalstin.gumroad.com/l/{gid}"))
    for p in packs:
        url = p.get("gumroad_url", "")
        m = re.search(r"/l/([a-z0-9-]+)", url or "")
        item_code = p.get("item_code", "")
        is_pack = item_code.upper().startswith("PACK-")
        if m:
            gid = m.group(1)
        elif is_pack:
            gid = item_code.lower().replace("_", "-")
        else:
            continue
        if any(x["gid"] == gid for x in products):
            continue
        title = p.get("product_title", "")
        if is_pack:
            base = title.split(" — ")[0].strip()
            slug = pack_slug_by_title().get(base, slugify(title))
            mp = pack_manuscripts().get(slug)
        else:
            slug = slugify(title)
            mp = best_manuscript(title, mans)
        inside = headings_of(mp) if mp else []
        if not inside:
            inside = ["Complete, zero-placeholder document", "Ready to adopt as-is",
                      "Grounded in production agent-governance practice"]
        products.append(dict(gid=gid, slug=slug, title=title,
                             price=fmt_price(p.get("price_usd", 19)), is_pack=is_pack,
                             tagline=fix_tagline(p.get("tagline", "")), description=p.get("description", ""),
                             inside=inside, gumroad_url=url or None,
                             file_path=p.get("file_path") or None))

    # Pack Standard v1 aliases: the live /products/ catalog links the 10 studio
    # packs under slugified full titles (e.g. healthcare-ai-agent-governance-pack-meridian-studio).
    # Emit the same page under that slug so those links resolve (canonical PDP).
    aliases = []
    for pr in products:
        if pr.get("is_pack"):
            ps_slug = slugify(pr["title"])
            if ps_slug != pr["slug"] and not any(x["slug"] == ps_slug for x in products):
                alias = dict(pr); alias["slug"] = ps_slug
                aliases.append(alias)
    products.extend(aliases)

    # render pages
    sm_entries = []
    asset_idx = build_asset_index()
    for i, pr in enumerate(products):
        d = os.path.join(SITE, "products", pr["slug"])
        os.makedirs(d, exist_ok=True)
        page_url = f"{BASE_URL}/products/{pr['slug']}/"
        inside_items = "\n".join(f"      <li>{esc(h)}</li>" for h in pr["inside"])
        rels = [products[(i + k) % len(products)] for k in (1, 2, 3)]
        related = "\n".join(
            f'      <a href="../{r["slug"]}/"><strong>{esc(r["title"])}</strong><div class="rp">${r["price"]}</div></a>'
            for r in rels)
        is_live = bool(pr["gumroad_url"])
        # Facts row: real metadata only — price, delivery (live products only),
        # pack type, and the count of "What's inside" sections. Never invented.
        facts = [f'<span class="fact"><b itemprop="price" content="{pr["price"]}">${pr["price"]}</b> one-time, <span itemprop="priceCurrency" content="USD">USD</span></span>']
        if is_live:
            facts.append('<span class="fact">Instant download via Gumroad</span>')
        if pr.get("is_pack"):
            facts.append('<span class="fact">Studio pack</span>')
        facts.append(f'<span class="fact"><b>{len(pr["inside"])}</b> sections inside</span>')
        facts_row = "\n      ".join(facts)
        file_facts = file_facts_line(pr, pr.get("file_path"), asset_idx)
        cover_path = os.path.join(SITE, "assets", "covers", f"{pr['gid']}.png")
        dims = png_dims(cover_path) if os.path.isfile(cover_path) else None
        cover_img = (f'<img itemprop="image" src="../../assets/covers/{pr["gid"]}.png" alt="{esc(pr["title"])} cover"'
                     f' fetchpriority="high" decoding="async" width="{dims[0]}" height="{dims[1]}">'
                     if os.path.isfile(cover_path) and dims else
                     (f'<img itemprop="image" src="../../assets/covers/{pr["gid"]}.png" alt="{esc(pr["title"])} cover"'
                      f' fetchpriority="high" decoding="async">'
                      if os.path.isfile(cover_path) else ""))
        og_dims = (f'<meta property="og:image:width" content="{dims[0]}">\n'
                   f'<meta property="og:image:height" content="{dims[1]}">') if dims else ""
        if is_live:
            buy_html = (f'<p class="instant" id="buy-trust">One-time · Instant PDF download via Gumroad</p>\n'
                        f'      <a class="btn" href="{pr["gumroad_url"]}" target="_blank" rel="noopener" aria-label="Buy {esc(pr["title"])} for ${pr["price"]} (opens in new tab)" aria-describedby="buy-trust">Get it now — ${pr["price"]}</a>\n'
                        f'      <p class="trust">Secure checkout via Gumroad · <a style="color:var(--accent)" href="https://help.gumroad.com">buyer protection</a> · Single-user license · Instant delivery</p>\n'
                        f'      <p class="trust">Lifetime access — yours forever in your Gumroad library</p>\n'
                        f'      <p class="notready">Not ready? <a href="../../playbook.md">Get the free MIT playbook</a> first.</p>')
        else:
            buy_html = ('<p class="instant">Publishing now — available shortly</p>\n'
                        '      <span class="btn" style="opacity:.7;cursor:default">Publishing — live soon</span>\n'
                        '      <p class="trust">This ghostcorpnet studio pack is moving through our publish queue</p>')
        breadcrumblist = json.dumps({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://koalstingkdelaney-gif.github.io/kestrelattice/"},
                {"@type": "ListItem", "position": 2, "name": "Products", "item": "https://koalstingkdelaney-gif.github.io/kestrelattice/products/"},
                {"@type": "ListItem", "position": 3, "name": pr["title"], "item": page_url}]}, indent=2)
        jsonld = json.dumps({
            "@context": "https://schema.org", "@type": "Product",
            "name": pr["title"], "description": pr["tagline"] or pr["description"],
            "image": f"{BASE_URL}/assets/covers/{pr['gid']}.png",
            "brand": {"@type": "Brand", "name": "ghostcorpnet"},
            "offers": {"@type": "Offer", "priceCurrency": "USD", "price": str(pr["price"]),
                       "availability": "https://schema.org/InStock" if is_live else "https://schema.org/PreOrder",
                       "url": pr["gumroad_url"] or page_url}}, indent=2)
        upsell = ""
        if pr["gid"] != "yzbumc":
            upsell = ('  <section style="border:1px solid var(--accent);border-radius:12px;'
                      'padding:24px;background:#1e1a16">\n'
                      '    <h2 style="margin-top:0">Want the whole library?</h2>\n'
                      '    <p><strong>The Complete ghostcorpnet Library</strong> — every ghostcorpnet product '
                      'in one bundle for $79. One purchase, everything we have shipped.</p>\n'
                      '    <p><a class="btn" href="../complete-kestrelattice-library/">Get the full library — $79</a></p>\n'
                      '  </section>')
        if is_live:
            sticky_bar = (f'<div class="pdp-sticky" id="pdp-sticky" role="region" aria-label="Quick buy: {esc(pr["title"])}">'
                          f'<span><b>{esc(pr["title"])}</b> \u00b7 ${pr["price"]}</span>'
                          f'<a class="btn" href="{pr["gumroad_url"]}" target="_blank" rel="noopener" aria-label="Buy {esc(pr["title"])} on Gumroad (opens in new tab)">Buy now</a></div>')
        else:
            sticky_bar = (f'<div class="pdp-sticky" id="pdp-sticky" role="region" aria-label="Availability: {esc(pr["title"])}">'
                          f'<span><b>{esc(pr["title"])}</b> \u00b7 ${pr["price"]}</span>'
                          '<span class="soon">Publishing soon</span></div>')
        page = PAGE.format(title=esc(pr["title"]), meta=esc(trunc_meta(pr["tagline"] or pr["description"])),
                           page_url=page_url, jsonld=jsonld, breadcrumblist=breadcrumblist, gid=pr["gid"], cover_img=cover_img,
                           tagline=esc(pr["tagline"]), price=pr["price"], buy_html=buy_html,
                           file_facts=file_facts,
                           facts_row=facts_row,
                           gumroad_url=pr["gumroad_url"] or "", description=esc(pr["description"]),
                           inside_items=inside_items, related=related, bundle_upsell=upsell,
                           studio=studio_block(pr, title_map), og_dims=og_dims,
                           next_step=next_step_block(pr, ladder), n_products=len(products),
                           sticky_bar=sticky_bar, fbt=fbt_block(pr, products))
        with open(os.path.join(d, "index.html"), "w") as f:
            f.write(page)
        sm_entries.append(f'  <url><loc>{page_url}</loc><lastmod>{page_lastmod(d)}</lastmod><changefreq>monthly</changefreq></url>')

    # sitemap
    sm_path = os.path.join(SITE, "sitemap.xml")
    sm = open(sm_path).read()
    added = 0
    for e in sm_entries:
        loc = re.search(r"<loc>([^<]+)</loc>", e).group(1)
        if loc not in sm:
            sm = sm.replace("</urlset>", e + "\n</urlset>")
            added += 1
    open(sm_path, "w").write(sm)
    refresh_sitemap_lastmods()
    print(f"product pages: {len(products)} written, sitemap +{added}")

if __name__ == "__main__":
    main()
