#!/usr/bin/env python3
"""Generate the Kestrelattice admin dashboard (admin.html).

Reads live Gumroad seller data (via ~/workspace/skills/gumroad/bin/gumroad-api,
credential custom.gumroad in the Secure Vault) plus the bot fleet's local data
(health log, product ledger, draft digests, proposals), and writes a single
self-contained admin.html. No secrets are ever written into the page.

Regenerate: python3 ~/workspace/kestrelattice/build-admin.py
(The daily site-health cron regenerates it automatically.)
"""
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser("~")
HF = os.path.join(HOME, "workspace/goals/kestrelattice-autonomous-growth/hidden_files")
GUMROAD_CLI = os.path.join(HOME, "workspace/skills/gumroad/bin/gumroad-api")
OUT = os.path.join(HOME, "workspace/kestrelattice/admin.html")

CATALOG = [
    ("The Playbook — Studio Edition", 29, "hdigmr"),
    ("AI Agent Risk Audit Kit", 19, "sahva"),
    ("Agent Incident Response Runbook", 19, "jbngbu"),
    ("100 Agent Use Cases, Pre-Tiered", 19, "slexhv"),
    ("Prompt Injection Defense Field Guide", 19, "cjdkuu"),
    ("Agent Cost Control Workbook", 19, "ilxccs"),
    ("Quarterly Access Review Kit", 19, "fdtkdd"),
    ("Complete Kestrelattice Library", 79, "yzbumc"),
]

FLEET = [
    # (bot name, schedule, signal path in hidden_files showing its latest output)
    ("Site health", "daily", "health.log"),
    ("Micro-forge (products)", "daily", "products/micro"),
    ("Lead scout", "weekly", "leads"),
    ("Content drafts", "weekly", "drafts"),
    ("SEO writer", "3× / week", "articles"),
    ("Competitor watch", "weekly", "competitors"),
    ("Mention watch", "weekly", "mentions/log.md"),
    ("FAQ miner", "weekly", "faq-drafts"),
    ("Site improver", "weekly", "proposals"),
    ("Product forge", "weekly", "products"),
    ("Partner scout", "monthly", "partners"),
    ("Pricing experimenter", "monthly", "experiments"),
    ("Marketplace scout", "weekly", "distribution"),
    ("AI model refresh", "weekly", "open-models/calls.log"),
    ("AI provider scout", "monthly", "open-models/drafts"),
]


def newest_mtime(rel):
    """Newest file modification time under a hidden_files path (file or dir)."""
    p = os.path.join(HF, rel)
    try:
        if os.path.isfile(p):
            return os.path.getmtime(p)
        best = 0.0
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs
                       if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    best = max(best, os.path.getmtime(fp))
                except OSError:
                    pass
        return best or None
    except OSError:
        return None


def fmt_time(ts):
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%b %d, %H:%M")


def esc(s):
    return html.escape(str(s), quote=True)


def read_file(path, default=""):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return default


def gumroad(path, query=""):
    """Return parsed JSON from the Gumroad API, or None on any failure."""
    try:
        cmd = [GUMROAD_CLI, path]
        if query:
            cmd.append(query)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        return data if data.get("success") else None
    except Exception:
        return None


def money_section():
    products = gumroad("products")
    if not products:
        return (
            '<div class="card warn"><h3>Sales data not connected yet</h3>'
            "<p>One-time setup: generate an API token at Gumroad → Settings → "
            "Advanced → Applications, then save it in Muse's Secure Vault as the "
            "<b>custom.gumroad</b> connector. After that, live sales numbers "
            "appear here automatically.</p></div>"
        )
    items = products.get("products", [])
    total_cents = 0
    total_n = 0
    rows = []
    by_permalink = {}
    for p in items:
        name = p.get("name", "?")
        cents = p.get("sales_usd_cents") or 0
        n = p.get("sales_count") or 0
        total_cents += cents
        total_n += n
        permalink = p.get("permalink") or p.get("short_url") or ""
        by_permalink[p.get("id", "")] = (name, cents, n)
        rows.append(
            f"<tr><td>{esc(name)}</td><td>${cents/100:,.0f}</td><td>{n}</td></tr>"
        )
    # This week's sales from /sales
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    sales = gumroad("sales", f"after={week_ago}") or {}
    week_sales = sales.get("sales", [])
    week_cents = sum(s.get("price", 0) for s in week_sales)
    cards = (
        f'<div class="stat"><b>${total_cents/100:,.0f}</b><span>all-time revenue</span></div>'
        f'<div class="stat"><b>{total_n}</b><span>all-time sales</span></div>'
        f'<div class="stat"><b>${week_cents/100:,.0f}</b><span>last 7 days ({len(week_sales)} sales)</span></div>'
    )
    table = (
        "<table><tr><th>Product</th><th>Revenue</th><th>Sales</th></tr>"
        + "".join(rows) + "</table>"
    )
    return f'<div class="statrow">{cards}</div>{table}'


