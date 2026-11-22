"""Acceptance checks for actual Tally scope, responsive cinema and privacy controls.

All external endpoints and application downloads are blocked. No production events.
"""
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
import json,os,tempfile
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';OUT=Path(tempfile.mkdtemp(prefix='moviebox-cinema-qa-'))
data=json.loads((SITE/'data/latest.json').read_text(encoding='utf-8'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(SITE)));Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
checks={};downloads=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
  for width in [320,390,720,1440,1920]:
   context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
   context.route('https://api.github.com/**',lambda route:route.fulfill(status=403,body='{}'))
   context.route('https://github.com/**/releases/download/**',lambda route:(downloads.append(route.request.url),route.abort()))
   context.route('https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site/**',lambda route:route.abort())
   context.add_init_script("window.__contexts=0;const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(...args){window.__contexts++;return original.apply(this,args);};")
   page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
   page.goto(url);page.wait_for_function("document.getElementById('windows-count').textContent!=='—'")
   assert page.locator('header a[href$="help/"]').is_visible()
   assert page.locator('.tq-chip').count()==0
   assert page.evaluate("window.__mbTier==='static'&&window.__contexts===0")
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   assert page.locator('#tickets .tk:visible').count()==len(data['repositories'])
   assert page.locator('.tally-row:visible').count()==len(data['repositories'])
   assert page.locator('.total-stat').count()==0
   expected=sum(repo['packages'] for repo in data['repositories'])
   assert int(page.locator('#combined-count').inner_text().replace(',',''))==expected
   assert 'package downloads across all releases' in page.locator('#combined-label').inner_text()
   peak=max(repo['packages'] for repo in data['repositories'])
   for repo in data['repositories']:
    bar=page.locator('[data-tally-repo="'+repo['name']+'"] i')
    width_value=bar.evaluate('node=>parseFloat(node.style.width)')
    assert abs(width_value-(repo['packages']/peak*100 if peak else 0))<.01
   details=page.locator('details.download-history');assert details.get_attribute('open') is None
   details.locator('summary').focus();page.keyboard.press('Enter')
   assert page.locator('#trend-interactive').bounding_box()['width']>0
   page.locator('#growth-range').select_option('168');page.locator('#trend-platform-moviebox-desktop').click()
   page.locator('#release-next').click();page_number=page.locator('#release-page-label').inner_text()
   details.locator('summary').click();details.locator('summary').click()
   assert page.locator('#growth-range').input_value()=='168'
   assert page.locator('#trend-platform-moviebox-desktop').get_attribute('aria-pressed')=='true'
   assert page.locator('#release-page-label').inner_text()==page_number
   page.locator('#count-mode').select_option('all')
   assert int(page.locator('#combined-count').inner_text().replace(',',''))==sum(repo['allAssets'] for repo in data['repositories'])
   assert 'Release-file downloads across all releases'==page.locator('#combined-label').inner_text()
   # Long historical labels stay inside their own cells rather than covering dates.
   page.locator('#platform-filter').select_option('Windows')
   old=next(r for r in data['repositories'] if r['platform']=='Windows')
   legacy=next((r for r in old['releases'] if '-selfsigned.' in r['tag']),None)
   if legacy:
    page.locator('#version-filter').select_option('moviebox-desktop:'+legacy['tag'])
    bounds=page.locator('#release-rows tr').first.evaluate("row=>{const a=row.children[1].querySelector('a').getBoundingClientRect(),b=row.children[2].getBoundingClientRect();return {text:a.right,date:b.left};}")
    assert bounds['text']+8<=bounds['date'],bounds
   if width>=720:
    a=page.locator('#windows-download').bounding_box();b=page.locator('#portable-download').bounding_box();assert abs(a['y']-b['y'])<2
   page.locator('.usage-control').click();page.wait_for_timeout(100)
   for action in ['allow','deny','close']:
    box=page.locator('[data-usage="'+action+'"]').bounding_box()
    assert box['height']>=44 and box['y']>=0 and box['y']+box['height']<=900,box
   title=page.locator('#usage-title').bounding_box();assert title['y']>=0
   assert page.locator('#usage-choice').inner_text()=='Off in this browser.'
   page.screenshot(path=str(OUT/f'privacy-{width}.png'));page.keyboard.press('Escape')
   assert page.locator('.usage-dialog').is_hidden()
   assert not errors,errors
   checks[str(width)]={'noOverflow':True,'fiveRealProjects':True,'correctTally':True,'detailStatePreserved':True,'privacyActionsVisible':True,'noWebGLForReducedMotion':True}
   context.close()
  for path in ['','windows/','android/','android-app/','samsung-tv/','android-tv/','help/','404.html']:
   page=browser.new_page();page.goto(url+path)
   icon=page.locator('link[rel="icon"][type="image/svg+xml"]').get_attribute('href');assert 'cinema-favicon.svg' in icon
   assert page.locator('link[rel="apple-touch-icon"]').count()==1
   page.close()
  browser.close()
finally:server.shutdown();server.server_close()
assert not downloads,downloads
(OUT/'result.json').write_text(json.dumps({'checks':checks,'allPageIcons':True,'applicationDownloads':0},indent=2))
print(json.dumps({'checks':checks,'allPageIcons':True,'applicationDownloads':0,'evidence':str(OUT)},indent=2))
