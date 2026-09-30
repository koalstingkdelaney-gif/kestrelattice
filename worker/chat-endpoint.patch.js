// STAGED — not yet deployed. Deploying needs a Cloudflare API re-login
// (one-time token / phone tap, same as the first deploy); the runtime does not
// retain the deploy token. When access is restored:
//   1. Insert the /chat handler below into worker/approvals-worker.js
//      (inside the fetch handler, next to the other routes).
//   2. wrangler secret put GROQ_API_KEY   (koalstin's Groq key — server-side only)
//   3. wrangler deploy
//   4. Add worker/chat-ui.snippet.html as a new panel section in build-admin.py
//      and rebuild the panel.
//
// Design: the chat lives in the PRIVATE admin panel (key-gated, noindex —
// never on the public site). It answers as the fleet coordinator with live
// fleet state injected from KV. It cannot approve, send, or change anything:
// actions still go through the panel's one-tap buttons (the approval queue).

// ---- insert into the fetch handler ----
if (req.method === "POST" && url.pathname === "/chat") {
  const ip = req.headers.get("cf-connecting-ip") || "unknown";
  if (!(await checkRateLimit(env, ip))) {
    return json({ ok: false, error: "rate_limited" }, 429);
  }
  let body;
  try { body = await req.json(); } catch { body = {}; }
  if (!body.key || body.key !== env.WRITE_KEY) {
    return json({ ok: false, error: "forbidden" }, 403);
  }
  const message = String(body.message || "").slice(0, 2000);
  const history = Array.isArray(body.history) ? body.history.slice(-10) : [];
  if (!message.trim()) return json({ ok: false, error: "empty" }, 400);

  // Live fleet context from KV
  const q = await readQueue(env);
  const pending = q.filter((i) => i.status === "pending").length;
  const approved = q.filter((i) => i.status === "approved").length;
  const outreachPending = q.filter(
    (i) => i.group === "outreach" && i.kind === "outreach_send" && i.status === "pending").length;
  let sentCount = 0;
  try {
    const ledger = await env.APPROVALS.get("outreach_sent_count");
    sentCount = parseInt(ledger || "0", 10);
  } catch (e) {}

  const system =
    "You are the ghostcorpnet fleet coordinator, talking to the business owner " +
    "in his private admin panel. Be terse and concrete. Live state: " +
    pending + " items awaiting his approval, " + approved + " approved/in-progress, " +
    outreachPending + " outreach pitches ready for his Send tap, " +
    sentCount + " pitches sent total. " +
    "The fleet: lead scout (daily), outreach sync (every 30m, drafts pitches), " +
    "approval watcher (every 15m, executes his approvals), SEO writer (3x/week), " +
    "site improver, micro-forge (product drafts), plus marketplace/partner/provider " +
    "scouts. You cannot approve, send, or change anything yourself — every action " +
    "needs his one-tap button in the panel. Never invent sales or customer data. " +
    "If asked about something you can't see, say so plainly.";

  const messages = [{ role: "system", content: system }];
  for (const h of history) {
    if (h.role === "user" || h.role === "assistant") {
      messages.push({ role: h.role, content: String(h.content || "").slice(0, 2000) });
    }
  }
  messages.push({ role: "user", content: message });

  const gr = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + env.GROQ_API_KEY,
    },
    body: JSON.stringify({
      model: "llama-3.3-70b-versatile",
      messages,
      max_tokens: 500,
      temperature: 0.4,
    }),
  });
  if (!gr.ok) return json({ ok: false, error: "ai_unavailable" }, 502);
  const gd = await gr.json();
  const reply = (gd.choices && gd.choices[0] && gd.choices[0].message.content || "").trim();
  return json({ ok: true, reply });
}
// ---- end insert ----
