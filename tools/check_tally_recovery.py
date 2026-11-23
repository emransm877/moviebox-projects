"""Browser regressions for real observations surviving reload and API outages.

Every request is mocked or blocked: no production telemetry or app downloads.
The retired analytics component is mounted only in this regression fixture.
"""
import copy
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from history_fixture import with_history

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
BASE = 'https://emransm877.github.io/moviebox-projects/'
ORIGINAL = json.loads((SITE / 'data/latest.json').read_text(encoding='utf-8'))
BASE_TIME = datetime.fromisoformat(ORIGINAL['observedAt']).astimezone(timezone.utc)
NOW = int((BASE_TIME + timedelta(hours=1)).timestamp() * 1000)
CACHE = 'moviebox.downloads.snapshot.v1'
MODE = 'moviebox.downloads.mode.v1'
RETRY = 'moviebox.downloads.retry.v1'
KINDS = ('apk', 'installer', 'portable', 'tv_bundle', 'tv_widget', 'checksums', 'other')
PACKAGES = KINDS[:5]
checks = {}
downloads = []


def snapshot(total, milliseconds):
    value = copy.deepcopy(ORIGINAL)
    value['observedAt'] = datetime.fromtimestamp(milliseconds / 1000, timezone.utc).isoformat()
    # Reuse genuine release identities/URLs, never growing production counters.
    # This keeps the regression valid when the real project reaches millions.
    for record in value['repositories']:
        for release in record['releases']:
            for asset in release['assets']:
                asset['count'] = 1 if asset['kind'] == 'checksums' else 0
    record = next(record for record in value['repositories'] if record['name'] == 'moviebox-android')
    asset = next(asset for release in record['releases'] for asset in release['assets'] if asset['kind'] == 'apk')
    asset['count'] = total
    for record in value['repositories']:
        record['kinds'] = {kind: sum(asset['count'] for release in record['releases'] for asset in release['assets'] if asset['kind'] == kind) for kind in KINDS}
        record['packages'] = sum(record['kinds'][kind] for kind in PACKAGES)
        record['allAssets'] = sum(record['kinds'].values())
    return value


HISTORY = {'schemaVersion': 1, 'points': [
    {'at': observed['observedAt'], 'packages': {repo['name']: repo['packages'] for repo in observed['repositories']}}
    for observed in [snapshot(900, NOW - 7200000), snapshot(999, NOW - 3600000)]
]}


