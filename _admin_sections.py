#!/usr/bin/env python3
"""Generate the ghostcorpnet admin dashboard (admin.html).

Reads live Gumroad seller data (via ~/workspace/skills/gumroad/bin/gumroad-api),
the approvals worker queue, outreach ledger, and bot log files, and writes a
single self-contained admin.html: KPI strip, alerts, revenue milestones, fleet
activity, approvals (one-tap), outreach, products, drafts, fleet, and extras.
No secrets are ever written into the page; it is served only from the
key-gated worker /admin route (wrong/missing key -> 404), noindex.

Regenerate: python3 ~/workspace/kestrelattice/build-admin.py
"""
import html
import glob
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
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

FLEET = [
    ("Site health", "daily", "health.log"),
    ("Micro-forge (products)", "daily", "products/micro"),
    ("Lead scout", "daily", "leads"),
    ("Content drafts", "daily", "drafts"),
    ("SEO writer", "3× / week", "articles"),
    ("Competitor watch", "weekly", "competitors"),
    ("Mention watch", "daily", "mentions/log.md"),
    ("FAQ miner", "weekly", "faq-drafts"),
    ("Site improver", "weekly", "proposals"),
    ("Product forge", "weekly", "products"),
    ("Partner scout", "weekly", "partners"),
    ("Pricing experimenter", "monthly", "experiments"),
    ("Marketplace scout", "daily", "distribution"),
    ("AI model refresh", "weekly", "open-models/calls.log"),
    ("AI provider scout", "monthly", "open-models/drafts"),
    ("TikTok studio", "daily", "tiktok"),
]
HEALTH_WINDOWS = {
    "daily": (36, 72),
    "3× / week": (96, 192),
    "weekly": (240, 408),
    "monthly": (1080, 1800),
}
# koalstin's four teams — every bot belongs to exactly one. Charters live in
# hidden_files/teams/. Rendered as cards at the top of the Fleet tab.
TEAMS = [
    ("Marketing", "Bring customers in.",
     "outreach-sync (5 min) · lead scout (daily) · 11 brand teams (daily + weekly) · "
     "SEO writers (3×/week) · TikTok studio (daily) · Pinterest / Medium / Shorts · "
     "affiliates · mention + competitor + partner watch"),
    ("Analytics", "Measure everything, report honestly.",
     "dashboard refresh (daily) · sale watch (5 min) · site health (daily) · "
     "pricing experiments (monthly) · watchdog (30 min) · worker-recovery probe (30 min)"),
    ("Coding", "Write and ship code.",
     "site improver (weekly) · UI scout (15 min) · AI model refresh (weekly) · "
     "AI provider scout (monthly)"),
    ("Development", "Build products and businesses.",
     "micro-forge (daily drafts) · product forge (weekly) · Gumroad publisher (daily) · "
     "business foundry (new brand weekly) · ecosystem expansion (monthly)"),
]
# Queue kinds that are NEVER auto-approved — they wait for a human tap.
HUMAN_KINDS = ("outreach_forget", "draft_approve", "draft_discard")


def health_of(schedule, ts):
    if not ts:
        return "never", "no data"
    age_h = (time.time() - ts) / 3600.0
    ok_h, warn_h = HEALTH_WINDOWS.get(schedule, (240, 408))
    if age_h <= ok_h:
        return "ok", "active"
    if age_h <= warn_h:
        return "warn", "quiet"
    return "stale", "stale"


def newest_mtime(rel):
    p = os.path.join(HF, rel)
    try:
        if os.path.isfile(p):
            return os.path.getmtime(p)
        best = 0.0
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
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


def curl_get(url):
    """Read-only GET with a browser UA (Cloudflare WAF blocks python urllib)."""
    try:
        r = subprocess.run(["curl", "-s", "-m", "25", "-A", UA, url],
                           capture_output=True, text=True, timeout=40)
        if r.returncode != 0:
            return None
        return json.loads(r.stdout)
    except Exception:
        return None


def gumroad(path, query=""):
    try:
        cmd = [sys.executable, GUMROAD_CLI, path]
        if query:
            cmd.append(query)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        return data if data.get("success") else None
    except Exception:
        return None


def gumroad_all_products():
    items, page_key, seen = [], None, set()
    for _ in range(20):
        q = f"page_key={urllib.parse.quote(page_key)}" if page_key else ""
        data = gumroad("products", q)
        if not data:
            return None if not items else items
        for p in data.get("products", []):
            if p.get("id") not in seen:
                seen.add(p.get("id"))
                items.append(p)
        page_key = data.get("next_page_key")
        if not page_key:
            break
    return items


def get_queue():
    try:
        sec = json.loads(read_file(os.path.join(HOME, "workspace/kestrelattice/worker/.secrets.json")))
        wurl = sec.get("worker_url", "").rstrip("/")
        if not wurl:
            return []
        q = curl_get(wurl + "/queue")
        return q if isinstance(q, list) else []
    except Exception:
        return []


def sent_today_count():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    n = 0
    for line in read_file(os.path.join(HF, "outreach/sent-ledger.jsonl")).splitlines():
        line = line.strip()
        if line:
            try:
                if json.loads(line).get("at", "").startswith(today):
                    n += 1
            except json.JSONDecodeError:
                pass
    return n


def last_watcher_run():
    """(label, css class) for the most recent watcher run or skip."""
    lines = [l for l in read_file(os.path.join(HF, "approvals/watcher-runs.log")).splitlines() if l.strip()]
    for line in reversed(lines[-25:]):
        m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(?::\d{2})?Z?\s*(.*)", line)
        if m:
            ts, rest = m.group(1), m.group(2).lower()
            when = ts.replace("T", " ") + "Z"
            if "skip" in rest:
                return f"skipped · {when}", "warn"
            if "completed" in rest or "done" in rest:
                return f"ran · {when}", "ok"
            return f"{when}", "ok"
    return "no runs logged", "never"


# ---------------------------------------------------------------- sections

def kpi_strip(products, queue):
    live = [p for p in products if p.get("published")] if products else []
    drafts = [p for p in products if not p.get("published")] if products else []
    catalog_value = sum((p.get("price") or 0) for p in live) / 100.0
    sends = sent_today_count()
    blocked = [i for i in queue if str(i.get("status", "")).startswith("blocked")]
    human_pending = [i for i in queue
                     if i.get("status") == "pending" and i.get("kind") in HUMAN_KINDS]
    taps = len(blocked) + len(human_pending)
    wstat, wcls = last_watcher_run()
    five = None
    if products:
        five = next((p.get("name") for p in products
                     if (p.get("price") or 0) == 500 and p.get("published")), None)

    def tile(value, label, sub="", css=""):
        return (f'<div class="kpi {css}"><div class="kpi-v">{value}</div>'
                f'<div class="kpi-l">{label}</div>'
                + (f'<div class="kpi-s">{sub}</div>' if sub else "") + '</div>')

    return (
        '<div class="kpirow">'
        + tile(f"{len(live)}", "live products",
               f"{len(drafts)} unpublished drafts" if drafts else "0 drafts", "accent")
        + tile(f"${catalog_value:,.0f}", "catalog value",
               "sum of live prices")
        + tile(f"{sends}<span class='kpi-cap'>/20</span>", "pitches sent today",
               "daily cap", "warn" if sends >= 20 else "")
        + tile(f"{taps}", "need your tap",
               "blocked + human-only", "bad" if taps else "")
        + tile(f'<span class="kpi-small">{esc(wstat)}</span>', "watcher",
               "last run", wcls)
        + '</div>'
        + (f'<p class="muted" style="margin:6px 2px 0">$5 entry product live: <b>{esc(five)}</b></p>' if five else "")
    )


