# KV diet: per-thread chat blob cache + inventions index blob (STAGED 2026-10-12)

## Why
Free-plan KV allows ~1,000 list() calls/day. Every `GET /sandbox/chat`
does `list({prefix})` + one `get()` per message key, and every
`GET /sandbox/inventions` lists the whole invention set. Before the
2026-10-12 inbox redesign, the chat bridge swept 55 threads every 3
minutes (~26,400 lists/day) and took the worker down daily (error 1101),
which blanked the panel's Sandbox tab.

The inbox redesign (panel pings `__inbox__`, bridge polls inboxes) already
brings lists to ~700/day — under budget. This patch is the long-term
hardening: it makes the two hot read paths list-free, so even a future
sweep-heavy client can't burn the budget again.

## Deploy
Needs the owner's Cloudflare re-auth tap (no stored API token on the VM),
then `wrangler deploy` (see codebot-deploy.md for the tap flow).

## Patch 1 — per-thread blob cache for /sandbox/chat

In `approvals-worker.js`, next to `pushSbThreadMsg` / `readSbThread`:

```js
// KV diet 2026-10-12: per-thread blob cache. Reads are 1 KV get, 0 lists.
// Writes go through (append per-item key + rewrite the small blob).
const SB_THREAD_BLOB_PREFIX = "sb_threadblob:";
const threadBlobKey = (sandbox_id, bot_id) =>
  SB_THREAD_BLOB_PREFIX + sandbox_id + ":" + bot_id;
const writeThreadBlob = async (sandbox_id, bot_id) => {
  // Rebuild from per-item keys (source of truth) after a write.
  const thread = await readSbThread(sandbox_id, bot_id);
  await env.APPROVALS.put(threadBlobKey(sandbox_id, bot_id), JSON.stringify(thread));
};
const readThreadCached = async (sandbox_id, bot_id) => {
  const raw = await env.APPROVALS.get(threadBlobKey(sandbox_id, bot_id));
  if (raw) {
    try { return JSON.parse(raw); } catch { /* fall through to rebuild */ }
  }
  const thread = await readSbThread(sandbox_id, bot_id);
  await env.APPROVALS.put(threadBlobKey(sandbox_id, bot_id), JSON.stringify(thread));
  return thread;
};
```

- In `GET /sandbox/chat`: replace `readSbThread(...)` with
  `readThreadCached(...)`.
- In `POST /sandbox/chat` and `POST /sandbox/chat-reply`: after
  `pushSbThreadMsg(...)`, add
  `await writeThreadBlob(sandbox_id, bot_id);`

Race note: two near-simultaneous posts to the same thread could interleave
blob rewrites. Chat posts are seconds apart minimum and the per-item keys
remain the source of truth; the next write self-heals the blob. Acceptable.

## Patch 2 — inventions index blob for /sandbox/inventions

```js
// KV diet 2026-10-12: inventions index blob. 1 get on read, 0 lists.
const SB_INV_INDEX = "sb_inventions_index";
const writeInvIndex = async () => {
  const all = await listSbPrefixed(SB_INVENTION_PREFIX); // rare: only on write
  all.sort((a, b) => String(a.at || "").localeCompare(String(b.at || "")));
  await env.APPROVALS.put(SB_INV_INDEX, JSON.stringify(all));
};
```

- In `readSbInventions()`: try `env.APPROVALS.get(SB_INV_INDEX)` first;
  fall back to the list path + populate the blob when missing.
- After each invention write site (the three `SB_INVENTION_PREFIX` puts
  near current lines 773, 786, 859, plus the /sandbox-sync merge): call
  `await writeInvIndex();`. Invention writes are a few per hour, so the
  extra list+put per write is negligible.

## Verification (after deploy)
1. `GET /sandbox/chat?sandbox_id=quarantine&bot_id=__inbox__` -> 200, thread array.
2. POST a chat message, GET the thread again -> message present (write-through works).
3. `GET /sandbox/inventions` -> 200, inventions array.
4. Panel Sandbox tab loads with live data (no snapshot fallback banner).
5. 24h later: no 1101s in any cron log.
