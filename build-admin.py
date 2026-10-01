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
.main{flex:1;min-width:0;max-width:1180px;margin:0 auto;padding:0 28px 120px;width:100%}
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
.tabitem.on{color:var(--accent)}
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
  border:1px solid var(--line);border-radius:var(--r);
  padding:22px 24px;margin:14px 0;box-shadow:var(--shadow)}
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
  min-height:44px;padding:11px 22px;border:0;border-radius:12px;
  background:linear-gradient(135deg,var(--accent),#ef9278);
  color:var(--accent-ink);font-weight:750;font-size:.9rem;cursor:pointer;font-family:inherit;
  box-shadow:0 3px 12px rgba(224,122,95,.32);transition:all .15s ease;white-space:nowrap}
.btn:hover{filter:brightness(1.07);transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn:disabled{opacity:.65;cursor:default;transform:none}
.btn-ghost{background:var(--panel2);color:var(--muted);border:1px solid var(--line2);box-shadow:none}
.btn-ghost:hover{color:var(--text);border-color:var(--faint);filter:none}
.btn-sm{min-height:38px;padding:8px 16px;font-size:.82rem;border-radius:10px}
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
var App = {brand:'all', tab:'overview'};
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
  if (['drafts','fleet','hive','captain','extras'].indexOf(tab) >= 0) brand = 'all';
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
}
TABS = [("overview", "Overview"), ("captain", "Captain"), ("approvals", "Approvals"), ("outreach", "Outreach"),
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
        '<div class="card"><h3>Google Analytics needs a one-time setup</h3>'
        "<p>Live visitor numbers can't be pulled with just a key — Google requires an "
        "OAuth client you create in Google Cloud Console (about 10 minutes at a computer). "
        "Say the word and I'll walk you through it; after that, traffic charts appear here.</p></div>"
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

    # ---------------- budget ----------------
    budget = st.get("budget") or {}
    spent = budget.get("usd_est") or 0
    cap = budget.get("daily_cap_usd") or 0
    try:
        spent = float(spent)
        cap = float(cap)
        pct = (spent / cap * 100) if cap else 0
        budget_bar = (
            '<div style="background:var(--panel2);border:1px solid var(--line);'
            'border-radius:8px;height:14px;overflow:hidden;margin:8px 0 4px">'
            f'<div style="height:100%;width:{min(100, pct):.2f}%;'
            'background:linear-gradient(90deg,var(--accent),#ef9278)"></div></div>'
            f'<p class="muted">${spent:.4f} of ${cap:.2f} daily cap'
            f' &middot; {pct:.2f}% used &middot; cycle {esc(str(budget.get("cycle", "?")))}'
            + (" &middot; <b>THROTTLED</b>" if budget.get("throttled") else "")
            + '</p>')
    except Exception:
        budget_bar = '<p class="muted">Budget unavailable</p>'
    by_task = budget.get("by_task") or {}
    bt_rows = "".join(
        f"<tr><td><span class='mono'>{esc(str(k))}</span></td>"
        f"<td>~{esc(str(v))} tokens</td></tr>"
        for k, v in sorted(by_task.items(), key=lambda kv: -(kv[1] or 0)))
    per_cycle = budget.get("per_cycle") or []
    pc_rows = "".join(
        f"<tr><td><span class='mono'>{esc(str(e.get('ts', '')))}</span></td>"
        f"<td><span class='mono'>{esc(str(e.get('actor', '')))}</span></td>"
        f"<td><span class='mono'>{esc(str(e.get('task_id') or '—'))}</span></td>"
        f"<td>{e.get('tokens_est') or 0}</td>"
        f"<td>${(e.get('usd_est') or 0):.6f}</td>"
        f"<td class='muted'>{esc(str(e.get('note', ''))[:80])}</td></tr>"
        for e in per_cycle[-6:])
    budget_card = (
        '<div class="card"><h3>Budget — daily AI spend</h3>' + budget_bar
        + ('<h3 style="margin-top:14px">Spend by task</h3>'
           '<div class="table-wrap"><table><thead><tr><th>Task</th>'
           '<th>Tokens (est)</th></tr></thead><tbody>' + bt_rows +
           '</tbody></table></div>' if bt_rows else
           '<p class="muted">No task-level spend recorded yet.</p>')
        + ('<h3 style="margin-top:14px">Recent ledger entries</h3>'
           '<div class="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th>'
           '<th>Task</th><th>Tokens</th><th>USD</th><th>Note</th></tr></thead>'
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
into its inbox. This panel box wakes up after the pending Cloudflare deploy (one tap).</p>
<div id="sent-thread" class="chat-thread"><p class="muted">Loading...</p></div>
<div class="chat-input"><input id="sent-input" type="text" placeholder="Talk to it like you talk to me..." maxlength="2000"><button class="btn" id="sent-send">Send</button></div>
</div>
<script>(function(){
function escH(s){var d=document.createElement("div");d.appendChild(document.createTextNode(s));return d.innerHTML;}
async function sentLoad(){
var thread=document.getElementById("sent-thread");
if(!thread||typeof WURL==="undefined"||!WURL||!WKEY){if(thread)thread.innerHTML="<p class='muted'>Not connected: no admin key on this device.</p>";return;}
try{
var r=await fetch(WURL+"/sentience-chat?key="+encodeURIComponent(WKEY));
var msgs=await r.json();
if(!Array.isArray(msgs)||!msgs.length){thread.innerHTML="<p class='muted'>No messages yet. Say hi.</p>";return;}
thread.innerHTML=msgs.map(function(m){
var who=m.from==="koalstin"?"you":"sentience";
return '<div class="chat-msg '+who+'"><span class="chat-who">'+who+'</span><p>'+escH(m.text)+"</p></div>";
}).join("");
thread.scrollTop=thread.scrollHeight;
}catch(e){}}
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


def _all_panes(products, queue, entries, title_map, omap):
    p = {}
    p["overview"] = (
        '<div class="hero"><h1>ghostcorpnet admin</h1>'
        '<p class="lede">Every business, one command center. Pick a brand in the '
        "sidebar — or stay here for the whole empire.</p></div>"
        + S.kpi_strip(products, queue)
        + brand_comparison_table(products, entries, queue, title_map, omap)
        + S.alerts_section(queue, products) + S.revenue_section(products) + S.activity_feed()
    )
    p["captain"] = (_sec("Private operator", "Sentience",
                         "One mind, yours alone. It runs the fleet, operates the ten brands, "
                         "hires freelancers, and does client work start to finish — so you don't have to.")
                    + _captain_html())
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
                  + S.fleet_section())
    p["hive"] = (_sec("Swarm control", "Hive",
                      "The 103-role HiveBrain: live task queue, workers, budget, migration.")
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
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
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
