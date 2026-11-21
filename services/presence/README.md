# MovieBox Live Presence

Small presence service for https://emransm877.github.io/moviebox-projects/.
Counts browser sessions with a heartbeat in the last 90 seconds, not lifetime visitors or unique people. Random IDs are shared between tabs; no names, emails or IP addresses are written by this application. Hosting providers still process normal HTTP requests.

The browser obtains a short-lived HMAC-signed session from the allowed origin. The server validates that token before renewing a presence row. IDs expire from counts after 90 seconds and expired rows are deleted on the next heartbeat/count request. No visit history is kept.

Origins, bounded input, token expiry/signatures and SQL binding are enforced. Anonymous endpoints are not proof of human identity; a determined client can simulate activity. Do not present this as an exact human headcount.

Runtime: Cloudflare Worker + D1, deployed through Sites. `PRESENCE_SECRET` is a server-only secret in Sites, never in source or the browser. Schema-only SQL migrations live under `drizzle/`.

This directory mirrors the deployed Worker, schema and tests for public review. Hosting configuration and the secret are managed separately by Sites. To test from this directory, run `node --test test/presence.test.mjs` (Node 24+ with `node:sqlite`). The tests use a real local SQLite database and do not contact production or download application releases. From the repository root, run `node --test services/presence/test/presence.test.mjs`.
