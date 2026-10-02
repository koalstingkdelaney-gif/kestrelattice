#!/usr/bin/env bash
# stamp-freshness.sh — stamp the proof-strip freshness line from the real
# deploy date at push time. Run this before EVERY git push that ships index.html.
# The line is never hand-dated: it derives from `git log -1 --format=%cs`
# (the previous deploy) and falls back to today's date when there is no git history.
set -u
SITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATE="$(git -C "$SITE" log -1 --format=%cs 2>/dev/null || date +%F)"
MONTH="$(date -d "$DATE" +"%b %Y" 2>/dev/null || date +"%b %Y")"
MONTHFULL="$(date -d "$DATE" +"%B %Y" 2>/dev/null || date +"%B %Y")"
python3 - "$SITE/index.html" "$MONTH" "$MONTHFULL" <<'EOF'
import re, sys
p, month, monthfull = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p).read()
s2, n = re.subn(r'<p class="freshness">.*?</p>',
                f'<p class="freshness">Fresh for {month} \u2014 catalog and guides updated</p>',
                s, count=1)
if n != 1:
    sys.exit("stamp-freshness.sh: freshness line not found")
s3, m = re.subn(r'<p class="footer-updated">.*?</p>',
                f'<p class="footer-updated">Last updated: {monthfull}</p>',
                s2, count=1)
if m != 1:
    sys.exit("stamp-freshness.sh: footer-updated line not found")
open(p, "w").write(s3)
print(f"stamped: Fresh for {month} / footer Last updated: {monthfull}")
EOF
