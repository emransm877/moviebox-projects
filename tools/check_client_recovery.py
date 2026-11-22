"""Exercise real browser recovery with mocked services; no production traffic/downloads."""
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1] / 'site'
BASE = 'https://emransm877.github.io/moviebox-projects/'
SERVICE = 'https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site'
NOW = 1795320000000
DATA = json.loads((ROOT / 'data/latest.json').read_text(encoding='utf-8'))
checks = {}


def source(route):
    relative = urlsplit(route.request.url).path.removeprefix('/moviebox-projects/')
    path = (ROOT / (relative or 'index.html')).resolve()
    if path.is_dir():
        path /= 'index.html'
    assert path.is_relative_to(ROOT.resolve())
    route.fulfill(status=200 if path.is_file() else 404,
                  body=path.read_bytes() if path.is_file() else b'missing',
                  content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')


def context(browser, state, consent=True):
    ctx = browser.new_context(viewport={'width': 1200, 'height': 900})
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});" +
                        ("localStorage.setItem('moviebox.usage-consent.v1','yes');" if consent else ''))
    ctx.route('**/*', lambda route: route.abort())
    ctx.route(BASE + '**', source)
    # Presence has its own suite/session; isolate optional-usage recovery here.
    ctx.route(BASE + 'presence.js*', lambda route: route.fulfill(content_type='text/javascript', body='/* isolated */'))

    def backend(route):
        headers = {'Access-Control-Allow-Origin': 'https://emransm877.github.io',
                   'Access-Control-Allow-Methods': 'POST,GET,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type'}
        if route.request.method == 'OPTIONS':
            route.fulfill(status=204, headers=headers)
            return
        path = urlsplit(route.request.url).path
        if path == '/api/session':
            state['sessions'] += 1
            if state.get('fail_session'):
                state['fail_session'] = False
                route.fulfill(status=503, headers=headers, content_type='application/json', body='{}')
                return
            if state.get('bad_session'):
                state['bad_session'] = False
                value = {'token': None, 'expiresAt': state['now'] + 1800000}
            else:
                value = {'token': 'fixture-token-' + str(state['sessions']), 'expiresAt': state['now'] + 1800000}
        elif path == '/api/usage':
            state['events'].append(route.request.post_data_json)
            value = {'accepted': True}
        else:
            value = {'count': 1, 'windowSeconds': 90}
        route.fulfill(headers=headers, content_type='application/json', body=json.dumps(value))

    ctx.route(SERVICE + '/**', backend)

    def github(route):
        state['api_calls'] += 1
        if state.get('api_failure'):
            route.fulfill(status=state['api_failure'], content_type='application/json',
                          headers={'access-control-allow-origin': '*',
                                   'access-control-expose-headers': 'x-ratelimit-remaining, x-ratelimit-reset',
                                   'x-ratelimit-remaining': '50',
                                   'x-ratelimit-reset': str((state['now'] + 3600000) // 1000)}, body='{}')
            return
        parts = urlsplit(route.request.url).path.split('/')
        repo = next((r for r in DATA['repositories'] if r['name'] == parts[3]),None)
        if repo is None:
            route.fulfill(status=404,body='{}')
            return
        if parts[-1] == 'latest':
            value = {'tag_name': repo['latestTag']}
        else:
            value = [{'id': index + 1, 'tag_name': release['tag'], 'html_url': release['url'],
                      'published_at': release['publishedAt'], 'draft': False, 'prerelease': release['prerelease'],
                      'assets': [{'id': a['id'], 'name': a['name'], 'download_count': a['count'],
                                  'browser_download_url': a['url'], 'size': a['size'], 'created_at': a['createdAt']}
                                 for a in release['assets']]} for index, release in enumerate(repo['releases'])]
        route.fulfill(content_type='application/json', body=json.dumps(value))

    ctx.route('https://api.github.com/**', github)
    def block_download(route):
        state['downloads'] += 1
        route.abort()
    ctx.route('https://github.com/**/releases/download/**', block_download)
    return ctx


def state(**extra):
    return {'now': NOW, 'sessions': 0, 'events': [], 'downloads': 0, 'api_calls': 0, **extra}


def click_download(page):
    page.evaluate("document.addEventListener('click',e=>{if(e.target.closest('a[href*=\"/releases/download/\"]'))e.preventDefault()},true)")
    page.locator('.guide-actions a').first.click()
    page.wait_for_timeout(150)


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None, headless=True)
    for failure in ['fail_session', 'bad_session']:
        current = state(**{failure: True})
        ctx = context(browser, current)
        page = ctx.new_page()
        page.clock.install(time=datetime.fromtimestamp(NOW/1000,timezone.utc))
        page.goto(BASE + 'windows/')
        page.wait_for_timeout(200)
        assert current['sessions'] == 1 and not current['events'], current
        click_download(page)
        assert current['sessions'] == 2, 'A failed or malformed session must not poison the next real click'
        assert len(current['events']) == 1 and current['events'][0]['event'] == 'download_click', current
        assert not current['downloads']
        checks[failure + '_next_click_recovers_without_replaying_failed_event'] = True
        ctx.close()

    current = state()
    ctx = context(browser, current)
    page = ctx.new_page()
    page.clock.install(time=datetime.fromtimestamp(NOW/1000,timezone.utc))
    page.goto(BASE + 'windows/')
    page.wait_for_timeout(200)
    assert len(current['events']) == 1 and current['sessions'] == 1
    current['now'] += 31 * 60000
    page.clock.fast_forward(31 * 60000)
    click_download(page)
    assert current['sessions'] == 2
    assert len(current['events']) == 2
    assert current['events'][-1]['token'] != current['events'][0]['token']
    assert not current['downloads']
    checks['expired_usage_session_renews_before_next_click'] = True
    ctx.close()

    current = state(api_failure=500)
    ctx = context(browser, current, consent=False)
    page = ctx.new_page()
    page.clock.install(time=datetime.fromtimestamp(NOW/1000,timezone.utc))
    page.goto(BASE)
    page.wait_for_function("document.getElementById('analytics').dataset.refreshState==='unavailable'")
    retry = page.evaluate('MovieBoxLiveCounts.load().catch(e=>e.retryAt-Date.now())')
    assert 0 < retry <= 60000, 'An ordinary 500 must not consume the hour-long rate-limit reset'
    current['api_failure'] = 0
    current['now'] += 61000
    page.clock.fast_forward(61000)
    result = page.evaluate('MovieBoxLiveCounts.load().then(value=>value.repositories.length)')
    assert result == 4 and not current['downloads']
    checks['transient_github_error_recovers_after_short_backoff'] = True
    ctx.close()

    current = state(api_failure=429)
    ctx = context(browser, current, consent=False)
    page = ctx.new_page()
    page.clock.install(time=datetime.fromtimestamp(NOW/1000,timezone.utc))
    page.goto(BASE)
    page.wait_for_function("document.getElementById('analytics').dataset.refreshState==='unavailable'")
    retry = page.evaluate('MovieBoxLiveCounts.load().catch(e=>e.retryAt-Date.now())')
    assert retry > 3500000
    before = current['api_calls']
    current['now'] += 61000
    page.clock.fast_forward(61000)
    page.evaluate('MovieBoxLiveCounts.load().catch(()=>null)')
    assert current['api_calls'] == before and not current['downloads']
    checks['actual_github_rate_limit_still_respects_reset'] = True
    ctx.close()
    browser.close()
print(json.dumps({'checks': checks, 'production_requests': 0, 'application_downloads': 0}, indent=2))
