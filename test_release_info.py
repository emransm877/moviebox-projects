"""Published download identity and future-release presentation contracts."""
import copy
import json
from pathlib import Path
import unittest
from tools.release_info import PLAN, display_version, published_release, theme_count


class ReleaseInformationTests(unittest.TestCase):
    def test_clean_version_labels_do_not_change_raw_tag_identity(self):
        self.assertEqual(display_version('v0.10.3-selfsigned.1'), '0.10.3 · Preview 1')
        self.assertEqual(display_version('v0.10.4'), '0.10.4')
        self.assertEqual(display_version('v0.2.0'), '0.2.0')
        self.assertEqual(display_version('release-with-custom-name'), 'release-with-custom-name')

    def test_upcoming_windows_release_needs_both_public_packages(self):
        repo={'name':'moviebox-desktop','latestTag':'v0.10.3','releases':[{
            'tag':'v0.10.3','publishedAt':'2026-11-14T00:00:00Z','prerelease':False,
            'assets':[{'kind':'installer','url':'https://github.com/emransm877/moviebox-desktop/releases/download/v0.10.3/setup.exe'},
                      {'kind':'portable','url':'https://github.com/emransm877/moviebox-desktop/releases/download/v0.10.3/app.zip'}]}]}
        previous = published_release(repo)
        candidate = copy.deepcopy(previous)
        candidate.update(tag='v0.10.4', publishedAt='2099-01-01T00:00:00Z', assets=[])
        repo['latestTag']='v0.10.4';repo['releases'].append(candidate)
        self.assertEqual(published_release(repo)['tag'], previous['tag'])
        self.assertEqual(theme_count(repo,published_release(repo)),5)
        installer = copy.deepcopy(next(asset for asset in previous['assets'] if asset['kind']=='installer'))
        installer['url']='https://github.com/emransm877/moviebox-desktop/releases/download/v0.10.4/MovieBox-Setup-0.10.4-windows-x64.exe'
        candidate['assets']=[installer]
        self.assertEqual(published_release(repo)['tag'], previous['tag'])
        portable = copy.deepcopy(next(asset for asset in previous['assets'] if asset['kind']=='portable'))
        portable['url']='https://github.com/emransm877/moviebox-desktop/releases/download/v0.10.4/MovieBox-Desktop-0.10.4-windows-x64.zip'
        candidate['assets'].append(portable)
        self.assertEqual(published_release(repo)['tag'],'v0.10.4')
        self.assertEqual(theme_count(repo,published_release(repo)),20)
        candidate['prerelease']=True
        self.assertEqual(published_release(repo)['tag'],previous['tag'])

    def test_published_asset_selection_does_not_drop_or_rewrite_history(self):
        snapshot=json.loads((Path(__file__).parent/'site/data/latest.json').read_text())
        before=copy.deepcopy(snapshot)
        for repo in snapshot['repositories']:
            self.assertIsNotNone(published_release(repo))
        self.assertEqual(snapshot,before)
        self.assertFalse(PLAN['unpublishedProjects']['nativeAndroidPhone']['replacesPublishedPatch'])
        self.assertEqual(PLAN['projects']['moviebox-android']['nextVersion'],'0.2.0')

    def test_expected_versions_never_generate_missing_download_links(self):
        snapshot=json.loads((Path(__file__).parent/'site/data/latest.json').read_text())
        index=(Path(__file__).parent/'site/index.html').read_text(encoding='utf-8')
        for repo in snapshot['repositories']:
            selected=published_release(repo)
            self.assertIn('/releases/download/'+selected['tag']+'/',index)
        for repo in snapshot['repositories']:
            expected='v'+PLAN['projects'][repo['name']]['nextVersion']
            if published_release(repo)['tag']!=expected:
                self.assertNotIn('/'+repo['name']+'/releases/download/'+expected+'/',index)



if __name__=='__main__':unittest.main()
