# Worker deployment and required secrets

The Worker source now contains the private admin fleet chat and the buyer-gated Code Bot endpoints. Deploying source is separate from configuring provider credentials and uploading the private admin HTML.

## One-time setup

1. In GitHub repository Settings → Secrets and variables → Actions, add `CLOUDFLARE_API_TOKEN` with permission to deploy Workers to the account configured in `worker/wrangler.toml`.
2. In Cloudflare Workers & Pages → `kestrelattice-approvals` → Settings → Variables and Secrets, add these as **secrets**:
   - `GROQ_API_KEY` — required for both chat endpoints.
   - `GUMROAD_API_KEY` — seller API token used to check paid sales for Code Bot.
3. Ensure the existing `WRITE_KEY`, `SERVER_KEY`, and `APPROVALS` KV binding remain configured. Do not put credentials in tracked source or static public pages.
4. Configure Gumroad to generate a license key for each sale of each eligible code product.

## Deployment

Merging a change under `worker/` to `main` triggers `.github/workflows/deploy-worker.yml`. It validates JavaScript and Python syntax, then deploys with Wrangler. If `CLOUDFLARE_API_TOKEN` is missing, the workflow deliberately fails instead of claiming a deployment succeeded.

After deploy, upload the Code Bot product context to `POST /codebot-context` using the existing `SERVER_KEY` header. Only include eligible products and IDs/permalinks that match Gumroad's sales records. Do not upload an empty context as a placeholder; the endpoint replaces the previous catalog.

## Private admin panel

`build-admin.py` now includes the checked-in Bot Chat and Code Bot panel fragments. The private admin HTML is stored in Worker KV and is not automatically rebuilt by the public GitHub Pages deploy. Regenerate it in the trusted local workspace and upload it through the existing private admin upload path. Never publish the generated admin HTML to GitHub Pages.

## Checkout and autonomous spending

The existing product checkout remains Gumroad. Stripe is not activated by this change because no Stripe account configuration or API/webhook secrets are available in the repository. Do not switch checkout providers until the account, webhook signing secret, price/product mapping, refund behavior, and test-mode flow are configured. Autonomous reinvestment must remain disabled by default and have a hard owner-set budget cap; sales revenue is not permission for an agent to spend without a configured policy.

## Live verification checklist

- `GET /queue` responds without modifying the approval queue.
- `POST /chat` with a valid owner key returns a Groq reply; without the key it returns 403.
- `POST /codebot-verify` rejects invalid keys and verifies a real eligible Gumroad license only after context and secrets are configured.
- `POST /codebot-chat` requires an unexpired session token and enforces daily/monthly usage guards.
- A real test buyer/license is required before declaring Code Bot production-ready.
