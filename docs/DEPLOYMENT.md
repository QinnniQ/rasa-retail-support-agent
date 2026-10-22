# Free portfolio deployment

The intended public address is `support.nickcloud.dev`. The public portfolio runs on Cloudflare Pages and its Pages Function, with a D1 database for fictional demo sessions and cases. It does **not** run Rasa Pro or the Python FastAPI service. The separate FastAPI and licensed Rasa path remain available for local use or a later hosted deployment.

## Cloudflare resources

- Pages project: `retail-support-agent-demo`, Git repository `QinnniQ/rasa-retail-support-agent`, production branch `main`.
- Root directory: `frontend`; build command: `npm ci && npm run build`; output directory: `dist`.
- D1 database: `retail-support-demo`, EU jurisdiction, bound as `DEMO_DB`. Its ID is in `frontend/wrangler.toml` and is not a credential.
- Encrypted Pages secret: `DEMO_RATE_SECRET`, a random 32-byte or longer value. Never put this in Git or a public build variable. Chat and case updates fail closed if it is missing.
- Custom domain: add `support.nickcloud.dev` through the Pages project's **Custom domains** workflow. Check that DNS targets the Pages project and that the certificate becomes active.
- Keep the Workers/Pages account on the **Free** plan. Do not opt into a paid plan. Free-plan limits stop function or D1 operations when exhausted; they do not create usage charges.

## Database initialization

The schema is versioned in `frontend/migrations/0001_public_demo.sql`. It contains only demo session state, generated case summaries, and short-lived rate-limit counters. No raw visitor message is stored in D1. The API removes records older than seven days on subsequent traffic. A long-idle database may still contain expired records until the next request; manual cleanup can be run if needed.

To apply later migrations with Wrangler from `frontend`, use `npx wrangler d1 migrations apply retail-support-demo --remote`. The first schema was also created in the Cloudflare SQL console during initial setup. Because the statements use `IF NOT EXISTS`, applying the versioned migration later is safe and will establish migration tracking.

## Public behavior and limits

The browser generates an unguessable session ID in session storage. The public Operations workspace shows and edits only cases in that browser session; assignments are stored as the fixed label `Demo medewerker`. A per-IP hourly limiter allows 40 chat or case-update requests, using an HMAC digest rather than a stored IP address. Chat input is limited to 1,000 characters and the page asks visitors not to enter personal data. There is no real retail handoff.

Cloudflare's current Workers Free quota includes 100,000 daily Function requests, while D1 includes 5 million rows read, 100,000 rows written per day, and 5 GB of total storage. These are shared account limits, and exceeding them makes the demo temporarily unavailable. Confirm current limits in the account before relying on them. [Pages Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/).

## Verification after publishing

1. Load the custom domain on desktop and mobile and confirm the address uses HTTPS.
2. Check `/api/status` returns `mode: demo`, `deployment: cloudflare`, and `case_store: ok`.
3. Choose **Ontbrekend artikel**, enter `KV-10482`, and confirm the fictional order and a case number appear.
4. Open Operations and confirm that case appears and can move to **In onderzoek**. A separate browser session must not see it.
5. Check that no Rasa server or FastAPI administrative endpoint is exposed, that Cloudflare remains on Free, and that Pages Functions and D1 usage remain comfortably below their limits.

## Optional hosted Python/Rasa path

If a licensed, genuine Rasa demo is desired later, run FastAPI, the action server, and Rasa on private container infrastructure with persistent storage and HTTPS. The Pages Function can instead proxy allowlisted `/api` calls to a hosted `API_ORIGIN`. That mode has hosting and licensing implications and is outside the zero-cost public portfolio deployment.
