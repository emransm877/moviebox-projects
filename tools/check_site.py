"""Browser verification of the real static site, with isolated fixture errors."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,threading,os,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]/'site'
out=Path(tempfile.mkdtemp(prefix='moviebox-site-qa-'))
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
data=json.loads((root/'data/latest.json').read_text(encoding='utf-8'))
windows=next(r for r in data['repositories'] if r['platform']=='Windows')
checks={};errors=[]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
        browser_context=browser.new_context()
        browser_context.route('https://api.github.com/**',lambda route:route.fulfill(status=403,content_type='application/json',body='{"message":"Fixture: offline rate-limit fallback"}'))
        page=browser_context.new_page();page.set_viewport_size({'width':1440,'height':1000})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(url);page.wait_for_function("document.getElementById('windows-count').textContent !== '—'")
        assert int(page.locator('#windows-count').inner_text().replace(',',''))==windows['packages']
        checks['application_counts_exclude_checksums']=True
        page.locator('#count-mode').select_option('all')
        assert int(page.locator('#windows-count').inner_text().replace(',',''))==windows['allAssets']
        checks['all_file_counts_match_github_asset_sum']=True
        page.locator('#platform-filter').select_option('Windows')
        page.locator('#version-filter').select_option('moviebox-desktop:'+windows['latestTag'])
        assert page.locator('#release-rows tr').count()==1
        assert 'Windows' in page.locator('#release-rows').inner_text()
        checks['platform_and_version_filters_work']=True
        page.locator('#count-mode').select_option('packages')
        for link in page.locator('#release-rows a').all():assert '.sha256' not in (link.get_attribute('href') or '')
        checks['package_mode_hides_checksum_assets']=True
        assert '/'+windows['latestTag']+'/' in page.locator('#windows-download').get_attribute('href')
        assert '/'+next(r for r in data['repositories'] if r['platform']=='Android')['latestTag']+'/' in page.locator('#android-download').get_attribute('href')
        checks['download_buttons_target_published_stable_assets']=True
        page.locator('summary').first.focus();page.keyboard.press('Enter')
        assert page.locator('details').first.get_attribute('open') is not None
        checks['faq_works_with_keyboard']=True
        page.screenshot(path=str(out/'desktop-top.png'))
        page.locator('#analytics').scroll_into_view_if_needed();page.screenshot(path=str(out/'desktop-analytics.png'))
        for width in [390,768,1280,1920]:
            page.set_viewport_size({'width':width,'height':900});page.goto(url)
            page.wait_for_function("document.getElementById('windows-count').textContent !== '—'")
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),str(width)
            if width >= 1280:
                for selector in ['.project-download', '.project-download .button', '.project-source']:
                    tops=page.locator(selector).evaluate_all('(nodes)=>nodes.map(node=>node.getBoundingClientRect().top)')
                    assert max(tops)-min(tops)<2,(width,selector,tops)
                checks['project_downloads_align_'+str(width)]=True
            for image in page.locator('img').all():
                image.scroll_into_view_if_needed()
                page.wait_for_function('(image)=>image.complete&&image.naturalWidth>0',arg=image.element_handle())
            page.evaluate('scrollTo(0,0)')
            if width==1280:
                page.locator('.project-grid').screenshot(path=str(out/'project-downloads.png'))
            checks['layout_and_images_'+str(width)]=True
            if width==390:page.screenshot(path=str(out/'mobile-top.png'));page.locator('#analytics').scroll_into_view_if_needed();page.screenshot(path=str(out/'mobile-analytics.png'))
        failure=browser_context.new_page();failure.set_viewport_size({'width':390,'height':900})
        failure.route('**/data/latest.json',lambda route:route.fulfill(status=503,body='unavailable'))
        failure.goto(url);failure.wait_for_function("document.getElementById('snapshot-status').classList.contains('error')")
        assert '/'+windows['latestTag']+'/' in failure.locator('#windows-download').get_attribute('href')
        checks['snapshot_failure_keeps_published_downloads_usable']=True
        baseline_page=browser_context.new_page()
        baseline_page.route('**/data/history.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps({'schemaVersion':1,'points':[]})))
        baseline_page.goto(url);baseline_page.wait_for_function("document.getElementById('growth-chart').textContent.includes('Earlier daily downloads cannot be reconstructed')")
        checks['baseline_has_no_invented_growth_history']=True
        history_page=browser_context.new_page();history_page.set_viewport_size({'width':900,'height':900})
        fake={'schemaVersion':1,'points':[{'at':'2026-11-21T12:00:00Z','packages':{'moviebox-android':194,'moviebox-desktop':236}},{'at':'2026-11-22T12:00:00Z','packages':{'moviebox-android':197,'moviebox-desktop':240,'moviebox-tizen':51}}]}
        history_page.route('**/data/history.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(fake)))
        history_page.goto(url);history_page.locator('.growth-bar').wait_for();assert '+7' in history_page.locator('.growth-bar').inner_text()
        checks['measured_growth_delta_renders_correctly']=True
        for route in ['windows/','android/','samsung-tv/','help/']:
            response=page.goto(url+route)
            assert response.status==200
            assert page.locator('h1').count()==1
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            assert page.locator('link[rel=canonical]').get_attribute('href').startswith('https://emransm877.github.io/moviebox-projects/')
        checks['all_product_guides_are_crawlable_and_responsive']=True
        live_context=browser.new_context();state={'increase':0,'limited':False,'requests':0}
        def github_fixture(route):
            from urllib.parse import urlsplit
            state['requests']+=1
            if state['limited']:
                route.fulfill(status=429,content_type='application/json',headers={'x-ratelimit-remaining':'0','x-ratelimit-reset':'1999999999'},body='{"message":"Fixture rate limit"}');return
            parts=urlsplit(route.request.url).path.split('/');name=parts[3];repo=next(r for r in data['repositories'] if r['name']==name)
            if parts[-1]=='latest':result={'tag_name':repo['latestTag']}
            else:
                result=[]
                for index,release in enumerate(repo['releases']):
                    assets=[{'id':a['id'],'name':a['name'],'download_count':a['count']+(state['increase'] if name=='moviebox-desktop' and a['kind']=='installer' and release['tag']==repo['latestTag'] else 0),'browser_download_url':a['url'],'size':a['size'],'created_at':a['createdAt']} for a in release['assets']]
                    result.append({'id':index+1,'tag_name':release['tag'],'html_url':release['url'],'published_at':release['publishedAt'],'prerelease':release['prerelease'],'draft':False,'assets':assets})
            route.fulfill(content_type='application/json',body=json.dumps(result))
        live_context.route('https://api.github.com/**',github_fixture)
        live=live_context.new_page();live.clock.install();live.goto(url)
        live.wait_for_function("document.getElementById('snapshot-status').textContent.startsWith('Refreshed from GitHub')")
        state['increase']=1;live.clock.fast_forward(10000)
        live.wait_for_function('(expected)=>document.getElementById("windows-count").textContent.replaceAll(",","")===String(expected)',arg=windows['packages']+1)
        checks['automatic_ten_second_refresh_updates_real_api_counts']=True
        state['limited']=True;live.clock.fast_forward(10000)
        live.wait_for_function("document.getElementById('snapshot-status').textContent.includes('GitHub rate limit reached')")
        assert int(live.locator('#windows-count').inner_text().replace(',',''))==windows['packages']+1
        checks['api_rate_limit_keeps_verified_counts_and_reports_pause']=True
        live_context.close()
        assert not errors,errors
        checks['no_browser_javascript_errors']=True
        browser.close()
finally:server.shutdown();server.server_close()
(out/'result.json').write_text(json.dumps({'checks':checks,'errors':errors,'passed':True},indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2));print('Browser evidence:',out)