def alerts_section(queue, products):
    alerts = []
    for i in queue:
        st = str(i.get("status", ""))
        if st.startswith("blocked"):
            alerts.append(
                ("blocked", i.get("title", i.get("code", "")), st, i.get("detail", "")))
        if i.get("kind") == "inbox_escalation" and st == "pending":
            alerts.append(
                ("escalation", i.get("title", i.get("code", "")),
                 "needs human", "A customer thread needs your personal reply."))
    try:
        prog = json.loads(read_file(os.path.join(HF, "approvals/progress.json")) or "{}")
    except json.JSONDecodeError:
        prog = {}
    live_n = len([p for p in (products or []) if p.get("published")])
    cu = prog.get("covers_uploaded") or 0
    covered = len(cu) if isinstance(cu, list) else cu
    if live_n and covered and live_n > covered:
        alerts.append(("covers", f"{live_n - covered} products missing cover art",
                       "info", "Generated locally; the watcher uploads them on its next run."))
    rec = prog.get("reconciled_2026-09-30_0245") or {}
    for name in rec.get("gumroad_unpublished", []) or []:
        if "dup" in name.lower():
            alerts.append(("duplicate", f"Duplicate live product: {name}",
                           "info", "Unpublish one — deleting is human-only."))
    if not alerts:
        return ('<div class="card ok-card"><h3>All clear</h3>'
                '<p class="muted">Nothing blocked, no duplicates, covers complete.</p></div>')
    items = ""
    for kind, title, status, detail in alerts:
        items += (
            '<div class="alert"><span class="pill blocked">' + esc(status) + '</span> '
            '<b>' + esc(title) + '</b>'
            + (f'<br><span class="muted">{esc(detail[:200])}</span>' if detail else "")
            + '</div>')
    return ('<div class="card warn"><h3>Alerts <span class="pill">' + str(len(alerts)) +
            '</span></h3>' + items + '</div>')


def money_latest_sale_html():
    """Latest-sale callout, fed by the approval watcher's sale watch (read-only).
    Shows only what the Gumroad API actually returned — never invented."""
    latest = None
    for line in read_file(os.path.join(HF, "money/sales-alerts.jsonl")).splitlines():
        line = line.strip()
        if line:
            try:
                latest = json.loads(line)
            except json.JSONDecodeError:
                continue
    if not latest:
        return ""
    price = (latest.get("price_cents") or 0) / 100.0
    return (
        '<div class="alert"><span class="pill ok">new sale</span> '
        f'<b>${price:,.0f}</b> — {esc(latest.get("product_name") or "a product")}'
        f' <span class="muted">{esc(str(latest.get("at") or "")[:16]).replace("T", " ")}</span></div>')


def revenue_section(products):
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    sales = gumroad("sales", f"after={week_ago}") or {}
    week_sales = sales.get("sales", [])
    week_cents = sum(s.get("price", 0) for s in week_sales)
    total_cents = 0
    total_n = 0
    if products:
        for p in products:
            total_cents += p.get("sales_usd_cents") or 0
            total_n += p.get("sales_count") or 0
    total = total_cents / 100.0
    milestones = [("First sale", 0), ("$10 — Gumroad Discover unlocks", 10),
                  ("$100 — first sales week", 100), ("$6,000 — monthly walk-away goal", 6000)]
    steps = ""
    for label, amt in milestones:
        hit = total >= amt and amt > 0
        cur = total < amt and (milestones.index((label, amt)) == 0 or
                               total >= milestones[milestones.index((label, amt)) - 1][1])
        cls = "hit" if hit else ("cur" if cur else "")
        dot = "✓" if hit else ("▸" if cur else "○")
        steps += (f'<div class="ms {cls}"><span class="ms-dot">{dot}</span>'
                  f'<span class="ms-l">{esc(label)}</span>'
                  f'<span class="ms-a">${amt:,}</span></div>')
    pct = min(100.0, (total / 6000.0) * 100.0)
    payouts = gumroad("payouts") or {}
    payout_list = payouts.get("payouts", []) if isinstance(payouts, dict) else []
    payout_note = (f"{len(payout_list)} payout(s) recorded"
                   if payout_list else "no payouts yet — weekly, $100 minimum")
    return (
        '<div class="card"><h3>Revenue</h3>'
        + money_latest_sale_html()
        + '<div class="statrow">'
        f'<div class="stat"><b>${total:,.0f}</b><span>all-time revenue</span></div>'
        f'<div class="stat"><b>{total_n}</b><span>all-time sales</span></div>'
        f'<div class="stat"><b>${week_cents/100:,.0f}</b><span>last 7 days ({len(week_sales)} sales)</span></div>'
        '</div>'
        f'<p class="muted">Gumroad payouts: {esc(payout_note)} (read-only — payouts themselves are never automated).</p>'
        + ("" if total_n else
           '<p class="muted">No sales yet — shown honestly. Every number here comes '
           'straight from the Gumroad API; nothing is estimated or projected.</p>')
        + '<div class="ms-track">' + steps + '</div>'
        '<div class="bar"><div class="bar-fill" style="width:' + f"{pct:.2f}" +
        '%"></div></div>'
        f'<p class="muted">Progress to the $6,000/month goal: {pct:.1f}%</p>'
        '</div>'
    )


def activity_feed():
    feeds = []
    def take(rel, n, name):
        lines = [l for l in read_file(os.path.join(HF, rel)).splitlines() if l.strip()]
        for l in lines[-n:]:
            m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})", l)
            ts = m.group(1) if m else ""
            feeds.append((ts, name, l[:220]))
    take("approvals/watcher-runs.log", 8, "watcher")
    take("site-improvements/scout.log", 4, "ui-scout")
    take("outreach/sync.log", 4, "outreach")
    feeds.sort(key=lambda x: x[0], reverse=True)
    rows = "".join(
        f'<li><span class="src">{esc(s)}</span> '
        f'<span class="mono">{esc(ts)}</span> — {esc(t)}</li>'
        for ts, s, t in feeds[:20]) or "<li>—</li>"
    return ('<div class="card"><h3>Fleet activity</h3>'
            '<p class="lede">Latest bot runs, newest first. Full logs live in the fleet workspace.</p>'
            f'<ul class="feed">{rows}</ul></div>')


def money_section(products):
    if not products:
        return (
            '<div class="card warn"><h3>Sales data not connected yet</h3>'
            "<p>One-time setup: generate an API token at Gumroad → Settings → "
            "Advanced → Applications, then save it in Muse's Secure Vault as the "
            "<b>custom.gumroad</b> connector. After that, live sales numbers "
            "appear here automatically.</p></div>"
        )
    rows = []
    for p in products:
        if not p.get("published"):
            continue
        name = p.get("name", "?")
        cents = p.get("sales_usd_cents") or 0
        n = p.get("sales_count") or 0
        price = (p.get("price") or 0) / 100.0
        url = (p.get("short_url") or p.get("permalink") or "").rstrip("/")
        disp = url.replace("https://", "").replace("http://", "")
        tags = p.get("tags") or []
        code_badge = (" <span class='badge code'>CODE</span>"
                      if any("code" in str(t).lower() for t in tags) else "")
        rows.append(
            f"<tr><td><b>{esc(name)}</b>{code_badge}<br><a class='mono' href='{esc(url)}' "
            f"target='_blank' rel='noopener'>{esc(disp)}</a></td>"
            f"<td>${price:,.0f}</td><td>${cents/100:,.0f}</td><td>{n}</td></tr>"
        )
    return (
        '<div class="table-wrap"><table><tr><th>Product</th><th>Price</th>'
        '<th>Revenue</th><th>Sales</th></tr>' + "".join(rows) + "</table></div>"
    )


