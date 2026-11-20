# MovieBox Projects

The independent community hub for the published **Windows**, **Android patch**
and **Samsung Tizen TV** projects maintained by Emran Hossain.

[Website](https://emransm877.github.io/moviebox-projects/) ·
[Windows](https://github.com/emransm877/moviebox-desktop) ·
[Android patch](https://github.com/emransm877/moviebox-android) ·
[Samsung TV](https://github.com/emransm877/moviebox-tizen)

Only projects with published downloads and documented working scope are offered
as ready downloads. Apple work and the new Android TV project remain development
work until verified. Device compatibility limits are explicit on each page.

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

The page attempts automatic public GitHub count refreshes every 10 seconds while
visible and offers a manual refresh button. GitHub caches and public API limits
can delay updates. The page shows the actual verified time and any rate-limit
pause; it never claims that an old snapshot was just refreshed.

Daily Actions snapshots retain an observation history for growth charts. Counts
measure file downloads, not people, installs or active users. Application-package
totals exclude checksums. TV bundles and raw widgets count as separate downloads.
Deleted assets retain their last observed peak in historical data. A newly added
platform's baseline is not counted as new daily growth. Daily data before tracking
started, or assets deleted before collection, cannot be reconstructed.

## SEO and ownership

The site has five unique canonical pages, relevant static content, breadcrumbs,
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

## Licensing and independence

Original hub code is MIT licensed. Names, logos, app screenshots and catalogue
artwork retain their respective owners' rights. Project-source licensing does
not grant rights to upstream applications or media. This is not affiliated with
MovieBox, Google, Microsoft or Samsung. No application release is published by
the website workflow.
