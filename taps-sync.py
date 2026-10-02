#!/usr/bin/env python3
"""Sync needs_human.jsonl -> worker KV (taps feed for the Action Center).

Run from the approval-watcher cron every 5 minutes, and once manually after
the worker code deploys. FAIL-SOFT: any error prints to stderr and exits 0 —
it must never break the caller's run.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HOME = os.path.expanduser("~")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
NEEDS_HUMAN = os.path.join(HOME, "workspace/sentience/state/needs_human.jsonl")
MIRRORED = os.path.join(
    HOME,
    "workspace/goals/kestrelattice-autonomous-growth/hidden_files/approvals/"
    "taps-resolved-mirrored.json",
)


def fail_soft(msg):
    print("taps-sync: %s" % msg, file=sys.stderr)


def curl(args, data_file=None):
    cmd = ["curl", "-s", "-A", UA] + args
    if data_file:
        cmd += ["--data-binary", "@" + data_file]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def main():
    try:
        with open(os.path.join(HOME, "workspace/kestrelattice/worker/.secrets.json")) as f:
            sec = json.load(f)
    except Exception as e:
        return fail_soft("worker secrets unreadable: %s" % e)
    wurl = sec.get("worker_url", "").rstrip("/")
    skey = sec.get("server_key", "")
    if not wurl or not skey:
        return fail_soft("worker secrets missing")

    taps = []
    try:
        with open(NEEDS_HUMAN) as f:
            lines = f.read().splitlines()
    except Exception as e:
        return fail_soft("needs_human.jsonl unreadable: %s" % e)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("kind") == "tap_resolved":
            continue  # resolution marker, not a live tap
        tid = d.get("id") or hashlib.sha1(
            (str(d.get("kind", "")) + str(d.get("title", ""))).encode()
        ).hexdigest()[:12]
        taps.append(
            {
                "id": tid,
                "kind": str(d.get("kind", "tap")),
                "title": str(d.get("title", "Needs your tap")),
                "detail": str(d.get("detail", "")),
                "tap": str(d.get("tap", "")),
                "ts": str(d.get("ts", "")),
            }
        )

    # Mirror panel resolutions back into needs_human.jsonl, append-only, so the
    # operator's source of truth learns what he already handled in the panel.
    try:
        r = curl(["-H", "x-server-key: " + skey, wurl + "/taps-resolved"])
        resolved = json.loads(r.stdout or "{}").get("resolved", {})
        seen = set(json.load(open(MIRRORED))) if os.path.exists(MIRRORED) else set()
        new = [i for i in resolved if i not in seen]
        if new:
            with open(NEEDS_HUMAN, "a") as f:
                for i in new:
                    f.write(
                        json.dumps(
                            {
                                "kind": "tap_resolved",
                                "id": i,
                                "choice": resolved[i].get("choice", "handled"),
                                "ts": resolved[i].get("ts", ""),
                                "via": "action_center",
                            }
                        )
                        + "\n"
                    )
            with open(MIRRORED, "w") as f:
                json.dump(sorted(seen | set(new)), f)
            print("taps-sync: mirrored %d resolution(s) to needs_human.jsonl" % len(new))
    except Exception as e:
        fail_soft("resolution mirror skipped: %s" % e)

    # Push the taps array. (Cloudflare WAF bans python urllib's default UA,
    # so this goes through curl like every other worker mutation.)
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(taps, f)
            tmp = f.name
        r = curl(
            [
                "-X", "POST",
                "-H", "x-server-key: " + skey,
                "-H", "Content-Type: application/json",
                wurl + "/taps-sync",
            ],
            data_file=tmp,
        )
        os.unlink(tmp)
        print("taps-sync: %s" % (r.stdout.strip()[:200] or r.stderr.strip()[:200]))
    except Exception as e:
        fail_soft("push failed: %s" % e)


if __name__ == "__main__":
    main()
