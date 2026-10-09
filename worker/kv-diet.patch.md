# KV-write diet — worker fix (needs deploy)

## Problem
`POST /sandbox-sync` re-puts the ENTIRE merged invention set (~72 KV puts)
every time the payload contains ≥1 new invention. At ~40 invention-bearing
syncs/day this burns ~1,500–2,900 of the 1,000/day free-plan KV write budget
by itself → error 1101 on all write routes (third outage: 2026-10-01,
2026-10-08, 2026-10-09). Full audit: subagent report 2026-10-09 (in chat).

## Fix (one word)
In `approvals-worker.js`, the `/sandbox-sync` invention block (~line 848):

```js
// BEFORE — re-puts every invention in KV on every sync:
for (const i of merged) {
  if (i && i.id) {
    await env.APPROVALS.put(SB_INVENTION_PREFIX + i.id, JSON.stringify(i));
  }
}

// AFTER — only the new/changed inventions from this payload:
for (const i of payloadInv) {
  if (i && i.id) {
    await env.APPROVALS.put(SB_INVENTION_PREFIX + i.id, JSON.stringify(i));
  }
}
```

Safe: per-id invention keys are written once at creation; status updates
(promote/ack) go through their own routes. KV-side items never need re-putting.

## Deploy — DONE 2026-10-09 15:07 EDT (version 8566e976) via owner one-time token (transient, never stored)
```bash
cd ~/workspace/kestrelattice/worker && \
CLOUDFLARE_API_TOKEN=<his-one-time-token> npx wrangler deploy approvals-worker.js \
  --name kestrelattice-approvals --compatibility-date 2024-01-01
```
Verify: `GET /sandbox/inventions` (server key) → 200; then one
`POST /sandbox-sync` with a single new invention → check only 1
`sb_invention:*` put (no 1101).

## Already fixed VM-side (no deploy needed, live now)
- `sandbox-sync.py`: rooms payload slimmed (dropped full file listing +
  memory_tail — gallery never rendered them); transcript pushes gated to
  ≥15 min; invention payloads batched to ≥1/hour.
- `_admin_sections.py` `upload_private`: sha256-guarded, skips upload when
  page content unchanged (BUILD_TS excluded from comparison).

## Expected result
~2,200–3,700 puts/day → ~400–600/day after the worker fix lands.
