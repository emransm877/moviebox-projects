# Continue the Galaxy website on either computer

The current readable source and full design archive are in the maintainer's private
[moviebox-galaxy-build](https://github.com/emransm877/moviebox-galaxy-build) repository.
Both computers need access to that repository. Follow its
`release/README-HOME-WORK.md`, pull before editing, and run
`python release/build_all.py`. This public repository retains the finished `site/`
tree, the counter/history/service tools and the published `gh-pages` history.

`tools/build_site.py` is the earlier layout generator. It now refuses to overwrite
this Galaxy site. Do not remove that safeguard or publish an older computer's
unported layout. No automatic builder or publisher was added.

The public artifact contains minified web code without source maps. Private
builders, design catalogues and review evidence must not be copied into `site/`
or `gh-pages`. `.galaxy-source.json` identifies the reviewed source/build.

Counter requests still run in visitors' browsers, with dated saved/cache fallback
and rate-limit recovery. GitHub counts file requests, not people or installations.
Actions remains disabled; its hourly saved snapshot collector therefore does not
run. Local collection can update saved data/history when needed, preserving all
existing points and asset peaks. Running a collector is not permission to run the
legacy layout generator or publish unreviewed changes.

The existing disabled workflow still calls that legacy generator. Simply
reenabling it will stop at the safeguard; its build/publish path must be ported
and reviewed before any specifically authorized future Actions run.

Publishing stays explicit: fetch the current remote first, verify the exact
artifact, obtain independent review, commit the finished `site/` tree on `main`,
then create a `gh-pages` commit with that exact tree and the current published
commit as parent. Keep `.nojekyll`, do not force-push, and do not enable or run
Actions without the owner's explicit instruction. See `LOCAL_DEVELOPMENT.md`.
