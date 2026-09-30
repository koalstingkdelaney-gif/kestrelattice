/**
 * Kestrelattice approval backend — Cloudflare Worker + KV.
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
 * KV binding: APPROVALS (keys: "queue" -> JSON array, "admin_html" -> string).
 * Secrets (wrangler secret put): WRITE_KEY, SERVER_KEY.
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
      if (!body.key || body.key !== env.WRITE_KEY) {
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

    return json({ ok: false, error: "not_found" }, 404);
  },
};