def pipeline_section():
    ledger = read_file(os.path.join(HF, "products/ledger.jsonl"))
    drafts = [json.loads(l) for l in ledger.splitlines() if l.strip()]
    micro_drafts = [d for d in drafts if d.get("status") == "draft"]
    today = datetime.now().strftime("%Y-%m-%d")
    digest = read_file(os.path.join(HF, f"products/micro/{today}-DIGEST.md"))
    titles = re.findall(r"- \*\*(.+?)\*\*", digest)
    if not titles:
        try:
            ds = sorted(f for f in os.listdir(os.path.join(HF, "products/micro"))
                        if f.endswith("-DIGEST.md"))
            if ds:
                digest = read_file(os.path.join(HF, "products/micro", ds[-1]))
                titles = re.findall(r"- \*\*(.+?)\*\*", digest)
        except OSError:
            pass
    micro_list = "".join(f"<li>{esc(t)}</li>" for t in titles) or "<li>—</li>"
    cards = (
        f'<div class="statrow">'
        f'<div class="stat"><b>{len(micro_drafts)}</b><span>product drafts</span></div>'
        f'<div class="stat"><b>{len(titles)}</b><span>titles in latest digest</span></div>'
        f'</div>'
    )
    return (
        cards +
        f'<details class="fold"><summary>Micro-product draft titles ({len(titles)})</summary>'
        f"<ol>{micro_list}</ol></details>"
    )


def backend_js():
    """Keyless build: the admin write key is NEVER embedded in the HTML.
    The browser-side code reads the key this device already has — the admin
    login page stores it in localStorage under
    "kestrelattice_admin_remember" when "Remember on this device" is ticked
    (its default). When the key is absent, every action fails gracefully
    with a "not connected" message instead of breaking."""
    wdir = os.path.join(HOME, "workspace/kestrelattice")
    wurl = read_file(os.path.join(wdir, ".worker-url")).strip().rstrip("/")
    return (
        '<script>\n'
        'const WURL = ' + json.dumps(wurl) + ';\n'
        'let WKEY = "";\n'
        'try { WKEY = new URLSearchParams(location.search).get("key") || localStorage.getItem("kestrelattice_admin_remember") || ""; } catch (e) {}\n'
        'async function approveCode(code, btn, doneLabel) {\n'
        '  if (!WURL || !WKEY) { alert("Not connected: no admin key on this device. Open the admin login page again and tick \\"Remember on this device\\"."); return false; }\n'
        '  if (btn) { btn.disabled = true; btn.textContent = "Working…"; }\n'
        '  try {\n'
        '    const r = await fetch(WURL + "/approve", {method: "POST",\n'
        '      headers: {"Content-Type": "application/json"},\n'
        '      body: JSON.stringify({code: code, key: WKEY})});\n'
        '    const d = await r.json();\n'
        '    if (d.ok) { if (btn) btn.textContent = doneLabel || "Done ✓"; return true; }\n'
        '  } catch (e) {}\n'
        '  if (btn) { btn.disabled = false; btn.textContent = "Retry"; }\n'
        '  return false;\n'
        '}\n'
        'function switchTab(name) {\n'
        '  document.querySelectorAll(".tabpane").forEach(p => p.classList.toggle("on", p.id === "tab-" + name));\n'
        '  document.querySelectorAll(".tabbtn").forEach(b => b.classList.toggle("on", b.dataset.tab === name));\n'
        '  try { history.replaceState(null, "", "#" + name); } catch (e) {}\n'
        '  window.scrollTo(0, 0);\n'
        '}\n'
        'document.addEventListener("DOMContentLoaded", function() {\n'
        '  const h = (location.hash || "#overview").slice(1);\n'
        '  switchTab(document.getElementById("tab-" + h) ? h : "overview");\n'
        '});\n'
        '</script>'
    )


def approvals_section():
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
            '<div class="table-wrap"><table><tr><th>Item</th><th>Status</th><th></th></tr>'
            + rows + "</table></div>"
            "<p class='muted'>One-tap approvals are activating — the backend "
            "finishes deploying shortly.</p>")
    # NOTE: the write key is intentionally NEVER read here — it is not
    # embedded in the page. The browser sends the key it already holds
    # (see backend_js); without it the UI fails gracefully.
    js = (
        '<div id="appr"><p class="muted">Loading approvals…</p></div>\n'
        '<script>\n'
        'const pill = s => s === "done" ? "<span class=\'pill ok\'>done</span>"'
        ' : s === "approved" ? "<span class=\'pill warn\'>approved ✓</span>"'
        ' : s.indexOf("blocked") === 0 ? "<span class=\'pill blocked\'>blocked</span>"'
        ' : "<span class=\'pill\'>waiting</span>";\n'
        'const doneCodes = JSON.parse(localStorage.getItem("apprDone") || "[]");\n'
        'async function loadApprovals() {\n'
        '  const el = document.getElementById("appr");\n'
        '  try {\n'
        '    const q = (await (await fetch(WURL + "/queue")).json()).filter(it => it.group !== "outreach" && it.group !== "drafts");\n'
        '    if (!q.length) { el.innerHTML = "<p class=\'muted\'>Nothing waiting for approval.</p>"; return; }\n'
        '    el.innerHTML = "<div class=\'table-wrap\'><table><tr><th>Item</th><th>Status</th><th></th></tr>" + q.map(it => {\n'
        '      const st = doneCodes.includes(it.code) && it.status === "pending" ? "approved" : it.status;\n'
        '      const btn = (st === "pending")\n'
        '        ? `<button class="btn" onclick="approve(\\\'${it.code}\\\', this)">Approve</button>`\n'
        '        : "<span class=\'muted\'>—</span>";\n'
        '      return `<tr><td><b>${it.title}</b><br><span class=\'muted\'>${it.detail || ""}</span><br><span class=\'muted\'>Needs: ${it.prereq || "—"}</span></td><td>${pill(st)}</td><td>${btn}</td></tr>`;\n'
        '    }).join("") + "</table></div>"\n'
        '      + "<p class=\'muted\'>Tap <b>Approve</b> — the fleet picks it up within ~15 minutes and does the work.<br>Routine site development auto-approves by policy — only items that move money, change prices, or send messages wait for your tap.</p>";\n'
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
        '// WURL/WKEY are declared in the late backend_js block (end of body),\n'
        '// so the first load must wait until they exist — DOMContentLoaded\n'
        '// fires after all parser-inserted scripts have run.\n'
        'document.addEventListener("DOMContentLoaded", loadApprovals);\n'
        '</script>'
    )
    return js


