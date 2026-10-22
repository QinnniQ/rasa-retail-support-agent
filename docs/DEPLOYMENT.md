# Deployment preparation

No deployment, DNS, or Cloudflare account settings were changed by this project.

The React build is static. Cloudflare Pages can serve `frontend/dist`; its Pages Function in `frontend/functions/api/[[path]].js` proxies a small `/api` route allowlist to a separately hosted **HTTPS** FastAPI origin configured as `API_ORIGIN`. It does not forward `/orders`, `/internal`, or Rasa administrative routes. The function does not contain an origin or credential in source code. The API, SQLite data, and optional Rasa stack must run on infrastructure that supports Python containers and persistent storage. Do not point Pages at a laptop localhost URL.

For a future Pages project: set root directory `frontend`, build command `npm ci && npm run build`, output `dist`, and configure `API_ORIGIN` for preview and production only after an HTTPS API is live. `frontend/wrangler.toml` describes the build output; review it against actual Cloudflare project settings before deployment. Route a proposed `support.nickcloud.dev` subdomain only after owner approval and DNS verification.

Before making the service public: replace the local operations token with identity and roles, require TLS end to end, add rate limits to chat and case APIs, protect the API origin from direct abuse, set retention/deletion rules, add audit and availability monitoring, move from a local SQLite volume to managed persistence if replicas are needed, and test with consented data and current policy. Do not publish a Rasa Pro runtime or its administrative endpoint without a licensed, private deployment plan.

References checked 22 October 2026: [Cloudflare Pages build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/), [Pages Function routes](https://developers.cloudflare.com/pages/functions/routing/), and [Wrangler configuration](https://developers.cloudflare.com/pages/functions/wrangler-configuration/).
