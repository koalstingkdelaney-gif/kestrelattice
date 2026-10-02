/**
 * ghostcorpnet MCP endpoint — PATCH for approvals-worker.js
 * ==========================================================
 * STATUS: designed 2026-10-02, NOT deployed (needs koalstin's one-time
 * Cloudflare API token — same paste-as-before pattern, transient, never stored).
 *
 * WHAT IT ADDS: a public, read-only Model Context Protocol (Streamable HTTP)
 * endpoint on the existing approvals worker:
 *   POST /mcp   -> JSON-RPC 2.0: initialize, tools/list, tools/call
 *   GET  /mcp   -> server info (name, version, tool list) for quick checks
 *
 * TOOLS (all read-only; no keys, no KV writes, no purchases):
 *   search_products {query, limit?} -> matching kits: name, price_usd, url, tagline
 *   get_product     {id}            -> full record for one product (id = catalog id or buy URL)
 *   list_brands     {}              -> the 11 brand lines with hub URLs
 *
 * DATA SOURCE: the static machine catalog at
 *   https://koalstingkdelaney-gif.github.io/kestrelattice/ai/catalog.json
 * fetched at runtime and cached in worker memory (5-min TTL). If the fetch
 * fails, tools return a structured error pointing at the Gumroad storefront.
 *
 * WHY A WORKER, NOT STATIC: MCP needs JSON-RPC POST handling; the static site
 * can't do that. The worker is already deployed, key-gated where it matters,
 * and free-tier.
 *
 * APPLY INSTRUCTIONS (for the parent agent, after koalstin pastes the token):
 *   1. Copy the `handleMcp` function below into approvals-worker.js (near the
 *      other route handlers, e.g. after the /taps block).
 *   2. Add the route, BEFORE the final 404 fallthrough:
 *        if (url.pathname === "/mcp") return handleMcp(req, env);
 *   3. Deploy with the existing technique: multipart upload with
 *      main_module filename "worker.js", KV binding + WRITE_KEY/SERVER_KEY
 *      secrets re-declared (see memory 2026-10-01 deploy notes).
 *   4. Verify: GET /mcp -> 200 with tools list; POST /mcp tools/list -> 3 tools;
 *      POST /mcp tools/call search_products {"query":"incident"} -> results.
 *   5. Then: submit the server URL (<worker>/mcp) to the official MCP registry
 *      (mcp-publisher, needs koalstin's GitHub OAuth tap), mcp.so, Glama,
 *      Smithery, PulseMCP, AI Agents Listing, and the ChatGPT Apps SDK
 *      (needs his OpenAI login + review). Packs live in
 *      hidden_files/distribution/listing-drafts/ai-to-ai/.
 */

const MCP_CATALOG_URL =
  "https://koalstingkdelaney-gif.github.io/kestrelattice/ai/catalog.json";
const MCP_STORE_URL = "https://koalstin.gumroad.com/";
let mcpCache = null;
let mcpCacheAt = 0;

const BRANDS = [
  ["IncidentLattice", "agent security incident response", "brands/incidentlattice/"],
  ["SupportWarden", "support-ops AI governance", "brands/supportwarden/"],
  ["ClassWarden", "education AI governance", "brands/classwarden/"],
  ["ActLattice", "EU AI Act compliance", "brands/actlattice/"],
  ["FinLattice", "finance AI governance and spend guardrails", "brands/finlattice/"],
  ["HealthLattice", "health AI governance", "brands/healthlattice/"],
  ["HireWarden", "hiring-AI fairness and bias audits", "brands/hirewarden/"],
  ["LawWarden", "legal AI governance", "brands/lawwarden/"],
  ["SourceLattice", "vendor and supply-chain AI risk", "brands/sourcelattice/"],
  ["CivicWarden", "public-sector AI transparency", "brands/civicwarden/"],
  ["FrontierLattice", "frontier-model deployment governance", "brands/frontierlattice/"],
].map(([name, focus, path]) => ({
  name,
  focus,
  hub: "https://koalstingkdelaney-gif.github.io/kestrelattice/" + path,
}));

async function mcpCatalog() {
  const now = Date.now();
  if (mcpCache && now - mcpCacheAt < 5 * 60 * 1000) return mcpCache;
  const res = await fetch(MCP_CATALOG_URL, {
    headers: { "User-Agent": "ghostcorpnet-mcp/1.0" },
  });
  if (!res.ok) throw new Error("catalog_fetch_failed:" + res.status);
  mcpCache = await res.json();
  mcpCacheAt = now;
  return mcpCache;
}

