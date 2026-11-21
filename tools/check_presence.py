"""Isolated browser presence scenarios. Never sends heartbeats to production."""
from pathlib import Path
import json,mimetypes,os
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/'site'
BASE='https://emransm877.github.io/moviebox-projects/'
SERVICE='https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site'
state={'ids':set(),'heartbeats':0,'fail':False,'assetDownloads':0}
def source(route):
    relative=urlsplit(route.request.url).path.removeprefix('/moviebox-projects/')
    path=(ROOT/(relative or 'index.html')).resolve()
    if path.is_dir():path=path/'index.html'
    assert path.is_relative_to(ROOT.resolve())
    route.fulfill(status=200 if path.is_file() else 404,body=path.read_bytes() if path.is_file() else b'missing',content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
def backend(route):
    headers={'Access-Control-Allow-Origin':'https://emransm877.github.io','Access-Control-Allow-Methods':'POST,GET,OPTIONS','Access-Control-Allow-Headers':'Content-Type','Cache-Control':'no-store'}
    if route.request.method=='OPTIONS':route.fulfill(status=204,headers=headers);return
    if state['fail']:route.fulfill(status=503,headers=headers,content_type='application/json',body='{"error":"service-unavailable"}');return
    data=route.request.post_data_json
    if urlsplit(route.request.url).path=='/api/session':body={'token':data['id']+'.mock-test-token','expiresAt':1795228800000+30*60*1000}
    else:
        state['ids'].add(data['token'].split('.')[0]);state['heartbeats']+=1
        body={'count':len(state['ids']),'windowSeconds':90,'observedAt':1795228800000}
    route.fulfill(status=200,headers=headers,content_type='application/json',body=json.dumps(body))
def context(browser,normal=True):
    ctx=browser.new_context(viewport={'width':1280,'height':900})
    if normal:ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
    ctx.route(BASE+'**',source)
    ctx.route('https://api.github.com/**',lambda route:route.fulfill(status=403,body='{}'))
    ctx.route(SERVICE+'/**',backend)
    def no_download(route):state['assetDownloads']+=1;route.abort()
    ctx.route('https://github.com/**/releases/download/**',no_download)
    return ctx
with sync_playwright() as p:
    browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
    first=context(browser);page=first.new_page();page.clock.install(time=1795228800000)
    page.goto(BASE);page.wait_for_function("document.getElementById('live-presence').dataset.state==='live'")
    assert page.locator('#presence-value').inner_text()=='1'
    initial=state['heartbeats'];page.clock.fast_forward(25000)
    page.wait_for_function("document.getElementById('live-presence').dataset.state==='live'")
    assert len(state['ids'])==1
    second_tab=first.new_page();second_tab.clock.install(time=1795228800000)
    second_tab.goto(BASE+'windows/');second_tab.wait_for_function("document.getElementById('live-presence').dataset.state==='live'")
    assert second_tab.locator('#presence-value').inner_text()=='1'
    second=context(browser);other=second.new_page();other.clock.install(time=1795228800000)
    other.goto(BASE);other.wait_for_function("document.getElementById('presence-value').textContent==='2'")
    assert len(state['ids'])==2
    before=state['heartbeats']
    page.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.fast_forward(60000)
    assert state['heartbeats']==before
    assert page.locator('#presence-value').inner_text()=='—'
    page.evaluate("Object.defineProperty(document,'hidden',{get:()=>false,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
    page.wait_for_function("document.getElementById('presence-value').textContent==='2'")
    state['fail']=True;page.clock.fast_forward(25000)
    page.wait_for_function("document.getElementById('live-presence').dataset.state==='unavailable'")
    assert page.locator('#presence-value').inner_text()=='—'
    state['fail']=False;page.clock.fast_forward(25000)
    page.wait_for_function("document.getElementById('live-presence').dataset.state==='live'")
    excluded=context(browser,normal=False);qa=excluded.new_page();before=state['heartbeats'];qa.goto(BASE)
    qa.wait_for_function("document.getElementById('live-presence').dataset.state==='off'")
    assert state['heartbeats']==before
    optout=first.new_page();optout.goto(BASE+'?presence=off')
    optout.wait_for_function("document.getElementById('live-presence').dataset.state==='off'")
    assert state['heartbeats']==before
    assert state['assetDownloads']==0
    browser.close()
print('Presence browser checks passed: real-response display, cross-tab deduplication, two browsers, hidden pause, outage/recovery, QA exclusion and opt-out. No production traffic or release downloads.')