def action_center_section():
    """The one-spot live tap list. Polls the worker /taps endpoint every 5s
    (approvals + needs-human taps, consolidated). Until the worker code with
    /taps is deployed, it falls back to the public /queue for approvals so
    the tab is useful immediately. Approve buttons execute via /approve;
    "Mark handled" hides a tap via /tap-resolve (write-key gated)."""
    return (
        '<div id="taplist"><p class="muted">Connecting to the live tap feed…</p></div>\n'
        '<script>\n'
        'async function loadTaps() {\n'
        '  const el = document.getElementById("taplist");\n'
        '  if (!WURL || !WKEY) { el.innerHTML = "<p class=\'muted\'>Not connected: no admin key on this device. Open the admin login page and tick \\"Remember on this device\\".</p>"; return; }\n'
        '  let d = null, tapsLive = false;\n'
        '  try {\n'
        '    const r = await fetch(WURL + "/taps?key=" + encodeURIComponent(WKEY));\n'
        '    if (r.ok) { d = await r.json(); tapsLive = !!(d && d.ok); }\n'
        '  } catch (e) {}\n'
        '  if (!tapsLive) {\n'
        '    try {\n'
        '      const q = await (await fetch(WURL + "/queue")).json();\n'
        '      d = {ok: true, approvals: q.filter(it => it.status === "pending" && it.group !== "outreach" && it.group !== "drafts"), taps: []};\n'
        '    } catch (e) { el.innerHTML = "<p class=\'muted\'>Tap feed unreachable — retrying…</p>"; return; }\n'
        '  }\n'
        '  const ap = d.approvals || [], tp = d.taps || [];\n'
        '  const stamp = new Date().toLocaleTimeString();\n'
        '  let html = "";\n'
        '  if (!ap.length && !tp.length) {\n'
        '    html = "<div class=\'tapcard\'><b>All clear \\u0001F389</b><p>Nothing needs your tap right now.</p></div>";\n'
        '  }\n'
        '  if (ap.length) {\n'
        '    html += "<div class=\'sec-title\'><div class=\'eyebrow\'>One tap each</div><h2>Approvals waiting (" + ap.length + ")</h2></div>";\n'
        '    html += "<div class=\'table-wrap\'><table><tr><th>Item</th><th></th></tr>" + ap.map(it =>\n'
        '      `<tr><td><b>${it.title}</b><br><span class=\'muted\'>${it.detail || ""}</span></td>` +\n'
        '      `<td style="white-space:nowrap"><button class="btn" onclick="tapApprove(\\\'${it.code}\\\', this)">Approve</button></td></tr>`\n'
        '    ).join("") + "</table></div>";\n'
        '  }\n'
        '  if (tp.length) {\n'
        '    html += "<div class=\'sec-title\'><div class=\'eyebrow\'>Your call</div><h2>Needs your tap (" + tp.length + ")</h2></div>";\n'
        '    html += tp.map(t =>\n'
        '      `<div class="tapcard"><b>${t.title}</b><p>${t.detail || ""}</p>` +\n'
        '      (t.tap ? `<p class="taphow">${t.tap}</p>` : "") +\n'
        '      `<button class="btn" onclick="tapResolve(\\\'${t.id}\\\', this)">Mark handled</button></div>`\n'
        '    ).join("");\n'
        '  }\n'
        '  if (!tapsLive) html += "<p class=\'muted\'>Tap sync activating — approvals above are live; the full tap list arrives with the next backend update.</p>";\n'
        '  html += `<p class=\'muted\' style=\'margin-top:16px\'>Live \\u00b7 refreshed ${stamp} \\u00b7 updates every 5 seconds</p>`;\n'
        '  el.innerHTML = html;\n'
        '}\n'
        'async function tapApprove(code, btn) {\n'
        '  const ok = await approveCode(code, btn, "Approved \\u2713");\n'
        '  if (ok) setTimeout(loadTaps, 800);\n'
        '}\n'
        'async function tapResolve(id, btn) {\n'
        '  btn.disabled = true; btn.textContent = "Working…";\n'
        '  try {\n'
        '    const r = await fetch(WURL + "/tap-resolve", {method: "POST",\n'
        '      headers: {"Content-Type": "application/json"},\n'
        '      body: JSON.stringify({id: id, key: WKEY, choice: "handled"})});\n'
        '    const dd = await r.json();\n'
        '    if (dd.ok) { loadTaps(); return; }\n'
        '  } catch (e) {}\n'
        '  btn.disabled = false; btn.textContent = "Retry";\n'
        '}\n'
        '// WURL/WKEY/approveCode are declared in the backend_js block (end of body),\n'
        '// so the first load must wait until they exist — DOMContentLoaded fires\n'
        '// after all parser-inserted scripts have run.\n'
        'document.addEventListener("DOMContentLoaded", function() {\n'
        '  loadTaps();\n'
        '  setInterval(loadTaps, 5000);\n'
        '});\n'
        '</script>'
    )


def outreach_section():
    items = []
    for line in read_file(os.path.join(HF, "outreach/queue.jsonl")).splitlines():
        line = line.strip()
        if line:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    ready = [i for i in items if i.get("status") == "ready"]
    needc = [i for i in items if i.get("status") == "needs-contact"]
    sent = [i for i in items if i.get("status") == "sent"]
    stats = (
        '<div class="statrow">'
        f'<div class="stat"><b>{len(ready)}</b><span>ready to send</span></div>'
        f'<div class="stat"><b>{len(needc)}</b><span>finding contact</span></div>'
        f'<div class="stat"><b>{len(sent)}</b><span>pitches sent</span></div>'
        '</div>'
    )
    if not ready and not needc and not sent:
        return stats + ("<p class='muted'>No outreach yet — the sync bot drafts pitches "
                        "from every lead scout run, around the clock.</p>")
    cards = []
    for it in ready:
        qid = it.get("id", "")
        cards.append(
            '<div class="card"><h3>' + esc(it.get("lead", "?")) + '</h3>'
            '<p>' + esc(it.get("why", "")) + '</p>'
            '<p class="muted">To: <b>' + esc(it.get("contact_email", "")) + '</b> '
            '<span class="mono">(' + esc(it.get("email_source", "")) + ')</span></p>'
            '<details class="fold"><summary>Pitch — ' + esc(it.get("subject", "")) + '</summary>'
            '<p style="white-space:pre-wrap">' + esc(it.get("pitch", "")) + '</p></details>'
            '<button class="btn" onclick="approveCode(\'OS-' + esc(qid) + '\', this, \'Queued ✓\')">Send pitch</button> '
            '<button class="btn" style="background:#3a352d;color:var(--muted)" '
            'onclick="approveCode(\'OF-' + esc(qid) + '\', this, \'Forgotten\')">Forget</button>'
            '<p class="muted" style="margin-top:8px">Your tap queues this pitch — the watcher sends it '
            'from your business Gmail within ~15 minutes. A short opt-out footer is appended.</p></div>'
        )
    need_html = ""
    if needc:
        rows = "".join(
            "<li><b>" + esc(i.get("lead", "?")) + "</b> — " + esc(i.get("why", "")) +
            ' <span class="muted">(still looking for a public contact email)</span></li>'
            for i in needc)
        need_html = ('<details class="fold"><summary>Finding a contact (' + str(len(needc)) +
                     ')</summary><ul>' + rows + '</ul></details>')
    return stats + "".join(cards) + need_html


def inbox_section(queue=None):
    """Customer inbox loop: replies received, auto-replies sent, opt-outs, escalations."""
    try:
        state = json.loads(read_file(os.path.join(HF, "inbox/state.json")) or "{}")
    except json.JSONDecodeError:
        state = {}
    queue = queue if queue is not None else get_queue()
    escs = [i for i in queue if i.get("kind") == "inbox_escalation"
            and i.get("status") == "pending"]
    recent = []
    for line in read_file(os.path.join(HF, "inbox/replied.jsonl")).splitlines():
        line = line.strip()
        if line:
            try:
                recent.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    recent = recent[-6:]
    stats = (
        '<div class="statrow">'
        f'<div class="stat"><b>{state.get("unread_customer_threads", 0)}</b>'
        '<span>unread customer threads</span></div>'
        f'<div class="stat"><b>{state.get("replies_sent_today", 0)}</b>'
        '<span>auto-replies today</span></div>'
        f'<div class="stat"><b>{state.get("optouts_total", 0)}</b>'
        '<span>opt-outs honored</span></div>'
        f'<div class="stat"><b>{len(escs)}</b><span>need your reply</span></div>'
        '</div>')
    esc_html = ""
    if escs:
        rows = ""
        for i in escs:
            title = i.get("title", i.get("code", ""))
            detail = i.get("detail") or ""
            money_btn = (
                ' <a class="btn ghost" href="https://app.gumroad.com/" target="_blank" '
                'rel="noopener">Open Gumroad dashboard</a>'
                if "refund" in (title + " " + detail).lower() else "")
            rows += (
                '<div class="alert"><span class="pill blocked">needs human</span> '
                '<b>' + esc(title) + '</b>'
                + ('<br><span class="muted">' + esc(detail[:220]) + '</span>' if detail else "")
                + '<br><button class="btn" onclick="approveCode(\'' + esc(i.get("code", "")) +
                '\', this, \'Handled ✓\')">Mark handled</button>' + money_btn + '</div>')
        esc_html = ('<div class="card warn"><h3>Waiting on you</h3>' + rows + '</div>')
    threat_html = ""
    threats = state.get("threat_fyi", []) or []
    if threats:
        trows = "".join(
            '<li><b>' + esc((t.get("from") or "?")[:60]) + '</b> — ' +
            esc((t.get("subject") or "")[:70]) +
            ' <span class="muted">' + esc(t.get("at", ""))[:16] + '</span></li>'
            for t in reversed(threats))
        threat_html = (
            '<div class="card"><h3>Quiet FYI — threats received</h3>'
            '<p class="muted">No reply sent, sender permanently opted out. '
            'No action needed unless you choose otherwise.</p>'
            '<ul>' + trows + '</ul></div>')
    hist = ""
    if recent:
        items = "".join(
            '<li><b>' + esc(r.get("action", "?")) + '</b> — ' +
            esc((r.get("subject") or r.get("to") or "")[:70]) +
            ' <span class="muted">' + esc(r.get("at", ""))[:16] + '</span></li>'
            for r in reversed(recent))
        hist = ('<details class="fold"><summary>Recent inbox activity (' + str(len(recent)) +
                ')</summary><ul>' + items + '</ul></details>')
    last = state.get("last_run", "")
    return (stats + esc_html + threat_html + hist +
            ('<p class="muted">Inbox watcher checks the business Gmail every ~10 minutes. '
             'Genuine questions get an automatic reply. Threats are never answered and never '
             'escalated — they are logged above as quiet FYI only. Money, refund, or '
             'complex threads come here instead. Last check: ' + esc(last.replace("T", " ").replace("Z", "Z")) +
             '.</p>' if last else '<p class="muted">Inbox watcher has not run yet.</p>'))


