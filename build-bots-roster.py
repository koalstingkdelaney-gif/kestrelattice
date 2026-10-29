#!/usr/bin/env python3
"""Build bots/fleet.json — the public roster of ghostcorpnet WEBSITE bots.

Sources (website/business fleet ONLY):
  - cron definitions under the kestrelattice-autonomous-growth goal
  - cron definitions under the leave-the-9-to-5 goal (if present)
  - hive role files (goal hive/roles/, or hidden_files/hive/roles/)
  - the Customer Swarm roster (hidden_files/growth/customer-swarm/roster.json):
    60 named hunter bots whose only job is getting customers

Excluded: game/sandbox/court/rogue bots, video (Shorts/TikTok) bots,
wholesaling bots, one-off runonce jobs, and disabled jobs.
Job lines are generic duty descriptions, scrubbed of emails, URLs,
paths, and dollar amounts.

Output: bots/fleet.json — an object {"generated_at", "stats", "bots"}.
"bots" is [{name, job, schedule}]. "stats" carries the owner's money
totals for the page's money strip, computed ONLY from verified sales
records (the approval watcher's sales ledger under hidden_files/money/,
cross-checked against the Gumroad API when reachable): paid totals,
paid order counts, today's paid total, free-download count, and an
"as_of" timestamp. Aggregates only — never buyer data. The stats live
inside fleet.json on purpose: the daily bots-roster-refresh cron commits
fleet.json, so the money strip stays current on the same ride.
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HOME = os.path.expanduser("~")
GOAL = os.path.join(HOME, "workspace/goals/kestrelattice-autonomous-growth")
CRON_DIRS = [
    os.path.join(GOAL, "crons"),
    os.path.join(HOME, "workspace/goals/leave-the-9-to-5-with-kestrelattice/crons"),
]
ROLE_DIRS = [
    os.path.join(GOAL, "hive/roles"),
    os.path.join(GOAL, "hidden_files/hive/roles"),
]
OUT = os.path.join(HOME, "workspace/kestrelattice/bots/fleet.json")
MONEY_DIR = os.path.join(GOAL, "hidden_files/money")
GUMROAD_API = os.path.join(
    HOME, "workspace/custom-connectors/custom.legacy-gumroad/bin/gumroad-api")
SWARM_ROSTER = os.path.join(
    GOAL, "hidden_files/growth/customer-swarm/roster.json")

# Substrings (lowercase, matched against the job/role id) that mean
# "not a website bot" for this roster.
EXCLUDE_SUBSTR = [
    "rotwood", "sandbox", "court", "ultron", "rogue",
    "shorts", "youtube", "tiktok", "wholesaling",
    "video",  # hive video roles (video-scripter, video-caption-writer)
]
EXCLUDE_IDS = {
    "sentience-sidechat-bridge", "kestrelattice-sentience-chat",
    "kestrelattice-sentience-reflect", "transcript-writer",
    "thumbnail-maker",
}

# Clean one-line duty summaries for ids whose titles are cryptic.
JOB_OVERRIDES = {
    "kestrelattice-approval-watcher": "Executes approved work — publishes products and applies site updates",
    "kestrelattice-outreach-sync": "Keeps the customer outreach queue in sync and deduplicated",
    "kestrelattice-mesh-sender": "Delivers queued fleet messages and retries failed sends",
    "kestrelattice-taps-sync": "Syncs the owner's one-tap approvals to the fleet",
    "kestrelattice-worker-reconcile": "Reconciles the fleet's work queues so nothing is lost or doubled",
    "kestrelattice-worker-recovery": "Detects stalled fleet workers and brings them back",
    "kestrelattice-dashboard-refresh": "Rebuilds the owner's admin dashboard so it is always current",
    "kestrelattice-fleet-sync": "Keeps every bot's schedule and roster in sync",
    "kestrelattice-self-repair": "Watches the fleet's own machinery and repairs breakage",
    "kestrelattice-self-optimize": "Tunes the fleet's own settings to work better",
    "kestrelattice-self-review": "Reviews the fleet's recent work and flags problems",
    "kestrelattice-model-refresh": "Keeps the fleet's AI models current and working",
    "kestrelattice-provider-scout": "Scouts new free AI providers for the fleet",
    "kestrelattice-ui-scout": "Scouts the website's interface for improvements",
    "kestrelattice-watchdog": "Watches the website and fleet for problems around the clock",
    "watchdog-security": "Watches the site and accounts for security problems",
    "kestrelattice-google-geeks": "Research crew — hunts leads, competitors, and answers online",
    "hive-brain": "Plans the hive workers' tasks and assigns the work",
    "kestrelattice-inbox-watch": "Watches the business inbox and handles routine replies",
    "kestrelattice-mesh-sender ": "Delivers queued fleet messages and retries failed sends",
    "universe-treasury": "Tracks the business's catalog of digital assets",
    "agency-outreach": "Finds local businesses and sends agency pitches",
    "agency-replies": "Handles replies to agency pitches and books intake",
    "agency-fiverr-inbox": "Checks the agency's Fiverr inbox for new orders",
    "revenue-flow": "Follows up free downloads and turns them toward paid products",
    "kestrelattice-money-pulse": "Weekly sales check — what sold and one thing to fix",
    "kestrelattice-sentience-operator": "Fleet captain — coordinates the other bots' work",
}

DOW3 = {"Mon": "Mon", "Tue": "Tue", "Wed": "Wed", "Thu": "Thu",
        "Fri": "Fri", "Sat": "Sat", "Sun": "Sun"}


def scrub(text):
    text = re.sub(r"(?i)\bkoalstin'?s\b", "the owner's", text)  # owner's name (possessive)
    text = re.sub(r"(?i)\bkoalstin\b|\bdelaney\b", "ghostcorpnet", text)  # owner's name
    text = re.sub(r"\S+@\S+", "", text)                    # emails
    text = re.sub(r"https?://\S+", "", text)               # urls
    text = re.sub(r"(~/|/home/)\S*", "", text)             # paths
    text = re.sub(r"\$[\d][\d,\.]*", "", text)             # dollar amounts
    text = re.sub(r"`[^`]*`", "", text)                    # code spans
    text = re.sub(r"\s+", " ", text).strip(" -—–·,")
    return text


def fmt_time(t):
    m = re.match(r"(\d{1,2}):(\d{2})", t or "")
    if not m:
        return ""
    hh, mm = int(m.group(1)), int(m.group(2))
    ap = "AM" if hh < 12 else "PM"
    hh = hh % 12 or 12
    return "%d:%02d %s" % (hh, mm, ap)


def schedule_str(fm, fname):
    kind = fm.get("kind", "")
    t = fmt_time(fm.get("time", ""))
    if kind == "interval":
        every = fm.get("every", "")
        if every:
            mm = re.match(r"(\d+)m$", every)
            hh = re.match(r"(\d+)h$", every)
            if mm:
                return "Every %s min" % mm.group(1)
            if hh:
                return "Every %s hr" % hh.group(1)
            return "Every %s" % every
        m = re.search(r"interval@(\S+?)\.md$", fname)
        return "Every %s" % m.group(1) if m else "Repeating"
    if kind == "daily":
        return "Daily · %s" % t if t else "Daily"
    if kind == "weekly":
        dows = fm.get("dow", "")
        days = ", ".join(DOW3.get(d, d) for d in re.findall(r"[A-Z][a-z]{2}", dows))
        return ("Weekly · %s %s" % (days, t)).strip()
    if kind == "monthly":
        return "Monthly · %s" % t if t else "Monthly"
    return kind.capitalize() if kind else ""


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw, body = text[3:end], text[end + 4:]
    fm = {}
    in_sched = False
    for line in fm_raw.splitlines():
        if re.match(r"^schedule:\s*$", line):
            in_sched = True
            continue
        if in_sched and line.startswith("  ") and ":" in line:
            k, v = line.strip().split(":", 1)
            fm[k.strip()] = v.strip()
            continue
        in_sched = False
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, body


def pretty_name(raw_id):
    name = raw_id
    for pfx in ("kestrelattice-",):
        if name.startswith(pfx):
            name = name[len(pfx):]
    return name.replace("-", " ").title()


def job_from_title(title, raw_id):
    if raw_id in JOB_OVERRIDES:
        return JOB_OVERRIDES[raw_id]
    t = scrub(title or "")
    t = re.sub(r"^ghostcorpnet\s+", "", t, flags=re.I)
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)  # trailing parenthetical
    if not t:
        return "Works on the website and business"
    return t[0].upper() + t[1:]


def cron_entries():
    out = []
    for base in CRON_DIRS:
        for path in sorted(glob.glob(os.path.join(base, "*", "*.md"))):
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            fm, _body = parse_frontmatter(text)
            raw_id = fm.get("id", os.path.basename(path).split("__")[0])
            low = raw_id.lower()
            if any(s in low for s in EXCLUDE_SUBSTR) or raw_id in EXCLUDE_IDS:
                continue
            if fm.get("enabled", "").lower() != "true":
                continue
            if fm.get("kind", "") == "runonce":
                continue
            name = scrub(fm.get("title", "")).strip("'\"") or pretty_name(raw_id)
            name = re.sub(r"^ghostcorpnet\s+", "", name, flags=re.I)
            name = name[0].upper() + name[1:] if name else pretty_name(raw_id)
            out.append({
                "name": name,
                "job": job_from_title(fm.get("title", ""), raw_id),
                "schedule": schedule_str(fm, os.path.basename(path)),
                "_id": raw_id,
            })
    return out


def role_entries():
    out = []
    seen_dirs = set()
    for base in ROLE_DIRS:
        if not os.path.isdir(base) or base in seen_dirs:
            continue
        seen_dirs.add(base)
        for path in sorted(glob.glob(os.path.join(base, "*.md"))):
            raw_id = os.path.basename(path)[:-3]
            low = raw_id.lower()
            if any(s in low for s in EXCLUDE_SUBSTR) or raw_id in EXCLUDE_IDS:
                continue
            text = open(path, encoding="utf-8", errors="replace").read()
            job = ""
            m = re.search(r"##\s*Purpose\s*\n+(.+)", text, re.S)
            if m:
                para = m.group(1).split("\n\n")[0]
                sent = re.split(r"(?<=[.!])\s+", para.strip())[0]
                job = scrub(sent)
                if "@" in job or len(job) < 12:
                    job = ""
            if not job:
                job = "Hive worker — %s for the website and product catalog" % \
                    raw_id.replace("-", " ")
            if len(job) > 160:
                job = job[:160].rsplit(" ", 1)[0].rstrip(",;:") + "…"
            out.append({
                "name": pretty_name(raw_id) + " (hive)",
                "job": job,
                "schedule": "On demand · hive",
                "_id": "hive-" + raw_id,
            })
    return out


def swarm_entries():
    """Customer Swarm hunters: name -> roster entry, job -> its assignment."""
    out = []
    if not os.path.isfile(SWARM_ROSTER):
        return out
    try:
        hunters = json.load(open(SWARM_ROSTER, encoding="utf-8"))
    except (OSError, ValueError):
        return out
    for h in hunters:
        name = scrub(h.get("name", ""))
        job = scrub(h.get("assignment", ""))
        if not name or not job:
            continue
        if len(job) > 160:
            job = job[:160].rsplit(" ", 1)[0].rstrip(",;:") + "…"
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        out.append({
            "name": name,
            "job": job,
            "schedule": "24/7 rotation",
            "_id": "swarm-" + slug,
        })
    return out


def money_stats():
    """Owner's money totals from verified sales records only.

    Base record: the approval watcher's lifetime ledger
    hidden_files/money/sales-alerts.jsonl (one row per Gumroad sale it
    has seen: id, price_cents, at). Cross-check: the Gumroad API's
    recent sales (last 7 days) are merged in by sale id, so a sale the
    watcher has not logged yet still counts. Gumroad's sale "price"
    field is in cents, same as the ledger's price_cents. A sale counts
    as an ORDER (and toward money made) only when price_cents > 0;
    $0 records are free downloads, counted separately and never
    dressed up as orders. Aggregates only — no buyer data is read
    into the output. Any failure leaves the ledger-only totals.
    """
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    records = {}  # sale id -> (price_cents, at_iso)

    alerts = os.path.join(MONEY_DIR, "sales-alerts.jsonl")
    try:
        with open(alerts, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                sid = row.get("id")
                if sid:
                    records[sid] = (int(row.get("price_cents") or 0),
                                    row.get("at") or "")
    except OSError:
        pass

    try:
        after = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        out = subprocess.run(
            ["python3", GUMROAD_API, "sales", "after=%s" % after],
            capture_output=True, text=True, timeout=60)
        data = json.loads(out.stdout)
        for sale in data.get("sales", []):
            sid = sale.get("id")
            if sid and sid not in records:
                records[sid] = (int(sale.get("price") or 0),
                                sale.get("created_at") or "")
    except Exception:
        pass  # API unreachable — ledger-only totals stand

    paid = [(c, at) for c, at in records.values() if c > 0]
    paid_today = [(c, at) for c, at in paid if at.startswith(today)]
    return {
        "money_made_usd": round(sum(c for c, _ in paid) / 100.0, 2),
        "orders": len(paid),
        "sales_today_usd": round(sum(c for c, _ in paid_today) / 100.0, 2),
        "orders_today": len(paid_today),
        "free_downloads": sum(1 for c, _ in records.values() if c == 0),
        "as_of": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Verified sales ledger + Gumroad sales check",
    }


def main():
    entries = cron_entries() + role_entries() + swarm_entries()
    seen, roster = set(), []
    for e in entries:
        if e["_id"] in seen:
            continue
        seen.add(e["_id"])
        roster.append({"name": e["name"], "job": e["job"],
                       "schedule": e["schedule"]})
    roster.sort(key=lambda e: e["name"].lower())
    stats = money_stats()
    payload = {
        "generated_at": stats["as_of"],
        "stats": stats,
        "bots": roster,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    print("roster: %d website bots -> %s" % (len(roster), OUT))
    print("stats: $%.2f made, %d orders, $%.2f today (as of %s)"
          % (stats["money_made_usd"], stats["orders"],
             stats["sales_today_usd"], stats["as_of"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
