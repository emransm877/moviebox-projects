# MovieBox Live Presence

Small presence service for https://emransm877.github.io/moviebox-projects/.
Counts browser sessions with a heartbeat in the last 90 seconds, not lifetime visitors or unique people. Random IDs are shared between tabs; no names, emails or IP addresses are written by this application. Hosting providers still process normal HTTP requests.

The browser obtains a short-lived HMAC-signed session from the allowed origin. The server validates that token before renewing a presence row. IDs expire from counts after 90 seconds and expired rows are deleted on the next heartbeat/count request. Presence keeps no visit history.

Optional usage counting is a separate feature, off until a browser opts in through the website's Usage statistics control. `/api/usage` accepts only explicit-consent, signed, allowlisted page-view/download-click events. It stores daily aggregate counts by project page, broad referral source, public post code and platform; no browser IDs, tokens, IP addresses, full URLs or personal information are stored in this table. A separate ephemeral signing ID is generated in page memory, without renewing presence. Aggregates expire after 90 days on subsequent event writes. `/api/usage-summary?days=7` exposes only aggregate counters, with a 1–30 day query window and an exact Origin requirement. Anonymous public endpoints can be simulated; these are event requests from consenting browsers, not unique people or proof of completed downloads/installs. The frontend respects DNT/GPC and never retries uncertain events. Hosting providers still process normal HTTP requests.

Origins, bounded input, token expiry/signatures and SQL binding are enforced. Anonymous endpoints are not proof of human identity; a determined client can simulate activity. Do not present this as an exact human headcount.

Runtime: Cloudflare Worker + D1, deployed through Sites. `PRESENCE_SECRET` is a server-only secret in Sites, never in source or the browser. Schema-only SQL migrations live under `drizzle/`.

Build: `node scripts/build.mjs`. Test: `node --test test/presence.test.mjs` (Node 24+ with `node:sqlite`). The tests use a real local SQLite database and do not contact production or download application releases.
