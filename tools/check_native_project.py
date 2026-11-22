"""Five-project publication fixture. Never publishes or downloads an application asset."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(tempfile.mkdtemp(prefix='moviebox-five-project-qa-'))
sys.path.insert(0,str(ROOT/'tools'))
from check_release_info import fixture

data=fixture(True,False)
native={'name':'moviebox-android-native','platform':'Android app','url':'https://github.com/emransm877/moviebox-android-native','latestTag':'v0.1.0',
 'releases':[{'tag':'v0.1.0','url':'https://github.com/emransm877/moviebox-android-native/releases/tag/v0.1.0','publishedAt':'2099-01-02T00:00:00Z','prerelease':False,
 'assets':[{'id':99887766,'name':'MovieBox-Android-App-0.1.0.apk','kind':'apk','count':8,'url':'https://github.com/emransm877/moviebox-android-native/releases/download/v0.1.0/MovieBox-Android-App-0.1.0.apk','size':5000000,'createdAt':'2099-01-02T00:00:00Z'}]}],
 'kinds':{'apk':8,'installer':0,'portable':0,'tv_bundle':0,'tv_widget':0,'checksums':0,'other':0},'packages':8,'allAssets':8}
data['repositories'].append(native)
staged=OUT/'site';shutil.copytree(ROOT/'site',staged)
(staged/'data/latest.json').write_text(json.dumps(data),encoding='utf-8')
spec=importlib.util.spec_from_file_location('native_build_fixture',ROOT/'tools/build_site.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.SITE=staged;builder.build()
assert 'noindex' not in (staged/'android-app/index.html').read_text()
assert '/android-app/' in (staged/'sitemap.xml').read_text()
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(staged)));threading.Thread(target=server.serve_forever,daemon=True).start()
checks=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
  for width in [390,768,1280,1920]:
   context=browser.new_context(viewport={'width':width,'height':1000})
   context.route('https://api.github.com/**',lambda route:route.fulfill(status=403,body='{}'))
   context.route('https://github.com/**/releases/download/**',lambda route:route.abort())
   page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
   page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function("document.getElementById('native-count').textContent==='8'")
   assert page.locator('.project-grid>.project:not([hidden])').count()==5
   assert page.locator('#downloads .quick-download:not([hidden])').count()==5
   assert 'All five projects' in page.locator('#platform-filter').inner_text()
   assert 'Five projects' in page.locator('#projects-title').inner_text()
   assert page.locator('.hero-facts').inner_text().find('Android App 6+')>=0
   assert page.locator('#native-version').inner_text()=='0.1.0'
   assert page.locator('#android-version').inner_text()=='0.2.0'
   assert '/moviebox-android-native/' in page.locator('#native-download').get_attribute('href')
   assert '/moviebox-android/' in page.locator('#android-download').get_attribute('href')
   assert page.locator('.preview-phone img').get_attribute('src').endswith('android-native-0.1.0-home.png')
   assert page.locator('#preview-windows-panel img').get_attribute('src').endswith('desktop-0.10.4-home.png')
   assert page.locator('#preview-samsung-tab').count()==1
   assert page.locator('#trend-platform-moviebox-android-native').count()==1
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   if width>720:
    page.locator('.project:not([hidden])').evaluate_all('(nodes)=>nodes.forEach(node=>{node.classList.add("is-flipped");node.querySelector(".flip-front").inert=true;node.querySelector(".flip-back").inert=false})')
    page.locator('.project-flip-inner').evaluate_all('(nodes)=>Promise.all(nodes.flatMap(node=>node.getAnimations().map(animation=>animation.finished)))')
    cards=page.locator('.project:not([hidden])').evaluate_all('(nodes)=>nodes.map(node=>({top:node.getBoundingClientRect().top,button:node.querySelector(".button").getBoundingClientRect().top}))')
    for card in cards:
     peers=[item for item in cards if abs(item['top']-card['top'])<2]
     assert max(item['button'] for item in peers)-min(item['button'] for item in peers)<2
   page.locator('img').evaluate_all('(nodes)=>Promise.all(nodes.map(node=>{node.loading="eager";return node.decode().catch(()=>{})}))')
   for image in page.locator('img').all():
    if image.is_visible():assert image.evaluate('node=>node.complete&&node.naturalWidth>0')
   page.screenshot(path=str(OUT/f'hub-{width}.png'),full_page=True)
   page.goto(f'http://127.0.0.1:{server.server_port}/android-app/')
   assert page.locator('h1').inner_text()=='MovieBox Android App'
   assert page.locator('img.guide-phone-shot').count()==1
   assert page.locator('.guide-actions a').first.get_attribute('href')==native['releases'][0]['assets'][0]['url']
   assert not errors,errors
   checks.append({'width':width,'fiveSeparateProjects':True,'realCaptureSelection':True,'alignedButtons':True,'noOverflow':True})
   context.close()
  browser.close()
finally:server.shutdown();server.server_close()
(OUT/'result.json').write_text(json.dumps({'checks':checks,'applicationDownloads':0},indent=2))
print(json.dumps({'checks':checks,'evidence':str(OUT),'applicationDownloads':0},indent=2))
