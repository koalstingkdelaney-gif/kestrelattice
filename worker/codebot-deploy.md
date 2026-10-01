# Code Bot — deploy steps

Everything below is built and staged. Going live needs ONE human step
(koalstin's 2-minute Cloudflare re-auth — same pending tap as the directory +
chat worker endpoints), then a deployer run.

## What the human does (phone, ~2 minutes)
1. Re-authenticate Cloudflare in the secure setup flow (the same one-time
   token/phone tap already on his list for the directory + chat endpoints).
   Tell the agent when it's done.

## What the agent does after the tap
1. `wrangler secret put GROQ_API_KEY` — his Groq key (server-side only, never
   in the browser). Reuse the same key the staged admin chat was designed for.
2. `wrangler secret put GUMROAD_API_KEY` — his Gumroad seller API token
   (used server-side to verify license keys against the sales list).
3. Insert `worker/codebot-endpoint.patch.js` into `worker/approvals-worker.js`
   fetch handler (before the final 404), plus the `sha256hex`/`utcDay`/
   `utcMonth`/quota-constant helpers near the other top-level helpers.
4. `wrangler deploy` the worker.
5. In Gumroad: enable license-key generation on every code product
   (product editor → enable "Generate a unique license key" per sale). Buyers
   get the key in their receipt email — without this, /codebot-verify can
   never match a key. (The code-product publish browser task should do this
   at publish time for all 12 code products.)
6. `python3 ~/workspace/goals/kestrelattice-autonomous-growth/hidden_files/codebot/build-codebot-context.py`
   — indexes the code-product zips and uploads the catalog to /codebot-context.
   Re-run after every code-product publish batch.
7. Commit + push the `code-bot/` site page (it's a static page; ships with the
   normal site build), curl-verify
   https://koalstingkdelaney-gif.github.io/kestrelattice/code-bot/ → 200.
8. Apply `worker/codebot-pdp.patch.md` to build-product-pages.py, rebuild
   PDPs, verify a code-product page shows the "Get coding help" button.
9. Wire `worker/codebot-panel.snippet.html` into build-admin.py (panel
   redesign coordinator owns this), rebuild + re-upload the panel.
10. Live test with a REAL license key (from any code-product test purchase or
    a key generated in Gumroad): POST /codebot-verify → expect `ok:true` +
    token; POST /codebot-chat → expect `ok:true` + a coding reply.
    Do NOT call it live until this test passes.

## Ongoing (automatic)
- `/codebot-stats?key=<WRITE_KEY>` feeds the admin panel's Code Bot section:
  questions today, active licenses, monthly usage vs the 5,000 cap, top
  license hashes, recent questions.
- Sales-list cache refreshes every 15 min; per-key quota resets at UTC
  midnight; sessions expire after 24h.
- Quota math: 5,000 calls/month via Groq's free tier is comfortably inside
  free limits; if it ever isn't, lower the monthly cap in the patch (one
  constant) — no redeploy of the site needed, just the worker.

## If the Groq model is retired
The weekly AI model refresh bot tracks provider model changes for the fleet.
If `llama-3.3-70b-versatile` ever 404s, swap the model string in the
/codebot-chat handler to the current Groq flagship and redeploy the worker.
