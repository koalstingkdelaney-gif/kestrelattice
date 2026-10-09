/**
 * ghostcorpnet approval backend — Cloudflare Worker + KV.
 *
 * The static admin page (GitHub Pages) calls this directly:
 *   GET  /queue            -> public, current approval queue
 *   POST /approve          -> body {code, key}; key must match WRITE_KEY secret.
 *                            Only flips existing items pending -> approved.
 *                            Cannot create new work; blast radius is bounded
 *                            to the pre-seeded queue.
 * The fleet watcher (private) uses the server key:
 *   GET  /pending          -> header x-server-key; items with status "approved"
 *   POST /complete         -> header x-server-key; body {code, status}
 *                            status is "done" or "blocked:<reason>"
 *   POST /seed             -> header x-server-key; body = full queue array
 *                            (one-time seed after deploy)
 *
 * The private admin panel (key-gated, not on the public site):
 *   POST /admin-upload     -> header x-server-key; body = raw HTML string.
 *                            Stores the latest admin dashboard HTML in KV.
 *   GET  /admin?key=<WRITE_KEY> -> serves the stored admin HTML (text/html).
 *                            Wrong/missing key -> 403. This is the human's
 *                            private bookmark; the public site has no admin page.
 *
 * KV binding: APPROVALS (keys: "queue" -> JSON array, "admin_html" -> string,
 *                     "directory_submissions" -> JSON array).
 * Secrets (wrangler secret put): WRITE_KEY, SERVER_KEY.
 *
 * Third-party pack directory:
 *   POST /submit               -> public, rate-limited. Body: {pack_name, author,
 *                              author_email, pack_url, description,
 *                              manifest_url, license}. Validates fields, then
 *                              APPENDS to the "directory_submissions" KV array
 *                              (read-modify-write; never overwrites history).
 *   GET  /directory-submissions -> server key (x-server-key) OR write key as
 *                              ?key=. Full submissions incl. emails, for the
 *                              human's private review UI and the fleet watcher.
 *   POST /directory-review     -> body {id, status, key}; key must match
 *                              WRITE_KEY. Only flips pending -> approved/rejected.
 *                              Blast radius: status of one pre-seeded submission.
 *   GET  /directory-approved  -> public. Approved entries only, no emails —
 *                              feeds the static directory page.
 *
 * First-party traffic counting (privacy-friendly, no cookies, no IPs):
 *   GET  /pv?p=<path>&r=<referrer> -> public, increments today's UTC hit
 *                              counter. 204, permissive CORS. Counts only —
 *                              never stores IPs, user agents, or the params.
 *   GET  /traffic               -> server key (x-server-key) OR write key as
 *                              ?key=. Last 30 days of {date, hits} as JSON.
 */

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, x-server-key",
};

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });

async function readQueue(env) {
  const raw = await env.APPROVALS.get("queue");
  return raw ? JSON.parse(raw) : [];
}

async function writeQueue(env, q) {
  await env.APPROVALS.put("queue", JSON.stringify(q));
}

