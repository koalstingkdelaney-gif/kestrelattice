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
