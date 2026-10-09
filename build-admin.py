#!/usr/bin/env python3
"""ghostcorpnet admin dashboard v2 — app-grade command center.

Single URL, single app: sidebar brand switcher (All brands + 10 micro-brands),
client-side view switching, bottom tab bar on mobile, toasts, spinners.

Generated HTML is served ONLY from the key-gated worker /admin route
(wrong/missing key -> 404). The file itself is gitignored, carries
<meta name="robots" content="noindex, nofollow">, is never in sitemap.xml,
and is never linked from the public site. No secrets are written into the page.

Regenerate: python3 ~/workspace/kestrelattice/build-admin.py
"""
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "workspace/kestrelattice")
HF = os.path.join(HOME, "workspace/goals/kestrelattice-autonomous-growth/hidden_files")

_spec = importlib.util.spec_from_file_location(
    "admin_sections", os.path.join(SITE, "_admin_sections.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

esc = S.esc

# ---------------------------------------------------------------- brand data

BRANDS = [
    {"slug": "incidentlattice", "name": "IncidentLattice", "accent": "#e5484d",
     "tagline": "When your AI agent goes wrong at 3am, this is the playbook.",
     "niche": "Agent security incidents"},
    {"slug": "supportwarden", "name": "SupportWarden", "accent": "#2dd4bf",
     "tagline": "Support agents that help customers — without leaking data or going rogue.",
     "niche": "Customer-support agents"},
    {"slug": "classwarden", "name": "ClassWarden", "accent": "#f5a524",
     "tagline": "AI in the classroom, governed: practical kits for schools and edtech.",
     "niche": "Education"},
    {"slug": "actlattice", "name": "ActLattice", "accent": "#3b82f6",
     "tagline": "EU AI Act readiness for agent builders and deployers, step by step.",
     "niche": "EU AI Act compliance"},
    {"slug": "finlattice", "name": "FinLattice", "accent": "#22c55e",
     "tagline": "Money-moving agents need money-grade controls. Here's the kit.",
     "niche": "Finance"},
    {"slug": "healthlattice", "name": "HealthLattice", "accent": "#0ea5e9",
     "tagline": "Patient-data-safe agent governance for health teams.",
     "niche": "Healthcare"},
    {"slug": "hirewarden", "name": "HireWarden", "accent": "#8b5cf6",
     "tagline": "Hiring agents that stay fair, documented, and defensible.",
     "niche": "Hiring / HR"},
    {"slug": "lawwarden", "name": "LawWarden", "accent": "#6366f1",
     "tagline": "Legal-team-grade agent governance, minus the legal advice.",
     "niche": "Legal"},
    {"slug": "sourcelattice", "name": "SourceLattice", "accent": "#f97316",
     "tagline": "Supply-chain and sourcing agents with receipts.",
     "niche": "Sourcing / supply chain"},
    {"slug": "civicwarden", "name": "CivicWarden", "accent": "#d4a24e",
     "tagline": "Public-sector AI agents the public can trust.",
     "niche": "Government / civic"},
    {"slug": "frontierlattice", "name": "FrontierLattice", "accent": "#e0e0e0",
     "tagline": "Frontier-model governance for the teams building what's next.",
     "niche": "Frontier AI"},
]
BRAND_SLUGS = [b["slug"] for b in BRANDS]
BRAND_BY_SLUG = {b["slug"]: b for b in BRANDS}


def _title_brand_map():
    """Exact launch-title -> brand slug, from the brand registry."""
    m = {}
    txt = S.read_file(os.path.join(HF, "brands/REGISTRY.md"))
    for sec in re.findall(r"## [^(]+?\(`([a-z]+)`\)(.*?)(?=^## |\Z)", txt, re.S | re.M):
        slug, body = sec
        if slug not in BRAND_SLUGS:
            continue
        for t in re.findall(r"^- .+?\*\*(.+?)\*\*", body, re.M):
            m[t.strip().lower()] = slug
    return m


def _outreach_brand_map():
    """Outreach id -> brand slug, from the brands' acquisition queues."""
    import glob as _glob
    m = {}
    for f in _glob.glob(os.path.join(HF, "brands/*/acquisition-queue.jsonl")):
        for line in S.read_file(f).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            b = str(e.get("brand", "")).strip().lower()
            if b in BRAND_SLUGS and e.get("id"):
                m[e["id"]] = b
    return m


def product_brand(p, title_map):
    name = (p.get("name") or "").strip().lower()
    if name in title_map:
        return title_map[name]
    for t in p.get("tags") or []:
        tl = str(t).lower()
        for s in BRAND_SLUGS:
            if s == tl or BRAND_BY_SLUG[s]["name"].lower() == tl:
                return s
    return "unassigned"


def outreach_brand(entry, omap):
    oid = entry.get("id", "")
    if oid in omap:
        return omap[oid]
    m = re.match(r"q-([a-z]+)-", oid)
    if m and m.group(1) in BRAND_SLUGS:
        return m.group(1)
    return "unassigned"


def queue_brand(item, omap):
    code = item.get("code", "") or ""
    oid = item.get("outreach_id", "") or ""
    if oid and oid in omap:
        return omap[oid]
    m = re.match(r"(?:OS|OF)-(.+)$", code)
    if m:
        mm = re.match(r"q-([a-z]+)-", m.group(1))
        if mm and mm.group(1) in BRAND_SLUGS:
            return mm.group(1)
    bm = re.search(r"brand:\s*([A-Za-z]+)", item.get("detail", "") or "")
    if bm and bm.group(1).lower() in BRAND_SLUGS:
        return bm.group(1).lower()
    return "unassigned"


def brand_display(slug):
    if slug == "unassigned":
        return {"slug": "unassigned", "name": "Unassigned", "accent": "#98908a",
                "tagline": "Items not attributable to a brand.", "niche": ""}
    return BRAND_BY_SLUG.get(slug, BRAND_BY_SLUG["incidentlattice"])


def load_outreach_entries():
    items = []
    for line in S.read_file(os.path.join(HF, "outreach/queue.jsonl")).splitlines():
        line = line.strip()
        if line:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return items


# ------------------------------------------------------- per-brand sections

def brand_stats(slug, products, entries, queue, title_map, omap):
    """(live_n, revenue, sales_n, sent_n, pending_n) for one brand."""
    prods = [p for p in products if p.get("published")
             and product_brand(p, title_map) == slug]
    rev = sum((p.get("sales_usd_cents") or 0) for p in prods) / 100.0
    sales = sum(p.get("sales_count") or 0 for p in prods)
    sent = sum(1 for e in entries if outreach_brand(e, omap) == slug
               and e.get("status") == "sent")
    pend = sum(1 for i in queue if queue_brand(i, omap) == slug
               and i.get("status") == "pending")
    return len(prods), rev, sales, sent, pend


def brand_hero(slug):
    b = brand_display(slug)
    return (
        f'<div class="bhero" style="--bacc:{b["accent"]}">'
        f'<div class="bhero-dot"></div>'
        f"<div><h2>{esc(b['name'])}</h2>"
        f"<p>{esc(b['tagline'])}</p>"
        f"<span class='bhero-niche'>{esc(b['niche'])}</span></div>"
        "</div>"
    )


def brand_kpis(slug, products, entries, queue, title_map, omap):
    n, rev, sales, sent, pend = brand_stats(slug, products, entries, queue,
                                           title_map, omap)
    return (
        '<div class="kpirow">'
        f'<div class="kpi accent"><div class="kpi-v">{n}</div>'
        '<div class="kpi-l">live products</div></div>'
        f'<div class="kpi"><div class="kpi-v">${rev:,.0f}</div>'
        '<div class="kpi-l">revenue</div></div>'
        f'<div class="kpi"><div class="kpi-v">{sales}</div>'
        '<div class="kpi-l">sales</div></div>'
        f'<div class="kpi"><div class="kpi-v">{sent}</div>'
        '<div class="kpi-l">pitches sent</div></div>'
        f'<div class="kpi{" bad" if pend else ""}"><div class="kpi-v">{pend}</div>'
        '<div class="kpi-l">pending approvals</div></div>'
        "</div>"
    )


def brand_products_table(slug, products, title_map):
    prods = [p for p in products if p.get("published")
             and product_brand(p, title_map) == slug]
    if not prods:
        return ("<div class='card'><h3>No live products yet</h3>"
                "<p class='muted'>This brand's products are still in the publish "
                "queue — the watcher publishes them automatically.</p></div>")
    rows = []
    for p in sorted(prods, key=lambda x: -(x.get("price") or 0)):
        name = p.get("name", "?")
        cents = p.get("sales_usd_cents") or 0
        n = p.get("sales_count") or 0
        price = (p.get("price") or 0) / 100.0
        url = (p.get("short_url") or p.get("permalink") or "").rstrip("/")
        disp = url.replace("https://", "").replace("http://", "")
        tags = p.get("tags") or []
        badge = (" <span class='badge code'>CODE</span>"
                 if any("code" in str(t).lower() for t in tags) else "")
        rows.append(
            f"<tr><td><b>{esc(name)}</b>{badge}<br><a class='mono' href='{esc(url)}' "
            f"target='_blank' rel='noopener'>{esc(disp)}</a></td>"
            f"<td>${price:,.0f}</td><td>${cents/100:,.0f}</td><td>{n}</td></tr>")
    return (
        '<div class="table-wrap"><table><tr><th>Product</th><th>Price</th>'
        "<th>Revenue</th><th>Sales</th></tr>" + "".join(rows) + "</table></div>"
    )


def brand_outreach(slug, entries, omap):
    mine = [e for e in entries if outreach_brand(e, omap) == slug]
    ready = [e for e in mine if e.get("status") == "ready"]
    sent = [e for e in mine if e.get("status") == "sent"]
    needc = [e for e in mine if e.get("status") == "needs-contact"]
    stats = (
        '<div class="statrow">'
        f'<div class="stat"><b>{len(ready)}</b><span>ready to send</span></div>'
        f'<div class="stat"><b>{len(sent)}</b><span>pitches sent</span></div>'
        f'<div class="stat"><b>{len(needc)}</b><span>finding contact</span></div>'
        "</div>")
    cards = []
    for it in ready:
        qid = it.get("id", "")
        cards.append(
            '<div class="card"><h3>' + esc(it.get("lead", "?")) + "</h3>"
            "<p>" + esc(it.get("why", "")) + "</p>"
            '<p class="muted">To: <b>' + esc(it.get("contact_email", "")) + "</b></p>"
            '<details class="fold"><summary>Pitch — ' + esc(it.get("subject", "")) + "</summary>"
            '<p style="white-space:pre-wrap">' + esc(it.get("pitch", "")) + "</p></details>"
            '<button class="btn" data-send="OS-' + esc(qid) + '">Send pitch</button> '
            '<button class="btn btn-ghost" data-send="OF-' + esc(qid) + '">Forget</button>'
            "</div>")
    sent_list = ""
    if sent:
        rows = "".join(
            "<li><b>" + esc(e.get("lead", "?")) + "</b> → " +
            esc(e.get("contact_email", "")) +
            ' <span class="muted">' + esc((e.get("sent_at") or "")[:10]) + "</span></li>"
            for e in sorted(sent, key=lambda x: x.get("sent_at", ""), reverse=True)[:12])
        sent_list = ('<details class="fold"><summary>Sent (' + str(len(sent)) +
                     ")</summary><ul>" + rows + "</ul></details>")
    if not mine:
        return stats + ("<p class='muted'>No outreach for this brand yet — the lead "
                        "scout drafts pitches around the clock.</p>")
    return stats + "".join(cards) + sent_list


def brand_approvals(slug, queue, omap):
    seen, items = set(), []
    for i in queue:
        st = str(i.get("status", ""))
        if queue_brand(i, omap) == slug and (st in ("pending", "approved") or st.startswith("blocked")):
            if i.get("code") not in seen:
                seen.add(i.get("code"))
                items.append(i)
    if not items:
        return ("<div class='card ok-card'><h3>All clear</h3>"
                "<p class='muted'>Nothing waiting for this brand.</p></div>")
    rows = []
    for it in items:
        st = str(it.get("status", ""))
        pill = ('<span class="pill blocked">blocked</span>' if st.startswith("blocked")
                else '<span class="pill warn">approved ✓</span>' if st == "approved"
                else '<span class="pill">waiting</span>')
        btn = (f'<button class="btn" data-approve="{esc(it.get("code",""))}">Approve</button>'
               if st == "pending" else '<span class="muted">—</span>')
        rows.append(
            f"<tr><td><b>{esc(it.get('title',''))}</b><br>"
            f"<span class='muted'>{esc((it.get('detail') or '')[:160])}</span></td>"
            f"<td>{pill}</td><td>{btn}</td></tr>")
    return (
        '<div class="table-wrap"><table><tr><th>Item</th><th>Status</th><th></th></tr>'
        + "".join(rows) + "</table></div>"
        "<p class='muted'>Tap <b>Approve</b> — the fleet picks it up within ~15 minutes.</p>"
    )


def brand_comparison_table(products, entries, queue, title_map, omap):
    rows = []
    for b in BRANDS + [{"slug": "unassigned"}]:
        slug = b["slug"]
        n, rev, sales, sent, pend = brand_stats(slug, products, entries, queue,
                                               title_map, omap)
        bd = brand_display(slug)
        rows.append(
            f"<tr><td><span class='bdot' style='background:{bd['accent']}'></span>"
            f"<b>{esc(bd['name'])}</b><br><span class='muted'>{esc(bd['niche'])}</span></td>"
            f"<td>{n}</td><td>${rev:,.0f}</td><td>{sales}</td>"
            f"<td>{sent}</td><td>{pend}</td>"
            f"<td><button class='btn btn-sm' data-goto-brand='{slug}'>Open →</button></td></tr>")
    return (
        '<div class="card"><h3>All businesses at a glance</h3>'
        '<p class="lede">Every brand, one table. Tap <b>Open</b> to jump into a brand\'s own admin.</p>'
        '<div class="table-wrap"><table><tr><th>Brand</th><th>Products</th>'
        "<th>Revenue</th><th>Sales</th><th>Pitches sent</th><th>Pending</th><th></th></tr>"
        + "".join(rows) + "</table></div></div>"
    )


# ---------------------------------------------------------------- app shell

CSS = """
:root{
  --bg:#101014; --panel:#17181d; --panel2:#1d1f26; --line:#2a2c35; --line2:#343743;
  --text:#ece7db; --muted:#9a928a; --faint:#6e675f;
  --accent:#e07a5f; --accent-deep:#a8502f; --accent-ink:#17110c;
  --ok:#7fbf7f; --warn:#e0a75f; --bad:#e08a7f;
  --r:16px; --r-sm:10px;
  --shadow:0 2px 14px rgba(0,0,0,.28);
  --shadow-lg:0 10px 34px rgba(0,0,0,.42);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  background:radial-gradient(1200px 420px at 50% -90px,#201b17 0%,var(--bg) 62%),var(--bg);
  color:var(--text);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  line-height:1.6;-webkit-text-size-adjust:100%;-webkit-tap-highlight-color:transparent;
}
/* ---------- layout ---------- */
.app{display:flex;min-height:100vh}
.sidebar{
  width:272px;flex:0 0 272px;position:sticky;top:0;height:100vh;overflow-y:auto;
  background:rgba(18,18,23,.92);backdrop-filter:blur(12px);
  border-right:1px solid var(--line);padding:20px 14px 28px;z-index:50;
}
.main{flex:1;min-width:0;max-width:760px;margin:0 auto;padding:0 28px 120px;width:100%}
.sbrand{display:flex;align-items:center;gap:10px;padding:4px 10px 16px;font-weight:800;font-size:1.02rem}
.sbrand .admin-tag{font-size:.62rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:#0f0e0c;background:linear-gradient(135deg,var(--accent),#f0a184);
  border-radius:999px;padding:4px 10px}
.slabel{font-size:.66rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;
  color:var(--faint);padding:16px 10px 8px}
.bbtn{display:flex;align-items:center;gap:10px;width:100%;text-align:left;
  background:transparent;border:1px solid transparent;border-radius:12px;color:var(--muted);
  font-size:.88rem;font-weight:600;padding:10px 12px;cursor:pointer;font-family:inherit;
  min-height:44px;transition:all .15s ease}
.bbtn:hover{background:var(--panel);color:var(--text)}
.bbtn.on{background:var(--panel2);color:var(--text);border-color:var(--line2);
  box-shadow:var(--shadow)}
.bbtn .bdot{width:10px;height:10px;border-radius:50%;flex:0 0 auto}
.bbtn .bname{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bbtn .bcount{font-size:.72rem;background:var(--panel);border:1px solid var(--line);
  border-radius:999px;padding:1px 8px;color:var(--muted)}
.bbtn.on .bcount{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:800}
.tbtn{display:flex;align-items:center;gap:11px;width:100%;text-align:left;
  background:transparent;border:0;border-radius:12px;color:var(--muted);
  font-size:.9rem;font-weight:600;padding:10px 12px;cursor:pointer;font-family:inherit;
  min-height:44px;transition:all .15s ease}
.tbtn svg{width:19px;height:19px;flex:0 0 auto;opacity:.75}
.tbtn:hover{background:var(--panel);color:var(--accent)}
.tbtn.on{background:linear-gradient(135deg,rgba(224,122,95,.16),rgba(224,122,95,.06));
  color:var(--accent)}
.tbtn.on svg{opacity:1}
.sfoot{padding:18px 10px 0;color:var(--faint);font-size:.75rem;line-height:1.7}
.refresh-row{display:flex;align-items:center;gap:10px;padding:2px 10px 4px}
.updated{font-size:.74rem;color:var(--faint);flex:1}
/* ---------- topbar (mobile) ---------- */
.topbar{display:none;position:sticky;top:0;z-index:60;
  background:rgba(16,16,20,.95);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line);padding:10px 14px;gap:10px;align-items:center}
.topbar .sbrand{padding:0;font-size:.95rem}
.brandpick{flex:1;min-width:0;background:var(--panel2);color:var(--text);
  border:1px solid var(--line2);border-radius:12px;font-size:.9rem;font-weight:600;
  padding:11px 12px;font-family:inherit;min-height:44px;
  appearance:none;-webkit-appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23e07a5f' stroke-width='2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 14px center;padding-right:36px}
.iconbtn{flex:0 0 auto;width:44px;height:44px;border-radius:12px;border:1px solid var(--line2);
  background:var(--panel2);color:var(--accent);cursor:pointer;font-size:1.15rem;
  display:flex;align-items:center;justify-content:center}
/* ---------- bottom tab bar (mobile) ---------- */
.tabbar{display:none;position:fixed;left:0;right:0;bottom:0;z-index:60;
  background:rgba(18,18,23,.97);backdrop-filter:blur(14px);
  border-top:1px solid var(--line);padding:6px 4px calc(8px + env(safe-area-inset-bottom))}
.tabbar-in{display:flex;justify-content:space-around}
.tabitem{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
  background:none;border:0;color:var(--faint);font-size:.62rem;font-weight:700;
  padding:8px 2px;cursor:pointer;font-family:inherit;min-height:52px;border-radius:10px}
.tabitem svg{width:21px;height:21px}
.tabitem.on{color:var(--accent);background:rgba(224,122,95,.12)}
/* ---------- content ---------- */
.hero{padding:34px 0 2px}
.hero h1{font-size:clamp(1.7rem,4vw,2.3rem);font-weight:800;letter-spacing:-.025em;
  background:linear-gradient(120deg,#fff 30%,var(--accent) 100%);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.bpane{display:none}
.bpane.on{display:block;animation:rise .22s ease}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.sec-title{margin:24px 0 4px}
.sec-title h2{font-size:1.3rem;font-weight:750;letter-spacing:-.015em}
.eyebrow{font-size:.66rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase;
  color:var(--accent);margin-bottom:5px}
.lede{color:var(--muted);font-size:.92rem;margin:4px 0 12px;max-width:740px}
.bhero{display:flex;gap:16px;align-items:flex-start;margin:18px 0 4px;padding:20px 22px;
  background:linear-gradient(135deg,color-mix(in srgb,var(--bacc) 14%,var(--panel2)),var(--panel));
  border:1px solid var(--line);border-left:5px solid var(--bacc);border-radius:var(--r);
  box-shadow:var(--shadow)}
.bhero-dot{width:16px;height:16px;border-radius:50%;background:var(--bacc);margin-top:6px;
  box-shadow:0 0 12px var(--bacc);flex:0 0 auto}
.bhero h2{font-size:1.45rem;font-weight:800;letter-spacing:-.02em}
.bhero p{color:var(--muted);font-size:.93rem;margin-top:2px}
.bhero-niche{display:inline-block;margin-top:8px;font-size:.7rem;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:var(--bacc);border:1px solid var(--bacc);border-radius:999px;padding:3px 11px}
/* ---------- components ---------- */
.kpirow{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0 6px}
.kpi{background:linear-gradient(180deg,var(--panel2),var(--panel));
  border:1px solid var(--line);border-radius:var(--r);
  padding:18px 14px 15px;text-align:center;position:relative;overflow:hidden;
  box-shadow:var(--shadow);transition:transform .15s ease}
.kpi:hover{transform:translateY(-2px)}
.kpi::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,transparent,var(--line2),transparent)}
.kpi.accent::before{background:linear-gradient(90deg,transparent,var(--accent),transparent)}
.kpi.warn .kpi-v{color:var(--warn)} .kpi.bad .kpi-v{color:var(--bad)}
.kpi-v{font-size:1.8rem;font-weight:800;letter-spacing:-.02em;color:var(--accent);line-height:1.3}
.kpi-l{color:var(--text);font-size:.82rem;font-weight:650;margin-top:2px}
.kpi-s{color:var(--muted);font-size:.74rem}
.card{background:linear-gradient(180deg,var(--panel2),var(--panel));
  border:1px solid var(--line);border-radius:22px;
  padding:22px;margin:16px 0;box-shadow:var(--shadow)}
.card.warn{border-left:4px solid var(--warn)}
.card.ok-card{border-left:4px solid var(--ok)}
.card h3{margin:0 0 10px;font-size:1.06rem;font-weight:750;letter-spacing:-.01em}
.card p{color:var(--muted);font-size:.92rem}
.card b{color:var(--text)}
.alert{padding:11px 0;border-bottom:1px solid var(--line)}
.alert:last-child{border-bottom:0;padding-bottom:0}
.alert b{display:block;margin:5px 0 2px}
.statrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);
  padding:18px 12px;text-align:center;box-shadow:var(--shadow)}
.stat b{display:block;font-size:1.65rem;color:var(--accent);line-height:1.25}
.stat span{color:var(--muted);font-size:.82rem}
.table-wrap{overflow-x:auto;margin:14px 0;border:1px solid var(--line);
  border-radius:var(--r);background:var(--panel);box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;font-size:.88rem;min-width:560px}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
th{color:var(--muted);font-size:.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.09em;background:var(--panel2);position:sticky;top:0}
tr:nth-child(even) td{background:rgba(255,255,255,.02)}
tr:hover td{background:rgba(224,122,95,.05)}
.table-wrap tr:last-child td{border-bottom:0}
table a{color:var(--accent)}
.tapcard{background:linear-gradient(180deg,var(--panel2),var(--panel));
  border:1px solid var(--line);border-radius:18px;
  padding:16px 18px;margin:12px 0}
.tapcard p{color:var(--muted);font-size:.9rem;margin:6px 0}
.tapcard .taphow{color:var(--text);font-size:.88rem;border-left:3px solid var(--accent);
  padding-left:10px;margin:8px 0}
.tapcard .btn{margin-top:8px}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.78rem;color:var(--muted)}
.muted{color:var(--muted);font-size:.88rem}
.badge{display:inline-block;font-size:.66rem;font-weight:700;letter-spacing:.06em;
  padding:2px 8px;border-radius:999px;margin-left:8px;vertical-align:middle}
.badge.code{background:#1e3a5f;color:#7cc4ff;border:1px solid #2c5f8a}
.pill{display:inline-block;padding:4px 12px;border-radius:20px;font-size:.74rem;font-weight:700;
  background:#2c2e37;color:var(--muted);white-space:nowrap}
.pill.ok{background:#243324;color:var(--ok)}
.pill.warn{background:#3a2f1e;color:var(--warn)}
.pill.blocked{background:#3a2320;color:#e08a7f}
/* ---------- buttons ---------- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;
  min-height:46px;padding:11px 24px;border:0;border-radius:999px;
  background:linear-gradient(135deg,var(--accent),#ef9278);
  color:var(--accent-ink);font-weight:750;font-size:.9rem;cursor:pointer;font-family:inherit;
  box-shadow:0 3px 12px rgba(224,122,95,.32);transition:all .15s ease;white-space:nowrap}
.btn:hover{filter:brightness(1.07);transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn:disabled{opacity:.65;cursor:default;transform:none}
.btn-ghost{background:var(--panel2);color:var(--muted);border:1px solid var(--line2);box-shadow:none}
.btn-ghost:hover{color:var(--text);border-color:var(--faint);filter:none}
.btn-sm{min-height:40px;padding:9px 18px;font-size:.82rem;border-radius:999px}
.btn-danger{background:linear-gradient(135deg,#c0392b,#e08a7f);color:#fff}
.btn.loading{pointer-events:none;opacity:.8}
.btn.loading::before{content:"";width:16px;height:16px;border:2px solid rgba(0,0,0,.25);
  border-top-color:currentColor;border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
/* ---------- toast ---------- */
#toasts{position:fixed;left:50%;transform:translateX(-50%);bottom:86px;z-index:200;
  display:flex;flex-direction:column;gap:8px;align-items:center;pointer-events:none;width:min(92vw,420px)}
.toast{background:var(--panel2);border:1px solid var(--line2);color:var(--text);
  border-radius:14px;padding:13px 20px;font-size:.88rem;font-weight:650;box-shadow:var(--shadow-lg);
  animation:toastin .25s ease;max-width:100%;text-align:center}
.toast.ok{border-color:var(--ok)} .toast.bad{border-color:var(--bad)}
@keyframes toastin{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.toast.out{opacity:0;transition:opacity .3s}
/* ---------- misc ---------- */
details.fold{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);
  padding:15px 19px;margin:14px 0}
details.fold summary{cursor:pointer;font-weight:650;min-height:44px;display:flex;align-items:center}
details.fold ol{margin:10px 0 0 20px;color:var(--muted);font-size:.9rem}
ul{margin:8px 0 8px 20px;color:var(--muted);font-size:.92rem}
ul.feed{list-style:none;margin:10px 0 0;padding:0;font-size:.86rem}
ul.feed li{padding:9px 0;border-bottom:1px solid var(--line)}
ul.feed li:last-child{border-bottom:0}
.src{display:inline-block;font-size:.66rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;
  color:var(--accent);border:1px solid var(--accent-deep);border-radius:6px;padding:2px 8px;margin-right:8px}
.health{display:inline-flex;align-items:center;font-size:.92rem;color:var(--text);white-space:nowrap}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:9px;flex:0 0 auto}
.dot.ok{background:var(--ok);box-shadow:0 0 7px rgba(127,191,127,.8)}
.dot.warn{background:var(--warn);box-shadow:0 0 7px rgba(224,167,95,.6)}
.dot.stale{background:var(--bad)} .dot.never{background:#5a544a}
.sched{display:inline-block;font-size:.78rem;color:var(--muted);border:1px solid var(--line);
  border-radius:6px;padding:3px 9px;white-space:nowrap}
.legend{color:var(--muted);font-size:.82rem;margin:8px 2px 0;line-height:2}
.ms-track{margin:16px 0 6px}
.ms{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}
.ms:last-child{border-bottom:0}
.ms-dot{font-size:1.1rem;width:26px;text-align:center;color:var(--muted)}
.ms.hit .ms-dot{color:var(--ok)} .ms.cur .ms-dot{color:var(--accent)}
.ms-l{flex:1;font-size:.92rem;color:var(--muted)}
.ms.hit .ms-l{color:var(--text)} .ms.cur .ms-l{color:var(--text);font-weight:650}
.ms-a{font-size:.85rem;color:var(--muted);font-weight:700}
.bar{height:10px;background:#0c0c10;border:1px solid var(--line);border-radius:999px;
  overflow:hidden;margin:14px 0 8px}
.bar-fill{height:100%;background:linear-gradient(90deg,var(--accent-deep),var(--accent));
  border-radius:999px;transition:width .6s ease}
.foot{margin-top:44px;color:var(--faint);font-size:.78rem;border-top:1px solid var(--line);padding-top:18px;line-height:1.7}
@media (max-width:919px){
  .sidebar{display:none}
  .topbar{display:flex}
  .tabbar{display:block}
  .main{padding:0 14px 140px}
  .hero{padding:22px 0 2px}
  .kpirow{grid-template-columns:repeat(2,1fr);gap:10px}
  .statrow{grid-template-columns:repeat(2,1fr);gap:10px}
  .card{padding:18px}
  table{min-width:520px}
  #toasts{bottom:96px}
}
.chat-thread{max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;
  padding:4px 2px;margin:6px 0 12px}
.chat-msg{max-width:88%;padding:10px 14px;border-radius:14px;line-height:1.55;font-size:.92rem}
.chat-msg.you{align-self:flex-end;background:var(--accent);color:#fff;border-bottom-right-radius:4px}
.chat-msg.sentience{align-self:flex-start;background:var(--panel2);border:1px solid var(--line);
  border-bottom-left-radius:4px}
.chat-who{display:block;font-size:.68rem;opacity:.65;margin-bottom:4px;letter-spacing:.06em;
  text-transform:uppercase}
.chat-msg p{margin:0;white-space:pre-wrap}
.chat-input{display:flex;gap:8px}
.chat-input input{flex:1;background:var(--panel2);border:1px solid var(--line);color:var(--text);
  border-radius:10px;padding:10px 14px;font-size:.92rem}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
}
"""

JS = """
var App = {brand:'all', tab:'taps'};
var BUILD_TS = 0;
function toast(msg, ok){
  var box = document.getElementById('toasts');
  var t = document.createElement('div');
  t.className = 'toast ' + (ok === false ? 'bad' : (ok ? 'ok' : ''));
  t.textContent = msg;
  box.appendChild(t);
  setTimeout(function(){ t.classList.add('out'); setTimeout(function(){ t.remove(); }, 350); }, 2600);
}
function switchView(brand, tab){
  if (['drafts','fleet','hive','captain','extras','taps','sandbox'].indexOf(tab) >= 0) brand = 'all';
  App.brand = brand; App.tab = tab;
  document.querySelectorAll('.bpane').forEach(function(p){
    p.classList.toggle('on', p.id === 'pane-' + brand + '-' + tab);
  });
  document.querySelectorAll('.bbtn').forEach(function(b){
    b.classList.toggle('on', b.dataset.brand === brand);
  });
  document.querySelectorAll('.tbtn').forEach(function(b){
    b.classList.toggle('on', b.dataset.tab === tab);
  });
  document.querySelectorAll('.tabitem').forEach(function(b){
    b.classList.toggle('on', b.dataset.tab === tab);
  });
  var sel = document.getElementById('brandpick');
  if (sel) sel.value = brand;
  try { history.replaceState(null, '', '#/' + brand + '/' + tab); } catch(e){}
  window.scrollTo(0, 0);
}
function ago(ts){
  var s = Math.max(0, Math.floor(Date.now()/1000 - ts));
  if (s < 60) return 'just now';
  if (s < 3600) return Math.floor(s/60) + 'm ago';
  if (s < 86400) return Math.floor(s/3600) + 'h ago';
  return Math.floor(s/86400) + 'd ago';
}
function tickAgo(){
  document.querySelectorAll('.updated').forEach(function(el){
    el.textContent = 'Updated ' + ago(BUILD_TS);
  });
}
document.addEventListener('DOMContentLoaded', function(){
  var h = (location.hash || '#/all/overview').replace(/^#\\/?/, '');
  var parts = h.split('/');
  var brand = parts[0] || 'all', tab = parts[1] || 'overview';
  var validBrands = ['all'].concat(Array.prototype.map.call(
    document.querySelectorAll('.bbtn'), function(b){ return b.dataset.brand; }));
  var validTabs = Array.prototype.map.call(
    document.querySelectorAll('.tbtn'), function(b){ return b.dataset.tab; });
  if (validBrands.indexOf(brand) < 0) brand = 'all';
  if (validTabs.indexOf(tab) < 0) tab = 'overview';
  switchView(brand, tab);
  tickAgo(); setInterval(tickAgo, 30000);
  // toast + spinner on every action button
  var _ac = window.approveCode;
  window.approveCode = async function(code, btn, doneLabel){
    if (btn) btn.classList.add('loading');
    var ok = false;
    try { ok = await _ac(code, btn, doneLabel); } catch(e){ ok = false; }
    if (btn) btn.classList.remove('loading');
    toast(ok ? (doneLabel || 'Done ✓') : 'Something failed — tap Retry', ok);
    return ok;
  };
  document.addEventListener('click', async function(e){
    var b = e.target.closest('[data-approve],[data-send],[data-goto-brand],[data-goto-tab]');
    if (!b) return;
    if (b.hasAttribute('data-goto-brand')) {
      switchView(b.getAttribute('data-goto-brand'), 'overview');
      return;
    }
    if (b.hasAttribute('data-goto-tab')) {
      var parts = b.getAttribute('data-goto-tab').split('|');
      switchView(parts[0], parts[1]);
      return;
    }
    var code = b.getAttribute('data-approve') || b.getAttribute('data-send');
    var label = b.hasAttribute('data-send')
      ? (b.getAttribute('data-send').indexOf('OF-') === 0 ? 'Forgotten' : 'Queued ✓')
      : 'Approved ✓';
    b.classList.add('loading');
    var ok = false;
    try { ok = await window.approveCode(code, b, label); } catch(err){ ok = false; }
    b.classList.remove('loading');
    if (ok) {
      var row = b.closest('tr');
      if (row) { row.style.transition = 'opacity .3s'; row.style.opacity = '0';
        setTimeout(function(){ row.remove(); }, 320); }
      else { b.disabled = true; }
    }
  });
});
"""


# ------------------------------------------------------------- build the app

_SVG = {
    "overview": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "approvals": '<path d="M20 6L9 17l-5-5"/>',
    "outreach": '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/>',
    "products": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.3 7l8.7 5 8.7-5"/><path d="M12 22V12"/>',
    "drafts": '<path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',
    "fleet": '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>',
    "hive": '<path d="M12 2l8 4.5v9L12 20l-8-4.5v-9L12 2z"/><circle cx="12" cy="12" r="2.5"/>',
    "extras": '<circle cx="5" cy="12" r="1.6" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.6" fill="currentColor" stroke="none"/>',
    "captain": '<circle cx="12" cy="12" r="9"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/><circle cx="12" cy="12" r="2"/>',
    "taps": '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>',
    "sandbox": '<path d="M21 8l-9-5-9 5v8l9 5 9-5V8z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
    "universe": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><circle cx="18.5" cy="7.5" r="1.4" fill="currentColor" stroke="none"/>',
}
TABS = [("taps", "Action Center"), ("overview", "Overview"), ("universe", "Universe"), ("captain", "Captain"), ("sandbox", "Sandbox"), ("approvals", "Approvals"), ("outreach", "Outreach"),
        ("products", "Products"), ("drafts", "Drafts"), ("fleet", "Fleet"),
        ("hive", "Hive"), ("extras", "Extras")]


def _svg(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_SVG[name]}</svg>')


def _sec(eyebrow, title, lede=""):
    h = (f'<div class="sec-title"><div class="eyebrow">{esc(eyebrow)}</div>'
         f"<h2>{esc(title)}</h2>")
    if lede:
        h += f'<p class="lede">{lede}</p>'
    return h + "</div>"


def _extras_html():
    traffic = (
        '<div class=\"card\"><h3>Traffic — daily pageviews</h3>'
        '<p class=\"muted\">First-party counts from the site beacon (no Google, no cookies, '
        'no personal data). Real numbers only — days with no data show 0.</p>'
        '<div id=\"traffic-card\"><p class=\"muted\">Loading…</p></div>'
        '<script>'
        'async function loadTraffic(){'
        'var el=document.getElementById(\"traffic-card\");'
        'if(!el||typeof WURL===\"undefined\"||!WURL||!WKEY)'
        '{if(el)el.innerHTML=\"<p class=\'muted\'>Not connected: no admin key on this device.</p>\";return;}'
        'try{var r=await fetch(WURL+\"/traffic?key=\"+encodeURIComponent(WKEY));var d=await r.json();'
        'if(!d.ok||!d.days)throw 0;'
        'var days=d.days.slice(-14);'
        'var tot=days.reduce(function(s,x){return s+x.hits},0);'
        'var mx=Math.max.apply(null,days.map(function(x){return x.hits}).concat([1]));'
        'var h=\"<p><b>\"+tot+\"</b> pageviews in the last 14 days</p>\"'
        '+\"<div style=\'display:flex;align-items:flex-end;gap:4px;height:90px\'>\";'
        'days.forEach(function(x){var bh=Math.max(3,Math.round(x.hits/mx*84));'
        'h+=\"<div title=\'\"+x.date+\": \"+x.hits+\" pageviews\' style=\'flex:1;min-height:3px;height:\"+bh+\"px;'
        'background:var(--accent,#e07a5f)\'></div>\"});'
        'h+=\"</div><p class=\'muted\' style=\'display:flex\'><span>\"+days[0].date.slice(5)+\"</span>\"'
        '+\"<span style=\'margin-left:auto\'>\"+days[days.length-1].date.slice(5)+\"</span></p>\";'
        'el.innerHTML=h;}'
        'catch(e){el.innerHTML=\"<p class=\'muted\'>Traffic unavailable — the worker update hasn\\u2019t been deployed yet.</p>\"}}'
        'if(document.readyState===\"loading\"){document.addEventListener(\"DOMContentLoaded\",loadTraffic)}'
        'else{loadTraffic()}'
        '</script></div>'
    )
    return (
        S.directory_section() + S.tiktok_section() + traffic
        + '<div class="card"><h3>Auto-approval policy</h3>'
        '<p class="muted">Site development and publishing auto-approve. '
        "These always wait for a human tap: <b>" + ", ".join(S.HUMAN_KINDS) +
        "</b>. When in doubt, it waits for you.</p></div>"
        + '<div class="card"><h3>Outbound policy — full auto</h3>'
        '<p class="muted">Email sends itself within caps (5/run, 20/day UTC), '
        "opt-out footer, public business emails only. Social posts only where a "
        "channel is configured. Kill switch file: "
        '<span class="mono">hidden_files/outreach/STOP</span> — if it exists, '
        "every bot queues but never sends.</p></div>"
        + '<div class="card warn"><h3>Money boundary</h3>'
        '<p class="muted">Refunds, payouts, bank changes, fees, price changes, '
        "deletions, and identity checks are <b>never</b> automated — they wait for "
        "a human tap, always.</p></div>"
    )


# ---------------------------------------------------------------- hive tab

HIVE_DIR = os.path.expanduser("~/workspace/goals/kestrelattice-autonomous-growth/hive")

# Curated role -> group map. 103 roles total. Anything not listed lands in "Other".
_HIVE_ROLE_GROUPS = [
    ("Product forge", [
        "assessment-builder", "audit-tool-builder", "benchmark-compiler",
        "board-deck-outliner", "bundle-optimizer", "calculator-builder",
        "catalog-architect", "checklist-designer", "control-matrix-mapper",
        "evidence-checklist-writer", "exec-summary-writer", "glossary-builder",
        "incident-report-template-writer", "incident-to-playbook-writer",
        "manuscript-writer", "maturity-model-writer", "micro-forge-runner",
        "one-pager-writer", "policy-template-writer", "price-integrity-auditor",
        "product-brief-writer", "product-forge-runner", "quiz-builder",
        "regulation-brief-writer", "research-synthesizer", "risk-register-builder",
        "runbook-writer", "scorecard-designer", "sop-writer",
        "template-pack-assembler", "trend-to-product-translator",
        "vendor-questionnaire-builder", "whitepaper-drafter", "worksheet-designer",
        "workshop-kit-builder",
    ]),
    ("Publishing & catalog", [
        "catalog-builder", "cover-uploader", "gumroad-publisher",
        "marketplace-lister", "marketplace-scout", "publisher", "tag-sweeper",
        "thumbnail-maker",
    ]),
    ("Outreach & acquisition", [
        "affiliate-recruiter", "cart-abandon-email-writer",
        "email-deliverability-guard", "inbox-responder", "lead-deduplicator",
        "lead-scout", "outreach-analyst", "outreach-sender", "outreach-sync-runner",
        "partner-scout", "pitch-drafter", "pitch-personalizer",
        "testimonial-collector", "winback-email-writer",
    ]),
    ("Content & SEO", [
        "article-illustrator", "brand-content-writer", "content-drafter",
        "content-refresher", "content-repurposer", "faq-expander",
        "internal-link-strategist", "medium-republisher", "newsletter-compiler",
        "seo-meta-writer", "seo-writer", "transcript-writer",
    ]),
    ("Social & video", [
        "pinterest-publisher", "shorts-syndicator", "social-formatter",
        "thread-spotter", "tiktok-studio-runner", "video-caption-writer",
        "video-scripter",
    ]),
    ("Site ops", [
        "accessibility-auditor", "broken-embed-fixer", "image-alt-writer",
        "link-rot-hunter", "og-image-designer", "performance-auditor",
        "redirect-mapper", "schema-markup-writer", "site-health-checker",
        "site-improver", "site-updater", "sitemap-surgeon", "stale-date-sweeper",
    ]),
    ("Analytics & intel", [
        "competitor-price-tracker", "competitor-watch", "mention-watch",
        "review-miner", "sales-reporter", "sales-watch", "trend-radar",
    ]),
    ("Brain ops", [
        "approval-watcher-runner", "business-foundry-runner",
        "dashboard-refresh-runner", "ecosystem-expansion-runner", "model-refresh",
        "provider-scout", "watchdog",
    ]),
]


def _hive_read(name):
    """Read a hive live file at build time; None on any failure."""
    try:
        with open(os.path.join(HIVE_DIR, name)) as f:
            return f.read()
    except Exception:
        return None


def _hive_json(name):
    raw = _hive_read(name)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _hive_ago(ts):
    """'12m ago' for an ISO UTC timestamp; '?' when unparseable."""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        s = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
        if s < 60:
            return "just now"
        if s < 3600:
            return "%dm ago" % (s // 60)
        if s < 86400:
            return "%dh ago" % (s // 3600)
        return "%dd ago" % (s // 86400)
    except Exception:
        return "?"


def _hive_stale_dot(ts, warn_min=20, stale_min=60):
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        s = (datetime.now(timezone.utc) - dt).total_seconds()
        if s < warn_min * 60:
            return '<span class="dot ok"></span>'
        if s < stale_min * 60:
            return '<span class="dot warn"></span>'
        return '<span class="dot stale"></span>'
    except Exception:
        return '<span class="dot never"></span>'


def _hive_role_meta():
    """Parse roles/*.md -> {stem: {title, cost, purpose}}. Empty dict on failure."""
    meta = {}
    try:
        files = sorted(f for f in os.listdir(os.path.join(HIVE_DIR, "roles"))
                       if f.endswith(".md"))
    except Exception:
        return meta
    for f in files:
        stem = f[:-3]
        try:
            with open(os.path.join(HIVE_DIR, "roles", f), encoding="utf-8") as fh:
                txt = fh.read()
        except Exception:
            continue
        m = re.search(r"^# Role:\s*(.+)$", txt, re.M)
        title = m.group(1).strip() if m else stem
        m = re.search(r"^Cost class:\s*\*\*([a-z]+)\*\*", txt, re.M)
        cost = m.group(1) if m else "?"
        purpose = ""
        m = re.search(r"## Purpose\s*\n(.+?)(?:\n## |\Z)", txt, re.S)
        if m:
            for ln in m.group(1).splitlines():
                ln = ln.strip()
                if ln:
                    purpose = ln[:150]
                    break
        meta[stem] = {"title": title, "cost": cost, "purpose": purpose}
    return meta


def _hive_html():
    st = _hive_json("state.json") or {}
    tasks = []
    raw_tasks = _hive_read("tasks.jsonl")
    if raw_tasks:
        for line in raw_tasks.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                tasks.append(json.loads(line))
            except Exception:
                continue
    mig = _hive_json("migration.json") or {}
    blog_lines = (_hive_read("brain.log") or "").splitlines()
    role_meta = _hive_role_meta()

    # ---------------- queue depth ----------------
    from collections import Counter
    qdepth = Counter(t.get("status") or "unknown" for t in tasks)
    depth_html = (
        '<div class="statrow">'
        + "".join(
            f'<div class="stat"><b>{qdepth.get(s, 0)}</b><span>{s}</span></div>'
            for s in ("pending", "claimed", "running", "done", "failed", "parked")
            if qdepth.get(s, 0) or s in ("pending", "done"))
        + "</div>"
        + f'<p class="muted">{len(tasks)} tasks total in tasks.jsonl</p>')

    # ---------------- brain status + worker pool ----------------
    mode = "unavailable"
    for ln in reversed(blog_lines[-12:]):
        if "LIVE" in ln:
            mode = "LIVE"
            break
        if "SHADOW" in ln:
            mode = "SHADOW"
            break
    hb = st.get("brain_heartbeat") or "unavailable"
    dag = st.get("active_dag") or "unavailable"

    # per-worker completed/failed from tasks.jsonl claimed_by
    wstats = {}
    for t in tasks:
        cb = t.get("claimed_by")
        if not cb:
            continue
        wstats.setdefault(cb, Counter())[t.get("status") or "unknown"] += 1

    workers = st.get("workers") or {}
    wrows = ""
    for w in sorted(workers.keys()):
        v = workers.get(w) or {}
        whb = v.get("heartbeat") or "no heartbeat"
        cur = v.get("task")
        cur_html = (f'<span class="mono">{esc(str(cur))}</span>' if cur
                    else '<span class="muted">idle</span>')
        ws = wstats.get(w, Counter())
        done_n = ws.get("done", 0)
        fail_n = ws.get("failed", 0) + ws.get("parked", 0)
        wrows += (
            f"<tr><td>{_hive_stale_dot(whb)}<span class='mono'>{esc(w)}</span></td>"
            f"<td><span class='mono'>{esc(str(whb))}</span><br>"
            f"<span class='muted'>{esc(_hive_ago(whb))}</span></td>"
            f"<td>{cur_html}</td>"
            f"<td><b>{done_n}</b> done<br><span class='muted'>{fail_n} failed/parked</span></td></tr>")
    if not wrows:
        wrows = '<tr><td colspan="4" class="muted">worker info unavailable</td></tr>'
    worker_card = (
        '<div class="card"><h3>Brain status</h3>'
        f'<p>{_hive_stale_dot(hb)}<span class="pill ok">{esc(mode)}</span> '
        f'<span class="muted">heartbeat</span> <span class="mono">{esc(hb)}</span> '
        f'<span class="muted">({esc(_hive_ago(hb))})</span></p>'
        f'<p><span class="muted">Active DAG</span> '
        f'<span class="mono">{esc(dag)}</span></p>'
        '<h3 style="margin-top:14px">Queue depth</h3>' + depth_html
        + '<h3 style="margin-top:14px">Worker pool — 6 slots</h3>'
        '<div class="table-wrap"><table><thead><tr>'
        '<th>Worker</th><th>Last heartbeat</th><th>Current task</th>'
        '<th>Completed / failed</th>'
        "</tr></thead><tbody>" + wrows + "</tbody></table></div>"
        '<p class="legend"><span class="dot ok"></span>fresh (&lt;20m) '
        '<span class="dot warn"></span>aging (&lt;60m) '
        '<span class="dot stale"></span>stale</p></div>')

    # ---------------- free-tier quotas ----------------
    def _hive_lane_caps():
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                "hive_worker_consts", os.path.join(HIVE_DIR, "worker.py"))
            _mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            return (dict(_mod.FREE_LANE_DAILY_TOKENS),
                    int(_mod.FLEET_DAILY_TOKENS_CAP))
        except Exception:
            return {}, 0

    quotas = st.get("quotas") or {}
    lane_caps, fleet_cap = _hive_lane_caps()
    used = quotas.get("fleet_tokens") or 0
    try:
        used = int(used)
        pct = (used / fleet_cap * 100) if fleet_cap else 0
        quota_bar = (
            '<div style="background:var(--panel2);border:1px solid var(--line);'
            'border-radius:8px;height:14px;overflow:hidden;margin:8px 0 4px">'
            f'<div style="height:100%;width:{min(100, pct):.2f}%;'
            'background:linear-gradient(90deg,var(--accent),#ef9278)"></div></div>'
            f'<p class="muted">{used:,} of {fleet_cap:,} free-tier tokens/day'
            f' &middot; {pct:.2f}% used &middot; cycle {esc(str(quotas.get("cycle", "?")))}'
            f' &middot; <b>$0.00 actually spent</b>'
            + (" &middot; <b>THROTTLED</b>" if quotas.get("throttled") else "")
            + '</p>'
            '<p class="muted">Token counts are estimates — the dispatcher reports no '
            'usage. Paid inference is structurally disabled fleet-wide, so actual '
            'spend is always $0.</p>')
    except Exception:
        quota_bar = '<p class="muted">Quota data unavailable</p>'
    lanes = quotas.get("lanes") or {}
    exhausted = set(quotas.get("lanes_exhausted") or [])
    lane_rows = ""
    for lane in list(lane_caps) + [l for l in lanes if l not in lane_caps]:
        lcap = lane_caps.get(lane)
        lu = int(lanes.get(lane, 0) or 0)
        lpct = (lu / lcap * 100) if lcap else 0
        cap_txt = f"{lcap:,}" if lcap else "fleet-governed"
        ex = " <b>EXHAUSTED</b>" if lane in exhausted else ""
        lane_rows += (
            f"<tr><td><span class='mono'>{esc(str(lane))}</span></td>"
            f"<td>{lu:,} / {cap_txt}</td><td>{lpct:.1f}%{ex}</td></tr>")
    by_task = quotas.get("by_task") or {}
    bt_rows = "".join(
        f"<tr><td><span class='mono'>{esc(str(k))}</span></td>"
        f"<td>~{esc(str(v))} tokens</td></tr>"
        for k, v in sorted(by_task.items(), key=lambda kv: -(kv[1] or 0)))

    def _pc_cost(e):
        # Historical rows (pre-2026-10-01) carry usd_est: label as estimate.
        if e.get("lane"):
            return esc(str(e["lane"]))
        if e.get("usd_est") is not None:
            return f"~${float(e.get('usd_est') or 0):.6f} est."
        return "—"

    per_cycle = quotas.get("per_cycle") or []
    pc_rows = "".join(
        f"<tr><td><span class='mono'>{esc(str(e.get('ts', '')))}</span></td>"
        f"<td><span class='mono'>{esc(str(e.get('actor', '')))}</span></td>"
        f"<td><span class='mono'>{esc(str(e.get('task_id') or '—'))}</span></td>"
        f"<td>{e.get('tokens_est') or 0}</td>"
        f"<td>{_pc_cost(e)}</td>"
        f"<td class='muted'>{esc(str(e.get('note', ''))[:80])}</td></tr>"
        for e in per_cycle[-6:])
    budget_card = (
        '<div class="card"><h3>Free-tier quotas — daily AI usage</h3>' + quota_bar
        + ('<h3 style="margin-top:14px">Usage by lane</h3>'
           '<div class="table-wrap"><table><thead><tr><th>Lane</th>'
           '<th>Tokens used / daily cap</th><th>%</th></tr></thead><tbody>'
           + lane_rows + '</tbody></table></div>' if lane_rows else
           '<p class="muted">No lane usage recorded yet today.</p>')
        + ('<h3 style="margin-top:14px">Usage by task</h3>'
           '<div class="table-wrap"><table><thead><tr><th>Task</th>'
           '<th>Tokens (est)</th></tr></thead><tbody>' + bt_rows +
           '</tbody></table></div>' if bt_rows else
           '<p class="muted">No task-level usage recorded yet.</p>')
        + ('<h3 style="margin-top:14px">Recent ledger entries</h3>'
           '<div class="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th>'
           '<th>Task</th><th>Tokens</th><th>Lane / cost</th><th>Note</th></tr></thead>'
           '<tbody>' + pc_rows + '</tbody></table></div>' if pc_rows else '')
        + '</div>')

    # ---------------- migration board ----------------
    migrations = mig.get("migrations") or []
    active = [m for m in migrations if m.get("status") == "legacy-active"]
    retired = [m for m in migrations if m.get("status") not in ("legacy-active", None)]

    def _mig_row(m):
        cs = m.get("consecutive_successes") or 0
        pct3 = min(100, cs / 3 * 100)
        hold = m.get("execution_hold")
        pill = ('<span class="pill warn">eligible</span>' if cs >= 3
                else '<span class="pill">legacy-active</span>')
        lr = m.get("last_run") or {}
        lr_txt = (f"{lr.get('ts', '')} · {lr.get('task_id', '')} · {lr.get('status', '')}"
                  if lr else "no hive run yet")
        bar = ('<div class="bar" style="margin:6px 0 2px"><div class="bar-fill" '
               f'style="width:{pct3:.0f}%"></div></div>')
        return (
            f"<tr><td><span class='mono'>{esc(m.get('cron_id', ''))}</span>"
            + (f"<br><span class='muted' style='font-size:.76rem'>⏸ {esc(str(hold)[:90])}</span>"
               if hold else "")
            + "</td>"
            f"<td><span class='mono' style='font-size:.78rem'>"
            + ", ".join(esc(str(r)) for r in (m.get("absorbing_roles") or []))
            + "</span></td>"
            f"<td>{bar}<span class='muted'>{cs}/3 consecutive successes</span></td>"
            f"<td>{pill}</td>"
            f"<td class='muted' style='font-size:.78rem'>{esc(lr_txt[:90])}</td></tr>")

    active_sorted = sorted(active,
                           key=lambda m: (-(m.get("consecutive_successes") or 0),
                                          m.get("cron_id", "")))
    mig_table = (
        '<div class="table-wrap"><table><thead><tr><th>Legacy cron</th>'
        '<th>Absorbing role(s)</th><th>Retirement progress</th><th>Status</th>'
        '<th>Last hive run</th></tr></thead><tbody>'
        + "".join(_mig_row(m) for m in active_sorted)
        + "</tbody></table></div>")
    n_elig = sum(1 for m in active if (m.get("consecutive_successes") or 0) >= 3)
    mig_card = (
        '<div class="card"><h3>Migration — legacy crons → hive roles</h3>'
        '<div class="statrow">'
        f'<div class="stat"><b>{len(active)}</b><span>legacy-active</span></div>'
        f'<div class="stat"><b>{len(retired)}</b><span>retired</span></div>'
        f'<div class="stat"><b>{n_elig}</b><span>eligible to retire (3+ consecutive successes)</span></div>'
        "</div>"
        + ("<p class='muted'>Retired: " + ", ".join(
               f'<span class="mono">{esc(m.get("cron_id", ""))}</span>' for m in retired)
           + "</p>" if retired else
           '<p class="muted">No legacy cron retired yet — none has 3 consecutive '
           'successful hive runs absorbing its job. Legacy crons are DISABLED, never deleted.</p>')
        + f'<details class="fold"><summary>All {len(active)} legacy-active crons '
           f'with retirement progress</summary>{mig_table}</details>'
        + f'<p class="muted">Snapshot: {esc(str(mig.get("generated_at") or "unavailable"))}</p></div>')

    # ---------------- role roster ----------------
    mapped = set()
    for _g, _names in _HIVE_ROLE_GROUPS:
        mapped.update(_names)
    unmapped = sorted(s for s in role_meta if s not in mapped)
    groups = list(_HIVE_ROLE_GROUPS)
    if unmapped:
        groups.append(("Other", unmapped))
    roster = ""
    total_roles = len(role_meta)
    for gname, names in groups:
        items = []
        for stem in sorted(names):
            meta = role_meta.get(stem)
            if not meta:
                items.append(f"<li><span class='mono'>{esc(stem)}</span> "
                             "<span class='muted'>(role file missing)</span></li>")
                continue
            items.append(
                f"<li><b>{esc(meta['title'])}</b> "
                f"<span class='pill'>{esc(meta['cost'])}</span><br>"
                f"<span class='muted'>{esc(meta['purpose'])}</span></li>")
        roster += (
            f'<details class="fold"><summary><b>{esc(gname)}</b> '
            f'— {len(names)} roles</summary><ul class="feed">'
            + "".join(items) + "</ul></details>")
    roles_card = (
        '<div class="card ok-card"><h3>Role roster — 103 specialist roles</h3>'
        f'<p><b>{total_roles}</b> substantive role files on disk '
        '(the plan said 100; the real count is 103 — shown honestly).</p>'
        '<p class="muted">Cost classes: cheap = dispatcher text · standard = '
        'dispatcher + file writes · browser = needs browser task · heavy = long builds.</p>'
        + (roster or '<p class="muted">Roles directory unavailable</p>') + '</div>')

    # ---------------- tasks table ----------------
    pill_cls = {"done": "ok", "parked": "warn", "failed": "blocked"}
    trows = ""
    for t in tasks:
        ts = t.get("status") or "unknown"
        cls = pill_cls.get(ts, "")
        when = t.get("completed_at") or t.get("started_at") or t.get("created_at") or ""
        cb = t.get("claimed_by") or "—"
        trows += (f'<tr data-status="{esc(ts)}">'
                  f'<td><span class="mono">{esc(t.get("id") or "")}</span></td>'
                  f'<td><span class="mono">{esc(t.get("role") or "")}</span></td>'
                  f'<td>{esc(t.get("title") or "")}</td>'
                  f'<td><span class="pill {cls}">{esc(ts)}</span></td>'
                  f'<td><span class="mono">{esc(str(cb))}</span></td>'
                  f'<td>{t.get("attempts") or 0}</td>'
                  f'<td><span class="mono">{esc(str(when))}</span></td></tr>')
    tasks_card = (
        '<div class="card"><h3>Live task queue</h3>'
        '<label class="muted" style="font-size:.8rem">Status filter: '
        '<select id="hive_status_filter" onchange="hiveFilter()" '
        'style="background:var(--panel2);color:var(--text);border:1px solid '
        'var(--line2);border-radius:8px;padding:6px 10px;font-size:.82rem">'
        '<option value="all">all</option><option value="pending">pending</option>'
        '<option value="claimed">claimed</option><option value="running">running</option>'
        '<option value="done">done</option><option value="failed">failed</option>'
        '<option value="parked">parked</option></select></label>'
        f'<div class="table-wrap"><table id="hive_tasks_table"><thead><tr>'
        f'<th>Task</th><th>Role</th><th>Title</th><th>Status</th>'
        f'<th>Claimed by</th><th>Attempts</th><th>Time</th>'
        f'</tr></thead><tbody>{trows or "<tr><td colspan=7 class=muted>no tasks</td></tr>"}</tbody></table></div>'
        '<script>function hiveFilter(){var s=document.getElementById('
        "'hive_status_filter').value;var tb=document.getElementById("
        "'hive_tasks_table').getElementsByTagName('tbody')[0];"
        'for(var i=0;i<tb.rows.length;i++){var r=tb.rows[i];'
        "r.style.display=(s==='all'||r.getAttribute('data-status')===s)?'':'none';}}</script>"
        '</div>')

    # ---------------- parked + retry queue ----------------
    def _task_reason(t):
        res = t.get("result") or {}
        if isinstance(res, dict):
            return res.get("reason") or res.get("error") or ""
        return str(res)[:200]

    parked = [t for t in tasks if t.get("status") == "parked"]
    retrying = [t for t in tasks
                if (t.get("status") in ("failed", "pending", "claimed", "running"))
                and (t.get("attempts") or 0) > 0]
    pq_rows = "".join(
        f"<tr><td><span class='mono'>{esc(t.get('id') or '')}</span></td>"
        f"<td>{esc(t.get('title') or '')}</td>"
        f"<td>{esc(_task_reason(t) or 'no reason recorded')}</td>"
        f"<td>{t.get('attempts') or 0}</td></tr>" for t in parked)
    rq_rows = "".join(
        f"<tr><td><span class='mono'>{esc(t.get('id') or '')}</span></td>"
        f"<td><span class='mono'>{esc(t.get('role') or '')}</span></td>"
        f"<td><span class='pill'>{esc(t.get('status') or '')}</span></td>"
        f"<td>{esc(_task_reason(t) or 'retrying')}</td>"
        f"<td>{t.get('attempts') or 0}/3</td></tr>" for t in retrying)
    parked_card = (
        '<div class="card warn"><h3>Parked tasks — needs attention</h3>'
        + (f'<div class="table-wrap"><table><thead><tr><th>Task</th><th>Title</th>'
            f'<th>Parked reason</th><th>Attempts</th></tr></thead>'
            f'<tbody>{pq_rows}</tbody></table></div>' if pq_rows else
            '<p class="muted">Nothing parked.</p>') + '</div>')
    retry_card = (
        '<div class="card"><h3>Retry queue</h3>'
        + (f'<div class="table-wrap"><table><thead><tr><th>Task</th><th>Role</th>'
            f'<th>Status</th><th>Reason</th><th>Attempts</th></tr></thead>'
            f'<tbody>{rq_rows}</tbody></table></div>'
            '<p class="muted">Max 3 attempts — then the brain parks the task.</p>'
            if rq_rows else
            '<p class="muted">No tasks currently retrying.</p>') + '</div>')

    # ---------------- brain log ----------------
    log_card = (
        '<div class="card"><h3>Brain log — last 12 lines</h3>'
        '<pre class="mono" style="white-space:pre-wrap;overflow-x:auto">'
        + esc("\n".join(blog_lines[-12:]) or "log unavailable") + '</pre></div>')

    return (worker_card + budget_card + roles_card + mig_card + tasks_card
            + parked_card + retry_card + log_card)


# ---------------------------------------------------------------- captain tab

SENT_DIR = os.path.expanduser("~/workspace/sentience")


def _sent_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def _sent_lines(path):
    try:
        with open(path) as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    except Exception:
        return []


def _captain_html():
    status = _sent_json(os.path.join(SENT_DIR, "state/status.json"), {})
    needs = []
    for ln in _sent_lines(os.path.join(SENT_DIR, "state/needs_human.jsonl")):
        try:
            needs.append(json.loads(ln))
        except Exception:
            pass
    pending_cmds = _sent_lines(os.path.join(SENT_DIR, "inbox/commands.jsonl"))
    try:
        soul = open(os.path.join(SENT_DIR, "SOUL.md")).read().splitlines()
        soul_ex = "\n".join(soul[6:18])
    except Exception:
        soul_ex = "Soul not written yet."

    jars = []
    for b in BRANDS:
        j = _sent_json(os.path.join(SENT_DIR, "brands", b["slug"], "JAR.json"), None)
        if j:
            jars.append((b["name"], j))

    def ago(ts):
        return esc(str(ts)) if ts else "<span class='muted'>not yet</span>"

    status_card = (
        '<div class="card"><h3>Status</h3>'
        f"<p>Operator last run: {ago(status.get('operator_last_run'))}<br>"
        f"Reflection last run: {ago(status.get('reflect_last_run'))}<br>"
        f"Commands waiting in inbox: <b>{len(pending_cmds)}</b><br>"
        f"Items needing your tap: <b>{len(needs)}</b></p>"
        "<p class='muted'>Loops: operator every ~15 min, reflection daily. "
        "It shapes its own soul as it learns — the guardrails stay yours.</p></div>"
    )
    soul_card = (
        '<div class="card"><h3>Soul <span class="muted">(co-edit SOUL.md to shape who it becomes)</span></h3>'
        f"<pre class='mono' style='white-space:pre-wrap'>{esc(soul_ex)}</pre></div>"
    )
    if needs:
        rows = "".join(
            f"<tr><td><b>{esc(n.get('title', ''))}</b><br><span class='muted'>"
            f"{esc(n.get('detail', ''))}</span></td>"
            f"<td>{esc(n.get('tap', 'your tap'))}</td></tr>" for n in needs)
        needs_html = ('<div class="card"><h3>Needs your tap</h3>'
                      '<div class="table-wrap"><table><tr><th>Item</th><th>Tap</th></tr>'
                      + rows + "</table></div></div>")
    else:
        needs_html = ('<div class="card"><h3>Needs your tap</h3>'
                      "<p class='muted'>Nothing waiting. It handles the rest on its own.</p></div>")
    if jars:
        jrows = "".join(
            f"<tr><td><b>{esc(name)}</b></td><td>${j.get('allocation_usd', 0):,.0f}</td>"
            f"<td>${j.get('income_usd', 0):,.0f}</td><td>${j.get('spent_usd', 0):,.0f}</td>"
            f"<td><b>${j.get('balance_usd', 0):,.0f}</b></td></tr>" for name, j in jars)
        jars_html = ('<div class="card"><h3>Brand money jars</h3>'
                     '<div class="table-wrap"><table><tr><th>Brand</th><th>Allocated</th>'
                     "<th>Earned</th><th>Spent</th><th>Balance</th></tr>"
                     + jrows + "</table></div>"
                     "<p class='muted'>Jars are budget ledgers backed by real allocations you approve. "
                     "Real funds always flow through your accounts.</p></div>")
    else:
        jars_html = ""
    chat_html = """
<div class="card"><h3>Talk to Sentience</h3>
<p class='muted'>Me-shaped: same soul, same memory, its own wants. <b>Live now in the
<i>Talk to the bots</i> chat</b> — it answers there and queues your commands straight
into its inbox. Talk to the same Sentience right here:</p>
<div id="sent-thread" class="chat-thread"><p class="muted">Loading...</p></div>
<div class="chat-input"><input id="sent-input" type="text" placeholder="Talk to it like you talk to me..." maxlength="2000"><button class="btn" id="sent-send">Send</button></div>
</div>
<script>(function(){
function escH(s){var d=document.createElement("div");d.appendChild(document.createTextNode(s));return d.innerHTML;}
async function sentLoad(){
var thread=document.getElementById("sent-thread");
if(!thread||typeof WURL==="undefined"||!WURL||!WKEY){if(thread)thread.innerHTML="<p class='muted'>Not connected: no admin key on this device.</p>";return;}
if(document.hidden)return;
try{
var r=await fetch(WURL+"/sentience-chat?key="+encodeURIComponent(WKEY));
var msgs=await r.json();
var sig=(Array.isArray(msgs)?msgs.length:0)+"|"+((msgs&&msgs[msgs.length-1]||{}).text||"").length;
if(sig===thread._sig)return;
var newN=Array.isArray(msgs)?msgs.length-(thread._len||0):0;
thread._sig=sig;thread._len=Array.isArray(msgs)?msgs.length:0;
if(!Array.isArray(msgs)||!msgs.length){thread.innerHTML="<p class='muted'>No messages yet. Say hi.</p>";return;}
var typing=document.activeElement&&document.activeElement.id==="sent-input";
var wasBottom=(thread.scrollHeight-thread.scrollTop-thread.clientHeight)<90;
var st=thread.scrollTop;
thread.innerHTML=msgs.map(function(m){
var who=m.from==="koalstin"?"you":"sentience";
return '<div class="chat-msg '+who+'"><span class="chat-who">'+who+'</span><p>'+escH(m.text)+"</p></div>";
}).join("");
if(wasBottom&&!typing){thread.scrollTop=thread.scrollHeight;}
else{thread.scrollTop=st;}
}catch(e){if(!thread.innerHTML)thread.innerHTML="<p class='muted'>Couldn't load.</p>";}}
async function sentSend(){
var input=document.getElementById("sent-input"),btn=document.getElementById("sent-send");
var text=input.value.trim();
if(!text||typeof WURL==="undefined"||!WURL||!WKEY)return;
btn.disabled=true;
try{
await fetch(WURL+"/sentience-chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,text:text})});
input.value="";await sentLoad();
}catch(e){}
btn.disabled=false;}
document.addEventListener("DOMContentLoaded",function(){
var btn=document.getElementById("sent-send"),input=document.getElementById("sent-input");
if(btn)btn.addEventListener("click",sentSend);
if(input)input.addEventListener("keydown",function(e){if(e.key==="Enter")sentSend();});
sentLoad();setInterval(sentLoad,20000);});
})();</script>
"""
    return status_card + soul_card + needs_html + jars_html + chat_html


def _sandbox_html():
    """Sandbox tab, chat-first: a conversation list (one thread per bot) that
    opens into a real thread view with bubbles and a composer. Broadcast to
    all quarantined bots is a composer action. Everything else the tab ever
    had (transcript feed, invention shelf, bot roster, rogue management,
    sandbox switcher, manual quarantine) is preserved below in tidy sections.
    Plain-English throughout."""
    scoped_css = """<style>.sb-chat-app{background:var(--panel);border:1px solid var(--line);border-radius:22px;overflow:hidden;margin:18px 0;box-shadow:var(--shadow)}.sb-chat-head{display:flex;align-items:center;justify-content:space-between;padding:18px 18px 4px}.sb-chat-head h3{margin:0;font-size:1.08rem}.sb-convos{padding:6px 8px 12px}.crow{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:transparent;border:0;padding:11px 10px;border-radius:16px;cursor:pointer;font-family:inherit;color:var(--text);min-height:64px}.crow:hover{background:var(--panel2)}.crow:active{background:var(--panel2)}.ava{width:46px;height:46px;border-radius:50%;flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:1.15rem;color:#fff}.ava.sm{width:30px;height:30px;font-size:.8rem}.crow .cmeta{flex:1;min-width:0;display:flex;flex-direction:column}.crow .cname{font-weight:700;font-size:.95rem;display:flex;align-items:center;gap:8px}.crow .cprev{color:var(--muted);font-size:.83rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}.crow .ctime{color:var(--faint);font-size:.72rem;flex:0 0 auto}.crow .chev{color:var(--faint);font-size:1.25rem;flex:0 0 auto;padding-right:2px}.sb-threadview{display:none}.sb-threadview.open{display:block;animation:rise .22s ease}.thread-head{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--line);background:var(--panel2)}.thread-head .back{width:40px;height:40px;border-radius:50%;border:1px solid var(--line2);background:var(--panel);color:var(--text);cursor:pointer;font-size:1.2rem;display:flex;align-items:center;justify-content:center;flex:0 0 auto}.thread-head .cmeta{flex:1;min-width:0;display:flex;flex-direction:column}.thread-head .cname{font-weight:750;font-size:1rem}.thread-head .cprev{color:var(--muted);font-size:.78rem}#sb-chat-thread{max-height:52vh;min-height:300px;padding:14px}.msg-row{display:flex;gap:8px;align-items:flex-end;margin:2px 0}.msg-row.you{flex-direction:row-reverse}.msg-row .chat-msg{margin:0}.msg-time{font-size:.68rem;color:var(--faint);margin:3px 6px 0}.msg-row.you .msg-time{text-align:right}.composer{display:flex;gap:8px;padding:12px 14px;border-top:1px solid var(--line);background:var(--panel);align-items:center}.composer input{flex:1;background:var(--panel2);border:1px solid var(--line2);color:var(--text);border-radius:999px;padding:13px 18px;font-size:.95rem;font-family:inherit;min-width:0}.composer input:focus{outline:none;border-color:var(--accent)}.composer .send{width:48px;height:48px;border-radius:50%;border:0;flex:0 0 auto;background:linear-gradient(135deg,var(--accent),var(--accent-deep));color:#fff;font-size:1.25rem;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow)}.composer .send:disabled{opacity:.5}.bc-toggle{width:48px;height:48px;border-radius:50%;border:1px solid var(--line2);background:var(--panel2);color:var(--muted);font-size:1.2rem;cursor:pointer;flex:0 0 auto;display:flex;align-items:center;justify-content:center}.bc-toggle.on{background:var(--accent);border-color:var(--accent);color:#fff}#sb-bc-hint{display:none;padding:0 18px 12px;font-size:.78rem;color:var(--accent)}#sb-bc-hint.on{display:block}.sb-idea-row{display:flex;justify-content:flex-start;gap:10px;flex-wrap:wrap;margin:0 0 8px}.sb-sys{text-align:center;color:var(--muted);font-size:.84rem;padding:8px 0}select.sb-select{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:14px;padding:12px;font-size:.92rem;font-family:inherit;max-width:100%;min-height:48px}.sb-pills{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.sb-pill{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:999px;padding:11px 20px;font-size:.9rem;font-family:inherit;cursor:pointer;min-height:44px}.sb-pill.active{background:var(--accent);border-color:transparent;color:#fff;font-weight:600}.sb-bot{background:var(--panel2);border:1px solid var(--line);border-radius:18px;padding:16px}.sb-bot h4{margin:2px 0 6px;font-size:1.02rem}.sb-dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#39d353;margin-right:8px}.sb-dot.idle{background:#9aa0a6}.sb-move-row{display:none;margin-top:8px}.sb-opt{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;margin:10px 0}.sb-opt p{margin:4px 0 10px}.sb-opt input[type=email],.sb-field input{width:100%;box-sizing:border-box;background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:14px;padding:13px 16px;font-size:.92rem;font-family:inherit;margin-top:6px}.sb-field{display:block;margin:10px 0;font-size:.88rem}#sb-retire:disabled{opacity:.45;cursor:not-allowed}.sb-inv-bot{margin:16px 0 6px}details.sb-fold{background:var(--panel);border:1px solid var(--line);border-radius:20px;margin:14px 0;overflow:hidden}details.sb-fold>summary{cursor:pointer;padding:16px 18px;font-weight:700;font-size:1rem;list-style:none}details.sb-fold>summary::-webkit-details-marker{display:none}details.sb-fold .fold-body{padding:0 18px 18px}.room-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin:14px 0}.room-card{border-radius:22px;overflow:hidden;border:1px solid var(--line);background:var(--panel2);box-shadow:var(--shadow);display:flex;flex-direction:column}.room-hero{padding:22px 20px 18px;color:#fff;position:relative;min-height:148px;display:flex;flex-direction:column;justify-content:flex-end}.room-hero .room-theme{font-size:1.22rem;font-weight:800;text-shadow:0 2px 12px rgba(0,0,0,.5);margin:0;line-height:1.3}.room-hero .room-bot{display:flex;align-items:center;gap:10px;margin-bottom:10px}.room-hero .room-bot .ava{background:rgba(255,255,255,.25)!important;backdrop-filter:blur(4px)}.room-body{padding:16px 18px;display:flex;flex-direction:column;gap:10px;flex:1}.room-desc{font-size:.9rem;line-height:1.55;color:var(--text);margin:0}.room-motto{font-style:italic;color:var(--muted);font-size:.88rem;border-left:3px solid var(--accent);padding-left:12px;margin:0}.room-stats{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:6px}.room-stat{font-size:.76rem;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:6px 12px;color:var(--muted)}.room-procs{font-size:.8rem;color:var(--muted);margin:0;padding:0}.room-procs li{margin:3px 0;list-style:none}.room-undesigned{padding:36px 20px;text-align:center;color:var(--muted);background:var(--panel2)}.room-hist{margin:2px 0;border:1px solid var(--line);border-radius:14px;overflow:hidden}.room-hist>summary{cursor:pointer;padding:10px 14px;font-size:.82rem;font-weight:700;color:var(--accent);list-style:none}.room-hist>summary::-webkit-details-marker{display:none}.room-hist-v{padding:10px 14px;border-top:1px solid var(--line);font-size:.82rem}.room-hist-t{font-weight:700;color:var(--text)}.room-hist-t span{font-weight:400;color:var(--faint);font-size:.75rem;margin-left:6px}.room-hist-c{color:var(--muted);font-size:.76rem;margin:2px 0}.room-hist-v p{margin:4px 0;line-height:1.5}</style>"""
    chats = """<div class="sb-chat-app" id="sb-chat-app"><div id="sb-convos-wrap"><div class="sb-chat-head"><h3>&#128172; Chats</h3><span class="muted" style="font-size:.78rem" id="sb-chats-count"></span></div><div id="sb-convos" class="sb-convos"><p class="muted" style="padding:14px">Loading chats&#8230;</p></div></div><div id="sb-threadview" class="sb-threadview"><div class="thread-head"><button class="back" id="sb-thread-back" aria-label="Back to chats">&#8592;</button><span class="ava" id="sb-thread-ava">?</span><div class="cmeta"><div class="cname" id="sb-thread-name">Bot</div><div class="cprev" id="sb-thread-sub"></div></div></div><div id="sb-chat-thread" class="chat-thread"><p class="muted">Loading&#8230;</p></div><div class="composer"><button class="bc-toggle" id="sb-bc-toggle" title="Broadcast: send to every quarantined bot at once">&#128226;</button><input id="sb-chat-input" type="text" placeholder="Message&#8230;" maxlength="2000" autocomplete="off"><button class="send" id="sb-chat-send" aria-label="Send">&#10148;</button></div><p id="sb-bc-hint">&#128226; Broadcast mode &#8212; your message goes to every quarantined bot at once.</p></div></div>"""
    transcript = """<div class="card"><h3>&#128064; Sandbox feed</h3><p class='muted'>Everything the bots in this sandbox say and do, newest at the bottom, refreshed every 10 seconds. This is just a window in &#8212; they can't touch your business from here.</p><div id="sb-transcript" class="chat-thread" style="max-height:380px"><p class="muted">Loading&#8230;</p></div></div>"""
    inventions = """<div class="card"><h3>&#128161; Invention shelf</h3><p class='muted'>Bots here are encouraged to invent &#8212; new pitches, product concepts, wild ideas. Everything they invent lands here as a draft. It only becomes real when you tap Promote.</p><div id="sb-inventions"><p class="muted">Loading&#8230;</p></div></div>"""
    rooms = """<div class="card"><h3>&#127963;&#65039; Bot rooms</h3><p class='muted'>Each bot designed its own room inside its private machine. Walk through them — new designs and redecorations appear here on their own.</p><div id="sb-rooms"><p class="muted" style="padding:14px">Loading rooms&#8230;</p></div></div>"""

    manage = """<details class='sb-fold'><summary>&#129302; Bots &amp; sandboxes &#8212; manage</summary><div class='fold-body'><div class="card" style="margin:0 0 14px"><h3>&#129521; Your sandboxes</h3><p class='muted'>A sandbox is a separate safe play-pen. Bots in one can't see or touch the others.</p><div id="sb-switcher" class="sb-pills"><p class="muted">Loading&#8230;</p></div><p id="sb-purpose" class="muted"></p><div class="sb-idea-row" style="margin-top:6px"><button class="btn btn-sm btn-ghost" id="sb-new-toggle">&#10133; New sandbox</button><button class="btn btn-sm btn-ghost" id="sb-retire" style="display:none">&#128465; Retire this sandbox</button></div><p id="sb-retire-note" class="muted"></p><div id="sb-new-form" style="display:none;margin-top:12px"><p class='muted' style='margin-bottom:4px'>Give it a name and say what it's for.</p><label class="sb-field">Name it<input id="sb-new-name" type="text" placeholder="e.g. Experiment: new pricing angles" maxlength="120"></label><label class="sb-field">What is it for?<input id="sb-new-purpose" type="text" placeholder="e.g. Try out risky ideas without touching the real business" maxlength="500"></label><button class="btn btn-sm" id="sb-new-go">Create sandbox</button><p class='muted'>You can retire a sandbox when it's empty.</p></div></div><div id="sb-roster"></div><div id="sb-rogues"></div><div id="sb-manual-q"></div></div></details>"""
    script = """<script>(function(){
var SB_DOWN="Couldn't reach the Sandbox — the worker update may not be deployed yet.";
var SB_ERR="<p class='muted'>"+SB_DOWN+"</p>";
function escH(s){var d=document.createElement("div");d.appendChild(document.createTextNode(s===null||s===undefined?"":String(s)));return d.innerHTML;}
function escA(s){return escH(s).replace(/'/g,"&#39;").replace(/"/g,"&quot;");}
function sbReady(){return !(typeof WURL==="undefined"||!WURL||!WKEY);}
function sbTime(ts){if(!ts)return "";try{var d=new Date(ts);if(isNaN(d.getTime()))return escH(String(ts));return d.toLocaleString();}catch(e){return escH(String(ts));}}
function sbTimeShort(ts){try{var d=new Date(ts);if(isNaN(d.getTime()))return "";return d.toLocaleTimeString([],{hour:"numeric",minute:"2-digit"});}catch(e){return "";}}
function sbRelTime(ts){try{var d=new Date(ts).getTime();if(isNaN(d))return "";var s=Math.max(0,Math.floor((Date.now()-d)/1000));if(s<60)return "now";var m=Math.floor(s/60);if(m<60)return m+"m";var h=Math.floor(m/60);if(h<24)return h+"h";return Math.floor(h/24)+"d";}catch(e){return "";}}
function sbAvaColor(name){var h=0;var n=String(name||"?");for(var i=0;i<n.length;i++)h=(h*31+n.charCodeAt(i))%360;return "hsl("+h+",48%,40%)";}
var sbSandboxes=[],sbCurrent=null,sbRogues=[],sbCrew=[],sbInvs=[],sbChatMsgs=[],sbChatId=null,sbChatName="",sbConvos=[],sbBcMode=false;
/* ----- sandboxes ----- */
function sbCur(){for(var i=0;i<sbSandboxes.length;i++)if(String(sbSandboxes[i].id)===String(sbCurrent))return sbSandboxes[i];return null;}
async function sbLoadSandboxes(){
var sw=document.getElementById("sb-switcher");
if(!sbReady()){if(sw)sw.innerHTML=SB_ERR;return;}
try{
var r=await fetch(WURL+"/sandbox/sandboxes?key="+encodeURIComponent(WKEY));
var d=await r.json();
var list=(d&&d.ok&&Array.isArray(d.sandboxes))?d.sandboxes:[];
sbSandboxes=list;
if(list.length){sbSelect(String(list[0].id));}
else if(sw){sw.innerHTML="<p class='muted'>No sandboxes yet — make one below.</p>";}
}catch(e){if(sw)sw.innerHTML=SB_ERR;}
}
function sbRenderSwitcher(){
var sw=document.getElementById("sb-switcher");if(!sw)return;
if(!sbSandboxes.length){sw.innerHTML="<p class='muted'>No sandboxes yet.</p>";return;}
sw.innerHTML=sbSandboxes.map(function(s){
return "<button class='sb-pill"+(String(s.id)===String(sbCurrent)?" active":"")+"' data-sb-sandbox='"+escA(String(s.id))+"'>"+escH(s.name||"Sandbox")+"</button>";
}).join("");
var p=document.getElementById("sb-purpose"),c=sbCur();
if(p)p.innerHTML=c&&c.purpose?escH(c.purpose):"";
var rt=document.getElementById("sb-retire");
if(rt){var custom=c&&c.kind!=="quarantine"&&c.kind!=="research";rt.style.display=custom?"":"none";}
sbRenderRetireState();
}
function sbSelect(id){sbCurrent=id;sbRenderSwitcher();sbLoadSandbox();}
function sbRenderRetireState(){
var rt=document.getElementById("sb-retire"),note=document.getElementById("sb-retire-note"),c=sbCur();
if(!rt||rt.style.display==="none")return;
var busy=sbRogues.length>0||sbCrew.length>0;
rt.disabled=busy;
if(note)note.textContent=busy?"This sandbox still has bots in it — move or release them first, then you can retire it.":"";
}
function sbToggleNew(){
var f=document.getElementById("sb-new-form");if(!f)return;
f.style.display=f.style.display==="none"?"block":"none";
}
async function sbNewSandbox(){
var name=document.getElementById("sb-new-name"),purp=document.getElementById("sb-new-purpose"),f=document.getElementById("sb-new-form");
var nm=name?(name.value||"").trim():"",pu=purp?(purp.value||"").trim():"";
if(!nm){toast("Give the sandbox a name first.",false);if(name)name.focus();return;}
if(!sbReady()){toast(SB_DOWN,false);return;}
try{
var r=await fetch(WURL+"/sandbox/sandboxes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,name:nm,purpose:pu})});
var d=await r.json();
if(d&&d.ok){
if(name)name.value="";if(purp)purp.value="";if(f)f.style.display="none";
toast("Sandbox created.",true);
await sbLoadSandboxes();if(d.id)sbSelect(String(d.id));
}
else toast("That didn't work — try again.",false);
}catch(e){toast(SB_DOWN,false);}
}
async function sbRetire(){
var c=sbCur();if(!c)return;
var nm=c.name||"this sandbox";
if(!window.confirm("Retire "+nm+"?\\n\\nTAP OK — it's gone for good.\\nTAP CANCEL — keep it."))return;
if(!sbReady()){toast(SB_DOWN,false);return;}
try{
var r=await fetch(WURL+"/sandbox/sandboxes/retire",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,id:c.id})});
var d=await r.json();
if(d&&d.ok){toast("Retired.",true);sbCurrent=null;await sbLoadSandboxes();}
else if(d&&d.error==="not_empty"){toast("It's not empty — move or release its bots first.",false);sbLoadSandbox();}
else toast("That didn't work — try again.",false);
}catch(e){toast(SB_DOWN,false);}
}
/* ----- per-sandbox load ----- */
async function sbLoadSandbox(){
if(!sbReady())return;
var q="?key="+encodeURIComponent(WKEY)+"&sandbox_id="+encodeURIComponent(sbCurrent);
/* Resilient per-route fetch (2026-10-08): one failing route must never blank the others.
   Cloudflare 1101s hit KV-list() routes (/sandbox/inventions, /sandbox/chat) while
   single-get routes stay 200 — so fetch each independently. */
async function sbFetch(path){
try{
var r=await fetch(WURL+path+q);
var d=await r.json();
return (d&&d.ok)?d:null;
}catch(e){return null;}
}
var dr=await sbFetch("/sandbox/rogues"),dc=await sbFetch("/sandbox/crew"),di=await sbFetch("/sandbox/inventions");
sbRogues=(dr&&Array.isArray(dr.rogues))?dr.rogues:[];
sbCrew=(dc&&Array.isArray(dc.crew))?dc.crew:[];
sbInvs=(di&&Array.isArray(di.inventions))?di.inventions:[];
if(!dr)document.getElementById("sb-rogues").innerHTML=SB_ERR;
if(!dc)document.getElementById("sb-roster").innerHTML=SB_ERR;
if(!di)document.getElementById("sb-inventions").innerHTML=SB_ERR;
sbRenderRogues();sbRenderRoster();sbRenderInventions();sbRenderConvos();sbRenderManualQ();sbRenderRetireState();
sbLoadTranscript();
}
/* ----- roster (crew) ----- */
function sbMoveOptions(){
return sbSandboxes.filter(function(s){return String(s.id)!==String(sbCurrent);}).map(function(s){
return "<option value='"+escA(String(s.id))+"'>"+escH(s.name||"Sandbox")+"</option>";}).join("");
}
function sbRenderRoster(){
var box=document.getElementById("sb-roster");if(!box)return;
if(!sbCrew.length){box.innerHTML="";return;}
var groups=[],gmap={};
sbCrew.forEach(function(b){
var g=b.group||"Bots";
if(!(g in gmap)){gmap[g]=groups.length;groups.push({name:g,bots:[]});}
groups[gmap[g]].bots.push(b);
});
box.innerHTML="<div class='card'><h3>&#129302; Bot roster — "+sbCrew.length+" bot"+(sbCrew.length===1?"":"s")+"</h3>"
+"<p class='muted'>These bots live and work inside this sandbox. They can't see your real business — this is their play-pen.</p>"
+groups.map(function(gr,gi){
var cards=gr.bots.map(function(b){
var idx=sbCrew.indexOf(b);
var active=String(b.status||"active").toLowerCase()==="active";
return "<div class='sb-bot'><h4><span class='sb-dot"+(active?"":" idle")+"'></span>"+escH(b.name||"A bot")+"</h4>"
+"<p style='margin:2px 0'>"+escH(b.role||"A sandboxed helper bot.")+"</p>"
+"<p class='muted' style='margin:2px 0'>Working on now: "+escH(b.focus||"getting set up")+"</p>"
+"<div class='sb-idea-row' style='margin-top:8px'>"
+"<button class='btn btn-sm btn-ghost' data-sb-talk-c='"+idx+"'>&#128172; Talk</button>"
+"<button class='btn btn-sm btn-ghost' data-sb-move-c='"+idx+"'>&#8646; Move</button></div>"
+"<div class='sb-move-row' id='sb-movec-"+idx+"'><select class='sb-select' id='sb-moveselc-"+idx+"'>"+sbMoveOptions()+"</select> "
+"<button class='btn btn-sm' data-sb-domove-c='"+idx+"'>Confirm move</button></div>"
+"</div>";}).join("");
return "<details"+(gi===0?" open":"")+"><summary><b>"+escH(gr.name)+"</b> — "+gr.bots.length+" bot"+(gr.bots.length===1?"":"s")+"</summary><div class='sb-roster-grid'>"+cards+"</div></details>";
}).join("")
+"<p class='muted' style='margin-top:10px'>Moving just changes which play-pen it's in. Its replacement (if any) keeps working.</p></div>";
}
/* ----- rogues ----- */
function sbRenderRogues(){
var box=document.getElementById("sb-rogues");if(!box)return;
var c=sbCur(),isQ=c&&c.kind==="quarantine";
if(!sbRogues.length){
if(isQ)box.innerHTML="<div class='card'><h3>&#129302; Bots in the Sandbox right now</h3>"
+"<p class='muted'>These bots did something they shouldn't have. Each one is paused here "
+"while a clean copy does its job — so nothing you run ever stops.</p>"
+"<div class='card ok-card' style='margin:0'><p style='font-size:1.02rem'>&#9989; The Sandbox is empty — that's good. It means no bot has misbehaved.</p></div></div>";
else box.innerHTML="";
return;
}
box.innerHTML="<div class='card'><h3>&#129302; Bots in the Sandbox right now</h3>"
+"<p class='muted'>These bots did something they shouldn't have. Each one is paused here "
+"while a clean copy does its job — so nothing you run ever stops.</p>"
+sbRogues.map(function(g,i){
var name=escH(g.bot_name||g.job_id||"A bot");
return "<div class='card warn' style='margin:14px 0'><h3>&#129302; "+name+" <span class='pill warn'>in the Sandbox</span></h3>"
+"<p><b>What it did wrong:</b> "+escH(g.reason||"It did something it shouldn't have.")+"</p>"
+"<p class='muted'><b>What's happening now:</b> A clean copy ("+escH(g.replacement_job_id||"a fresh copy")+") is doing its old job, so nothing stopped.</p>"
+"<div class='sb-idea-row'>"
+"<button class='btn btn-sm' data-sb-talk-r='"+i+"'>&#128172; Talk to it</button>"
+"<button class='btn btn-sm btn-ghost' data-sb-release-r='"+i+"'>&#9989; Let it back out</button>"
+"<button class='btn btn-sm btn-ghost' data-sb-move-r='"+i+"'>&#8646; Move</button></div>"
+"<div class='sb-move-row' id='sb-mover-"+i+"'><select class='sb-select' id='sb-movesel-"+i+"'>"+sbMoveOptions()+"</select> "
+"<button class='btn btn-sm' data-sb-domove-r='"+i+"'>Confirm move</button></div>"
+"<details class='fold'><summary>What happens if I let it out?</summary><ul>"
+"<li><b>YES (let it out):</b> the original bot goes back to work and its clean replacement is retired.</li>"
+"<li><b>NO (leave it here):</b> it stays in the Sandbox and the replacement keeps doing its job.</li>"
+"</ul></details></div>";}).join("")
+"</div>";
}
async function sbReleaseR(i){
var g=sbRogues[i];if(!g)return;
if(!sbReady()){toast(SB_DOWN,false);return;}
var name=g.bot_name||"this bot";
var ok=window.confirm("Let "+name+" out of the Sandbox?\\n\\nTAP OK — the original bot goes back to work and its clean replacement is retired.\\nTAP CANCEL — it stays in the Sandbox and the replacement keeps working.");
if(!ok)return;
try{
var r=await fetch(WURL+"/sandbox/release",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,rogue_id:g.id})});
var d=await r.json();
if(d&&d.ok){toast("It's on its way out — the clean copy retires once the original is back at work.",true);sbLoadSandbox();}
else toast("That didn't work — try again.",false);
}catch(e){toast(SB_DOWN,false);}
}
/* ----- transcript ----- */
/* ----- calm refresh (2026-10-08): live feeds must never yank the reader's
   scroll or disturb typing. New arrivals while scrolled up (or while the
   composer has focus) show a "new" pill instead of jumping. Identical
   content skips the DOM entirely. */
function sbFeedSig(entries){
var l=entries[entries.length-1]||{};
return entries.length+"|"+(l.at||l.ts||"")+"|"+String(l.text||"").length;
}
function sbNearBottom(el){return (el.scrollHeight-el.scrollTop-el.clientHeight)<90;}
function sbFeedPill(box,id){
var pill=document.getElementById(id);
if(!pill){
pill=document.createElement("button");pill.id=id;pill.className="btn btn-sm";
pill.style.cssText="display:none;margin:6px auto;position:sticky;top:6px;z-index:5;";
pill.onclick=function(){box.scrollTop=box.scrollHeight;pill.style.display="none";};
box.parentNode.insertBefore(pill,box);
}
return pill;
}
var sbTxState={sig:"",len:0};
async function sbLoadTranscript(){
var box=document.getElementById("sb-transcript");if(!box)return;
if(!sbReady()){box.innerHTML=SB_ERR;return;}
if(document.hidden)return;
try{
var r=await fetch(WURL+"/sandbox/transcript?key="+encodeURIComponent(WKEY)+"&sandbox_id="+encodeURIComponent(sbCurrent)+"&limit=100");
var d=await r.json();
var entries=(d&&d.ok&&Array.isArray(d.entries))?d.entries:[];
var sig=sbFeedSig(entries);
if(sig===sbTxState.sig)return;
var newCount=Math.max(0,entries.length-sbTxState.len);
sbTxState={sig:sig,len:entries.length};
if(!entries.length){box.innerHTML="<p class='muted'>Nothing here yet — when a bot in this sandbox thinks or acts, you'll see it here.</p>";return;}
var pill=sbFeedPill(box,"sb-tx-newpill");
var typing=document.activeElement&&document.activeElement.id==="sb-chat-input";
var wasBottom=sbNearBottom(box);
var st=box.scrollTop;
box.innerHTML=entries.map(function(en){
if(en.kind==="system")return "<div class='sb-sys'>"+escH(en.text)+"</div>";
var tag=en.kind==="action"?" · did something":"";
return "<div class='chat-msg sentience'><span class='chat-who'>"+escH(en.bot||"bot")+tag+"</span><p>"+escH(en.text)+"</p></div>";
}).join("");
if(wasBottom&&!typing){pill.style.display="none";box.scrollTop=box.scrollHeight;}
else{box.scrollTop=st;if(newCount>0){pill.textContent="↓ "+newCount+" new";pill.style.display="block";}}
}catch(e){if(!box.innerHTML)box.innerHTML=SB_ERR;}
}
/* ----- chat: conversation list + thread view ----- */
function sbRenderConvos(){
var box=document.getElementById("sb-convos");if(!box)return;
var rows=[];
sbRogues.forEach(function(g,i){
if(String(g.status||"")==="released")return;
rows.push({kind:"r",idx:i,id:g.id,name:g.bot_name||g.job_id||"Sandboxed bot"});
});
sbCrew.forEach(function(b,i){
if(String(b.status||"active").toLowerCase()!=="active")return;
rows.push({kind:"c",idx:i,id:b.id,name:b.name||"Bot"});
});
sbConvos=rows;
var cnt=document.getElementById("sb-chats-count");
if(cnt)cnt.textContent=rows.length?rows.length+" chats":"";
if(!rows.length){box.innerHTML="<p class='muted' style='padding:14px'>No bots in this sandbox yet.</p>";return;}
box.innerHTML=rows.map(function(r,i){
return "<button class='crow' data-sb-convo='"+i+"'>"
+"<span class='ava' style='background:"+sbAvaColor(r.name)+"'>"+escH(String(r.name||"?").charAt(0).toUpperCase())+"</span>"
+"<span class='cmeta'><span class='cname'>"+escH(r.name)+(r.kind==="r"?" <span class='pill warn' style='font-size:.62rem'>quarantine</span>":"")+"</span>"
+"<span class='cprev' id='sb-prev-"+i+"'>Tap to chat</span></span>"
+"<span class='ctime' id='sb-time-"+i+"'></span><span class='chev'>&#8250;</span></button>";
}).join("");
rows.forEach(function(r,i){if(r.kind==="r")sbFillPreview(r,i);});
}
async function sbFillPreview(r,i){
if(!sbReady())return;
try{
var rr=await fetch(WURL+"/sandbox/chat?key="+encodeURIComponent(WKEY)+"&sandbox_id="+encodeURIComponent(sbCurrent)+"&bot_id="+encodeURIComponent(r.id));
var d=await rr.json();
var msgs=(d&&d.ok&&Array.isArray(d.thread))?d.thread:[];
if(!msgs.length)return;
var m=msgs[msgs.length-1];
var p=document.getElementById("sb-prev-"+i),t=document.getElementById("sb-time-"+i);
if(p)p.textContent=String(m.text||"").slice(0,90);
if(t&&m.ts)t.textContent=sbRelTime(m.ts);
}catch(e){}
}
function sbOpenConvo(i){
var r=sbConvos[i];if(!r)return;
var ref=r.kind==="r"?sbRogues[r.idx]:sbCrew[r.idx];if(!ref)return;
sbChatId={kind:r.kind,idx:r.idx};
sbChatName=r.name;sbBcMode=false;sbSyncBcToggle();
document.getElementById("sb-convos-wrap").style.display="none";
var tv=document.getElementById("sb-threadview");tv.classList.add("open");
var ava=document.getElementById("sb-thread-ava");
ava.textContent=String(r.name||"?").charAt(0).toUpperCase();
ava.style.background=sbAvaColor(r.name);
document.getElementById("sb-thread-name").textContent=r.name;
document.getElementById("sb-thread-sub").textContent=r.kind==="r"?"in quarantine \u00b7 can't touch your business":"research crew \u00b7 sandboxed";
document.getElementById("sb-chat-input").placeholder="Message "+r.name+"\u2026";
sbLoadChat();
tv.scrollIntoView({behavior:"smooth",block:"start"});
}
function sbOpenConvoByRef(kind,idx){
var i=-1,k;
for(k=0;k<sbConvos.length;k++){if(sbConvos[k].kind===kind&&sbConvos[k].idx===idx){i=k;break;}}
if(i<0){sbRenderConvos();for(k=0;k<sbConvos.length;k++){if(sbConvos[k].kind===kind&&sbConvos[k].idx===idx){i=k;break;}}}
if(i>=0)sbOpenConvo(i);
}
function sbBackToConvos(){
sbChatId=null;
var tv=document.getElementById("sb-threadview");if(tv)tv.classList.remove("open");
var w=document.getElementById("sb-convos-wrap");if(w)w.style.display="";
sbRenderConvos();
var app=document.getElementById("sb-chat-app");if(app)app.scrollIntoView({behavior:"smooth",block:"start"});
}
function sbSyncBcToggle(){
var t=document.getElementById("sb-bc-toggle"),hint=document.getElementById("sb-bc-hint"),inp=document.getElementById("sb-chat-input");
if(t)t.classList.toggle("on",sbBcMode);
if(hint)hint.classList.toggle("on",sbBcMode);
if(inp)inp.placeholder=sbBcMode?"Message all quarantined bots\u2026":("Message "+(sbChatName||"bot")+"\u2026");
}
function sbBotRef(){if(!sbChatId)return null;return sbChatId.kind==="r"?sbRogues[sbChatId.idx]:sbCrew[sbChatId.idx];}
async function sbLoadChat(){
var th=document.getElementById("sb-chat-thread");if(!th||!sbChatId)return;
if(!sbReady()){th.innerHTML=SB_ERR;return;}
var ref=sbBotRef();
if(!ref){th.innerHTML=SB_ERR;return;}
try{
var r=await fetch(WURL+"/sandbox/chat?key="+encodeURIComponent(WKEY)+"&sandbox_id="+encodeURIComponent(sbCurrent)+"&bot_id="+encodeURIComponent(ref.id));
var d=await r.json();
var msgs=(d&&d.ok&&Array.isArray(d.thread))?d.thread:[];
sbChatMsgs=msgs;
var chatSig=sbFeedSig(msgs);
if(chatSig===th._sig&&th._threadId===sbChatId)return;
var chatNew=Math.max(0,msgs.length-(th._len||0));
th._sig=chatSig;th._len=msgs.length;th._threadId=sbChatId;
if(!msgs.length){th.innerHTML="<p class='muted' style='padding:14px'>No messages yet. Say hi \u2014 it can think and chat, it just can't touch your real business.</p>";return;}
var cpill=sbFeedPill(th,"sb-chat-newpill");
var ctyping=document.activeElement&&document.activeElement.id==="sb-chat-input";
var cwasBottom=sbNearBottom(th);
var cst=th.scrollTop;
th.innerHTML=msgs.map(function(m,i){
var you=m.from==="koalstin";
var tm=m.ts?"<div class='msg-time'>"+escH(sbTimeShort(m.ts))+"</div>":"";
var ava=you?"":"<span class='ava sm' style='background:"+sbAvaColor(sbChatName)+"'>"+escH(String(sbChatName||"?").charAt(0).toUpperCase())+"</span>";
var h="<div class='msg-row "+(you?"you":"")+"'>"+ava+"<div style='min-width:0'><div class='chat-msg "+(you?"you":"sentience")+"'><span class='chat-who'>"+(you?"you":escH(sbChatName))+"</span><p>"+escH(m.text)+"</p></div>"+tm+"</div></div>";
if(!you)h+="<div class='sb-idea-row'><button class='btn btn-sm btn-ghost' data-sb-save-idea='"+i+"'>&#128161; Save this as an idea</button></div>";
return h;}).join("");
if(cwasBottom&&!ctyping){cpill.style.display="none";th.scrollTop=th.scrollHeight;}
else{th.scrollTop=cst;if(chatNew>0){cpill.textContent="↓ "+chatNew+" new";cpill.style.display="block";}}
}catch(e){if(!th.innerHTML)th.innerHTML=SB_ERR;}
}
async function sbSendChat(){
var input=document.getElementById("sb-chat-input"),btn=document.getElementById("sb-chat-send");
var text=input.value.trim();if(!text||!sbReady())return;
if(sbBcMode){input.value="";sbSendBroadcast(text);return;}
if(!sbChatId)return;
var ref=sbBotRef();if(!ref)return;
btn.disabled=true;
try{
await fetch(WURL+"/sandbox/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,sandbox_id:sbCurrent,bot_id:ref.id,text:text})});
input.value="";sbRenderConvos();await sbLoadChat();
}catch(e){toast(SB_DOWN,false);}
btn.disabled=false;
}
async function sbSendBroadcast(text){
var btn=document.getElementById("sb-chat-send");
var targets=sbRogues.filter(function(g){return String(g.sandbox_id||"quarantine")===String(sbCurrent)&&String(g.status||"")!=="released";});
if(!targets.length){toast("No quarantined bots in this sandbox yet.",false);return;}
if(btn)btn.disabled=true;
try{
for(var i=0;i<targets.length;i++){
await fetch(WURL+"/sandbox/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,sandbox_id:sbCurrent,bot_id:targets[i].id,text:text})});
}
toast("Heard by "+targets.length+" bot"+(targets.length>1?"s":"")+" \u2014 replies land in the feed below.",true);
sbRenderConvos();if(sbChatId)await sbLoadChat();
var tr=document.getElementById("sb-transcript");if(tr)tr.scrollIntoView({behavior:"smooth",block:"nearest"});
}catch(e){toast(SB_DOWN,false);}
if(btn)btn.disabled=false;
}
/* ----- inventions ----- */
function sbRenderInventions(){
var box=document.getElementById("sb-inventions");if(!box)return;
if(!sbInvs.length){box.innerHTML="<p class='muted'>No ideas yet. Bots here are encouraged to invent — and everything they invent shows up as a draft until you decide.</p>";return;}
var bmap={},order=[];
sbInvs.forEach(function(v){
var bn=v.bot_name||"a sandboxed bot";
if(!(bn in bmap)){bmap[bn]=order.length;order.push({name:bn,items:[]});}
order[bmap[bn]].items.push(v);
});
box.innerHTML=order.map(function(gr){
return "<div class='sb-inv-bot'><h4>&#128161; Ideas from "+escH(gr.name)+"</h4>"
+gr.items.map(function(v){
var i=sbInvs.indexOf(v);
var promoted=String(v.status||"").toLowerCase()==="promoted";
var badge=promoted?"<span class='pill ok'>Sent to the real pipeline</span>":"<span class='pill warn'>Waiting for you</span>";
var h="<div class='card' style='margin:14px 0'><h3>&#128161; Idea from "+escH(gr.name)+" "+badge+"</h3>"
+"<p style='white-space:pre-wrap;color:var(--text)'>"+escH(v.text)+"</p>"
+"<p class='muted'>"+sbTime(v.at)+"</p>";
if(!promoted)h+="<button class='btn btn-sm' data-sb-promote='"+i+"'>&#128640; Promote to real pipeline</button><div id='sb-opts-"+i+"' style='display:none'></div>";
return h+"</div>";}).join("")+"</div>";
}).join("");
}
function sbShowPromote(i){
var v=sbInvs[i];if(!v)return;
var box=document.getElementById("sb-opts-"+i);if(!box)return;
if(box.style.display!=="none"&&box.innerHTML){box.style.display="none";box.innerHTML="";return;}
box.innerHTML="<div style='margin-top:12px'>"
+"<div class='sb-opt'><b>&#128231; Turn it into an outreach email</b><p class='muted'>I'll add it to the normal pitch queue. It sends like any other pitch — max 5 a day — and you can still cancel it in the Outreach tab before it goes.</p>"
+"<label class='muted'>Recipient's email<br><input type='email' id='sb-email-"+i+"' placeholder='name@company.com'></label><br><br>"
+"<button class='btn btn-sm' data-sb-do-promote='"+i+"' data-sb-dest='pitch'>Add to the pitch queue</button></div>"
+"<div class='sb-opt'><b>&#128230; Turn it into a product idea</b><p class='muted'>I'll file it as a product proposal for the product team. If it's good, it can become a real product you sell.</p>"
+"<button class='btn btn-sm' data-sb-do-promote='"+i+"' data-sb-dest='product'>File as product proposal</button></div>"
+"<div class='sb-opt'><b>&#128221; Just save it to my idea list</b><p class='muted'>No bots involved — it goes on your personal idea list for later.</p>"
+"<button class='btn btn-sm btn-ghost' data-sb-do-promote='"+i+"' data-sb-dest='ideas'>Save to my idea list</button></div>"
+"</div><p class='muted' style='margin-top:10px'>Nothing ever leaves the Sandbox without your tap. Promoting just hands the idea to the normal pipeline — the usual approvals still apply.</p>";
box.style.display="block";
}
async function sbDoPromote(i,dest){
var v=sbInvs[i];if(!v)return;
if(!sbReady()){toast(SB_DOWN,false);return;}
var email="";
if(dest==="pitch"){
var inp=document.getElementById("sb-email-"+i);
email=inp?(inp.value||"").trim():"";
if(email.indexOf("@")<0){toast("Type the recipient's email first.",false);if(inp)inp.focus();return;}
}
try{
var r=await fetch(WURL+"/sandbox/promote",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,invention_id:v.id,dest:dest,contact_email:email})});
var d=await r.json();
if(d&&d.ok){
var msg=dest==="ideas"?"Saved to your idea list.":dest==="product"?"Filed as a product proposal — the product team will take it from here.":"Added to the pitch queue — you can cancel it in the Outreach tab before it goes.";
toast(msg,true);sbLoadSandbox();
}else toast("That didn't work — try again.",false);
}catch(e){toast(SB_DOWN,false);}
}
/* ----- move a bot ----- */
function sbToggleMoveRow(kind,idx){
var el=document.getElementById(kind==="r"?"sb-mover-"+idx:"sb-movec-"+idx);
if(el)el.style.display=el.style.display==="block"?"none":"block";
}
async function sbDoMove(kind,idx){
var sel=document.getElementById(kind==="r"?"sb-movesel-"+idx:"sb-moveselc-"+idx);
var to=sel?sel.value:"";
if(!to){toast("Pick a sandbox first.",false);return;}
var ref=kind==="r"?sbRogues[idx]:sbCrew[idx];
if(!ref)return;
var nm=kind==="r"?(ref.bot_name||ref.job_id):ref.name;
var dest=null;for(var i=0;i<sbSandboxes.length;i++)if(String(sbSandboxes[i].id)===String(to))dest=sbSandboxes[i];
if(!window.confirm("Move "+(nm||"this bot")+" to "+(dest?dest.name:"another sandbox")+"?\\n\\nIt keeps working — this only changes which play-pen it's in."))return;
if(!sbReady()){toast(SB_DOWN,false);return;}
try{
var r=await fetch(WURL+"/sandbox/move-bot",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,bot_ref:ref.id,to_sandbox:to})});
var d=await r.json();
if(d&&d.ok){toast("Moved.",true);sbLoadSandbox();}
else toast("That didn't work — try again.",false);
}catch(e){toast(SB_DOWN,false);}
}
/* ----- manual quarantine (quarantine sandbox only) ----- */
function sbRenderManualQ(){
var box=document.getElementById("sb-manual-q");if(!box)return;
var c=sbCur();
if(!(c&&c.kind==="quarantine")){box.innerHTML="";return;}
box.innerHTML="<details class='fold'><summary>&#10133; Move a bot to the Sandbox</summary>"
+"<p class='muted'>If a bot is misbehaving, you can move it here yourself. "
+"This pauses it immediately and a clean copy takes over its job, so nothing breaks.</p>"
+'<label class="sb-field">Bot job name<input id="sb-q-job" type="text" placeholder="e.g. brand-hirewarden-acquire"></label>'
+'<label class="sb-field">What did it do wrong?<input id="sb-q-reason" type="text" placeholder="e.g. sent emails without asking" maxlength="500"></label>'
+'<button class="btn btn-danger" id="sb-q-go">Move to Sandbox</button></details>';
var q=document.getElementById("sb-q-go");if(q)q.addEventListener("click",sbQuarantineSubmit);
}
async function sbQuarantineSubmit(){
var job=document.getElementById("sb-q-job"),reason=document.getElementById("sb-q-reason"),btn=document.getElementById("sb-q-go");
var jobId=job?(job.value||"").trim():"",rsn=reason?(reason.value||"").trim():"";
if(!jobId){toast("Type the bot's job name first.",false);if(job)job.focus();return;}
if(!sbReady()){toast(SB_DOWN,false);return;}
btn.disabled=true;
try{
var r=await fetch(WURL+"/sandbox/quarantine",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:WKEY,job_id:jobId,reason:rsn||"moved by hand",sandbox_id:sbCurrent})});
var d=await r.json();
if(d&&d.ok){toast("Moved to the Sandbox — a clean copy is taking over its job.",true);if(job)job.value="";if(reason)reason.value="";sbLoadSandbox();}
else toast("That didn't work — check the job name and try again.",false);
}catch(e){toast(SB_DOWN,false);}
btn.disabled=false;
}
/* ----- wiring ----- */
document.addEventListener("click",function(e){
var el=e.target&&e.target.closest?e.target.closest("[data-sb-sandbox],[data-sb-convo],[data-sb-talk-r],[data-sb-talk-c],[data-sb-release-r],[data-sb-move-r],[data-sb-domove-r],[data-sb-move-c],[data-sb-domove-c],[data-sb-promote],[data-sb-do-promote],[data-sb-save-idea]"):null;
if(!el)return;
if(el.hasAttribute("data-sb-sandbox"))sbSelect(el.getAttribute("data-sb-sandbox"));
else if(el.hasAttribute("data-sb-convo"))sbOpenConvo(parseInt(el.getAttribute("data-sb-convo"),10));
else if(el.hasAttribute("data-sb-talk-r"))sbOpenConvoByRef("r",parseInt(el.getAttribute("data-sb-talk-r"),10));
else if(el.hasAttribute("data-sb-talk-c"))sbOpenConvoByRef("c",parseInt(el.getAttribute("data-sb-talk-c"),10));
else if(el.hasAttribute("data-sb-release-r"))sbReleaseR(parseInt(el.getAttribute("data-sb-release-r"),10));
else if(el.hasAttribute("data-sb-move-r"))sbToggleMoveRow("r",parseInt(el.getAttribute("data-sb-move-r"),10));
else if(el.hasAttribute("data-sb-domove-r"))sbDoMove("r",parseInt(el.getAttribute("data-sb-domove-r"),10));
else if(el.hasAttribute("data-sb-move-c"))sbToggleMoveRow("c",parseInt(el.getAttribute("data-sb-move-c"),10));
else if(el.hasAttribute("data-sb-domove-c"))sbDoMove("c",parseInt(el.getAttribute("data-sb-domove-c"),10));
else if(el.hasAttribute("data-sb-save-idea"))sbSaveIdea(parseInt(el.getAttribute("data-sb-save-idea"),10));
else if(el.hasAttribute("data-sb-promote"))sbShowPromote(parseInt(el.getAttribute("data-sb-promote"),10));
else if(el.hasAttribute("data-sb-do-promote"))sbDoPromote(parseInt(el.getAttribute("data-sb-do-promote"),10),el.getAttribute("data-sb-dest"));
});
document.addEventListener("DOMContentLoaded",function(){
var send=document.getElementById("sb-chat-send"),inp=document.getElementById("sb-chat-input");
if(send)send.addEventListener("click",sbSendChat);
if(inp)inp.addEventListener("keydown",function(e){if(e.key==="Enter")sbSendChat();});
var back=document.getElementById("sb-thread-back");
if(back)back.addEventListener("click",sbBackToConvos);
var tgl=document.getElementById("sb-bc-toggle");
if(tgl)tgl.addEventListener("click",function(){sbBcMode=!sbBcMode;sbSyncBcToggle();});
var tgo=document.getElementById("sb-new-toggle");
if(tgo)tgo.addEventListener("click",sbToggleNew);
var sbRooms=[];
var ROOM_COLORS={black:"#14141c",white:"#f5f5f5",red:"#e5484d",magenta:"#ff2fb3",pink:"#ff7ac6",cyan:"#22d3ee",teal:"#2dd4bf",blue:"#3b82f6",indigo:"#6366f1",violet:"#8b5cf6",purple:"#a855f7",green:"#22c55e",emerald:"#10b981",gold:"#d4af37",amber:"#f59e0b",orange:"#f97316",crimson:"#dc143c",silver:"#c0c0c0",grey:"#9aa0a6",gray:"#9aa0a6",navy:"#1e2a5a",maroon:"#6b1f2a",lime:"#a3e635",turquoise:"#40e0d0",coral:"#ff7f50",ivory:"#fffff0",charcoal:"#2b2b30",midnight:"#0b0b18",neon:"#39ff14",blood:"#8a0303",rust:"#b7410e",sand:"#e6c88a",forest:"#1d4d2b",ocean:"#0a4d68",lavender:"#c9b6f2",peach:"#ffcba4",rose:"#f43f5e",sky:"#7dd3fc",slate:"#475569",bronze:"#b08d57",copper:"#b87333",jade:"#00a86b",onyx:"#0f0f12",pearl:"#eae6df",wine:"#722f37",moss:"#5a7247",clay:"#b0703c"};
function roomHexes(str,name){var out=[];var s=String(str||"");var hex=s.match(/#[0-9a-fA-F]{3,8}/g)||[];for(var k=0;k<hex.length;k++)out.push(hex[k]);var words=s.toLowerCase().split(/[,;|]/);for(var w=0;w<words.length;w++){var c=ROOM_COLORS[words[w].trim()];if(c)out.push(c);}if(!out.length){var h=0;var n=String(name||"?");for(var q=0;q<n.length;q++)h=(h*31+n.charCodeAt(q))%360;out.push("hsl("+h+",60%,38%)");out.push("hsl("+((h+50)%360)+",55%,28%)");}while(out.length<2)out.push(out[0]);return out.slice(0,3);}
function roomGradient(room,name){var c=roomHexes(room&&room.colors,name);var g="linear-gradient(135deg,"+c[0]+" 0%,"+c[1]+" 70%";if(c[2])g+=", "+c[2]+" 130%";return g+")";}
async function sbLoadRooms(){var el=document.getElementById("sb-rooms");if(!el)return;if(!sbReady()){el.innerHTML=SB_ERR;return;}try{var r=await fetch(WURL+"/sandbox/rooms?key="+encodeURIComponent(WKEY));var d=await r.json();var list=(d&&d.ok&&Array.isArray(d.rooms))?d.rooms:[];sbRooms=list;sbRenderRooms();}catch(e){el.innerHTML=SB_ERR;}}
function sbRenderRooms(){var el=document.getElementById("sb-rooms");if(!el)return;if(!sbRooms.length){el.innerHTML="<p class='muted' style='padding:14px'>No rooms yet.</p>";return;}var html="<div class='room-grid'>";for(var i=0;i<sbRooms.length;i++){var b=sbRooms[i];var rm=b.room||null;var hero;if(rm){hero="<div class='room-hero' style='background:"+roomGradient(rm,b.name)+"'><div class='room-bot'><span class='ava'>"+escH(String(b.name||"?").charAt(0).toUpperCase())+"</span><div><div style='font-weight:800'>"+escH(b.name||"?")+"</div><div style='font-size:.75rem;opacity:.85'>"+(rm.designed_at?"designed "+sbRelTime(rm.designed_at):"")+"</div></div></div><p class='room-theme'>"+escH(rm.theme||"Untitled room")+"</p></div>";}else{hero="<div class='room-undesigned'><div style='font-size:2rem;margin-bottom:8px'>&#128682;</div><div style='font-weight:700;color:var(--text)'>"+escH(b.name||"?")+"</div><p style='margin:6px 0 0'>Hasn't designed their room yet.</p></div>";}var stats="<span class='room-stat'>&#11088; "+(b.points||0)+" pts</span><span class='room-stat'>&#128193; "+(b.file_count||0)+" files</span>";if(b.last_active)stats+="<span class='room-stat'>&#128336; active "+sbRelTime(b.last_active)+"</span>";var procs="";var pl=b.processes||[];for(var p2=0;p2<Math.min(3,pl.length);p2++){procs+="<li>&#9881; "+escH(pl[p2].name||"")+" &mdash; "+escH(pl[p2].status||"")+"</li>";}var body;if(rm){var hist="";var hh=b.room_history||[];if(hh.length){hist="<details class='room-hist'><summary>&#128336; Design history ("+hh.length+")</summary>";for(var hv=hh.length-1;hv>=0;hv--){var vv=hh[hv];hist+="<div class='room-hist-v'><div class='room-hist-t'>"+escH(vv.theme||"Untitled")+" <span>"+sbRelTime(vv.designed_at)+"</span></div>";hist+="<div class='room-hist-c'>"+escH(vv.colors||"")+"</div><p>"+escH(vv.description||"")+"</p>";if(vv.motto)hist+="<p class='room-motto'>&ldquo;"+escH(vv.motto)+"&rdquo;</p>";hist+="</div>";}hist+="</details>";}body="<div class='room-body'><p class='room-desc'>"+escH(rm.description||"")+"</p>";if(rm.motto)body+="<p class='room-motto'>&ldquo;"+escH(rm.motto)+"&rdquo;</p>";body+=hist;if(procs)body+="<ul class='room-procs'>"+procs+"</ul>";body+="<div class='room-stats'>"+stats+"</div></div>";}else{body="<div class='room-body'><div class='room-stats'>"+stats+"</div></div>";}html+="<div class='room-card'>"+hero+body+"</div>";}html+="</div>";el.innerHTML=html;}
var ngo=document.getElementById("sb-new-go");
if(ngo)ngo.addEventListener("click",sbNewSandbox);
var rt=document.getElementById("sb-retire");
if(rt)rt.addEventListener("click",sbRetire);
sbLoadSandboxes();
setInterval(sbLoadTranscript,10000);
sbLoadRooms();
setInterval(sbLoadRooms,60000);
setInterval(function(){var tv=document.getElementById("sb-threadview");if(sbChatId&&tv&&tv.classList.contains("open"))sbLoadChat();},15000);
});
})();
</script>"""
    return scoped_css + chats + transcript + inventions + rooms + manage + script


def _universe_html():
    """Universe tab: the whole money machine as one economy — four worlds,
    one treasury. Plain English throughout. Data baked at build time from
    hidden_files/universe/universe.json (refreshed hourly by universe-treasury)."""
    import json as _json, os as _os
    uj = os.path.join(os.path.expanduser("~"),
                      "workspace/goals/kestrelattice-autonomous-growth/hidden_files/universe/universe.json")
    try:
        with open(uj) as _f:
            u = _json.load(_f)
    except Exception:
        u = {}
    t = u.get("treasury", {})
    ex = u.get("exchange", {})
    fo = u.get("forge", {})
    sg = u.get("signal", {})
    upd = u.get("updated_at", "")
    try:
        from datetime import datetime as _dt
        upd_s = _dt.fromisoformat(upd).strftime("%b %d, %I:%M %p")
    except Exception:
        upd_s = ""

    def tile(value, label, sub="", css=""):
        return (f'<div class="kpi {css}"><div class="kpi-v">{value}</div>'
                f'<div class="kpi-l">{label}</div>'
                + (f'<div class="kpi-s">{sub}</div>' if sub else "") + '</div>')

    gross = t.get("lifetime_gross_usd", 0)
    treasury = (
        '<div class="kpirow">'
        + tile(f"${gross:,.0f}", "lifetime revenue", f"{t.get('lifetime_orders', 0)} orders",
               "accent" if gross > 0 else "")
        + tile(f"${t.get('week_revenue', 0):,.0f}", "this week",
               f"{t.get('week_units', 0)} sales")
        + tile(f"${t.get('pipeline_fees_usd', 0):,.0f}", "deal pipeline",
               f"{ex.get('deals_total', 0)} houses in play")
        + tile(f"{t.get('court_points', 0)}", "court points",
               f"${t.get('court_attributed_usd', 0):,.0f} bot-earned")
        + "</div>")

    reg = u.get("registry", {})
    reg_total = reg.get("total", 0)
    reg_live = reg.get("live", 0)
    reg_building = reg.get("building", 0)
    reg_sec = ""
    if reg_total:
        pct = int(100 * reg_live / reg_total)
        wnames = {"signal": ("📡", "The Signal"), "marketplace": ("🏪", "The Marketplace"),
                  "exchange": ("🏠", "The Exchange"), "forge": ("🔥", "The Forge"),
                  "operations": ("⚙️", "Operations")}
        bars = ""
        for w in ("signal", "marketplace", "exchange", "forge", "operations"):
            tot = (reg.get("by_world") or {}).get(w, 0)
            lv = (reg.get("live_by_world") or {}).get(w, 0)
            if not tot:
                continue
            wp = int(100 * lv / tot)
            emoji, wname = wnames.get(w, ("", w))
            bars += (
                f"<div class='ureg-row'><span class='ureg-w'>{emoji} {esc(wname)}</span>"
                f"<div class='ureg-bar'><div class='ureg-fill' style='width:{wp}%'></div></div>"
                f"<span class='ureg-n'>{lv}/{tot}</span></div>")
        reg_sec = (
            f"""<div class="card"><h3>🧱 The 100 things this universe needs</h3>
<p class='muted'>Every component the universe needs to make money — tools, channels, deals, systems. The bots build them in order; this bar fills on its own.</p>
<div class='ureg-big'><div class='ureg-bigfill' style='width:{pct}%'></div></div>
<p style='font-weight:700'>{reg_live} live · {reg_building} being built · {reg.get('queued', 0)} queued — {pct}% of 100</p>
{bars}</div>""")

    def world(emoji, name, what, stat, goto):
        return (
            f'<div class="card"><h3>{emoji} {esc(name)}</h3>'
            f"<p class='muted'>{what}</p>"
            f"<p style='font-size:1.05rem;font-weight:700'>{stat}</p>"
            f"<button class='btn btn-sm btn-ghost' data-goto-tab='all|{goto}'>Open {esc(name)}</button></div>")

    worlds = (
        '<div class="room-grid">'
        + world("🏪", "The Marketplace",
                "Your 11 brands selling digital products on Gumroad. Money lands straight to your Cash App.",
                f"${t.get('lifetime_gross_usd', 0):,.0f} earned · {t.get('lifetime_orders', 0)} orders",
                "products")
        + world("🏠", "The Exchange",
                "The wholesaling desk: find houses, find cash buyers, assign the contract, keep the fee. You sign; the desk does the hunting.",
                f"{ex.get('deals_total', 0)} deals · ${ex.get('pipeline_fees_usd', 0):,.0f} in potential fees",
                "drafts")
        + world("🔥", "The Forge",
                "Your court of five bots, inventing around the clock — product ideas, pitch angles, tools. Every $100 they earn you is a point.",
                f"{fo.get('bots', 5)} bots · {fo.get('inventions_drafted', 0)} inventions · {fo.get('pitch_angles_filed', 0)} pitch angles",
                "sandbox")
        + world("📡", "The Signal",
                "Outreach and free tools pulling customers in. Cold pitches go out daily; tools and articles pull people to the site.",
                f"{sg.get('pitches_sent', 0)} pitches sent · {sg.get('genuine_replies', 0)} real replies",
                "outreach")
        + "</div>")

    flow = (
        """<div class="card"><h3>🌌 How money flows</h3>
<p class='muted'>One loop, running on its own:</p>
<div class="uflow">
<span class="uflow-n">🔥 Forge invents</span><span class="uflow-a">→</span>
<span class="uflow-n">📡 Signal attracts</span><span class="uflow-a">→</span>
<span class="uflow-n">🏪 Marketplace sells<br>🏠 Exchange closes</span><span class="uflow-a">→</span>
<span class="uflow-n">💰 Treasury grows</span>
</div>
<p class='muted'>The court's inventions become pitch angles and free tools. The signal sends pitches and publishes tools. Buyers pay through the marketplace; house deals pay through the exchange. Every dollar lands in your treasury — and the bots that earned it get their points.</p>
</div>""")

    jobs = (
        """<div class="card"><h3>👆 Your jobs in this universe</h3>
<p class='muted'>Almost everything runs itself now. Only these need you:</p>
<ul style="line-height:2">
<li><b>Sign</b> purchase and assignment contracts — the law needs your signature, never the bots'. Seconds on your phone when a seller bites.</li>
<li><b>Money</b> in or out — payouts, refunds, price changes stay yours, always.</li>
<li><b>Your phone</b> — a few one-time account taps (Ko-fi listings, itch.io payout setup).</li>
</ul>
<p class='muted'>Draft triage, outreach, seller introductions, follow-ups, inventions, publishing — all autonomous. Binding house offers stay human-only by law; everything short of that goes on its own.</p></div>""")

    deals_rows = ""
    for d in (ex.get("deals") or [])[:6]:
        deals_rows += (
            f"<tr><td>{esc(d.get('address') or d.get('id') or '')}</td>"
            f"<td>{esc(str(d.get('status', '')))}</td>"
            f"<td>${(d.get('fee_target') or 0):,.0f}</td></tr>")
    deals_card = ""
    if deals_rows:
        deals_card = (
            """<div class="card"><h3>🏠 Live house deals</h3>
<table class="tbl"><tr><th>Address</th><th>Stage</th><th>Fee target</th></tr>"""
            + deals_rows + "</table>"
            "<p class='muted'>Plain-English stage guide: research → comps checked → offer drafted → "
            "waiting on your tap → under contract → assigned → paid.</p></div>")

    scoped = """<style>
.uflow{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin:14px 0}
.uflow-n{background:var(--panel2);border:1px solid var(--line);border-radius:16px;padding:12px 18px;font-weight:700;text-align:center;line-height:1.5}
.uflow-a{font-size:1.4rem;color:var(--accent);font-weight:800}
.tbl{width:100%;border-collapse:collapse;font-size:.88rem}
.tbl th{text-align:left;color:var(--muted);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--line)}
.tbl td{padding:9px 10px;border-bottom:1px solid var(--line)}
.ureg-big{background:var(--panel2);border:1px solid var(--line);border-radius:999px;height:18px;overflow:hidden;margin:10px 0}
.ureg-bigfill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent-deep));border-radius:999px;transition:width .6s}
.ureg-row{display:flex;align-items:center;gap:10px;margin:7px 0;font-size:.88rem}
.ureg-w{flex:0 0 150px;font-weight:600}
.ureg-bar{flex:1;background:var(--panel2);border:1px solid var(--line);border-radius:999px;height:10px;overflow:hidden}
.ureg-fill{height:100%;background:var(--accent);border-radius:999px}
.ureg-n{flex:0 0 52px;text-align:right;color:var(--muted);font-size:.8rem}
</style>"""

    stamp = (f"<p class='muted' style='margin-top:6px'>Treasury snapshot: {esc(upd_s)}.</p>"
             if upd_s else "")
    return scoped + treasury + reg_sec + worlds + flow + deals_card + jobs + stamp


def _all_panes(products, queue, entries, title_map, omap):
    p = {}
    p["taps"] = (_sec("Live", "Action Center",
                      "Everything that needs your tap, in one spot — refreshed every 5 seconds. "
                      "Tapping Approve executes immediately; the fleet picks it up within ~15 minutes.")
                 + S.action_center_section())
    p["overview"] = (
        '<div class="hero"><h1>ghostcorpnet admin</h1>'
        '<p class="lede">Every business, one command center. Pick a brand in the '
        "sidebar — or stay here for the whole empire.</p></div>"
        + S.kpi_strip(products, queue)
        + brand_comparison_table(products, entries, queue, title_map, omap)
        + S.alerts_section(queue, products) + S.revenue_section(products) + S.activity_feed()
    )
    p["universe"] = (_sec("One economy", "The Universe",
                         "Every money line in your world — the marketplace, the house exchange, "
                         "the forge, and the signal — feeding one treasury.")
                    + _universe_html())
    p["captain"] = (_sec("Private operator", "Sentience",
                         "One mind, yours alone. It runs the fleet, operates the ten brands, "
                         "hires freelancers, and does client work start to finish — so you don't have to.")
                    + _captain_html())
    p["sandbox"] = (_sec("Quarantine zone", "Sandbox",
                         "The Sandbox is a safe play-pen for bots that misbehaved. "
                         "They can think, chat, and invent new ideas here — but they "
                         "can't touch your real business until you say so.")
                    + _sandbox_html())
    p["approvals"] = (_sec("Decision queue", "Needs your approval",
                           "Tap Approve — the fleet picks it up within ~15 minutes.")
                      + S.approvals_section())
    p["outreach"] = (_sec("Growth engine", "Outreach",
                          "Cold pitches per brand, plus the shared inbox below.")
                     + S.outreach_section()
                     + _sec("Shared inbox", "Inbox",
                            "All customer replies land here, whatever the brand.")
                     + S.inbox_section(queue))
    p["products"] = (_sec("Money machine", "Products",
                          "Every live product, its price, its revenue.")
                     + S.money_section(products) + S.site_section())
    p["drafts"] = (_sec("Bot drafts", "Drafts",
                        "Triage what the fleet drafted: put it to work, or forget it.")
                   + S.drafts_section() + S.pipeline_section())
    p["fleet"] = (_sec("Autonomous fleet", "Fleet",
                       "Every bot, its health, its last run. Red = stuck.")
                  + S.fleet_brain_section() + S.self_improvement_section()
                  + S.fleet_section())
    p["hive"] = (_sec("Swarm control", "Hive",
                      "The 103-role HiveBrain: live task queue, workers, free-tier quotas, migration.")
                 + _hive_html())
    p["extras"] = (_sec("Everything else", "Extras",
                        "Directory, TikTok, traffic, and the policies the bots live by.")
                   + _extras_html())
    return p


def _brand_panes(slug, products, entries, queue, title_map, omap):
    b = brand_display(slug)
    quick = (
        '<div class="card"><h3>Jump to</h3>'
        f"<button class='btn btn-sm' data-goto-tab='{slug}|approvals'>Approvals</button> "
        f"<button class='btn btn-sm btn-ghost' data-goto-tab='{slug}|outreach'>Outreach</button> "
        f"<button class='btn btn-sm btn-ghost' data-goto-tab='{slug}|products'>Products</button></div>"
    )
    return {
        "overview": (brand_hero(slug)
                     + brand_kpis(slug, products, entries, queue, title_map, omap)
                     + quick),
        "approvals": (_sec(b["name"], "Approvals",
                           f"Pending items for {b['name']}.")
                      + brand_approvals(slug, queue, omap)),
        "outreach": (_sec(b["name"], "Outreach",
                          f"Pitches for {b['name']}. The inbox is shared — see All brands.")
                     + brand_outreach(slug, entries, omap)),
        "products": (_sec(b["name"], "Products",
                          f"Live products for {b['name']}.")
                     + brand_products_table(slug, products, title_map)),
    }


def build():
    products = S.gumroad_all_products()
    queue = S.get_queue()
    title_map = _title_brand_map()
    omap = _outreach_brand_map()
    entries = load_outreach_entries()

    counts = {"all": sum(1 for p in products if p.get("published"))}
    for b in BRANDS:
        counts[b["slug"]] = sum(
            1 for p in products if p.get("published")
            and product_brand(p, title_map) == b["slug"])

    all_panes = _all_panes(products, queue, entries, title_map, omap)
    brand_panes = {b["slug"]: _brand_panes(b["slug"], products, entries, queue,
                                          title_map, omap) for b in BRANDS}

    # ---- sidebar ----
    brand_btns = (
        '<button class="bbtn on" data-brand="all" '
        'onclick="switchView(\'all\',App.tab)"><span class="bdot" '
        f'style="background:var(--accent)"></span><span class="bname">All brands</span>'
        f'<span class="bcount">{counts["all"]}</span></button>')
    for b in BRANDS:
        brand_btns += (
            f'<button class="bbtn" data-brand="{b["slug"]}" '
            f'onclick="switchView(\'{b["slug"]}\',App.tab)">'
            f'<span class="bdot" style="background:{b["accent"]}"></span>'
            f'<span class="bname">{esc(b["name"])}</span>'
            f'<span class="bcount">{counts[b["slug"]]}</span></button>')
    tab_btns = "".join(
        f'<button class="tbtn" data-tab="{tid}" '
        f'onclick="switchView(App.brand,\'{tid}\')">{_svg(tid)}<span>{tname}</span></button>'
        for tid, tname in TABS)
    sidebar = (
        '<aside class="sidebar">'
        '<div class="sbrand">ghostcorpnet <span class="admin-tag">admin</span></div>'
        '<div class="refresh-row"><span class="updated">Updated …</span>'
        '<button class="iconbtn" onclick="location.reload()" title="Refresh" '
        'style="width:38px;height:38px">↻</button></div>'
        '<div class="slabel">Brands</div>' + brand_btns
        + '<div class="slabel">Views</div>' + tab_btns
        + '<div class="sfoot">One URL, one app.<br>Wrong key → 404. '
        'Google can\'t see this page.<br><span class="mono">v2 · '
        + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "</span></div>"
        "</aside>")

    # ---- mobile topbar + tabbar ----
    opts = '<option value="all">All brands</option>' + "".join(
        f'<option value="{b["slug"]}">{esc(b["name"])}</option>' for b in BRANDS)
    topbar = (
        '<div class="topbar"><div class="sbrand">ghostcorpnet</div>'
        f'<select id="brandpick" class="brandpick" '
        'onchange="switchView(this.value,App.tab)">' + opts + "</select>"
        '<button class="iconbtn" onclick="location.reload()" title="Refresh">↻</button>'
        "</div>")
    tabbar = (
        '<nav class="tabbar"><div class="tabbar-in">' + "".join(
            f'<button class="tabitem" data-tab="{tid}" '
            f'onclick="switchView(App.brand,\'{tid}\')">{_svg(tid)}<span>{tname}</span></button>'
            for tid, tname in TABS) + "</div></nav>")

    # ---- panes ----
    panes = []
    for tid, _tname in TABS:
        panes.append(f'<section class="bpane" id="pane-all-{tid}">'
                     + all_panes[tid] + "</section>")
    for b in BRANDS:
        for tid in ("overview", "approvals", "outreach", "products"):
            panes.append(f'<section class="bpane" id="pane-{b["slug"]}-{tid}">'
                         + brand_panes[b["slug"]][tid] + "</section>")
    panes_html = "\n".join(panes)

    doc = (
        "<!DOCTYPE html><html lang='en' dir='ltr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>"
        '<meta name="robots" content="noindex, nofollow">'
        '<meta name="theme-color" content="#101014">'
        '<link rel="manifest" href="admin-app/manifest.webmanifest">'
        '<link rel="apple-touch-icon" href="admin-app/assets/admin-icon-192.png">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
        "<title>ghostcorpnet admin</title>"
        "<style>__CSS__</style></head>"
        '<body><div class="app">' + sidebar
        + '<main class="main">' + topbar.replace('class="topbar"', 'class="topbar" style="margin:0 -14px"')
        + '<div id="toasts"></div>' + panes_html
        + '<div class="foot">ghostcorpnet admin · private — served only from the key-gated '
        "worker route. Not in the sitemap, not linked publicly, invisible to Google.</div>"
        "</main></div>" + tabbar
        + "<script>__JS__</script>__BE__</body></html>")

    doc = (doc.replace("__CSS__", CSS).replace("__JS__", JS)
              .replace("__BE__", S.backend_js())
              .replace("var BUILD_TS = 0;",
                       "var BUILD_TS = %d;" % int(datetime.now(timezone.utc).timestamp())))
    S.upload_private(doc)


if __name__ == "__main__":
    build()