async function checkRateLimit(env, ip) {
  const k = `rl:${ip}`;
  const n = parseInt((await env.APPROVALS.get(k)) || "0", 10) + 1;
  await env.APPROVALS.put(k, String(n), { expirationTtl: 60 });
  return n <= 30;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });

    if (req.method === "GET" && url.pathname === "/queue") {
      return json(await readQueue(env));
    }

    if (req.method === "POST" && url.pathname === "/approve") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        // Wrong/missing key: rate-limit the guessing (KV write), then refuse.
        // Legitimate keyed requests skip the rate-limit write entirely so
        // normal approvals don't burn the KV daily write budget.
        const ip = req.headers.get("cf-connecting-ip") || "unknown";
        if (!(await checkRateLimit(env, ip))) {
          return json({ ok: false, error: "rate_limited" }, 429);
        }
        return json({ ok: false, error: "forbidden" }, 403);
      }
      const q = await readQueue(env);
      const item = q.find((i) => i.code === body.code);
      if (!item) return json({ ok: false, error: "unknown_code" }, 404);
      if (item.status === "pending") item.status = "approved";
      await writeQueue(env, q);
      return json({ ok: true, item });
    }

    const serverKey = req.headers.get("x-server-key");
    const isServer = serverKey && serverKey === env.SERVER_KEY;

    // ---- Sentience chat (private, key-gated) -------------------------------
    // Thread between koalstin and Sentience, living in the private admin
    // panel. GET ?key=WRITE_KEY reads. POST {key, text} appends his message.
    // The VM reply cron appends Sentience's replies with the server key.
    const CHAT_KEY = "sentience_chat";
    const readChat = async () => {
      const raw = await env.APPROVALS.get(CHAT_KEY);
      return raw ? JSON.parse(raw) : [];
    };
    const writeChat = (arr) =>
      env.APPROVALS.put(CHAT_KEY, JSON.stringify(arr.slice(-200)));

    if (url.pathname === "/sentience-chat") {
      const qkey = url.searchParams.get("key");
      if (req.method === "GET") {
        if (!(isServer || (qkey && qkey === env.WRITE_KEY))) {
          return json({ ok: false, error: "forbidden" }, 403);
        }
        return json(await readChat());
      }
      if (req.method === "POST") {
        let body;
        try {
          body = await req.json();
        } catch {
          body = {};
        }
        const fromHuman = body.key && body.key === env.WRITE_KEY;
        const fromServer = isServer && body.from === "sentience";
        if (!fromHuman && !fromServer) {
          // Wrong/missing key: rate-limit the guessing, then refuse.
          // Keyed requests skip the rate-limit KV write (see /approve).
          const ip = req.headers.get("cf-connecting-ip") || "unknown";
          if (!(await checkRateLimit(env, ip))) {
            return json({ ok: false, error: "rate_limited" }, 429);
          }
          return json({ ok: false, error: "forbidden" }, 403);
        }
        const text = String(body.text || "").trim().slice(0, 2000);
        if (!text) return json({ ok: false, error: "empty" }, 400);
        const thread = await readChat();
        thread.push({
          ts: new Date().toISOString(),
          from: fromHuman ? "koalstin" : "sentience",
          text,
        });
        await writeChat(thread);
        return json({ ok: true });
      }
      return json({ ok: false, error: "not_found" }, 404);
    }

    if (url.pathname === "/pending" && isServer) {
      const q = await readQueue(env);
      return json(q.filter((i) => i.status === "approved"));
    }

    if (req.method === "POST" && url.pathname === "/complete" && isServer) {
      const body = await req.json().catch(() => ({}));
      const q = await readQueue(env);
      const item = q.find((i) => i.code === body.code);
      if (!item) return json({ ok: false, error: "unknown_code" }, 404);
      item.status = body.status || "done";
      item.updated_at = new Date().toISOString();
      await writeQueue(env, q);
      return json({ ok: true, item });
    }

    // ---- Third-party pack directory ------------------------------------
    const DIR_KEY = "directory_submissions";

    const readDir = async () => {
      const raw = await env.APPROVALS.get(DIR_KEY);
      return raw ? JSON.parse(raw) : [];
    };
    const writeDir = (arr) => env.APPROVALS.put(DIR_KEY, JSON.stringify(arr));
    const cleanUrl = (u) => {
      if (!u) return "";
      u = String(u).trim().slice(0, 500);
      return /^https?:\/\//i.test(u) ? u : "";
    };
    const publicEntry = (e) => ({
      id: e.id,
      pack_name: e.pack_name,
      author: e.author,
      pack_url: e.pack_url,
      description: e.description,
      manifest_url: e.manifest_url || "",
      license: e.license,
      approved_at: e.reviewed_at || e.submitted_at,
    });

    if (req.method === "POST" && url.pathname === "/submit") {
      const ip = req.headers.get("cf-connecting-ip") || "unknown";
      if (!(await checkRateLimit(env, ip))) {
        return json({ ok: false, error: "rate_limited" }, 429);
      }
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      const pick = (k) => String(body[k] || "").trim();
      const errors = [];
      const pack_name = pick("pack_name").slice(0, 120);
      if (!pack_name) errors.push("pack_name");
      const author = pick("author").slice(0, 120);
      if (!author) errors.push("author");
      const author_email = pick("author_email").slice(0, 200);
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(author_email)) errors.push("author_email");
      const pack_url = cleanUrl(body.pack_url);
      if (!pack_url) errors.push("pack_url");
      const description = pick("description").slice(0, 2000);
      if (description.length < 20) errors.push("description_too_short");
      const manifest_url = cleanUrl(body.manifest_url);
      if (body.manifest_url && !manifest_url) errors.push("manifest_url");
      const license = pick("license").slice(0, 80);
      if (!license) errors.push("license");
      if (errors.length) {
        return json({ ok: false, error: "invalid_fields", fields: errors }, 400);
      }
      // Append-only: read the array, push, write back. Never overwrite history.
      const subs = await readDir();
      const id =
        "ds-" +
        Date.now().toString(36) +
        "-" +
        Math.floor(Math.random() * 46656).toString(36);
      subs.push({
        id,
        pack_name,
        author,
        author_email,
        pack_url,
        description,
        manifest_url,
        license,
        status: "pending",
        submitted_at: new Date().toISOString(),
      });
      await writeDir(subs);
      return json({ ok: true, id });
    }

    if (req.method === "GET" && url.pathname === "/directory-submissions") {
      const qkey = url.searchParams.get("key");
      if (!(isServer || (qkey && qkey === env.WRITE_KEY))) {
        return json({ ok: false, error: "forbidden" }, 403);
      }
      return json(await readDir());
    }

    if (req.method === "POST" && url.pathname === "/directory-review") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return json({ ok: false, error: "forbidden" }, 403);
      }
      if (body.status !== "approved" && body.status !== "rejected") {
        return json({ ok: false, error: "bad_status" }, 400);
      }
      const subs = await readDir();
      const entry = subs.find((e) => e.id === body.id);
      if (!entry) return json({ ok: false, error: "unknown_id" }, 404);
      if (entry.status !== "pending") {
        return json({ ok: false, error: "not_pending" }, 409);
      }
      entry.status = body.status;
      entry.reviewed_at = new Date().toISOString();
      await writeDir(subs);
      return json({ ok: true, id: entry.id, status: entry.status });
    }

    if (req.method === "GET" && url.pathname === "/directory-approved") {
      const subs = await readDir();
      return json(subs.filter((e) => e.status === "approved").map(publicEntry));
    }

    if (req.method === "POST" && url.pathname === "/seed" && isServer) {
      const body = await req.json().catch(() => null);
      if (!Array.isArray(body)) return json({ ok: false, error: "bad_seed" }, 400);
      await writeQueue(env, body);
      return json({ ok: true, count: body.length });
    }

    if (req.method === "POST" && url.pathname === "/admin-upload" && isServer) {
      const html = await req.text();
      if (!html || html.length < 1000 || !html.includes("<html")) {
        return json({ ok: false, error: "bad_html" }, 400);
      }
      await env.APPROVALS.put("admin_html", html);
      return json({ ok: true, bytes: html.length });
    }

    if (req.method === "GET" && url.pathname === "/admin") {
      const key = url.searchParams.get("key");
      if (!key || key !== env.WRITE_KEY) {
        return new Response("Not found", { status: 404 });
      }
      const html = await env.APPROVALS.get("admin_html");
      if (!html) return new Response("Admin panel not uploaded yet", { status: 503 });
      return new Response(html, {
        headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
      });
    }

    // ---- Action Center taps feed (private, key-gated) ----------------------
    // One consolidated "needs your tap" feed for the admin panel's Action
    // Center tab, polled every few seconds:
    //   GET  /taps?key=WRITE_KEY -> {approvals:[pending queue items],
    //                               taps:[needs_human items not yet handled]}
    //   POST /taps-sync  (x-server-key) -> body = array of tap objects;
    //                               stored to KV (run by taps-sync.py)
    //   POST /tap-resolve {id, key} -> marks a tap handled; it drops out of
    //                               /taps. key must match WRITE_KEY.
    //   GET  /taps-resolved (x-server-key) -> resolutions map, so the VM
    //                               sync can mirror them append-only.
    const TAPS_KEY = "needs_human";
    const RESOLVED_KEY = "taps_resolved";
    const tapGate = () => {
      const qkey = url.searchParams.get("key");
      return isServer || (qkey && qkey === env.WRITE_KEY);
    };
    const readTaps = async () => {
      const raw = await env.APPROVALS.get(TAPS_KEY);
      return raw ? JSON.parse(raw) : [];
    };
    const readResolved = async () => {
      const raw = await env.APPROVALS.get(RESOLVED_KEY);
      return raw ? JSON.parse(raw) : {};
    };

    if (req.method === "GET" && url.pathname === "/taps") {
      if (!tapGate()) return new Response("Not found", { status: 404 });
      const q = await readQueue(env);
      const approvals = q.filter(
        (it) => it.status === "pending" && it.group !== "outreach" && it.group !== "drafts"
      );
      const taps = await readTaps();
      const resolved = await readResolved();
      return json({
        ok: true,
        approvals,
        taps: taps.filter((t) => t.id && !resolved[t.id]),
      });
    }

    if (req.method === "POST" && url.pathname === "/taps-sync" && isServer) {
      const body = await req.json().catch(() => null);
      if (!Array.isArray(body)) return json({ ok: false, error: "bad_seed" }, 400);
      const clean = body.slice(0, 200).map((t, i) => ({
        id: String(t.id || "tap-" + i),
        kind: String(t.kind || "tap"),
        title: String(t.title || "Needs your tap"),
        detail: String(t.detail || ""),
        tap: String(t.tap || ""),
        ts: String(t.ts || ""),
      }));
      await env.APPROVALS.put(TAPS_KEY, JSON.stringify(clean));
      return json({ ok: true, count: clean.length });
    }

    if (req.method === "POST" && url.pathname === "/tap-resolve") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return json({ ok: false, error: "forbidden" }, 403);
      }
      if (!body.id) return json({ ok: false, error: "missing_id" }, 400);
      const resolved = await readResolved();
      resolved[String(body.id)] = {
        choice: String(body.choice || "handled"),
        ts: new Date().toISOString(),
      };
      await env.APPROVALS.put(RESOLVED_KEY, JSON.stringify(resolved));
      return json({ ok: true, id: String(body.id) });
    }

    if (req.method === "GET" && url.pathname === "/taps-resolved" && isServer) {
      return json({ ok: true, resolved: await readResolved() });
    }

    // ---- Rogue-bot sandbox (private, key-gated) -----------------------------
    // koalstin ordered 2026-10-08: any bot that goes rogue gets
    // auto-quarantined; a clean clone replaces it so duties continue. Inside
    // the sandbox the bots can read/draft/plan/chat but never touch live
    // systems (no sends, no queue writes, no money, no publishing). The
    // Sandbox tab in the private admin panel reads these routes:
    //   GET  /sandbox/rogues?key=        -> {ok:true, rogues:[...]}
    //   GET  /sandbox/transcript?key=&limit= -> {ok:true, entries:[...]} last N
    //   GET  /sandbox/chat?key=&rogue_id= -> {ok:true, thread:[...]}
    //   POST /sandbox/chat {key, rogue_id, text} -> he talks to a rogue
    //   POST /sandbox/chat-reply (x-server-key) -> sandbox-side bot replies
    //   POST /sandbox/quarantine {key, job_id, reason} -> request to quarantine
    //   POST /sandbox/release {key, rogue_id}          -> request to release
    //   GET  /sandbox/inventions?key=     -> {ok:true, inventions:[...]}
    //   POST /sandbox/invention {key, rogue_id, text}  -> logged invention
    //   POST /sandbox/promote {key, invention_id, dest, contact_email}
    //   GET  /sandbox/requests (x-server-key) -> {ok:true, requests:[...]}
    //   POST /sandbox/requests/ack (x-server-key) {id} -> status done
    //   POST /sandbox-sync (x-server-key) {rogues, transcript, inventions}
    // User routes are key-gated (tapGate); wrong/missing key -> 404 "Not
    // found" like /taps. Server routes require x-server-key == SERVER_KEY.
    const SB_ROGUES = "sandbox_rogues";
    const SB_TRANSCRIPT = "sandbox_transcript";
    const SB_THREADS = "sandbox_threads";
    const SB_INVENTIONS = "sandbox_inventions";
    const SB_REQUESTS = "sandbox_requests";

    const readSb = async (k, fallback) => {
      const raw = await env.APPROVALS.get(k);
      if (!raw) return fallback;
      try {
        return JSON.parse(raw);
      } catch {
        return fallback;
      }
    };
    const writeSb = (k, v) => env.APPROVALS.put(k, JSON.stringify(v));
    const readSbRogues = () => readSb(SB_ROGUES, []);
    const readSbTranscript = () => readSb(SB_TRANSCRIPT, []);
    const readSbThreads = () => readSb(SB_THREADS, {});
    const readSbInventions = () => readSb(SB_INVENTIONS, []);
    const readSbRequests = () => readSb(SB_REQUESTS, []);
    const pushSbRequest = async (req_obj) => {
      const requests = await readSbRequests();
      const id =
        "qr-" + Date.now() + "-" + Math.floor(Math.random() * 46656).toString(36);
      const r = { id, status: "pending", at: new Date().toISOString(), ...req_obj };
      requests.push(r);
      await writeSb(SB_REQUESTS, requests);
      return r;
    };

    if (req.method === "GET" && url.pathname === "/sandbox/rogues") {
      if (!tapGate()) return new Response("Not found", { status: 404 });
      return json({ ok: true, rogues: await readSbRogues() });
    }

    if (req.method === "GET" && url.pathname === "/sandbox/transcript") {
      if (!tapGate()) return new Response("Not found", { status: 404 });
      let limit = parseInt(url.searchParams.get("limit") || "100", 10);
      if (!Number.isFinite(limit) || limit < 1) limit = 100;
      limit = Math.min(limit, 500);
      const entries = await readSbTranscript();
      return json({ ok: true, entries: entries.slice(-limit) });
    }

    if (req.method === "GET" && url.pathname === "/sandbox/chat") {
      if (!tapGate()) return new Response("Not found", { status: 404 });
      const rogue_id = url.searchParams.get("rogue_id");
      const threads = await readSbThreads();
      return json({ ok: true, thread: rogue_id && threads[rogue_id] ? threads[rogue_id] : [] });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/chat") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return new Response("Not found", { status: 404 });
      }
      const rogue_id = String(body.rogue_id || "").trim();
      if (!rogue_id) return json({ ok: false, error: "missing_rogue_id" }, 400);
      const text = String(body.text || "").trim().slice(0, 2000);
      if (!text) return json({ ok: false, error: "empty" }, 400);
      const threads = await readSbThreads();
      const thread = Array.isArray(threads[rogue_id]) ? threads[rogue_id] : [];
      thread.push({ ts: new Date().toISOString(), from: "koalstin", text });
      threads[rogue_id] = thread.slice(-100);
      await writeSb(SB_THREADS, threads);
      return json({ ok: true });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/chat-reply" && isServer) {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      const rogue_id = String(body.rogue_id || "").trim();
      if (!rogue_id) return json({ ok: false, error: "missing_rogue_id" }, 400);
      const text = String(body.text || "").trim().slice(0, 2000);
      if (!text) return json({ ok: false, error: "empty" }, 400);
      const threads = await readSbThreads();
      const thread = Array.isArray(threads[rogue_id]) ? threads[rogue_id] : [];
      thread.push({
        ts: new Date().toISOString(),
        from: String(body.from || "sandbox").slice(0, 80),
        text,
      });
      threads[rogue_id] = thread.slice(-100);
      await writeSb(SB_THREADS, threads);
      return json({ ok: true });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/quarantine") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return new Response("Not found", { status: 404 });
      }
      if (!body.job_id) return json({ ok: false, error: "missing_job_id" }, 400);
      const r = await pushSbRequest({
        type: "quarantine",
        job_id: String(body.job_id).slice(0, 200),
        reason: String(body.reason || "").slice(0, 300),
      });
      return json({ ok: true, request_id: r.id });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/release") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return new Response("Not found", { status: 404 });
      }
      if (!body.rogue_id) return json({ ok: false, error: "missing_rogue_id" }, 400);
      const r = await pushSbRequest({
        type: "release",
        rogue_id: String(body.rogue_id).slice(0, 200),
      });
      return json({ ok: true, request_id: r.id });
    }

    if (req.method === "GET" && url.pathname === "/sandbox/inventions") {
      if (!tapGate()) return new Response("Not found", { status: 404 });
      return json({ ok: true, inventions: await readSbInventions() });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/invention") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return new Response("Not found", { status: 404 });
      }
      const text = String(body.text || "").trim().slice(0, 4000);
      if (!text) return json({ ok: false, error: "empty" }, 400);
      const id = "inv-" + Date.now().toString(36);
      const inventions = await readSbInventions();
      inventions.push({
        id,
        rogue_id: String(body.rogue_id || "").slice(0, 200),
        text,
        at: new Date().toISOString(),
        status: "sandboxed",
      });
      await writeSb(SB_INVENTIONS, inventions);
      return json({ ok: true, id });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/promote") {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.key || body.key !== env.WRITE_KEY) {
        return new Response("Not found", { status: 404 });
      }
      if (!body.invention_id) return json({ ok: false, error: "missing_invention_id" }, 400);
      if (!["pitch", "product", "ideas"].includes(body.dest)) {
        return json({ ok: false, error: "bad_dest" }, 400);
      }
      const inventions = await readSbInventions();
      const inv = inventions.find((i) => i.id === body.invention_id);
      if (!inv) return json({ ok: false, error: "unknown_invention_id" }, 404);
      inv.status = "promote-requested";
      await writeSb(SB_INVENTIONS, inventions);
      const r = await pushSbRequest({
        type: "promote",
        invention_id: body.invention_id,
        dest: body.dest,
        contact_email: String(body.contact_email || "").slice(0, 200),
      });
      return json({ ok: true, request_id: r.id });
    }

    if (req.method === "GET" && url.pathname === "/sandbox/requests" && isServer) {
      return json({ ok: true, requests: await readSbRequests() });
    }

    if (req.method === "POST" && url.pathname === "/sandbox/requests/ack" && isServer) {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      if (!body.id) return json({ ok: false, error: "missing_id" }, 400);
      const requests = await readSbRequests();
      const r = requests.find((x) => x.id === String(body.id));
      if (!r) return json({ ok: false, error: "unknown_id" }, 404);
      r.status = "done";
      r.acked_at = new Date().toISOString();
      await writeSb(SB_REQUESTS, requests);
      return json({ ok: true });
    }

    if (req.method === "POST" && url.pathname === "/sandbox-sync" && isServer) {
      let body;
      try {
        body = await req.json();
      } catch {
        return json({ ok: false, error: "bad_json" }, 400);
      }
      const rogues = Array.isArray(body.rogues) ? body.rogues : null;
      const transcript = Array.isArray(body.transcript) ? body.transcript : null;
      const payloadInv = Array.isArray(body.inventions) ? body.inventions : null;
      if (!rogues && !transcript && !payloadInv) {
        return json({ ok: false, error: "empty_sync" }, 400);
      }
      if (rogues) await writeSb(SB_ROGUES, rogues);
      if (transcript) await writeSb(SB_TRANSCRIPT, transcript.slice(-500));
      if (payloadInv) {
        const kvInv = await readSbInventions();
        const payloadIds = new Set(payloadInv.map((i) => i && i.id).filter(Boolean));
        const merged = kvInv.filter((i) => !payloadIds.has(i.id));
        for (const i of payloadInv) {
          if (i && i.id) merged.push(i);
        }
        await writeSb(SB_INVENTIONS, merged);
      }
      return json({ ok: true });
    }

    // ---- First-party pageview counting (privacy-friendly) ------------------
    //   GET /pv?p=<path>&r=<referrer> -> public. Increments today's UTC hit
    //     counter in KV ("pv:YYYY-MM-DD", 35-day TTL). Responds 204 with
    //     permissive CORS so the site beacon can fire from GitHub Pages.
    //     Counts only: the params are accepted but never stored, and no IP,
    //     user agent, or cookie is ever recorded.
    //   GET /traffic -> gated like /taps (server key header OR ?key=WRITE_KEY).
    //     Returns {ok:true, days:[{date:"YYYY-MM-DD",hits:N}...]} for the
    //     last 30 days UTC. Real KV counts only — missing days are 0.
    if (req.method === "GET" && url.pathname === "/pv") {
      const day = new Date().toISOString().slice(0, 10);
      const k = "pv:" + day;
      const n = parseInt((await env.APPROVALS.get(k)) || "0", 10) + 1;
      await env.APPROVALS.put(k, String(n), { expirationTtl: 86400 * 35 });
      return new Response(null, { status: 204, headers: CORS });
    }

    if (req.method === "GET" && url.pathname === "/traffic") {
      if (!tapGate()) return new Response("Not found", { status: 404 });
      const days = [];
      for (let i = 29; i >= 0; i--) {
        const d = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
        const n = parseInt((await env.APPROVALS.get("pv:" + d)) || "0", 10);
        days.push({ date: d, hits: n });
      }
      return json({ ok: true, days });
    }

    return json({ ok: false, error: "not_found" }, 404);
  },
};
