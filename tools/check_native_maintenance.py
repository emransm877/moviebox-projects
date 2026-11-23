"""Local fixture-only native guide acceptance; never requests an APK or telemetry."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import importlib.util
import json,os,shutil,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(tempfile.mkdtemp(prefix='moviebox-native-maintenance-'))
staged=OUT/'site';shutil.copytree(ROOT/'site',staged)
snapshot=json.loads((staged/'data/latest.json').read_text(encoding='utf-8'))
native=next(repo for repo in snapshot['repositories'] if repo['name']=='moviebox-android-native')
release=next(item for item in native['releases'] if item['tag']==native['latestTag'])
release['tag']='v0.1.1';release['url']='https://github.com/emransm877/moviebox-android-native/releases/tag/v0.1.1'
for asset in release['assets']:
    asset['name']=asset['name'].replace('0.1.0','0.1.1')
    asset['url']=asset['url'].replace('0.1.0','0.1.1')
native['latestTag']='v0.1.1'
(staged/'data/latest.json').write_text(json.dumps(snapshot),encoding='utf-8')
spec=importlib.util.spec_from_file_location('native_maintenance_build_fixture',ROOT/'tools/build_site.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.SITE=staged;builder.build()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(staged)))
threading.Thread(target=server.serve_forever,daemon=True).start()
checks=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
        for width in [390,1280]:
            context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
            context.route('https://**',lambda route:route.abort())
            page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/android-app/')
            assert page.locator('#library-backup').count()==1
            assert page.locator('#offline-downloads').count()==1
            assert page.locator('#subtitle-storage').count()==1
            assert page.locator('#optional-updates').count()==1
            assert '131 scoped scenarios' in page.locator('#phone-validation').inner_text()
            assert page.locator('.guide-actions a').first.get_attribute('href').endswith('/v0.1.1/MovieBox-Android-App-0.1.1.apk')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(OUT/f'guide-{width}.png'),full_page=True)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            assert page.locator('.native-scene img').get_attribute('src').endswith('android-native-0.1.1-home.png')
            assert page.locator('.native-scene .im a').get_attribute('href').endswith('android-native-0.1.1-home.png')
            assert '0.1.1 build 4' in page.locator('.native-scene .capture-caption').inner_text()
            assert page.locator('.native-scene img').evaluate("image=>{const photo=image.getBoundingClientRect(),frame=image.closest('.im').getBoundingClientRect();return photo.top>=frame.top-1&&photo.bottom<=frame.bottom+1}")
            page.locator('.native-scene').screenshot(path=str(OUT/f'native-project-{width}.png'))
            assert page.locator('.tally-list .tally-row:not([hidden])').count()==5
            assert '0.1.1'==page.locator('#native-version').inner_text()
            assert not errors,errors
            checks.append({'width':width,'nativeGuideSections':True,'publishedFixtureVersion':True,'fiveTallyRows':True,'noOverflow':True})
            context.close()
        browser.close()
finally:
    server.shutdown();server.server_close()
(OUT/'results.json').write_text(json.dumps({'checks':checks,'fixtureOnly':True,'applicationDownloads':0},indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'evidence':str(OUT),'applicationDownloads':0},indent=2))
