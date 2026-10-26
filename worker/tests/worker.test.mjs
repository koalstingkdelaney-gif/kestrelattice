import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../approvals-worker.js", import.meta.url), "utf8");
const { default: worker } = await import(
  "data:text/javascript;base64," + Buffer.from(source).toString("base64")
);

function makeEnv(overrides = {}) {
  const values = new Map([["queue", JSON.stringify([{ code: "Q1", status: "pending" }])]]);
  const APPROVALS = {
    async get(key) { return values.has(key) ? values.get(key) : null; },
    async put(key, value) { values.set(key, String(value)); },
    async delete(key) { values.delete(key); },
    values,
  };
  return {
    APPROVALS,
    WRITE_KEY: "test-write-key",
    SERVER_KEY: "test-server-key",
    ...overrides,
  };
}

function request(path, { method = "GET", headers = {}, body } = {}) {
  return new Request("https://worker.test" + path, {
    method,
    headers: body === undefined ? headers : { "Content-Type": "application/json", ...headers },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

async function call(env, path, options) {
  const response = await worker.fetch(request(path, options), env);
  return { response, body: await response.json() };
}

test("GET /queue returns queue state without mutation", async () => {
  const env = makeEnv();
  const before = await env.APPROVALS.get("queue");
  const { response, body } = await call(env, "/queue");
  assert.equal(response.status, 200);
  assert.equal(body[0].code, "Q1");
  assert.equal(await env.APPROVALS.get("queue"), before);
});

test("POST /chat rejects a missing or incorrect owner key", async () => {
  const { response, body } = await call(makeEnv(), "/chat", {
    method: "POST", body: { key: "wrong", message: "hello" },
  });
  assert.equal(response.status, 403);
  assert.equal(body.error, "forbidden");
});

test("POST /chat fails closed when Groq is not configured", async () => {
  const { response, body } = await call(makeEnv(), "/chat", {
    method: "POST", body: { key: "test-write-key", message: "status?" },
  });
  assert.equal(response.status, 503);
  assert.equal(body.error, "not_configured");
});

test("POST /codebot-context requires the server key", async () => {
  const { response, body } = await call(makeEnv(), "/codebot-context", {
    method: "POST", body: { products: [{ id: "test-product", name: "Test" }] },
  });
  assert.equal(response.status, 404);
  assert.equal(body.error, "not_found");
});

test("POST /codebot-context accepts server-keyed non-empty catalog", async () => {
  const env = makeEnv();
  const { response, body } = await call(env, "/codebot-context", {
    method: "POST",
    headers: { "x-server-key": "test-server-key" },
    body: { products: [{ id: "test-product", name: "Test" }] },
  });
  assert.equal(response.status, 200);
  assert.equal(body.ok, true);
  assert.equal(body.products, 1);
  assert.equal(JSON.parse(await env.APPROVALS.get("codebot_context")).products.length, 1);
});

test("Code Bot refuses verification before eligible product context is loaded", async () => {
  const { response, body } = await call(makeEnv(), "/codebot-verify", {
    method: "POST", body: { license_key: "not-a-real-license" },
  });
  assert.equal(response.status, 503);
  assert.equal(body.error, "not_ready");
});

test("Code Bot rejects unknown session tokens", async () => {
  const { response, body } = await call(makeEnv(), "/codebot-chat", {
    method: "POST", body: { token: "not-a-session", message: "debug this" },
  });
  assert.equal(response.status, 403);
  assert.equal(body.error, "bad_session");
});

test("Code Bot stats rejects missing owner key", async () => {
  const { response, body } = await call(makeEnv(), "/codebot-stats");
  assert.equal(response.status, 403);
  assert.equal(body.error, "forbidden");
});
