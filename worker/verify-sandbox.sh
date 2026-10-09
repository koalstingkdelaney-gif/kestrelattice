#!/bin/bash
# Sandbox route verification — run AFTER a successful wrangler deploy.
# Loads keys from .secrets.json (never prints them). Uses curl with a browser
# User-Agent (python urllib gets Cloudflare 1010 from the WAF).
set -u
cd "$(dirname "$0")"
URL=$(python3 -c "import json;print(json.load(open('.secrets.json'))['worker_url'])")
WK=$(python3 -c "import json;print(json.load(open('.secrets.json'))['write_key'])")
SK=$(python3 -c "import json;print(json.load(open('.secrets.json'))['server_key'])")
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
ok=0; fail=0
check() { # check <label> <expected_ok> <curl-args...>
  local label="$1" expect="$2"; shift 2
  local body code
  body=$(curl -sS -A "$UA" -m 30 "$@" 2>/dev/null)
  code=$(curl -sS -A "$UA" -m 30 -o /dev/null -w "%{http_code}" "$@" 2>/dev/null)
  if [ "$code" = "$expect" ] && echo "$body" | grep -q '"ok":true'; then
    echo "PASS [$code] $label"; ok=$((ok+1))
  else
    echo "FAIL [got $code] $label -> $body"; fail=$((fail+1))
  fi
}
echo "== sandbox GET routes (write key) =="
check "GET /sandbox/sandboxes" 200 "$URL/sandbox/sandboxes?key=$WK"
check "GET /sandbox/rogues" 200 "$URL/sandbox/rogues?key=$WK"
check "GET /sandbox/crew" 200 "$URL/sandbox/crew?key=$WK"
check "GET /sandbox/transcript" 200 "$URL/sandbox/transcript?key=$WK&limit=5"
check "GET /sandbox/chat (missing thread -> [])" 200 "$URL/sandbox/chat?key=$WK&sandbox_id=nosb&bot_id=nobot"
check "GET /sandbox/inventions" 200 "$URL/sandbox/inventions?key=$WK"
echo "== auth denials =="
code=$(curl -sS -A "$UA" -m 30 -o /dev/null -w "%{http_code}" "$URL/sandbox/rogues" 2>/dev/null)
[ "$code" = "404" ] && { echo "PASS [404] /sandbox/rogues no key -> 404"; ok=$((ok+1)); } || { echo "FAIL [got $code] /sandbox/rogues no key"; fail=$((fail+1)); }
echo "== create + retire a dry-run sandbox =="
sbx=$(curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/sandboxes" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"name\":\"Verify Dry Run\",\"purpose\":\"verify script dry run\"}" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('id','') if d.get('ok') else '')")
[ -n "$sbx" ] && echo "$sbx" | grep -q "^sb-verify-dry-run-" && { echo "PASS create sandbox -> $sbx"; ok=$((ok+1)); } || { echo "FAIL create sandbox -> $sbx"; fail=$((fail+1)); }
echo "$sbx" | grep -q . && curl -sS -A "$UA" -m 30 "$URL/sandbox/sandboxes?key=$WK" | grep -q "$sbx" && { echo "PASS sandbox listed"; ok=$((ok+1)); } || { echo "FAIL sandbox not listed"; fail=$((fail+1)); }
echo "== sandbox-scoped chat round-trip =="
check "POST /sandbox/chat (koalstin msg)" 200 -X POST "$URL/sandbox/chat" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"sandbox_id\":\"$sbx\",\"bot_id\":\"dryrun-bot\",\"text\":\"hello from verify\"}"
check "POST /sandbox/chat-reply (server)" 200 -X POST "$URL/sandbox/chat-reply" -H "Content-Type: application/json" -H "x-server-key: $SK" -d "{\"sandbox_id\":\"$sbx\",\"bot_id\":\"dryrun-bot\",\"text\":\"sandbox reply\"}"
body=$(curl -sS -A "$UA" -m 30 "$URL/sandbox/chat?key=$WK&sandbox_id=$sbx&bot_id=dryrun-bot" 2>/dev/null)
echo "$body" | grep -q "hello from verify" && echo "$body" | grep -q "sandbox reply" && { echo "PASS thread shows both messages"; ok=$((ok+1)); } || { echo "FAIL thread missing messages -> $body"; fail=$((fail+1)); }
body=$(curl -sS -A "$UA" -m 30 "$URL/sandbox/chat?key=$WK&sandbox_id=$sbx&bot_id=other-bot" 2>/dev/null)
echo "$body" | grep -q '"thread":\[\]' && { echo "PASS thread scoping: other-bot empty"; ok=$((ok+1)); } || { echo "FAIL thread not sandbox-scoped -> $body"; fail=$((fail+1)); }
echo "== dry-run request lifecycle (quarantine + release + move-bot) =="
rid=$(curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/quarantine" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"job_id\":\"brand-dryrun-acquire\",\"reason\":\"verify dry run\",\"sandbox_id\":\"$sbx\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('request_id',''))")
[ -n "$rid" ] && { echo "PASS quarantine -> request_id $rid"; ok=$((ok+1)); } || { echo "FAIL quarantine dry run"; fail=$((fail+1)); }
curl -sS -A "$UA" -m 30 -H "x-server-key: $SK" "$URL/sandbox/requests" | grep -q "\"id\":\"$rid\".*pending" && { echo "PASS /sandbox/requests shows pending"; ok=$((ok+1)); } || { echo "FAIL requests missing pending $rid"; fail=$((fail+1)); }
check "POST /sandbox/requests/ack" 200 -X POST "$URL/sandbox/requests/ack" -H "Content-Type: application/json" -H "x-server-key: $SK" -d "{\"id\":\"$rid\"}"
curl -sS -A "$UA" -m 30 -H "x-server-key: $SK" "$URL/sandbox/requests" | grep -q "\"id\":\"$rid\".*\"status\":\"done\"" && { echo "PASS dry-run request acked (done)"; ok=$((ok+1)); } || { echo "FAIL ack not reflected"; fail=$((fail+1)); }
rid2=$(curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/release" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"rogue_id\":\"dryrun-rogue\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('request_id',''))")
curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/requests/ack" -H "Content-Type: application/json" -H "x-server-key: $SK" -d "{\"id\":\"$rid2\"}" >/dev/null 2>&1
[ -n "$rid2" ] && { echo "PASS release dry run -> $rid2 (acked)"; ok=$((ok+1)); } || { echo "FAIL release dry run"; fail=$((fail+1)); }
ridm=$(curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/move-bot" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"bot_ref\":\"dryrun-bot\",\"to_sandbox\":\"$sbx\"}" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('request_id','') if d.get('ok') else '')")
[ -n "$ridm" ] && curl -sS -A "$UA" -m 30 -H "x-server-key: $SK" "$URL/sandbox/requests" | grep -q "\"id\":\"$ridm\".*\"type\":\"move_bot\".*\"to_sandbox\":\"$sbx\"" && { echo "PASS move-bot request -> $ridm"; ok=$((ok+1)); } || { echo "FAIL move-bot lifecycle"; fail=$((fail+1)); }
curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/requests/ack" -H "Content-Type: application/json" -H "x-server-key: $SK" -d "{\"id\":\"$ridm\"}" >/dev/null 2>&1
echo "== invention + promote (sandbox-scoped) =="
invid=$(curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/invention" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"sandbox_id\":\"$sbx\",\"bot_id\":\"dryrun-bot\",\"bot_name\":\"Dryrun Bot\",\"text\":\"verify test invention\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('id',''))")
[ -n "$invid" ] && { echo "PASS invention -> $invid"; ok=$((ok+1)); } || { echo "FAIL invention"; fail=$((fail+1)); }
rid3=$(curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/promote" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"invention_id\":\"$invid\",\"dest\":\"ideas\",\"contact_email\":\"n/a\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('request_id',''))")
curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/requests/ack" -H "Content-Type: application/json" -H "x-server-key: $SK" -d "{\"id\":\"$rid3\"}" >/dev/null 2>&1
[ -n "$rid3" ] && { echo "PASS promote -> $rid3 (acked)"; ok=$((ok+1)); } || { echo "FAIL promote"; fail=$((fail+1)); }
curl -sS -A "$UA" -m 30 "$URL/sandbox/inventions?key=$WK&sandbox_id=$sbx" | grep -q "\"id\":\"$invid\".*\"status\":\"promote-requested\"" && { echo "PASS invention status flipped to promote-requested"; ok=$((ok+1)); } || { echo "FAIL invention status not flipped"; fail=$((fail+1)); }
echo "== server sync (new keys) =="
check "POST /sandbox-sync (server)" 200 -X POST "$URL/sandbox-sync" -H "Content-Type: application/json" -H "x-server-key: $SK" -d '{"sandboxes":[],"crew":[],"rogues":[],"transcript":[],"inventions":[]}'
curl -sS -A "$UA" -m 30 "$URL/sandbox/rogues?key=$WK&sandbox_id=$sbx" | grep -q '"ok":true' && { echo "PASS sandbox_id filter param accepted"; ok=$((ok+1)); } || { echo "FAIL sandbox_id filter"; fail=$((fail+1)); }
echo "== retire the dry-run sandbox =="
curl -sS -A "$UA" -m 30 -X POST "$URL/sandbox/sandboxes/retire" -H "Content-Type: application/json" -d "{\"key\":\"$WK\",\"id\":\"$sbx\"}" | grep -q '"ok":true' && { echo "PASS retire sandbox $sbx"; ok=$((ok+1)); } || { echo "FAIL retire sandbox"; fail=$((fail+1)); }
curl -sS -A "$UA" -m 30 "$URL/sandbox/sandboxes?key=$WK" | grep -q "$sbx" && { echo "FAIL retired sandbox still listed"; fail=$((fail+1)); } || { echo "PASS retired sandbox gone from list"; ok=$((ok+1)); }
echo "---- result: $ok passed, $fail failed ----"
exit $((fail>0))
