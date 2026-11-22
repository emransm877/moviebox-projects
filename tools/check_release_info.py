"""Mock future GitHub metadata: complete releases promote consistently, partial uploads do not."""
import copy
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'site/data/latest.json').read_text(encoding='utf-8'))
TARGETS={'moviebox-desktop':('windows','0.10.4','installer'),
         'moviebox-tizen':('tv','0.9.3','tv_bundle'),
         'moviebox-android-tv':('androidtv','0.2.0','apk')}

def recount(snapshot):
    # Keep simulated release lists and their summaries consistent, like the API.
    for repo in snapshot['repositories']:
        kinds={kind:sum(asset['count'] for release in repo['releases'] for asset in release['assets'] if asset['kind']==kind)
               for kind in ('apk','installer','portable','tv_bundle','tv_widget','checksums','other')}
        repo.update(kinds=kinds,packages=sum(kinds[k] for k in ('apk','installer','portable','tv_bundle','tv_widget')),allAssets=sum(kinds.values()))
    return snapshot

# Promotion must be exercised from the historical stable baseline, even after
# the staged versions really ship. Native publication is exercised separately
# by check_native_project; do not append a duplicate native repository there.
DATA['repositories']=[repo for repo in DATA['repositories'] if repo['name']!='moviebox-android-native']
for repo in DATA['repositories']:
    if repo['name'] not in TARGETS:continue
    target=tuple(int(part) for part in TARGETS[repo['name']][1].split('.'))
    def version(release):
        return tuple(int(part) for part in release['tag'].lstrip('v').split('-')[0].split('.'))
    repo['releases']=[release for release in repo['releases'] if version(release)<target]
    stable=[release for release in repo['releases'] if not release['prerelease']]
    assert stable,('Historical promotion fixture baseline missing',repo['name'])
    repo['latestTag']=max(stable,key=version)['tag']
recount(DATA)


def fixture(complete=True,preview=False):
    snapshot=copy.deepcopy(DATA)
    for repo in snapshot['repositories']:
        if repo['name'] not in TARGETS:continue
        prefix,target,_=TARGETS[repo['name']]
        prior=next(release for release in repo['releases'] if release['tag']==repo['latestTag'])
        release=copy.deepcopy(prior);old=release['tag'];release['tag']='v'+target
        release['url']=repo['url']+'/releases/tag/'+release['tag']
        release['publishedAt']='2099-01-01T00:00:00Z';release['prerelease']=preview
        for asset in release['assets']:
            asset['url']=asset['url'].replace('/'+old+'/', '/v'+target+'/').replace(old.lstrip('v'),target)
            asset['name']=asset['name'].replace(old.lstrip('v'),target)
            asset['id']+=90000000;asset['count']=0
        if not complete:release['assets']=[asset for asset in release['assets'] if asset['kind']=='installer'] if prefix=='windows' else []
        repo['latestTag']=release['tag'];repo['releases'].append(release)
    return recount(snapshot)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'site')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
            for complete,preview in [(False,False),(True,True),(True,False)]:
                snapshot=fixture(complete,preview)
                for width in [390,1440]:
                    context=browser.new_context(viewport={'width':width,'height':1000})
                    context.route('https://api.github.com/**',lambda route:route.fulfill(status=403,body='{}'))
                    context.route('**/data/latest.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(snapshot)))
                    page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function("document.getElementById('windows-count').textContent!=='—'")
                    for repo_name,(prefix,target,kind) in TARGETS.items():
                        current=next(repo for repo in DATA['repositories'] if repo['name']==repo_name)
                        expected='v'+target if complete and not preview else current['latestTag']
                        assert page.locator('#'+prefix+'-version').inner_text()==expected.lstrip('v')
                        identifier=prefix+'-download'
                        if prefix=='windows':identifier='windows-download'
                        primary=page.locator('#'+identifier).get_attribute('href')
                        assert '/'+expected+'/' in primary,(prefix,primary,expected)
                        assert page.locator('[data-download-source="'+identifier+'"]').get_attribute('href')==primary
                    expected_themes='20' if complete and not preview else '5'
                    for prefix in ['windows','androidtv']:
                        assert page.locator('[data-theme-source="'+prefix+'"]').inner_text()==expected_themes
                    assert page.locator('[data-tizen-scope]').inner_text().endswith('10' if complete and not preview else '9')
                    assert page.locator('#android-version').inner_text()=='0.2.0'
                    assert '/moviebox-android/releases/download/v0.2.0/' in page.locator('#android-download').get_attribute('href')
                    assert not errors,errors
                    checks.append({'width':width,'complete':complete,'preview':preview,'pass':True})
                    context.close()
            browser.close()
    finally:server.shutdown();server.server_close()
    print(json.dumps({'published_release_promotion':checks,'production_release_files_downloaded':0},indent=2))


if __name__=='__main__':main()