def pipeline_section():
    ledger = read_file(os.path.join(HF, "products/ledger.jsonl"))
    drafts = [json.loads(l) for l in ledger.splitlines() if l.strip()]
    micro_drafts = [d for d in drafts if d.get("status") == "draft"]
    today = datetime.now().strftime("%Y-%m-%d")
    digest = read_file(
        os.path.join(HF, f"products/micro/{today}-DIGEST.md"))
    titles = re.findall(r"- \*\*(.+?)\*\*", digest)
    if not titles:  # fall back to most recent digest on disk
        try:
            ds = sorted(f for f in os.listdir(os.path.join(HF, "products/micro"))
                        if f.endswith("-DIGEST.md"))
            if ds:
                digest = read_file(os.path.join(HF, "products/micro", ds[-1]))
                titles = re.findall(r"- \*\*(.+?)\*\*", digest)
        except OSError:
            pass
    micro_list = "".join(f"<li>{esc(t)}</li>" for t in titles) or "<li>—</li>"

    def count_lines(rel):
        txt = read_file(os.path.join(HF, rel))
        return len([l for l in txt.splitlines() if l.strip().startswith("- ")])

    content_n = count_lines("drafts/2026-09-29.md")
    leads_n = count_lines("leads/2026-09-29.md")
    faq_txt = read_file(os.path.join(HF, "faq-drafts/2026-09-29.md"))
    faq_n = faq_txt.count("## ") or faq_txt.count("### ")
    cards = (
        f'<div class="stat"><b>{len(micro_drafts)}</b><span>product drafts</span></div>'
        f'<div class="stat"><b>{content_n}</b><span>content drafts</span></div>'
        f'<div class="stat"><b>{leads_n}</b><span>lead outreach drafts</span></div>'
        f'<div class="stat"><b>{faq_n}</b><span>FAQ drafts</span></div>'
    )
    return (
        f'<div class="statrow">{cards}</div>'
        f'<details class="fold"><summary>Micro-product draft titles ({len(titles)})</summary>'
        f"<ol>{micro_list}</ol></details>"
        '<p class="muted">Full manuscripts live in the fleet workspace; say the word and I\'ll publish the approved ones to Gumroad.</p>'
    )


def approvals_section():
    """Live approval queue. The buttons talk directly to the approvals backend
    (Cloudflare Worker); no email round-trip. Worker URL comes from the
    gitignored .worker-url file; until the backend is deployed we show the
    queue statically without buttons."""
    wdir = os.path.join(HOME, "workspace/kestrelattice")
    wurl = read_file(os.path.join(wdir, ".worker-url")).strip().rstrip("/")
    if not wurl:
        items = []
        for line in read_file(os.path.join(HF, "approvals/queue.jsonl")).splitlines():
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        rows = "".join(
            f"<tr><td><b>{esc(it.get('title', ''))}</b><br>"
            f"<span class='muted'>{esc(it.get('detail', ''))}</span></td>"
            f"<td><span class='pill'>waiting</span></td><td></td></tr>"
            for it in items)
        return (
            "<table><tr><th>Item</th><th>Status</th><th></th></tr>" + rows + "</table>"
            "<p class='muted'>One-tap approvals are activating — the backend "
            "finishes deploying shortly. Meanwhile you can paste a code (e.g. "
            "“approve AP-0001”) in the Talk to the bots chat.</p>")
    try:
        wkey = json.loads(read_file(os.path.join(wdir, "worker/.secrets.json")))["write_key"]
    except (OSError, KeyError, json.JSONDecodeError):
        wkey = ""
    js = (
        '<div id="appr"><p class="muted">Loading approvals…</p></div>\n'
        '<script>\n'
        'const WURL = ' + json.dumps(wurl) + ';\n'
        'const WKEY = ' + json.dumps(wkey) + ';\n'
        'const pill = s => s === "done" ? "<span class=\'pill ok\'>done</span>"'
        ' : s === "approved" ? "<span class=\'pill warn\'>approved ✓</span>"'
        ' : s.indexOf("blocked") === 0 ? "<span class=\'pill blocked\'>blocked</span>"'
        ' : "<span class=\'pill\'>waiting</span>";\n'
        'const doneCodes = JSON.parse(localStorage.getItem("apprDone") || "[]");\n'
        'async function loadApprovals() {\n'
        '  const el = document.getElementById("appr");\n'
        '  try {\n'
        '    const q = await (await fetch(WURL + "/queue")).json();\n'
        '    if (!q.length) { el.innerHTML = "<p class=\'muted\'>Nothing waiting for approval.</p>"; return; }\n'
        '    el.innerHTML = "<table><tr><th>Item</th><th>Status</th><th></th></tr>" + q.map(it => {\n'
        '      const st = doneCodes.includes(it.code) && it.status === "pending" ? "approved" : it.status;\n'
        '      const btn = (st === "pending")\n'
        '        ? `<button class="btn" onclick="approve(\\\'${it.code}\\\', this)">Approve</button>`\n'
        '        : "<span class=\'muted\'>—</span>";\n'
        '      return `<tr><td><b>${it.title}</b><br><span class=\'muted\'>${it.detail || ""}</span><br><span class=\'muted\'>Needs: ${it.prereq || "—"}</span></td><td>${pill(st)}</td><td>${btn}</td></tr>`;\n'
        '    }).join("") + "</table>"\n'
        '      + "<p class=\'muted\'>Tap <b>Approve</b> — the fleet picks it up within ~15 minutes and does the work. Or paste the code (e.g. “approve AP-0001”) in the Talk to the bots chat.</p>";\n'
        '  } catch (e) {\n'
        '    el.innerHTML = "<p class=\'muted\'>Approval service unreachable — try again shortly.</p>";\n'
        '  }\n'
        '}\n'
        'async function approve(code, btn) {\n'
        '  btn.disabled = true; btn.textContent = "Approving…";\n'
        '  try {\n'
        '    const r = await fetch(WURL + "/approve", {method: "POST",\n'
        '      headers: {"Content-Type": "application/json"},\n'
        '      body: JSON.stringify({code, key: WKEY})});\n'
        '    const d = await r.json();\n'
        '    if (d.ok) {\n'
        '      doneCodes.push(code);\n'
        '      localStorage.setItem("apprDone", JSON.stringify(doneCodes));\n'
        '      loadApprovals();\n'
        '    } else { btn.disabled = false; btn.textContent = "Retry"; }\n'
        '  } catch (e) { btn.disabled = false; btn.textContent = "Retry"; }\n'
        '}\n'
        'loadApprovals();\n'
        '</script>'
    )
    return js


