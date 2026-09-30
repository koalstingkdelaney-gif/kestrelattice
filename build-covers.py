#!/usr/bin/env python3
"""Generate branded Gumroad cover PNGs for ghostcorpnet products.

Reads pending-listings.jsonl (plus the original 8 catalog products) and
renders a 1200x1600 cover per product in assets/covers/<gumroad_id>.png
using the ghostcorpnet dark-slate/terracotta brand. Idempotent: skips
covers that already exist unless --force is passed.
"""
import json, os, re, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.expanduser("~/workspace/goals/kestrelattice-autonomous-growth/hidden_files")
SITE = os.path.expanduser("~/workspace/kestrelattice")
OUT = os.path.join(SITE, "assets", "covers")

BG = (18, 18, 18)
PANEL = (28, 26, 24)
ACCENT = (224, 122, 95)
TEXT = (232, 226, 216)
MUTED = (154, 145, 127)
LINE = (51, 46, 38)

W, H = 1200, 1600

def font(size, bold=True):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for p in (f"/usr/share/fonts/truetype/dejavu/{name}", name):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()

ORIGINALS = [
    ("hdigmr", "The Playbook — Studio Edition", 29, "The governed-agent playbook: policies, schemas, and rollout in one PDF."),
    ("sahva", "AI Agent Risk Audit Kit", 19, "Scored risk-tier self-assessment and 40-point audit checklist."),
    ("jbngbu", "Agent Incident Response Runbook", 19, "Severity levels, triage procedures, kill-switch checklists."),
    ("slexhv", "100 Agent Use Cases, Pre-Tiered", 19, "100 concrete use cases, each pre-tiered with key controls."),
    ("cjdkuu", "Prompt Injection Defense Field Guide", 19, "15 attack scenarios, 6 layered defenses, 20 test prompts."),
    ("ilxccs", "Agent Cost Control Workbook", 19, "Budget worksheets, metering setup, kill-on-overspend rules."),
    ("fdtkdd", "Quarterly Access Review Kit", 19, "Grant inventory, re-certification sign-off, 90-day calendar."),
    ("yzbumc", "The Complete ghostcorpnet Library", 79, "Every playbook and kit in one download."),
]

def products():
    seen = set()
    out = []
    for pid, title, price, tag in ORIGINALS:
        out.append({"id": pid, "title": title, "price": price, "tagline": tag})
        seen.add(pid)
    for fname in ("pending-listings.jsonl", "pending-packs.jsonl"):
        path = os.path.join(BASE, "marketplace", fname)
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        p = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    url = p.get("gumroad_url") or ""
                    m = re.search(r"/l/([a-z0-9-]+)", url)
                    if m:
                        pid = m.group(1)
                    elif str(p.get("item_code", "")).upper().startswith("PACK-"):
                        pid = p["item_code"].lower().replace("_", "-")
                    else:
                        continue
                    if pid in seen:
                        continue
                    seen.add(pid)
                    out.append({"id": pid, "title": p["product_title"],
                                "price": p.get("price_usd", 19),
                                "tagline": p.get("tagline", "")})
    return out

def render(title, price, tagline):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # top accent bar
    d.rectangle([0, 0, W, 14], fill=ACCENT)
    # wordmark
    d.text((80, 70), "KESTRELATTICE", font=font(44), fill=MUTED)
    d.line([80, 140, W - 80, 140], fill=LINE, width=2)
    # price pill
    pill = f"${price}"
    fb = font(40)
    bb = d.textbbox((0, 0), pill, font=fb)
    pw = bb[2] - bb[0] + 48
    d.rounded_rectangle([80, 180, 80 + pw, 244], radius=18, fill=ACCENT)
    d.text((104, 190), pill, font=fb, fill=(22, 18, 16))
    # title (wrapped)
    y = 300
    for para in textwrap.wrap(title, width=18):
        f = font(96)
        bb = d.textbbox((0, 0), para, font=f)
        d.text((80, y), para, font=f, fill=TEXT)
        y += (bb[3] - bb[1]) + 18
    # terracotta rule under title
    d.rectangle([80, y + 20, 280, y + 28], fill=ACCENT)
    # tagline
    y += 80
    for para in textwrap.wrap(tagline, width=42):
        f = font(40, bold=False)
        bb = d.textbbox((0, 0), para, font=f)
        d.text((80, y), para, font=f, fill=MUTED)
        y += (bb[3] - bb[1]) + 14
    # footer
    d.line([80, H - 160, W - 80, H - 160], fill=LINE, width=2)
    d.text((80, H - 120), "Instant PDF download · Self-serve", font=font(34, bold=False), fill=MUTED)
    d.text((80, H - 70), "kestrelattice", font=font(34), fill=ACCENT)
    return img

def main():
    force = "--force" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    made, skipped = 0, 0
    for p in products():
        dest = os.path.join(OUT, f"{p['id']}.png")
        if os.path.exists(dest) and not force:
            skipped += 1
            continue
        render(p["title"], p["price"], p["tagline"]).save(dest)
        made += 1
    print(f"covers: {made} generated, {skipped} already existed -> {OUT}")

if __name__ == "__main__":
    main()
