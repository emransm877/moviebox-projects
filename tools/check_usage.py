"""Exercise opt-in attribution using mocked endpoints; no production events or asset downloads."""
import json,mimetypes,os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/'site';BASE='https://emransm877.github.io/moviebox-projects/'
SERVICE='https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site';events=[];downloads=[]
def source(route):
    path=(ROOT/(urlsplit(route.request.url).path.removeprefix('/moviebox-projects/') or 'index.html')).resolve()
    if path.is_dir():path/='index.html'
    assert path.is_relative_to(ROOT.resolve())
    route.fulfill(status=200 if path.is_file() else 404,body=path.read_bytes() if path.is_file() else b'missing',content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
def backend(route):
    headers={'Access-Control-Allow-Origin':'https://emransm877.github.io','Access-Control-Allow-Methods':'POST,GET,OPTIONS','Access-Control-Allow-Headers':'Content-Type'}
    if route.request.method=='OPTIONS':route.fulfill(status=204,headers=headers);return
    path=urlsplit(route.request.url).path;data=route.request.post_data_json
    if path=='/api/usage':events.append(data);body={'accepted':True}
    elif path=='/api/session':body={'token':'mock-token','expiresAt':9999999999999}
    else:body={'count':0,'windowSeconds':90}
    route.fulfill(status=202 if path=='/api/usage' else 200,headers=headers,content_type='application/json',body=json.dumps(body))
def context(browser,script="Object.defineProperty(navigator,'webdriver',{get:()=>false});"):
    ctx=browser.new_context(viewport={'width':390,'height':844});ctx.add_init_script(script)
    ctx.route(BASE+'**',source);ctx.route(SERVICE+'/**',backend)
    ctx.route('https://api.github.com/**',lambda route:route.fulfill(status=403,body='{}'))
    def block(route):downloads.append(route.request.url);route.abort()
    ctx.route('https://github.com/**/releases/download/**',block)
    return ctx
with sync_playwright() as p:
    browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
    ctx=context(browser);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'?utm_source=facebook&utm_content=r01');page.wait_for_timeout(200);assert not events
    page.locator('.usage-control').click();assert page.locator('.usage-dialog').is_visible()
    page.locator('[data-usage=allow]').click();page.wait_for_function("localStorage.getItem('moviebox.usage-consent.v1')==='yes'");page.wait_for_timeout(250)
    assert len(events)==1 and events[0]['source']=='facebook' and events[0]['content']=='r01'
    page.goto(BASE+'windows/');page.wait_for_timeout(250)
    assert len(events)==2 and events[-1]['route']=='windows' and events[-1]['source']=='facebook'
    page.evaluate("document.addEventListener('click',e=>{if(e.target.closest('a[href*=\"/releases/download/\"]'))e.preventDefault()},true)")
    page.locator('.guide-actions a').first.click();page.wait_for_timeout(250)
    assert events[-1]['event']=='download_click' and events[-1]['platform']=='windows'
    assert not downloads
    page.locator('.usage-control').click();page.locator('[data-usage=deny]').click();before=len(events)
    page.goto(BASE+'android/');page.wait_for_timeout(200);assert len(events)==before
    page.locator('.usage-control').click();assert page.locator('#usage-choice').inner_text()=='Off in this browser.'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.keyboard.press('Escape');assert not errors
    ctx.close()
    for init in ["localStorage.setItem('moviebox.usage-consent.v1','yes');", "Object.defineProperty(navigator,'webdriver',{get:()=>false});Object.defineProperty(navigator,'doNotTrack',{get:()=> '1'});localStorage.setItem('moviebox.usage-consent.v1','yes');"]:
        ctx=context(browser,init);page=ctx.new_page();before=len(events);page.goto(BASE);page.wait_for_timeout(200);assert len(events)==before;ctx.close()
    browser.close()
print(json.dumps({'default_off':True,'consent_and_withdrawal':True,'facebook_attribution_survives_internal_navigation':True,'download_click_counted_without_download':True,'privacy_signal_and_webdriver_excluded':True,'mobile_dialog_no_overflow':True,'application_downloads':len(downloads)}))
