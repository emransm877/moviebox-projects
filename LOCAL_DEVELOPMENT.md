# Local development

Clone this repository and work from its root. Development checks run locally by default; GitHub remains the source host and retains necessary production automation.

## Environment

Run `python tools/local_doctor.py` (`python3` on systems where that is the Python 3 command). This read-only preflight detects the host and basic tools; it does not install dependencies or certify a build. Use the project's supported runtime versions below and existing lockfiles. Do not upgrade dependencies just to run checks.

For Python, create an isolated environment with `python -m venv .venv`. Use `.venv/Scripts/python.exe` on Windows and `.venv/bin/python` on Linux/macOS for installation and checks (activation is optional). Replace `python` below with that interpreter. Existing pinned requirements remain authoritative. Where requirements contain ranges, exact historical dependency resolution is not guaranteed; record a tested lock separately before upgrading.

For Node projects with package-lock.json use `npm ci`; without a lockfile use `npm install` and review the generated lock before committing. Use the declared packageManager if present. Native SDKs and first dependency downloads need internet access. Local-first does not make external APIs or production services offline.

## Repository commands

Use Python 3.12, Node 24, and Playwright 1.65.1 for browser checks. Run `python -m pip install playwright==1.65.1` then `python -m playwright install chromium` (Linux may additionally need `python -m playwright install-deps chromium`). Run `python tools/build_site.py`, `python -m unittest test_download_analytics test_seo test_release_info`, and `node --test services/presence/test/presence.test.mjs`. Run the remaining browser checks recorded below before changing site behavior. Preview with `python -m http.server 8090 --directory site`. The existing hourly workflow is retained in source, but repository Actions is currently disabled: hosted collection and checks do not run. Keep existing observation history. Local collection can refresh snapshots before publishing; never reset historic counters.

## Existing hosted command reference

These are the pre-migration commands for reproducing checks locally. Use the correct host shell (PowerShell paths on Windows, Bash on Unix); install requirements from the workflow. Publishing commands are intentionally excluded.

### site.yml / verify

```text
python -m pip install playwright==1.65.1
python -m playwright install --with-deps chromium
python tools/build_site.py
python -m unittest test_download_analytics test_seo test_release_info
python tools/check_site.py
python tools/check_release_info.py
python tools/check_native_project.py
python tools/check_cinema.py
node --test services/presence/test/presence.test.mjs
python tools/check_presence.py
python tools/check_usage.py
python tools/check_client_recovery.py
python tools/check_tally_recovery.py
```


## Automation and releases

Development workflows are manual fallbacks; select Run workflow in GitHub only when local execution is impractical. Retained production workflows keep their existing triggers and approval gates. Existing release downloads are unaffected by changing development triggers. Manual workflow artifacts expire after the retention shown in each workflow and are not durable release downloads.

Before pushing a workflow change, inspect current branch protection/rulesets and preserve required check names or coordinate their replacement. A manual workflow does not automatically satisfy required PR checks. Never weaken protection merely to make a push pass.

Rollback: inspect the migration commit with `git show <migration-commit>`, then `git revert <migration-commit>` and push under normal repository policy. Reverting automatic triggers may start cloud jobs; review the resulting diff first. Avoid reverting later production state or historical statistics. Account billing and Actions permissions were not changed.

For a new project, choose its existing/native tooling, record supported runtime versions, commit an appropriate dependency lock and environment example without secrets, define local validation commands and platform limits, and classify any proposed cloud automation before adding it. Do not copy an unrelated stack's build script.

## Direct static Pages publishing

The owner prefers local builds, tests and Agency reviews. The current live Pages
source is `gh-pages` at `/`, with `.nojekyll` present. Actions stays disabled.
Source development stays on `main`; pushing `main` alone does not publish the site.

After local checks pass, commit the finished `site/` changes to `main`. Publish a
new artifact commit whose parent is the current `origin/gh-pages` and whose tree
is exactly the committed `site/` tree. This retains publishing history and avoids
force-pushing an unrelated subtree history:

```text
git fetch origin gh-pages
git rev-parse HEAD:site
git rev-parse origin/gh-pages
git commit-tree <site-tree-from-first-rev-parse> -p <published-commit-from-second-rev-parse> -m "Publish locally verified website"
git push origin <new-commit-from-commit-tree>:refs/heads/gh-pages
```

Replace the angle-bracket values with the actual command output. `HEAD` must be
the reviewed source commit containing the built static files. Confirm `.nojekyll`
is in that tree. Inspect remote publication changes before pushing; if the remote
advances, fetch and prepare a new commit against it. Never force-push. A separate
publishing worktree with ordinary commits is also suitable if it preserves the
`.git` worktree pointer and uses exactly the reviewed generated files.
Changing hosting configuration is not a routine per-release step.
The one-time Pages source selection is Settings > Pages > Deploy from a branch >
`gh-pages` > `/ (root)`. It is already configured for this repository.

GitHub Pages can deploy this prebuilt content directly while Actions is disabled;
see [GitHub's publishing documentation](https://github.blog/changelog/2024-07-08-pages-legacy-worker-sunset/).
The GitHub Pages hosting service still performs publication; `.nojekyll` avoids the
Jekyll build. This does not run the project's Actions workflow.

After publication, verify the actual live page, key downloads links, Tally and
Google verification file. Run `python tools/check_live_seo.py --output local-live-seo.json`
locally. Do not download application packages just to verify links. Keep generated
reports, credentials and machine-specific files out of git.

Public browser count polling remains active. With Actions disabled, the existing
hourly snapshot schedule is inactive; run the collector locally when fresh stored
observations are needed, preserving history. Never silently enable a workflow to
restore that schedule.
