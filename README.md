# MovieBox Projects

The independent community hub for the published **Windows**, **Android patch**,
**Samsung Tizen TV** and **Android TV / Google TV** projects maintained by Emran Hossain.

[Website](https://emransm877.github.io/moviebox-projects/) ·
[Windows](https://github.com/emransm877/moviebox-desktop) ·
[Android patch](https://github.com/emransm877/moviebox-android) ·
[Samsung TV](https://github.com/emransm877/moviebox-tizen) · [Android TV](https://github.com/emransm877/moviebox-android-tv)

Only projects with published downloads and documented working scope are offered
as ready downloads. Android TV 0.1.0 is published with signed-artifact runtime
evidence. Apple work remains outside ready downloads. Device compatibility limits
are explicit on each page.

## Maintain the site

This is a buildless static site with Python metadata tooling:

```text
python tools/collect_downloads.py
python tools/build_site.py
python -m unittest test_download_analytics test_seo
python -m http.server 8090 --directory site
```

Open `http://localhost:8090/`. `tools/check_site.py` runs browser checks with the
pinned Playwright version in `.github/workflows/site.yml`. No app account,
signing key or GitHub token is sent to visitors' browsers.

## Live counts and historical observations

The eye badge is a separate [live browser presence counter](docs/LIVE_PRESENCE.md):
visible project pages send anonymous heartbeats to a small Worker/D1 service.
It counts browsers active in the last 90 seconds, shares IDs across tabs, and
shows a dash during outages. Automated/local QA and `?presence=off` are excluded.
It is not an exact count of people and does not affect GitHub download counters.
Backend source and SQLite tests are available in [services/presence](services/presence/).
The browser scenarios in `tools/check_presence.py` intercept the backend and never
send test traffic to production or download release files.

The page attempts automatic public GitHub count refreshes every 10 seconds while
visible and offers a manual refresh button. GitHub caches and public API limits
can delay updates. The page shows the actual verified time and any rate-limit
pause; it never claims that an old snapshot was just refreshed.

Hourly Actions snapshots retain an observation history for growth charts. Counts
measure file downloads, not people, installs or active users. Application-package
totals exclude checksums. TV bundles and raw widgets count as separate downloads.
Deleted assets retain their last observed peak in historical data. A newly added
platform's baseline is not counted as new daily growth. Daily data before tracking
started, or assets deleted before collection, cannot be reconstructed.

## SEO and ownership

The site has six unique canonical pages, relevant static content, breadcrumbs,
honest JSON-LD, social metadata, a 1200×630 social card and an XML sitemap. No
invented ratings, reviews or ranking guarantees are used. Project Pages hosts
this site under a path; the effective robots file is at the host root, not this
project's `/robots.txt`. A missing host-root robots file allows normal crawling.

To verify Google Search Console, add the **URL-prefix** property
`https://emransm877.github.io/moviebox-projects/`, choose HTML tag and add its public
verification value to `site/verification.json` under `google`. Never put account
passwords or login codes there. Regenerate, deploy, then verify and submit
`https://emransm877.github.io/moviebox-projects/sitemap.xml` through your own account.
The `bing` key accepts a public Bing verification value similarly.

Google's alternative HTML-file verification is also supported. The current
owner-provided file is `site/googledf06fecf9831794f.html`; keep its contents
unchanged and retain it after verification. The build leaves verification files
untouched. Click **Verify** in Search Console once this file is live, then submit
the sitemap above. Hosting the file alone does not confirm account verification
or indexing.

Every deployment runs `tools/check_live_seo.py` against the public site: five
HTTP-200 canonical pages, unique titles, indexability, sitemap URLs, a real 404,
the old URL's redirect/canonical, and the exact Google verification file bytes.
Its result is retained as the `live-seo-audit` Actions artifact. This is a
technical crawlability check, not an invented ranking score or a field Core Web
Vitals measurement.

Responsive WebP copies reduce screenshot transfer sizes while original captures
remain available. CSS and JavaScript URLs contain content fingerprints to avoid
mixing cached assets with updated pages. Regenerate image derivatives only when
original screenshots change using `python tools/prepare_web_images.py` with the
existing Playwright setup.

## Licensing and independence

Original hub code is MIT licensed. Names, logos, app screenshots and catalogue
artwork retain their respective owners' rights. Project-source licensing does
not grant rights to upstream applications or media. This is not affiliated with
MovieBox, Google, Microsoft or Samsung. No application release is published by
the website workflow.
