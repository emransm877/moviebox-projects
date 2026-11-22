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
project_count=len(data['repositories'])
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
        assert page.locator('.native-scene img').is_visible()
        assert page.locator('.android-capture').count()==0
        assert page.locator('.scene img').count()==project_count
        assert page.locator('.scene img').evaluate_all("nodes=>nodes.every(node=>getComputedStyle(node).objectFit==='contain')")
        for image in page.locator('.scene img').all():
            assert image.locator('xpath=ancestor::a').get_attribute('href').startswith('assets/')
        checks['all_platform_scenes_keep_full_capture_and_open_original']=True
        assert page.evaluate("MovieBoxLiveCounts.kind('MovieBox-Setup-0.10.3-windows-x64-SELF-SIGNED-TEST.exe','moviebox-desktop')")=='installer'
        assert page.evaluate("MovieBoxLiveCounts.kind('MovieBox-Desktop-0.10.3-windows-x64-SELF-SIGNED-TEST.zip','moviebox-desktop')")=='portable'
        assert page.evaluate("MovieBoxLiveCounts.kind('MovieBox-TEST-ONLY.cer','moviebox-desktop')")=='other'
        assert page.locator('#tickets .tk:not([hidden])').count()==project_count
        assert page.locator('#tickets').is_visible()
        assert page.locator('#projects').is_visible()
        for quick in page.locator('[data-download-source]').all():
            original=page.locator('#'+quick.get_attribute('data-download-source'))
            assert quick.get_attribute('href')==original.get_attribute('href')
        checks['compact_downloads_link_to_exact_published_assets']=True
        assert page.locator('#refresh-live').count()==0
        assert page.locator('#snapshot-status').count()==0
        assert page.locator('.chart-method').count()==0
        checks['requested_sync_and_explainer_removed']=True
        assert page.locator('.project-grid > .project:not([hidden])').count()==project_count
        android_tv=next(repo for repo in data['repositories'] if repo['platform']=='Android TV')
        assert page.evaluate('(tag)=>MovieBoxReleaseInfo.label(tag)',android_tv['latestTag']) in page.locator('#android-tv-project').inner_text()
        assert page.locator('#android-tv-project a[href*="/releases/download/"]').count()==1
        assert page.locator('#androidtv-download').is_visible()
        assert '/'+android_tv['latestTag']+'/' in page.locator('#androidtv-download').get_attribute('href')
        assert page.locator('.flip-open').count()==0
        page.locator('#androidtv-download').focus()
        assert page.locator('#androidtv-download').evaluate('node=>node===document.activeElement')
        checks['download_scenes_are_direct_and_keyboard_accessible']=True
        touch=browser.new_context(viewport={'width':390,'height':900},has_touch=True,is_mobile=True,reduced_motion='reduce')
        touch.route('https://api.github.com/**',lambda route:route.fulfill(status=403,body='{}'))
        mobile=touch.new_page();mobile.goto(url)
        assert mobile.locator('#tickets').is_visible()
        assert mobile.locator('#projects').is_visible()
        assert mobile.locator('#tickets .tk:visible').count()==project_count
        assert mobile.locator('.scene:visible').count()==project_count
        assert mobile.evaluate("window.__mbTier==='static'")
        mobile.locator('details.download-history>summary').tap()
        mobile.locator('#trend-interactive').scroll_into_view_if_needed()
        mobile.locator('#trend-interactive').tap()
        assert mobile.locator('.trend-tooltip').is_visible(), 'Touch details must persist after finger lift'
        mobile.locator('.trend-caption').tap()
        assert mobile.locator('.trend-tooltip').is_hidden(), 'Outside tap dismisses touch details'
        mobile.locator('#trend-interactive').tap()
        mobile.keyboard.press('Escape')
        assert mobile.locator('.trend-tooltip').is_hidden()
        checks['touch_tooltip_persists_and_dismisses_outside_or_escape']=True
        touch.close();checks['mobile_uses_direct_tickets_flat_scenes_and_static_hero']=True
        checks['published_project_cards_with_real_downloads']=True
        assert page.locator('details.download-history').get_attribute('open') is None
        page.locator('details.download-history>summary').click()
        assert page.locator('#trend-interactive').bounding_box()['width']>0
        page.locator('#count-mode').select_option('all')
        assert int(page.locator('#windows-count').inner_text().replace(',',''))==windows['allAssets']
        checks['all_file_counts_match_github_asset_sum']=True
        total_releases=sum(len(repo['releases']) for repo in data['repositories'])
        assert page.locator('#release-rows tr').count()==min(5,total_releases)
        assert page.locator('#release-previous').is_disabled()
        first_page=page.locator('#release-rows').inner_text()
        page.locator('#release-next').focus();page.keyboard.press('Enter')
        assert page.locator('#release-page-label').inner_text().startswith('Page 2 ')
        assert page.locator('#release-rows').inner_text()!=first_page
        page.locator('#release-previous').click()
        assert page.locator('#release-rows').inner_text()==first_page
        page.locator('#release-page-size').select_option('10')
        assert page.locator('#release-rows tr').count()==min(10,total_releases)
        while page.locator('#release-next').is_enabled():page.locator('#release-next').click()
        assert page.locator('#release-rows tr').count()==(total_releases%10 or 10)
        assert page.locator('#release-range').inner_text().endswith('of '+str(total_releases)+' releases')
        page.locator('#release-page-size').select_option('5')
        checks['release_pagination_keyboard_page_size_and_last_page']=True
        page.locator('#platform-filter').select_option('Windows')
        page.locator('#version-filter').select_option('moviebox-desktop:'+windows['latestTag'])
        assert page.locator('#release-rows tr').count()==1
        assert page.locator('#release-page-label').inner_text()=='Page 1 of 1'
        assert page.locator('#release-next').is_disabled()
        assert 'Windows' in page.locator('#release-rows').inner_text()
        checks['platform_and_version_filters_work']=True
        legacy=next((release for release in windows['releases'] if '-selfsigned.' in release['tag']),None)
        if legacy:
            page.locator('#version-filter').select_option('moviebox-desktop:'+legacy['tag'])
            assert '-selfsigned.' not in page.locator('#release-rows').inner_text()
            assert 'Preview 1' in page.locator('#release-rows').inner_text()
            assert legacy['tag'] in page.locator('#release-rows td').nth(1).locator('a').get_attribute('href')
            assert page.locator('#version-filter').input_value()=='moviebox-desktop:'+legacy['tag']
            page.locator('#version-filter').select_option('moviebox-desktop:'+windows['latestTag'])
        checks['clean_preview_labels_preserve_real_release_identity']=True
        page.locator('#count-mode').select_option('packages')
        for link in page.locator('#release-rows a').all():assert '.sha256' not in (link.get_attribute('href') or '')
        checks['package_mode_hides_checksum_assets']=True
        assert '/'+windows['latestTag']+'/' in page.locator('#windows-download').get_attribute('href')
        assert '/'+next(r for r in data['repositories'] if r['platform']=='Android')['latestTag']+'/' in page.locator('#android-download').get_attribute('href')
        checks['download_buttons_target_published_stable_assets']=True
        page.locator('.faq summary').first.focus();page.keyboard.press('Enter')
        assert page.locator('.faq details').first.get_attribute('open') is not None
        checks['faq_works_with_keyboard']=True
        page.screenshot(path=str(out/'desktop-top.png'))
        page.locator('#analytics').scroll_into_view_if_needed();page.screenshot(path=str(out/'desktop-analytics.png'))
        for width in [390,768,1024,1280,1920]:
            page.set_viewport_size({'width':width,'height':900});page.goto(url)
            page.wait_for_function("document.getElementById('windows-count').textContent !== '—'")
            page.mouse.move(0,0)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),str(width)
            assert page.locator('.tally-row p').evaluate_all("nodes=>nodes.every(node=>node.scrollWidth<=node.clientWidth+1)")
            quick_rows=page.locator('#tickets .tk:not([hidden])')
            if width<=720:
                assert page.locator('#projects').is_visible()
                assert page.locator('#tickets').is_visible()
                for button in quick_rows.all():assert button.bounding_box()['height']>=44
                assert page.locator('#tickets').bounding_box()['y']<page.locator('#projects').bounding_box()['y']
                assert page.locator('#tickets').bounding_box()['height']<480
                page.locator('#tickets').screenshot(path=str(out/'mobile-quick-downloads.png'))
                checks['compact_ticket_downloads_before_mobile_scenes']=True
            else:
                assert page.locator('#tickets').is_visible()
                assert page.locator('#projects').is_visible()
            if width >= 768:
                page.locator('details.download-history>summary').click()
                assert page.locator('.analytics-header').bounding_box()['height']<210
                cards=page.locator('.project:not([hidden])').evaluate_all('(nodes)=>nodes.map(node=>({top:node.getBoundingClientRect().top,button:node.querySelector(".button").getBoundingClientRect().top,width:node.querySelector(".button").getBoundingClientRect().width,footerWidth:node.querySelector(".project-download").getBoundingClientRect().width}))')
                for card in cards:
                    peers=[other for other in cards if abs(other['top']-card['top'])<2]
                    assert max(other['button'] for other in peers)-min(other['button'] for other in peers)<2,(width,cards)
                    assert card['width']<=card['footerWidth']+2,(width,card)
                checks['card_actions_align_each_row_'+str(width)]=True
            if width >= 1280:
                for selector in ['.project:not([hidden]) .project-download', '.project:not([hidden]) .project-download .button', '.project:not([hidden]) .project-source']:
                    positions=page.locator(selector).evaluate_all('(nodes)=>nodes.map(node=>({row:node.closest(".project").getBoundingClientRect().top,top:node.getBoundingClientRect().top}))')
                    for position in positions:
                        tops=[other['top'] for other in positions if abs(other['row']-position['row'])<2]
                        assert max(tops)-min(tops)<2,(width,selector,tops)
                checks['project_downloads_align_'+str(width)]=True
            for image in page.locator('img').all():
                if not image.is_visible():continue
                image.scroll_into_view_if_needed()
                page.wait_for_function('(image)=>image.complete&&image.naturalWidth>0',arg=image.element_handle())
            page.evaluate('scrollTo(0,0)')
            if width==1280:
                page.locator('.project-grid').screenshot(path=str(out/'project-downloads.png'))
            checks['layout_and_images_'+str(width)]=True
            if width==390:page.screenshot(path=str(out/'mobile-top.png'));page.locator('#analytics').scroll_into_view_if_needed();page.screenshot(path=str(out/'mobile-analytics.png'))
        failure=browser_context.new_page();failure.set_viewport_size({'width':390,'height':900})
        failure.route('**/data/latest.json',lambda route:route.fulfill(status=503,body='unavailable'))
        failure.goto(url);failure.wait_for_function("document.getElementById('analytics').dataset.state==='unavailable'")
        assert '/'+windows['latestTag']+'/' in failure.locator('#windows-download').get_attribute('href')
        checks['snapshot_failure_keeps_published_downloads_usable']=True
        baseline_page=browser_context.new_page()
        baseline_page.route('**/data/history.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps({'schemaVersion':1,'points':[]})))
        baseline_page.goto(url);baseline_page.wait_for_function("document.querySelector('#growth-chart .trend-empty')!==null")
        checks['baseline_has_no_invented_growth_history']=True
        history_page=browser_context.new_page();history_page.set_viewport_size({'width':900,'height':900})
        fake={'schemaVersion':1,'points':[{'at':'2026-11-21T12:00:00Z','packages':{'moviebox-android':194,'moviebox-desktop':236}},{'at':'2026-11-21T13:00:00Z','packages':{'moviebox-android':197,'moviebox-desktop':240,'moviebox-tizen':51}}]}
        history_page.route('**/data/history.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(fake)))
        history_page.goto(url);history_page.locator('details.download-history>summary').click();history_page.locator('#trend-interactive').wait_for()
        assert history_page.locator('.trend-caption strong').inner_text()=='+7'
        history_page.locator('#trend-interactive').focus()
        assert 'Android patch +3' in history_page.locator('.trend-tooltip').inner_text()
        assert 'Windows +4' in history_page.locator('.trend-tooltip').inner_text()
        assert 'Samsung TV +0' in history_page.locator('.trend-tooltip').inner_text()
        history_page.keyboard.press('Escape');assert history_page.locator('.trend-tooltip').is_hidden()
        history_page.keyboard.press('End');assert history_page.locator('.trend-tooltip').is_visible()
        history_page.locator('#growth-range').select_option('24')
        assert history_page.locator('#growth-range').input_value()=='24'
        assert history_page.locator('.trend-caption strong').inner_text()=='+7'
        assert history_page.locator('.trend-line').count()==len(data['repositories'])
        history_page.locator('#trend-platform-moviebox-desktop').click()
        assert history_page.locator('.trend-caption strong').inner_text()=='+4'
        assert history_page.locator('.trend-line').count()==1
        history_page.locator('#trend-interactive').focus();history_page.keyboard.press('Home')
        assert 'Nov 21' in history_page.locator('.trend-tooltip').inner_text()
        checks['observed_growth_platform_filters_keyboard_and_tooltip']=True
        guide_routes=['windows/','android/','samsung-tv/','android-tv/','help/']
        if any(repo['name']=='moviebox-android-native' for repo in data['repositories']):guide_routes.append('android-app/')
        for route in guide_routes:
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
            parts=urlsplit(route.request.url).path.split('/');name=parts[3];repo=next((r for r in data['repositories'] if r['name']==name),None)
            if repo is None:route.fulfill(status=404,body='{}');return
            if parts[-1]=='latest':result={'tag_name':repo['latestTag']}
            else:
                result=[]
                for index,release in enumerate(repo['releases']):
                    assets=[{'id':a['id'],'name':a['name'],'download_count':a['count']+(state['increase'] if name=='moviebox-desktop' and a['kind']=='installer' and release['tag']==repo['latestTag'] else 0),'browser_download_url':a['url'],'size':a['size'],'created_at':a['createdAt']} for a in release['assets']]
                    result.append({'id':index+1,'tag_name':release['tag'],'html_url':release['url'],'published_at':release['publishedAt'],'prerelease':release['prerelease'],'draft':False,'assets':assets})
            route.fulfill(content_type='application/json',body=json.dumps(result))
        live_context.route('https://api.github.com/**',github_fixture)
        live=live_context.new_page();live.clock.install();live.goto(url)
        live.wait_for_function("document.getElementById('analytics').dataset.state==='live'")
        live.locator('details.download-history>summary').click()
        state['increase']=1;live.clock.fast_forward(10000)
        live.wait_for_function('(expected)=>document.getElementById("windows-count").textContent.replaceAll(",","")===String(expected)',arg=windows['packages']+1)
        checks['automatic_ten_second_refresh_updates_real_api_counts']=True
        live.locator('#trend-platform-moviebox-desktop').click()
        live.locator('#growth-range').select_option('24')
        live.locator('#version-filter').select_option('moviebox-desktop:'+windows['latestTag'])
        live.clock.fast_forward(10000)
        live.wait_for_function('(value)=>document.getElementById("version-filter").value===value',arg='moviebox-desktop:'+windows['latestTag'])
        assert live.locator('#release-rows tr').count()==1
        assert live.locator('#growth-range').input_value()=='24'
        assert live.locator('#trend-platform-moviebox-desktop').get_attribute('aria-pressed')=='true'
        live.locator('#version-filter').select_option('all');live.locator('#release-next').click()
        live.clock.fast_forward(10000)
        assert live.locator('#release-page-label').inner_text().startswith('Page 2 ')
        checks['live_refresh_preserves_release_filters_and_page']=True
        state['limited']=True;live.clock.fast_forward(10000)
        live.wait_for_function("document.getElementById('analytics').dataset.refreshState==='unavailable'")
        assert int(live.locator('#windows-count').inner_text().replace(',',''))==windows['packages']+1
        checks['api_rate_limit_keeps_verified_counts']=True
        live_context.close()
        assert not errors,errors
        checks['no_browser_javascript_errors']=True
        browser.close()
finally:server.shutdown();server.server_close()
(out/'result.json').write_text(json.dumps({'checks':checks,'errors':errors,'passed':True},indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2));print('Browser evidence:',out)