def drafts_section():
    try:
        resolved = json.loads(read_file(os.path.join(HF, "outreach/drafts-resolved.json")) or "{}")
    except json.JSONDecodeError:
        resolved = {}
    groups = []
    for fn in ("2026-09-29.md", "2026-09-30.md"):
        p = os.path.join(HF, "drafts", fn)
        if os.path.exists(p):
            n = read_file(p).count("## ")
            groups.append(("content-" + fn[:-3], "Content drafts · " + fn[:-3],
                           str(n) + " pieces", "Each piece becomes an article on your site."))
    ld = glob.glob(os.path.join(HF, "distribution/listing-drafts/**/*.md"), recursive=True)
    if ld:
        groups.append(("listings", "Marketplace listing drafts", str(len(ld)) + " drafts",
                       "Staged as ready for your manual paste — marketplace accounts still need you."))
    if os.path.exists(os.path.join(HF, "catalog/tag-drafts-2026-09-30.md")):
        groups.append(("tags", "Gumroad tag sweep", "60 products",
                       "Applies the drafted tags to your live products."))
    fq = glob.glob(os.path.join(HF, "faq-drafts/*"))
    if fq:
        groups.append(("faq", "FAQ drafts", str(len(fq)) + " files",
                       "Published as articles on your site."))
    open_groups = [g for g in groups
                   if resolved.get("DA-" + g[0]) not in ("done", "forgotten")
                   and resolved.get("DD-" + g[0]) != "forgotten"]
    if not open_groups:
        return ("<p class='muted'>Nothing waiting — every draft the bots produced has been "
                "triaged. New drafts appear here automatically.</p>")
    cards = []
    for g, label, count, meaning in open_groups:
        cards.append(
            '<div class="card"><h3>' + esc(label) + '</h3>'
            '<p><b>' + esc(count) + '</b> · ' + esc(meaning) + '</p>'
            '<button class="btn" onclick="approveCode(\'DA-' + esc(g) + '\', this, \'Working ✓\')">Put to work</button> '
            '<button class="btn" style="background:#3a352d;color:var(--muted)" '
            'onclick="approveCode(\'DD-' + esc(g) + '\', this, \'Forgotten\')">Forget</button></div>'
        )
    return "".join(cards)


def directory_section():
    js = (
        '<div id="dirsub"><p class="muted">Loading submissions…</p></div>\n'
        '<script>\n'
        'const escH = s => String(s == null ? "" : s).replace(/[&<>"\\\']/g, c => '
        '({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","\\\'":"&#39;"}[c]));\n'
        'async function reviewDir(id, st, btn) {\n'
        '  btn.disabled = true; btn.textContent = "Working…";\n'
        '  try {\n'
        '    const r = await fetch(WURL + "/directory-review", {method: "POST",\n'
        '      headers: {"Content-Type": "application/json"},\n'
        '      body: JSON.stringify({id: id, status: st, key: WKEY})});\n'
        '    const d = await r.json();\n'
        '    if (d.ok) { btn.textContent = st === "approved" ? "Approved ✓" : "Rejected ✓"; loadDir(); return; }\n'
        '  } catch (e) {}\n'
        '  btn.disabled = false; btn.textContent = "Retry";\n'
        '}\n'
        'async function loadDir() {\n'
        '  const el = document.getElementById("dirsub");\n'
        '  if (!WURL || !WKEY) { el.innerHTML = "<p class=\'muted\'>Backend not connected.</p>"; return; }\n'
        '  try {\n'
        '    const r = await fetch(WURL + "/directory-submissions?key=" + encodeURIComponent(WKEY), {cache: "no-store"});\n'
        '    const subs = await r.json();\n'
        '    const pend = subs.filter(s => s.status === "pending");\n'
        '    const decided = subs.filter(s => s.status !== "pending");\n'
        '    const live = subs.filter(s => s.status === "approved").length;\n'
        '    const pEl = document.getElementById("dir-pend"); if (pEl) pEl.textContent = pend.length;\n'
        '    const lEl = document.getElementById("dir-live"); if (lEl) lEl.textContent = live;\n'
        '    if (!subs.length) { el.innerHTML = "<p class=\'muted\'>No submissions yet — builders use the form at yoursite/directory/submit/.</p>"; return; }\n'
        '    const row = s => `<tr><td><b>${escH(s.pack_name)}</b> by ${escH(s.author)}<br>` +\n'
        '      `<span class=\'muted\'>${escH(s.description || "").slice(0, 180)}${(s.description || "").length > 180 ? "…" : ""}</span><br>` +\n'
        '      `<span class=\'mono\'>${escH(s.pack_url || "")}${s.manifest_url ? " · <a href=\'" + escH(s.manifest_url) + "\' target=\'_blank\' rel=\'noopener\'>manifest</a>" : ""}</span><br>` +\n'
        '      `<span class=\'muted\'>${escH(s.author_email || "")} · ${escH(s.license || "")} · ${escH((s.submitted_at || "").slice(0, 10))}</span></td>` +\n'
        '      `<td><button class="btn" onclick="reviewDir(\\\'${escH(s.id)}\\\', \\\'approved\\\', this)">Approve</button> ` +\n'
        '      `<button class="btn" style="background:#3a352d;color:var(--muted)" onclick="reviewDir(\\\'${escH(s.id)}\\\', \\\'rejected\\\', this)">Reject</button></td></tr>`;\n'
        '    let html = "";\n'
        '    if (pend.length) {\n'
        '      html += "<h3>Pending review (" + pend.length + ")</h3>" +\n'
        '        "<div class=\'table-wrap\'><table><tr><th>Submission</th><th></th></tr>" +\n'
        '        pend.map(row).join("") + "</table></div>";\n'
        '    }\n'
        '    if (decided.length) {\n'
        '      html += "<details class=\'fold\'><summary>Decided (" + decided.length + ")</summary>" +\n'
        '        "<div class=\'table-wrap\'><table><tr><th>Pack</th><th>Status</th></tr>" +\n'
        '        decided.map(s => `<tr><td><b>${escH(s.pack_name)}</b> by ${escH(s.author)}</td>` +\n'
        '          `<td><span class=\'pill ${s.status === "approved" ? "ok" : "blocked"}\'>${escH(s.status)}</span></td></tr>`).join("") +\n'
        '        "</table></div></details>";\n'
        '    }\n'
        '    el.innerHTML = html;\n'
        '  } catch (e) {\n'
        '    el.innerHTML = "<p class=\'muted\'>Submission service unreachable — try again shortly.</p>";\n'
        '  }\n'
        '}\n'
        '// WURL/WKEY are declared in the late backend_js block (end of body),\n'
        '// so the first load must wait until they exist — DOMContentLoaded\n'
        '// fires after all parser-inserted scripts have run.\n'
        'document.addEventListener("DOMContentLoaded", loadDir);\n'
        '</script>'
    )
    return (
        '<div class="statrow">'
        '<div class="stat"><b id="dir-pend">…</b><span>pending review</span></div>'
        '<div class="stat"><b id="dir-live">…</b><span>live in directory</span></div>'
        '</div>' + js
    )


