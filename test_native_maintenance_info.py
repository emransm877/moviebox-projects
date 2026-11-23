"""Native maintenance presentation must follow published metadata, not the plan."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent/'tools'))
from build_site import native_maintenance_sections
from release_info import published_release


class NativeMaintenanceInformationTests(unittest.TestCase):
    def test_original_apk_does_not_gain_unpublished_features(self):
        self.assertEqual(native_maintenance_sections({'tag':'v0.1.0'}),'')

    def test_current_maintenance_explains_data_and_update_choices(self):
        text=native_maintenance_sections({'tag':'v0.1.1'})
        for phrase in ['Back up library','merges','Wi-Fi','Roaming is disabled',
                       'Retry requests a fresh source','Offline HLS/DASH',
                       'subtitle currently playing','not instant push notifications',
                       '131 scoped scenarios','29 unit tests','one physical phone']:
            self.assertIn(phrase,text)
        self.assertNotIn('/releases/download/',text)

    def test_future_release_does_not_inherit_specific_test_counts(self):
        text=native_maintenance_sections({'tag':'v0.1.2'})
        self.assertNotIn('131',text)
        self.assertNotIn('29 unit',text)
        self.assertIn('selected release',text)

    def test_unparseable_tag_does_not_infer_features(self):
        self.assertEqual(native_maintenance_sections({'tag':'test-preview'}),'')

    def test_incomplete_and_preview_maintenance_cannot_replace_existing_apk(self):
        old={'tag':'v0.1.0','url':'https://github.com/emransm877/moviebox-android-native/releases/tag/v0.1.0',
             'publishedAt':'2026-11-23T00:00:00Z','prerelease':False,
             'assets':[{'kind':'apk','url':'https://github.com/emransm877/moviebox-android-native/releases/download/v0.1.0/MovieBox-Android-App-0.1.0.apk'}]}
        new=copy.deepcopy(old);new.update(tag='v0.1.1',publishedAt='2026-11-24T00:00:00Z',assets=[])
        repo={'name':'moviebox-android-native','latestTag':'v0.1.1','releases':[old,new]}
        self.assertEqual(published_release(repo)['tag'],'v0.1.0')
        self.assertEqual(native_maintenance_sections(published_release(repo)),'')
        new['assets']=[{'kind':'apk','url':'https://github.com/emransm877/moviebox-android-native/releases/download/v0.1.1/MovieBox-Android-App-0.1.1.apk'}]
        new['prerelease']=True
        self.assertEqual(published_release(repo)['tag'],'v0.1.0')
        new['prerelease']=False
        self.assertEqual(published_release(repo)['tag'],'v0.1.1')


if __name__=='__main__':unittest.main()