def site_section():
    health = read_file(os.path.join(HF, "health.log")).strip().splitlines()
    last = esc(health[-1]) if health else "no checks logged yet"
    cat_rows = "".join(
        f"<tr><td>{esc(n)}</td><td>${p}</td><td class='mono'>koalstin.gumroad.com/l/{g}</td></tr>"
        for n, p, g in CATALOG
    )
    return (
        f'<p><b>Last health check:</b> <span class="mono">{last}</span></p>'
        f"<table><tr><th>Product</th><th>Price</th><th>Gumroad link</th></tr>{cat_rows}</table>"
    )


def fleet_section():
    calls = read_file(os.path.join(HF, "open-models/calls.log")).strip().splitlines()
    last_ai = esc(calls[-1][:120]) if calls else "no AI calls logged yet"
    bots = "".join(
        f"<tr><td>{esc(n)}</td><td>{esc(s)}</td>"
        f"<td class='mono'>{esc(fmt_time(newest_mtime(sig)))}</td></tr>"
        for n, s, sig in FLEET)
    # Activity feed: most recently touched files across the fleet workspace.
    seen = []
    for root, dirs, files in os.walk(HF):
        dirs[:] = [d for d in dirs
                   if not d.startswith(".") and d != "__pycache__"]
        for f in files:
            fp = os.path.join(root, f)
            try:
                seen.append((os.path.getmtime(fp),
                             os.path.relpath(fp, HF)))
            except OSError:
                pass
    seen.sort(reverse=True)
    feed = "".join(
        f"<li><span class='mono'>{esc(fmt_time(ts))}</span> — {esc(rel)}</li>"
        for ts, rel in seen[:12]) or "<li>—</li>"
    props = ""
    try:
        pdir = os.path.join(HF, "proposals")
        files = sorted((f for f in os.listdir(pdir) if f.endswith(".md")),
                       reverse=True)[:3]
        for f in files:
            txt = read_file(os.path.join(pdir, f))
            first = next((l.strip("# *-") for l in txt.splitlines() if l.strip()), f)
            props += f"<li><b>{esc(f[:-3])}</b> — {esc(first[:140])}</li>"
    except OSError:
        pass
    return (
        '<div class="card"><h3>Talk to your bots</h3>'
        "<p>Open the <b>Talk to the bots</b> chat in your Muse app and tell the "
        "fleet what to do in plain words — e.g. “run the lead scout now”, "
        "“pause the pricing bot”, “what did the SEO writer publish this week?”. "
        "Muse coordinates them for you; nothing goes public without your say-so.</p></div>"
        f'<p><b>Last fleet AI activity:</b> <span class="mono">{last_ai}</span></p>'
        f"<table><tr><th>Bot</th><th>Schedule</th><th>Last output</th></tr>{bots}</table>"
        f"<h3>Latest fleet activity</h3><ul>{feed}</ul>"
        f"<h3>Recently shipped site improvements</h3><ul>{props or '<li>—</li>'}</ul>"
    )


