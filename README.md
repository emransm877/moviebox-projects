# MovieBox Projects

The independent community hub for the published **Windows**, **Android app**, **Android patch**,
**Samsung Tizen TV** and **Android TV / Google TV** projects maintained by Emran Hossain.

[Website](https://emransm877.github.io/moviebox-projects/) ·
[Windows](https://github.com/emransm877/moviebox-desktop) ·
[Android app](https://github.com/emransm877/moviebox-android-native) ·
[Android patch](https://github.com/emransm877/moviebox-android) ·
[Samsung TV](https://github.com/emransm877/moviebox-tizen) · [Android TV](https://github.com/emransm877/moviebox-android-tv)

## Download the apps

**This repository hosts the website, not the app installers.** Its Releases list
is empty because each app publishes its installation files in its own repository.
Choose your device below, or use the [download website](https://emransm877.github.io/moviebox-projects/).

| Your device / project | Current version | Installation files |
| --- | --- | --- |
| Windows PC | 0.10.4 | [Setup EXE and portable ZIP](https://github.com/emransm877/moviebox-desktop/releases/tag/v0.10.4) |
| Android phone — native app | 0.1.1 | [Android App APK](https://github.com/emransm877/moviebox-android-native/releases/tag/v0.1.1) |
| Android phone — separate patch | 0.2.0 | [Android patch APK](https://github.com/emransm877/moviebox-android/releases/tag/v0.2.0) |
| Samsung Tizen TV | 0.9.3 | [TV installation bundle](https://github.com/emransm877/moviebox-tizen/releases/tag/v0.9.3) |
| Android TV / Google TV | 0.2.0 | [Android TV APK](https://github.com/emransm877/moviebox-android-tv/releases/tag/v0.2.0) |

The native Android app and Android patch are separate installations with separate
saved lists. Check each project's installation guide and compatibility notes.

The native Android App **0.1.1** reliability update is published. It adds library backup/recovery, Wi-Fi-first downloads with per-file mobile-data consent, bounded subtitle storage and more reliable optional reminders. Its exact release APK passed 131 scoped phone scenarios and 29 unit tests on one Android 17 phone; broader device compatibility remains unverified. [Release, APK and checksum](https://github.com/emransm877/moviebox-android-native/releases/tag/v0.1.1).

Only projects with published downloads and documented working scope are offered
as ready downloads. Android TV has a published APK with bounded runtime
evidence. The native **MovieBox Android App** is a separate project and does not replace
the Android patch. Its complete 0.1.0 APK is published in
`emransm877/moviebox-android-native`; all five projects have separate downloads
and installation guides. Publication gating still excludes an incomplete or
preview-only native APK from ready downloads and the sitemap. Apple work remains outside ready downloads. Device compatibility limits
are explicit on each page.

## Website design

The cinema theme follows the supplied d08 reference: a responsive title screen,
download tickets, genuine application captures and the simple Tally total with
five colored bars. The Tally uses actual GitHub counters across all releases;
file requests are not people or installs. Detailed chart filters, observation
history and release pagination remain under **Download history and releases**.

Desktop smoke rendering adapts to performance and pauses offscreen. Phones,
coarse pointers, reduced-motion settings, weak devices and software renderers use
a lightweight static background. Download links and installation guides work
without JavaScript. The guides share the theme, with readable document layouts.

## Maintain the site

This is a buildless static site with Python metadata tooling:

```text
python tools/collect_downloads.py
python tools/build_site.py
python -m unittest test_download_analytics test_seo test_release_info
python -m http.server 8090 --directory site
```

Open `http://localhost:8090/`. `tools/check_site.py` runs browser checks with the
pinned Playwright version in `.github/workflows/site.yml`. No app account,
signing key or GitHub token is sent to visitors' browsers. Recovery checks in
`tools/check_client_recovery.py` mock all external services and verify failed or
expired optional-usage sessions, short retries after ordinary API failures, and
GitHub rate-limit pauses. They never download application release files.

## Release information

`release-plan.json` records the next coordinated Windows, Samsung TV and Android
TV versions. It is a maintainer plan, not proof of a published download. Public
buttons only select a non-preview release whose full required package set appears
in the collected GitHub metadata. The same policy drives desktop cards, mobile
download buttons and generated installation guides. Incomplete uploads retain
the previous complete release instead of mixing installer/ZIP versions.

Historical release IDs and asset counters stay unchanged. Their presentation is
cleaned for visitors: `v0.10.3-selfsigned.1` appears as `0.10.3 - Preview 1`, while
links and version filters keep the exact underlying tag. Technical Windows signing
facts remain in the linked desktop signing policy; a short label is not a claim of
public certificate trust.

After each approved release is fully uploaded, run the collector and site builder
above. Verify the new download set and release notes before deploying. The current
native phone APK is never substituted for the published patch. `tools/check_native_project.py`
checks the five-project publication state at mobile, tablet and desktop widths,
using synthetic metadata without fetching any release assets. New platform history
begins with its first real observation; earlier points are not backfilled with zero.

`site/assets/screenshots.json` records genuine captures, device scope, source
dimensions and SHA-256 hashes. The builder chooses a capture no newer than the
published release; Windows 0.10.4 and Samsung 0.9.3 captures therefore activate
with those actual releases. Android TV captions identify emulator captures.

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
visible. GitHub caches and public API limits can delay updates; the last verified
numbers remain available during an outage. The collector timestamp is retained
in the public data, without a misleading manual-refresh control.

The retained data includes earlier observation history. GitHub Actions is currently
disabled; hourly hosted collection is paused. Local collection can update snapshots
before publishing. The homepage no longer includes the history disclosure. Counts
measure file downloads, not people, installs or active users. Application-package
totals exclude checksums. TV bundles and raw widgets count as separate downloads.
Deleted assets retain their last observed peak in historical data. A newly added
platform's baseline is not counted as new daily growth. Daily data before tracking
started, or assets deleted before collection, cannot be reconstructed.

## SEO and ownership

The site has seven core canonical pages, relevant static content, breadcrumbs,
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

After publishing, run `python tools/check_live_seo.py` locally against the public site: all published
HTTP-200 canonical pages, unique titles, indexability, sitemap URLs, a real 404,
the old URL's redirect/canonical, and the exact Google verification file bytes.
Save its result locally with `--output`; historical runs also have
`live-seo-audit` Actions artifacts. This is a
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

## Publishing without GitHub Actions

Build, test and obtain Agency review locally. The live site publishes prebuilt
static files from the `gh-pages` branch root with `.nojekyll`. The website address
is unchanged. Repository Actions remains disabled. See
[the local publishing instructions](LOCAL_DEVELOPMENT.md#direct-static-pages-publishing).
Do not enable or trigger Actions without the owner's explicit confirmation.
