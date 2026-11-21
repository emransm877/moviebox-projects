# Optional anonymous usage counts

The footer's **Usage statistics** control lets a visitor allow or turn off optional page-view and download-click counting. The default is off. This is separate from the eye badge's short-lived live presence count. Global Privacy Control and Do Not Track keep optional measurement off. Automated checks and `?presence=off` are excluded.

Only daily aggregate counters are stored: project page, source (`facebook`, `direct` or `other`), allowlisted public post code, event type and platform. No analytics browser identifier, name, email, IP address, full URL, raw referrer or token is stored in the aggregate database. The browser stores its yes/no preference locally and, only when opted in, keeps broad campaign context in the current tab for up to 30 minutes. An ephemeral signing ID/token exists in page memory to validate event submissions; it is not saved in analytics rows or reused as a cross-page analytics identifier. Hosting providers process ordinary HTTP traffic.

Aggregates are retained for up to 90 days and old rows are removed on subsequent event writes. Aggregate summaries are publicly readable at the existing service's `/api/usage-summary?days=7` endpoint with the site's exact Origin header. The window supports 1–30 days in Bangladesh time. No past data is reconstructed. A failed request is unavailable, not a made-up zero.

These are **event requests from consenting browsers**, not unique people, completed downloads or installations. Reloads and repeated clicks can count again. Blockers, non-consent, unavailable networks and leaving the page before transmission can omit events. Anonymous endpoints are not proof of human activity and a determined client can simulate requests. GitHub release counters remain a different measurement and are never altered by this feature.

Tracked Facebook links use UTMs before any fragment. Only source and an allowlisted public post code are retained; arbitrary query values and private information are discarded. Internal navigation retains the broad campaign context in the opted-in tab without modifying release URLs.

No Meta Pixel, advertising SDK, new paid analytics service or third-party analytics cookie is installed. The private marketing report reads aggregate evidence; it does not infer an installation from a visit or click.