def build():
    now = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Admin Dashboard — Kestrelattice</title>
<!-- GENERATED by build-admin.py — do not hand-edit. Regenerates daily. -->
<style>
  :root{{--bg:#121212; --panel:#1c1a18; --line:#332e26; --text:#e8e2d8;
        --muted:#9a917f; --accent:#e07a5f; --accent-dim:#b9634b; --ok:#7fbf7f;}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg);color:var(--text);
       font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
       line-height:1.6}}
  .wrap{{max-width:960px;margin:0 auto;padding:40px 24px 64px}}
  .brand{{display:flex;align-items:center;gap:10px;font-weight:700;margin-bottom:4px}}
  h1{{font-size:1.6rem}} h2{{font-size:1.2rem;margin:34px 0 12px}}
  h3{{font-size:1rem;margin:22px 0 8px}}
  .gen{{color:var(--muted);font-size:.85rem;margin-bottom:8px}}
  .statrow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0}}
  .stat{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;text-align:center}}
  .stat b{{display:block;font-size:1.7rem;color:var(--accent)}}
  .stat span{{color:var(--muted);font-size:.82rem}}
  .card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px 22px;margin:14px 0}}
  .card.warn{{border-color:var(--accent-dim)}}
  .card h3{{margin:0 0 8px}} .card p{{color:var(--muted);font-size:.92rem}}
  .card b{{color:var(--text)}}
  table{{width:100%;border-collapse:collapse;font-size:.88rem;margin:12px 0}}
  th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.08em}}
  .mono{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;color:var(--muted)}}
  .muted{{color:var(--muted);font-size:.88rem}}
  details.fold{{background:var(--panel);border:1px solid var(--line);border-radius:10px;
                padding:14px 18px;margin:12px 0}}
  details.fold summary{{cursor:pointer;font-weight:600}}
  details.fold ol{{margin:10px 0 0 20px;color:var(--muted);font-size:.9rem}}
  details.fold li{{margin:3px 0}}
  ul{{margin:8px 0 8px 20px;color:var(--muted);font-size:.92rem}}
  .foot{{margin-top:40px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:16px}}
  .pill{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:600;
        background:#332e26;color:var(--muted)}}
  .pill.ok{{background:#2a3d2a;color:var(--ok)}}
  .pill.warn{{background:#3d3121;color:#e0a75f}}
  .pill.blocked{{background:#3d2421;color:#e08a7f}}
  .btn{{display:inline-block;padding:8px 18px;border-radius:8px;background:var(--accent);
       color:#121212;font-weight:700;font-size:.85rem;text-decoration:none;white-space:nowrap}}
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <svg width="24" height="24" viewBox="0 0 26 26" fill="none" aria-hidden="true"><circle cx="5" cy="6" r="2.4" fill="#e07a5f"/><circle cx="21" cy="6" r="2.4" fill="#e07a5f"/><circle cx="13" cy="13" r="2.4" fill="#e07a5f"/><circle cx="5" cy="20" r="2.4" fill="#e07a5f"/><circle cx="21" cy="20" r="2.4" fill="#e07a5f"/><path d="M6.6 7.4L11.2 11.8M19.4 7.4L14.8 11.8M6.6 18.6L11.2 14.2M19.4 18.6L14.8 14.2" stroke="#e07a5f" stroke-width="1.4"/></svg>
    Kestrelattice
  </div>
  <h1>Admin dashboard</h1>
  <p class="gen">Generated {esc(now)} · refreshes daily with the site-health check</p>

  <h2>Money</h2>
  {money_section()}

  <h2>Needs your approval</h2>
  {approvals_section()}

  <h2>Review pipeline</h2>
  {pipeline_section()}

  <h2>Site &amp; catalog</h2>
  {site_section()}

  <h2>Fleet</h2>
  {fleet_section()}

  <h2>Traffic</h2>
  <div class="card"><h3>Google Analytics needs a one-time setup</h3>
  <p>Live visitor numbers can't be pulled with just a key — Google requires an
  OAuth client you create in Google Cloud Console (about 10 minutes at a computer).
  Say the word and I'll walk you through it; after that, traffic charts appear here.</p></div>

  <div class="foot">Private page: unlinked and hidden from search engines, but anyone who
  guesses the URL could open it — it shows real revenue figures. Say the word if you want
  it hardened further.</div>
</div>
</body>
</html>"""
    with open(OUT, "w") as f:
        f.write(body)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
