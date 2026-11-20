"""Public release metadata only. No app telemetry, credentials or user identifiers."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

REPOSITORIES = [('moviebox-android', 'Android'), ('moviebox-desktop', 'Windows'), ('moviebox-tizen', 'Samsung TV'), ('moviebox-android-tv', 'Android TV')]
OWNER = 'emransm877'

def classify(name, repo):
    name = name.lower()
    if name.endswith(('.sha256', '.sha512')) or name in ('sha256sums.txt', 'checksums.txt'):
        return 'checksums'
    if repo == 'moviebox-android' and re.fullmatch(r'moviebox-android-[0-9.]+\.apk', name):
        return 'apk'
    if repo == 'moviebox-android-tv' and re.fullmatch(r'moviebox-android-tv-[0-9.]+\.apk', name):
        return 'apk'
    if repo == 'moviebox-desktop' and re.fullmatch(r'moviebox-setup-[0-9.]+-windows-x64\.exe', name):
        return 'installer'
    if repo == 'moviebox-desktop' and re.fullmatch(r'moviebox-(?:desktop-)?[0-9.]+-windows-x64(?:-portable)?\.zip', name):
        return 'portable'
    if repo == 'moviebox-tizen' and re.fullmatch(r'moviebox-tv-[0-9.]+-install-bundle\.zip',name):
        return 'tv_bundle'
    if repo == 'moviebox-tizen' and re.fullmatch(r'moviebox-tv-[0-9.]+-unsigned\.wgt',name):
        return 'tv_widget'
    return 'other'

def normalise(repo, platform, releases):
    output = []
    for release in releases:
        if release.get('draft'): continue
        assets = []
        for asset in release.get('assets', []):
            url = asset['browser_download_url']
            if not url.startswith(f'https://github.com/{OWNER}/{repo}/releases/download/'):
                raise ValueError('Unexpected download origin')
            count = asset['download_count']
            if not isinstance(count, int) or count < 0: raise ValueError('Invalid download count')
            assets.append({'id': asset['id'], 'name': asset['name'], 'count': count,
                'kind': classify(asset['name'], repo), 'url': url, 'size': asset['size'],
                'createdAt': asset['created_at'], 'digest': asset.get('digest')})
        output.append({'tag': release['tag_name'], 'url': release['html_url'],
            'publishedAt': release['published_at'], 'prerelease': release['prerelease'], 'assets': assets})
    kinds = {kind: sum(a['count'] for r in output for a in r['assets'] if a['kind'] == kind)
             for kind in ('apk', 'installer', 'portable', 'tv_bundle', 'tv_widget', 'checksums', 'other')}
    return {'name': repo, 'platform': platform, 'url': f'https://github.com/{OWNER}/{repo}',
            'releases': output, 'kinds': kinds, 'packages': sum(kinds[k] for k in ('apk', 'installer', 'portable', 'tv_bundle', 'tv_widget')),
            'allAssets': sum(kinds.values())}

def update_history(history, snapshot):
    """Retain observed asset peaks when assets disappear or are replaced.

    This is a measurement series from collection start, not historical daily
    GitHub events. Re-observing an old ID never creates a false negative delta.
    """
    if history.get('schemaVersion', 1) != 1: raise ValueError('Unknown history schema')
    known = dict(history.get('assetPeaks', {}))
    for repo in snapshot['repositories']:
        for release in repo['releases']:
            for asset in release['assets']:
                key = repo['name'] + ':' + str(asset['id'])
                old = known.get(key, {})
                known[key] = {'count': max(asset['count'], old.get('count', 0)), 'kind': asset['kind'], 'repo': repo['name']}
    totals = {repo: sum(a['count'] for a in known.values() if a['repo'] == repo and a['kind'] in ('apk','installer','portable','tv_bundle','tv_widget')) for repo, _ in REPOSITORIES}
    point = {'at': snapshot['observedAt'], 'packages': totals}
    points = list(history.get('points', []))
    if not points:
        points = [point]
    elif points[-1]['at'][:13] == point['at'][:13] and len(points) > 1:
        points[-1] = point
    elif points[-1] != point:
        points.append(point)
    return {'schemaVersion': 1, 'trackingStartedAt': history.get('trackingStartedAt', snapshot['observedAt']),
            'assetPeaks': known, 'points': points}

def api(path):
    if not path.startswith('/repos/' + OWNER + '/'): raise ValueError('Unexpected repository')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'MovieBox-public-downloads', 'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GITHUB_TOKEN')
    if token: headers['Authorization'] = 'Bearer ' + token
    for attempt in range(3):
        try:
            with urlopen(Request('https://api.github.com' + path, headers=headers), timeout=25) as response:
                return json.load(response)
        except OSError:
            if attempt == 2: raise
            time.sleep(1 + attempt)

def collect():
    repositories = []
    for repo, platform in REPOSITORIES:
        releases = []
        for page in range(1, 101):
            batch = api(f'/repos/{OWNER}/{repo}/releases?per_page=100&page={page}')
            releases.extend(batch)
            if len(batch) < 100: break
        else: raise RuntimeError('Release pagination exceeded the safety limit')
        # Release responses may truncate their embedded assets; paginate explicitly.
        for release in releases:
            assets = []
            for page in range(1, 101):
                batch = api(f'/repos/{OWNER}/{repo}/releases/{release["id"]}/assets?per_page=100&page={page}')
                assets.extend(batch)
                if len(batch) < 100: break
            else: raise RuntimeError('Asset pagination exceeded the safety limit')
            release['assets'] = assets
        record = normalise(repo, platform, releases)
        latest = api(f'/repos/{OWNER}/{repo}/releases/latest')
        record['latestTag'] = latest['tag_name']
        repositories.append(record)
    return {'schemaVersion': 1, 'observedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'repositories': repositories}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'site/data')
    args = parser.parse_args()
    # Fetch and validate everything before replacing the last successful snapshot.
    snapshot = collect(); args.output.mkdir(parents=True, exist_ok=True)
    path = args.output/'history.json'
    old = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    history = update_history(old, snapshot)
    for name, data in [('latest.json', snapshot), ('history.json', history)]:
        target = args.output/name; temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8'); temporary.replace(target)
    print('Saved public asset counts:', {r['name']: {'packages': r['packages'], 'all_assets': r['allAssets']} for r in snapshot['repositories']})

if __name__ == '__main__': main()