def fixture(browser, cache=None, mode=None, blocked=False, api_status=403):
    state = {'disk': snapshot(999, NOW - 3600000), 'live': snapshot(1106, NOW),
             'api_status': api_status, 'api_calls': 0, 'disk_calls': 0}
    context = browser.new_context(reduced_motion='reduce', viewport={'width': 1100, 'height': 850})
    # A single context survives page reload, exactly as the owner's browser does.
    if cache is not None or mode is not None:
        seed = {'snapshot': cache, 'mode': mode}
        context.add_init_script('''(() => {if (!localStorage.getItem('tally-fixture-seeded')) {
          const seed = %s;
          if (seed.snapshot !== null) localStorage.setItem('%s', JSON.stringify(seed.snapshot));
          if (seed.mode !== null) localStorage.setItem('%s', seed.mode);
          localStorage.setItem('tally-fixture-seeded', 'yes');
        }})();''' % (json.dumps(seed), CACHE, MODE))
    if blocked:
        context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Storage blocked','SecurityError')}});")

    def route(request):
        url = urlsplit(request.request.url)
        if url.hostname == 'github.com' and '/releases/download/' in url.path:
            downloads.append(request.request.url)
            request.abort()
            return
        if request.request.url.startswith('https://api.github.com/'):
            state['api_calls'] += 1
            if state['api_status']:
                headers = {'x-ratelimit-remaining': '0', 'x-ratelimit-reset': str((NOW + 1800000) // 1000)}
                request.fulfill(status=state['api_status'], headers=headers, content_type='application/json', body='{}')
                return
            parts = url.path.split('/')
            repo = next(record for record in state['live']['repositories'] if record['name'] == parts[3])
            if parts[-1] == 'latest':
                payload = {'tag_name': repo['latestTag']}
            else:
                payload = [{'id': index + 1, 'tag_name': release['tag'], 'html_url': release['url'],
                            'published_at': release['publishedAt'], 'draft': False, 'prerelease': release['prerelease'],
                            'assets': [{'id': asset['id'], 'name': asset['name'], 'download_count': asset['count'],
                                        'browser_download_url': asset['url'], 'size': asset['size'],
                                        'created_at': asset['createdAt'], 'digest': asset.get('digest')}
                                       for asset in release['assets']]}
                           for index, release in enumerate(repo['releases'])]
            request.fulfill(content_type='application/json', body=json.dumps(payload))
            return
        if request.request.url.startswith(BASE):
            relative = url.path.removeprefix('/moviebox-projects/')
            if relative == 'data/latest.json':
                state['disk_calls'] += 1
                request.fulfill(content_type='application/json', body=json.dumps(state['disk']))
            elif relative == 'data/history.json':
                request.fulfill(content_type='application/json', body=json.dumps(HISTORY))
            else:
                path = (SITE / (relative or 'index.html')).resolve()
                if path.is_dir():
                    path /= 'index.html'
                assert path.is_relative_to(SITE.resolve())
                request.fulfill(status=200 if path.is_file() else 404,
                                content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream',
                                body=with_history(path.read_bytes()) if path == SITE / 'index.html' else path.read_bytes() if path.is_file() else b'missing')
            return
        request.abort()

    context.route('**/*', route)
    page = context.new_page()
    # Playwright numeric ``time`` is seconds; use an explicit UTC datetime so
    # cache future-date and rate-reset checks exercise real 2026 timestamps.
    page.clock.install(time=datetime.fromtimestamp(NOW / 1000, timezone.utc))
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE + '?presence=off')
    return context, page, state, errors


def expect_count(page, count):
    page.wait_for_function("expected => document.getElementById('combined-count').textContent.replace(/,/g,'') === String(expected)", arg=count)


def settle(page):
    page.wait_for_function("document.getElementById('analytics').dataset.refreshState === 'unavailable'")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None, headless=True)

    # The reported failure: a successful newer result must survive refresh while
    # the remote API rejects the next request. All-files mode is a separate total.
    context, page, state, errors = fixture(browser, api_status=0)
    expect_count(page, 1106)
    saved = page.evaluate('(key) => JSON.parse(localStorage.getItem(key))', CACHE)
    assert sum(repo['packages'] for repo in saved['repositories']) == 1106
    state['api_status'] = 403
    page.reload(); expect_count(page, 1106); settle(page)
    calls = state['api_calls']
    page.locator('#count-mode').select_option('all', force=True)
    expected_all = sum(repo['allAssets'] for repo in state['live']['repositories'])
    expect_count(page, expected_all)
    page.reload(); settle(page); expect_count(page, expected_all)
    assert page.locator('#count-mode').input_value() == 'all'
    assert 'Release-file downloads' in page.locator('#combined-label').inner_text()
    assert state['api_calls'] == calls, 'Reload ignored server retry deadline'
    page.clock.fast_forward(20000)
    assert state['api_calls'] == calls, 'Ten-second refresh ignored server retry deadline'
    checks['live_reload_rate_limit_and_mode'] = True
    state['api_status'] = 0
    page.clock.fast_forward(1800000)
    page.wait_for_function("document.getElementById('analytics').dataset.state === 'live'")
    assert state['api_calls'] > calls, 'Expired retry deadline permanently blocked recovery'
    expect_count(page, expected_all)
    checks['api_resumes_after_retry_deadline'] = True
    assert not errors, errors
    context.close()

    # A newer disk collection wins, including while public API backoff persists.
    context, page, state, errors = fixture(browser, cache=snapshot(1106, NOW - 1000))
    expect_count(page, 1106); settle(page)
    assert page.locator('#growth-chart svg').count() == 1, 'Cached totals suppressed valid saved trend history'
    calls = state['api_calls']
    state['disk'] = snapshot(1110, NOW + 5000)
    page.clock.fast_forward(10050)
    expect_count(page, 1110)
    assert state['api_calls'] == calls
    assert not errors, errors
    checks['newer_static_during_backoff_and_history'] = True
    context.close()

    # This is a freshness policy, not an invented monotonic floor. GitHub can
    # genuinely remove/re-upload an asset, so newer lower totals must be shown.
    context, page, state, errors = fixture(browser, cache=snapshot(1200, NOW - 1000), api_status=0)
    state['live'] = snapshot(1080, NOW)
    # Route state can be consumed before return; force the next poll to cover it.
    page.clock.fast_forward(10050)
    expect_count(page, 1080)
    assert not errors, errors
    checks['newer_legitimate_decrease'] = True
    context.close()

    # Invalid local observations are discarded rather than becoming numbers or
    # unsafe download links. Each starts in a fresh browser context.
    bad = []
    value = snapshot(1106, NOW - 1000); value['repositories'].pop(0); bad.append(('partial', value))
    value = snapshot(1106, NOW - 1000); value['repositories'][0]['packages'] += 1; bad.append(('inconsistent', value))
    value = snapshot(1106, NOW - 1000); value['repositories'][1] = copy.deepcopy(value['repositories'][0]); bad.append(('duplicate', value))
    value = snapshot(1106, NOW - 1000); value['observedAt'] = 'bad-date'; bad.append(('bad_timestamp', value))
    value = snapshot(1106, NOW + 86400000); bad.append(('future_timestamp', value))
    value = snapshot(1106, NOW - 1000); value['repositories'][0]['releases'][0]['assets'][0]['url'] = 'https://example.invalid/untrusted.apk'; bad.append(('unsafe_origin', value))
    value = snapshot(1106, NOW - 1000)
    record = value['repositories'][0]
    record['releases'][0]['assets'][0]['count'] = 9007199254740991
    record['kinds'] = {kind: sum(asset['count'] for release in record['releases'] for asset in release['assets'] if asset['kind'] == kind) for kind in KINDS}
    record['packages'] = sum(record['kinds'][kind] for kind in PACKAGES)
    record['allAssets'] = sum(record['kinds'].values())
    bad.append(('aggregate_overflow', value))
    for name, value in bad:
        context, page, state, errors = fixture(browser, cache=value)
        try:
            expect_count(page, 999); settle(page)
        except Exception as error:
            raise AssertionError(f'Rejected cache case {name}: observed {page.locator("#combined-count").inner_text()}') from error
        assert not errors, (name, errors)
        checks['invalid_cache_' + name] = True
        context.close()

    context, page, state, errors = fixture(browser)
    expect_count(page, 999); settle(page)
    page.evaluate("key => localStorage.setItem(key, '{broken JSON')", CACHE)
    page.reload(); expect_count(page, 999); settle(page)
    assert not errors, errors
    checks['invalid_cache_malformed_json'] = True
    context.close()

    context, page, state, errors = fixture(browser, cache=snapshot(1200, NOW - 7200000))
    expect_count(page, 999); settle(page)
    assert not errors, errors
    checks['older_higher_cache_does_not_override_source'] = True
    context.close()

    context, page, state, errors = fixture(browser, blocked=True, api_status=0)
    expect_count(page, 1106)
    page.locator('#count-mode').select_option('all', force=True)
    expect_count(page, sum(repo['allAssets'] for repo in state['live']['repositories']))
    assert not errors, errors
    checks['storage_denied_still_works'] = True
    context.close()

    # The external font requests remain blocked by fixture(). The four-digit
    # total must fit a narrow phone even when only the system fallback is usable.
    context, page, state, errors = fixture(browser, api_status=0)
    expect_count(page, 1106)
    for width in (320, 390, 1440):
        page.set_viewport_size({'width': width, 'height': 850})
        for mode, expected in [('packages', 1106), ('all', sum(repo['allAssets'] for repo in state['live']['repositories']))]:
            page.locator('#count-mode').select_option(mode, force=True)
            expect_count(page, expected)
            page.wait_for_function("""() => {
                const total = document.getElementById('combined-count');
                return total.clientWidth > 0 && total.scrollWidth <= total.clientWidth;
            }""")
            assert page.locator('#combined-count').inner_text() == page.evaluate('value => value.toLocaleString()', expected)
    assert not errors, errors
    checks['fallback_font_total_fits_phone_and_desktop'] = True
    context.close()

    browser.close()

assert not downloads, downloads
print(json.dumps({'checks': checks, 'applicationDownloads': 0, 'productionRequests': 0}, indent=2))