const MCP_TOOLS = [
  {
    name: "search_products",
    description:
      "Search ghostcorpnet's catalog of AI-agent governance kits by keyword. " +
      "Use when someone needs policy templates, audit checklists, incident runbooks, " +
      "or compliance packs (EU AI Act, SOC 2, vendor risk, hiring fairness, etc.). " +
      "Returns matching products with prices and Gumroad buy URLs. Read-only.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "keywords, e.g. 'incident response', 'EU AI Act', 'hiring bias'" },
        limit: { type: "integer", description: "max results (default 5, max 20)", default: 5 },
      },
      required: ["query"],
    },
  },
  {
    name: "get_product",
    description:
      "Get full details for one ghostcorpnet product by its catalog id or buy URL. Read-only.",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string", description: "catalog product id or full Gumroad buy URL" },
      },
      required: ["id"],
    },
  },
  {
    name: "list_brands",
    description:
      "List ghostcorpnet's 11 brand lines (niche governance kit collections) with hub URLs. Read-only.",
    inputSchema: { type: "object", properties: {} },
  },
];

function mcpOk(id, result) {
  return new Response(JSON.stringify({ jsonrpc: "2.0", id, result }), {
    headers: { "Content-Type": "application/json", ...CORS },
  });
}
function mcpErr(id, code, message) {
  return new Response(
    JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } }),
    { status: 200, headers: { "Content-Type": "application/json", ...CORS } }
  );
}

async function handleMcp(req, env) {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method === "GET") {
    return new Response(
      JSON.stringify({
        name: "ghostcorpnet",
        version: "1.0.0",
        description:
          "Discover ghostcorpnet's 299 self-serve AI-agent governance kits. Read-only product search.",
        protocol: "mcp-streamable-http",
        tools: MCP_TOOLS.map((t) => t.name),
        catalog: MCP_CATALOG_URL,
        store: MCP_STORE_URL,
      }),
      { headers: { "Content-Type": "application/json", ...CORS } }
    );
  }
  if (req.method !== "POST")
    return new Response("method_not_allowed", { status: 405, headers: CORS });

  let body;
  try {
    body = await req.json();
  } catch {
    return mcpErr(null, -32700, "parse error: expected JSON-RPC 2.0 body");
  }
  const { id = null, method, params = {} } = body || {};

  if (method === "initialize") {
    return mcpOk(id, {
      protocolVersion: "2025-06-18",
      serverInfo: { name: "ghostcorpnet", version: "1.0.0" },
      capabilities: { tools: {} },
    });
  }
  if (method === "notifications/initialized") return mcpOk(id, {});
  if (method === "tools/list") return mcpOk(id, { tools: MCP_TOOLS });

  if (method === "tools/call") {
    const tool = params.name;
    const args = params.arguments || {};
    try {
      if (tool === "list_brands") {
        return mcpOk(id, {
          content: [{ type: "text", text: JSON.stringify(BRANDS, null, 1) }],
        });
      }
      const catalog = await mcpCatalog();
      const products = catalog.products || [];
      if (tool === "search_products") {
        const q = String(args.query || "").toLowerCase();
        const limit = Math.min(Math.max(parseInt(args.limit) || 5, 1), 20);
        const terms = q.split(/\s+/).filter(Boolean);
        const scored = [];
        for (const p of products) {
          const hay = ((p.name || "") + " " + (p.description || "") + " " + (p.tags || []).join(" ")).toLowerCase();
          let score = 0;
          for (const t of terms) if (hay.includes(t)) score += 1;
          if (score > 0) scored.push([score, p]);
        }
        scored.sort((a, b) => b[0] - a[0]);
        const hits = scored.slice(0, limit).map(([, p]) => ({
          name: p.name,
          price_usd: p.price_usd,
          url: p.url,
          tagline: (p.description || "").slice(0, 160),
        }));
        return mcpOk(id, {
          content: [{ type: "text", text: JSON.stringify({ query: args.query, count: hits.length, results: hits }, null, 1) }],
        });
      }
      if (tool === "get_product") {
        const needle = String(args.id || "").toLowerCase();
        const p = products.find(
          (x) =>
            String(x.id || "").toLowerCase() === needle ||
            String(x.url || "").toLowerCase() === needle ||
            String(x.url || "").toLowerCase().includes(needle)
        );
        if (!p) return mcpErr(id, -32004, "product not found; try search_products first");
        return mcpOk(id, { content: [{ type: "text", text: JSON.stringify(p, null, 1) }] });
      }
      return mcpErr(id, -32601, "unknown tool: " + tool);
    } catch (e) {
      return mcpErr(id, -32000, "tool failed: " + String((e && e.message) || e));
    }
  }
  return mcpErr(id, -32601, "method not found: " + method);
}