def tiktok_section():
    entries = []
    for line in read_file(os.path.join(HF, "tiktok/log.jsonl")).splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    staged = [e for e in entries if e.get("status") == "staged"]
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    recent = [e for e in staged if e.get("date", "") >= week_ago]
    try:
        ch = json.loads(read_file(os.path.join(HF, "outreach/channels.json")) or "{}")
        tt = ch.get("tiktok", {})
    except json.JSONDecodeError:
        tt = {}
    uname = tt.get("username") or "—"
    cards = (
        '<div class="statrow">'
        f'<div class="stat"><b>{len(staged)}</b><span>videos staged</span></div>'
        f'<div class="stat"><b>{len(recent)}</b><span>staged this week</span></div>'
        f'<div class="stat"><b>@{esc(uname)}</b><span>TikTok account</span></div>'
        '</div>'
    )
    if not staged:
        body = "<p class='muted'>No videos yet — the TikTok studio bot makes one every morning.</p>"
    else:
        body = "".join(
            "<div class='card'><h3>" + esc(e.get("brand", "?")) +
            " <span class='muted'>· " + esc(e.get("date", "")) + "</span></h3>"
            "<p class='mono'>" + esc(e.get("video", "")) + "</p>"
            "<p>" + esc(e.get("caption", "")) + "</p>"
            "<p class='muted'>Angle: " + esc(e.get("angle", "")) + "</p></div>"
            for e in reversed(staged[-10:])
        )
    return (
        cards + body +
        "<p class='muted'>Account <b>@ghostcorpnetai</b> is live (created on your phone). "
        "Bots make the videos; you post from the TikTok app — TikTok blocks bot logins. "
        "Each video has a matching .txt file in the staged folder with the exact "
        "caption, hashtags, and script to copy-paste.</p>"
    )


def site_section():
    health = read_file(os.path.join(HF, "health.log")).strip().splitlines()
    last = esc(health[-1]) if health else "no checks logged yet"
    return f'<p><b>Last health check:</b> <span class="mono">{last}</span></p>'


def fleet_section():
    calls = read_file(os.path.join(HF, "open-models/calls.log")).strip().splitlines()
    last_ai = esc(calls[-1][:120]) if calls else "no AI calls logged yet"
    rows = []
    for n, s, sig in FLEET:
        ts = newest_mtime(sig)
        cls, label = health_of(s, ts)
        rows.append(
            f"<tr><td><span class='health'><span class='dot {cls}'></span>{esc(n)}</span></td>"
            f"<td><span class='sched'>{esc(s)}</span></td>"
            f"<td class='mono'>{esc(fmt_time(ts))}</td>"
            f"<td><span class='pill {cls}'>{label}</span></td></tr>")
    bots = "".join(rows)
    team_cards = "".join(
        f"<div class='team' style='border:1px solid var(--line);border-radius:10px;"
        f"padding:12px 14px;margin:0 0 10px'>"
        f"<h4 style='margin:0 0 2px'>{esc(n)}</h4>"
        f"<p class='muted' style='margin:0 0 6px'>{esc(t)}</p>"
        f"<p style='margin:0;font-size:.92rem'>{esc(m)}</p></div>"
        for n, t, m in TEAMS)
    teams_html = (
        "<div class='card'><h3>Your teams</h3>"
        "<p class='muted'>Four teams, one owner: you. They run their loops, ship their "
        "output, and report honestly. Sentience commands all four.</p>"
        f"{team_cards}</div>")
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
        f'{teams_html}'
        '<div class="card"><h3>Talk to your bots</h3>'
        "<p>Open the <b>Talk to the bots</b> chat in your Muse app and tell the "
        "fleet what to do in plain words — e.g. “run the lead scout now”, "
        "“pause the pricing bot”, “what did the SEO writer publish this week?”. "
        "Muse coordinates them for you; nothing goes public without your say-so.</p></div>"
        f'<p><b>Last fleet AI activity:</b> <span class="mono">{last_ai}</span></p>'
        f'<div class="table-wrap"><table><tr><th>Bot</th><th>Schedule</th><th>Last output</th><th>Status</th></tr>{bots}</table></div>'
        '<p class="legend"><span class="dot ok"></span>active — produced within its schedule window &nbsp;'
        '<span class="dot warn"></span>quiet — overdue once &nbsp;'
        '<span class="dot stale"></span>stale — well overdue &nbsp;'
        '<span class="dot never"></span>no data — never produced output</p>'
        f"<h3>Recently shipped site improvements</h3><ul>{props or '<li>—</li>'}</ul>"
    )


def build():
    now = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    products = gumroad_all_products() or []
    queue = get_queue()
    kpi = kpi_strip(products, queue)
    alerts = alerts_section(queue, products)
    revenue = revenue_section(products)
    feed = activity_feed()
    tabs = [
        ("taps", "\u26a1 Action Center"), ("overview", "Overview"), ("approvals", "Approvals"), ("outreach", "Outreach"),
        ("products", "Products"), ("drafts", "Drafts"), ("fleet", "Fleet"),
        ("extras", "Extras"),
    ]
    tabbtns = "".join(
        f'<button class="tabbtn" data-tab="{t}" onclick="switchTab(\'{t}\')">{l}</button>'
        for t, l in tabs)
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Admin Dashboard — ghostcorpnet</title>
<!-- GENERATED by build-admin.py — do not hand-edit. -->
<style>
  :root{{--bg:#101014; --panel:#17181d; --panel2:#1e2027; --line:#2a2c35;
        --text:#ece7db; --muted:#98908a; --accent:#e07a5f; --accent-deep:#a8502f;
        --ok:#7fbf7f; --warn:#e0a75f; --bad:#e08a7f; --radius:14px;}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  html{{scroll-behavior:smooth}}
  body{{background:radial-gradient(1200px 400px at 50% -80px,#1d1a18 0%,var(--bg) 60%),var(--bg);
       color:var(--text);
       font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
       line-height:1.6;-webkit-text-size-adjust:100%}}
  header.top{{position:sticky;top:0;z-index:100;background:rgba(16,16,20,.94);
       backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}
  header.top .inner{{max-width:1120px;margin:0 auto;padding:12px 24px;
       display:flex;align-items:center;gap:14px}}
  .brand{{display:flex;align-items:center;gap:10px;font-weight:800;font-size:1.05rem;
       letter-spacing:-.01em;color:var(--text);text-decoration:none;flex:0 0 auto}}
  .admin-tag{{font-size:.66rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
       color:#0f0e0c;background:linear-gradient(135deg,var(--accent),#f0a184);
       border-radius:999px;padding:4px 11px}}
  .tabs{{display:flex;gap:4px;margin-left:auto;overflow-x:auto;scrollbar-width:none}}
  .tabs::-webkit-scrollbar{{display:none}}
  .tabbtn{{background:transparent;border:1px solid transparent;border-radius:9px;
       color:var(--muted);font-size:.85rem;font-weight:600;padding:8px 13px;cursor:pointer;
       white-space:nowrap;font-family:inherit}}
  .tabbtn:hover{{color:var(--accent);background:var(--panel)}}
  .tabbtn.on{{color:var(--accent);background:var(--panel);border-color:var(--line)}}
  .wrap{{max-width:1120px;margin:0 auto;padding:0 24px 90px}}
  .hero{{padding:40px 0 4px}}
  .hero h1{{font-size:clamp(1.8rem,4.5vw,2.5rem);font-weight:800;letter-spacing:-.025em;
       background:linear-gradient(120deg,#fff 30%,var(--accent) 100%);
       -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
  .gen{{color:var(--muted);font-size:.86rem;margin-top:8px}}
  .tabpane{{display:none;padding-top:26px}}
  .tabpane.on{{display:block;animation:fade .25s ease}}
  @keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
  .sec-title{{margin:26px 0 4px}}
  .sec-title h2{{font-size:1.35rem;font-weight:750;letter-spacing:-.015em}}
  .eyebrow{{font-size:.68rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase;
       color:var(--accent);margin-bottom:5px}}
  .lede{{color:var(--muted);font-size:.92rem;margin:4px 0 12px;max-width:740px}}
  .kpirow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0 6px}}
  .kpi{{background:linear-gradient(180deg,var(--panel2),var(--panel));
       border:1px solid var(--line);border-radius:var(--radius);
       padding:18px 14px 15px;text-align:center;position:relative;overflow:hidden;
       box-shadow:0 2px 10px rgba(0,0,0,.25)}}
  .kpi::before{{content:"";position:absolute;top:0;left:0;right:0;height:3px;
       background:linear-gradient(90deg,transparent,var(--line),transparent)}}
  .kpi.accent::before{{background:linear-gradient(90deg,transparent,var(--accent),transparent)}}
  .kpi.warn .kpi-v{{color:var(--warn)}} .kpi.bad .kpi-v{{color:var(--bad)}}
  .kpi-v{{font-size:1.85rem;font-weight:800;letter-spacing:-.02em;color:var(--accent);line-height:1.3}}
  .kpi-small{{font-size:.95rem;font-weight:700}}
  .kpi-cap{{font-size:1rem;color:var(--muted);font-weight:600}}
  .kpi-l{{color:var(--text);font-size:.82rem;font-weight:650;margin-top:2px}}
  .kpi-s{{color:var(--muted);font-size:.74rem}}
  .card{{background:linear-gradient(180deg,var(--panel2),var(--panel));
       border:1px solid var(--line);border-radius:var(--radius);
       padding:22px 24px;margin:14px 0;box-shadow:0 2px 12px rgba(0,0,0,.22)}}
  .card.warn{{border-left:4px solid var(--warn)}}
  .card.ok-card{{border-left:4px solid var(--ok)}}
  .card h3{{margin:0 0 10px;font-size:1.08rem;font-weight:750;letter-spacing:-.01em}}
  .card p{{color:var(--muted);font-size:.92rem}}
  .card b{{color:var(--text)}}
  .alert{{padding:11px 0;border-bottom:1px solid var(--line)}}
  .alert:last-child{{border-bottom:0;padding-bottom:0}}
  .alert b{{display:block;margin:5px 0 2px}}
  .statrow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:14px 0}}
  .stat{{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
       padding:18px 12px;text-align:center}}
  .stat b{{display:block;font-size:1.7rem;color:var(--accent);line-height:1.25}}
  .stat span{{color:var(--muted);font-size:.82rem}}
  .table-wrap{{overflow-x:auto;margin:14px 0;border:1px solid var(--line);
       border-radius:var(--radius);background:var(--panel)}}
  .table-wrap table{{margin:0}}
  table{{width:100%;border-collapse:collapse;font-size:.88rem;margin:14px 0;min-width:600px}}
  th,td{{text-align:left;padding:10px 14px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{color:var(--muted);font-size:.7rem;font-weight:700;text-transform:uppercase;
       letter-spacing:.09em;background:var(--panel2)}}
  tr:nth-child(even) td{{background:rgba(255,255,255,.02)}}
  tr:hover td{{background:rgba(224,122,95,.05)}}
  .table-wrap tr:last-child td,.table-wrap tr:last-child th{{border-bottom:0}}
  table a{{color:var(--accent)}}
  .tapcard{{background:linear-gradient(180deg,var(--panel2),var(--panel));
       border:1px solid var(--line);border-radius:var(--radius);
       padding:16px 18px;margin:12px 0}}
  .tapcard p{{color:var(--muted);font-size:.9rem;margin:6px 0}}
  .tapcard .taphow{{color:var(--text);font-size:.88rem;border-left:3px solid var(--accent);
       padding-left:10px;margin:8px 0}}
  .tapcard .btn{{margin-top:8px}}
  .mono{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;color:var(--muted)}}
  .muted{{color:var(--muted);font-size:.88rem}}
  .badge{{display:inline-block;font-size:.68rem;font-weight:700;letter-spacing:.06em;
    padding:2px 8px;border-radius:999px;margin-left:8px;vertical-align:middle}}
  .badge.code{{background:#1e3a5f;color:#7cc4ff;border:1px solid #2c5f8a}}
  .legend{{color:var(--muted);font-size:.82rem;margin:8px 2px 0;line-height:2}}
  details.fold{{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
       padding:15px 19px;margin:14px 0}}
  details.fold summary{{cursor:pointer;font-weight:650}}
  details.fold ol{{margin:10px 0 0 20px;color:var(--muted);font-size:.9rem}}
  details.fold li{{margin:3px 0}}
  ul{{margin:8px 0 8px 20px;color:var(--muted);font-size:.92rem}}
  ul.feed{{list-style:none;margin:10px 0 0;padding:0;font-size:.86rem}}
  ul.feed li{{padding:9px 0;border-bottom:1px solid var(--line)}}
  ul.feed li:last-child{{border-bottom:0}}
  .src{{display:inline-block;font-size:.68rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;
       color:var(--accent);border:1px solid var(--accent-deep);border-radius:6px;padding:2px 8px;margin-right:8px}}
  .health{{display:inline-flex;align-items:center;font-size:.92rem;color:var(--text);white-space:nowrap}}
  .dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:9px;flex:0 0 auto}}
  .dot.ok{{background:var(--ok);box-shadow:0 0 7px rgba(127,191,127,.8)}}
  .dot.warn{{background:var(--warn);box-shadow:0 0 7px rgba(224,167,95,.6)}}
  .dot.stale{{background:var(--bad)}} .dot.never{{background:#5a544a}}
  .sched{{display:inline-block;font-size:.78rem;color:var(--muted);border:1px solid var(--line);
       border-radius:6px;padding:3px 9px;white-space:nowrap}}
  .pill{{display:inline-block;padding:3px 11px;border-radius:20px;font-size:.74rem;font-weight:700;
        background:#2c2e37;color:var(--muted);white-space:nowrap}}
  .pill.ok{{background:#243324;color:var(--ok)}}
  .pill.warn{{background:#3a2f1e;color:var(--warn)}}
  .pill.stale{{background:#3a2320;color:var(--bad)}}
  .pill.never{{background:#26241f;color:var(--muted)}}
  .pill.blocked{{background:#3a2320;color:#e08a7f}}
  .btn{{display:inline-block;padding:9px 20px;border:0;border-radius:9px;background:linear-gradient(135deg,var(--accent),#ef9278);
       color:#161210;font-weight:750;font-size:.86rem;cursor:pointer;white-space:nowrap;font-family:inherit;
       box-shadow:0 2px 8px rgba(224,122,95,.3)}}
  .btn:hover{{filter:brightness(1.08)}}
  .btn:disabled{{opacity:.6;cursor:default}}
  .ms-track{{margin:16px 0 6px}}
  .ms{{display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)}}
  .ms:last-child{{border-bottom:0}}
  .ms-dot{{font-size:1.1rem;width:26px;text-align:center;color:var(--muted)}}
  .ms.hit .ms-dot{{color:var(--ok)}}
  .ms.cur .ms-dot{{color:var(--accent)}}
  .ms.hit .ms-l{{color:var(--text)}}
  .ms-l{{flex:1;font-size:.92rem;color:var(--muted)}}
  .ms.cur .ms-l{{color:var(--text);font-weight:650}}
  .ms-a{{font-size:.85rem;color:var(--muted);font-weight:700}}
  .bar{{height:10px;background:#0c0c10;border:1px solid var(--line);border-radius:999px;
       overflow:hidden;margin:14px 0 8px}}
  .bar-fill{{height:100%;background:linear-gradient(90deg,var(--accent-deep),var(--accent));
       border-radius:999px;transition:width .6s ease}}
  .foot{{margin-top:48px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:18px}}
  @media (max-width:680px){{
    header.top .inner{{padding:10px 14px;gap:8px}}
    .brand{{font-size:.95rem}}
    .tabbtn{{padding:7px 10px;font-size:.78rem}}
    .wrap{{padding:0 14px 64px}}
    .hero{{padding-top:28px}}
    .kpirow{{grid-template-columns:repeat(2,1fr);gap:10px}}
    .kpi{{padding:14px 8px 12px}}
    .kpi-v{{font-size:1.5rem}}
    .statrow{{grid-template-columns:repeat(2,1fr);gap:10px}}
    .card{{padding:17px 18px}}
    table{{min-width:520px}}
  }}
</style>
</head>
<body>
<header class="top">
  <div class="inner">
    <a class="brand" href="https://koalstingkdelaney-gif.github.io/kestrelattice/">
      <svg width="22" height="22" viewBox="0 0 26 26" fill="none" aria-hidden="true"><circle cx="5" cy="6" r="2.4" fill="#e07a5f"/><circle cx="21" cy="6" r="2.4" fill="#e07a5f"/><circle cx="13" cy="13" r="2.4" fill="#e07a5f"/><circle cx="5" cy="20" r="2.4" fill="#e07a5f"/><circle cx="21" cy="20" r="2.4" fill="#e07a5f"/><path d="M6.6 7.4L11.2 11.8M19.4 7.4L14.8 11.8M6.6 18.6L11.2 14.2M19.4 18.6L14.8 14.2" stroke="#e07a5f" stroke-width="1.4"/></svg>
      ghostcorpnet <span class="admin-tag">admin</span>
    </a>
    <nav class="tabs" role="tablist">{tabbtns}</nav>
  </div>
</header>
<div class="wrap">
  <div class="hero">
    <h1>Command center</h1>
    <p class="gen">Generated {esc(now)} · every number below is live data, refreshed automatically</p>
  </div>
  {backend_js()}

  <div class="tabpane" id="tab-overview">
    <div class="sec-title"><div class="eyebrow">At a glance</div><h2>Overview</h2></div>
    {kpi}
    {alerts}
    {revenue}
    {feed}
  </div>

  <div class="tabpane" id="tab-approvals">
    <div class="sec-title"><div class="eyebrow">Your call</div><h2>Needs your approval</h2>
    <p class="lede">One tap approves — the fleet picks it up within ~15 minutes. Routine site development auto-approves by policy; only money, price, or messaging items wait here.</p></div>
    {approvals_section()}
  </div>

  <div class="tabpane" id="tab-outreach">
    <div class="sec-title"><div class="eyebrow">Sales</div><h2>Outreach</h2>
    <p class="lede">Bots find leads and draft pitches around the clock. Read each pitch and tap <b>Send pitch</b> — it goes out from your business Gmail within ~15 minutes. Cap: 20/day.</p></div>
    {outreach_section()}
    <div class="sec-title"><div class="eyebrow">Customers</div><h2>Inbox replies</h2>
    <p class="lede">When customers write back, the bots answer genuine questions on their own. Money, refund, legal, or complex threads wait here for your personal reply.</p></div>
    {inbox_section(queue)}
  </div>

  <div class="tabpane" id="tab-products">
    <div class="sec-title"><div class="eyebrow">Storefront</div><h2>Products</h2>
    <p class="lede">Everything live on Gumroad right now, with per-product revenue.</p></div>
    {money_section(products)}
    {site_section()}
  </div>

  <div class="tabpane" id="tab-drafts">
    <div class="sec-title"><div class="eyebrow">Triage</div><h2>Drafts</h2>
    <p class="lede">Everything the bots drafted. <b>Put to work</b> moves a group into the pipeline; <b>Forget</b> archives it.</p></div>
    {drafts_section()}
    <div class="sec-title"><div class="eyebrow">In progress</div><h2>Review pipeline</h2></div>
    {pipeline_section()}
  </div>

  <div class="tabpane" id="tab-fleet">
    <div class="sec-title"><div class="eyebrow">Bots</div><h2>Fleet</h2>
    <p class="lede">Health is judged against each bot's schedule and when it last produced output.</p></div>
    {fleet_section()}
  </div>

  <div class="tabpane" id="tab-extras">
    <div class="sec-title"><div class="eyebrow">Platform</div><h2>Directory submissions</h2>
    <p class="lede">Third-party packs submitted via the public form. Listing is free — approvals never move money.</p></div>
    {directory_section()}
    <div class="sec-title"><div class="eyebrow">Video</div><h2>TikTok studio</h2>
    <p class="lede">One video a day, staged and ready. Copy the caption from its .txt file and post from your phone.</p></div>
    {tiktok_section()}
    <div class="sec-title"><div class="eyebrow">Visitors</div><h2>Traffic</h2></div>
    <div class="card"><h3>Google Analytics needs a one-time setup</h3>
    <p>Live visitor numbers can't be pulled with just a key — Google requires an
    OAuth client you create in Google Cloud Console (about 10 minutes at a computer).
    Say the word and I'll walk you through it; after that, traffic charts appear here.</p></div>
  </div>

  <div class="foot">Private: this panel is served only from your key-gated worker URL — it is not
  on the public site and is never indexed. Bookmark your private link and don't share it.</div>
</div>
</body>
</html>"""
    with open(OUT, "w") as f:
        f.write(body)
    print("wrote", OUT)
    upload_private(body)


def upload_private(html):
    """Publish the dashboard to the key-gated worker route (not the public site)."""
    import tempfile
    try:
        sec = json.loads(read_file(os.path.join(HOME, "workspace/kestrelattice/worker/.secrets.json")))
        wurl, skey = sec.get("worker_url", ""), sec.get("server_key", "")
        if not wurl or not skey:
            print("upload skipped: worker secrets missing")
            return
        # Defense in depth: the write key must NEVER be embedded in the page.
        # Compare-only (never printed/logged); refuse to publish on any leak.
        wkey = sec.get("write_key", "")
        if wkey and wkey in html:
            print("private upload BLOCKED: write key value found in generated "
                  "HTML — refusing to publish. Fix the generator first.")
            return
        # NOTE: Cloudflare WAF blocks python urllib — use curl.
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(html)
            tmp = f.name
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", "-A", UA, "-H", "x-server-key: " + skey,
             "-H", "Content-Type: text/html; charset=utf-8",
             "--data-binary", "@" + tmp, wurl.rstrip("/") + "/admin-upload"],
            capture_output=True, text=True, timeout=120)
        os.unlink(tmp)
        print("private upload:", r.stdout.strip()[:120] or r.stderr.strip()[:120])
    except Exception as e:
        print("private upload failed:", e)


if __name__ == "__main__":
    build()
