import copy
import unittest
from tools.collect_downloads import classify, normalise, update_history

def fixture(count=10):
    return {'schemaVersion':1,'observedAt':'2026-11-21T12:00:00+00:00','repositories':[{'name':'moviebox-desktop','releases':[{'assets':[{'id':1,'count':count,'kind':'installer'}]}]}]}

class DownloadAnalyticsTests(unittest.TestCase):
    def test_hourly_observations_preserve_first_baseline_and_latest_in_hour(self):
        first=fixture(10);history=update_history({},first)
        second=fixture(12);second['observedAt']='2026-11-21T12:30:00+00:00';history=update_history(history,second)
        third=fixture(14);third['observedAt']='2026-11-21T12:55:00+00:00';history=update_history(history,third)
        self.assertEqual(len(history['points']),2)
        self.assertEqual(history['points'][0]['packages']['moviebox-desktop'],10)
        self.assertEqual(history['points'][-1]['packages']['moviebox-desktop'],14)
        fourth=fixture(16);fourth['observedAt']='2026-11-21T13:05:00+00:00';history=update_history(history,fourth)
        self.assertEqual(len(history['points']),3)
    def test_checksums_never_inflate_application_downloads(self):
        self.assertEqual(classify('MovieBox-Setup-0.10.3-windows-x64.exe','moviebox-desktop'),'installer')
        self.assertEqual(classify('MovieBox-Desktop-0.10.3-windows-x64.zip','moviebox-desktop'),'portable')
        self.assertEqual(classify('MovieBox-Android-0.2.0.apk','moviebox-android'),'apk')
        self.assertEqual(classify('MovieBox-Setup-0.10.3-windows-x64.exe.sha256','moviebox-desktop'),'checksums')
        self.assertEqual(classify('SHA256SUMS.txt','moviebox-desktop'),'checksums')
        self.assertEqual(classify('debug-evidence.zip','moviebox-desktop'),'other')
        self.assertEqual(classify('MovieBox-TV-0.9.2-install-bundle.zip','moviebox-tizen'),'tv_bundle')
        self.assertEqual(classify('MovieBox-TV-0.9.2-unsigned.wgt','moviebox-tizen'),'tv_widget')
    def test_deleted_reset_and_new_assets_preserve_observed_history(self):
        baseline=fixture();history=update_history({},baseline)
        next_day=fixture(12);next_day['observedAt']='2026-11-22T12:00:00+00:00'
        history=update_history(history,next_day)
        deleted=fixture();deleted['observedAt']='2026-11-23T12:00:00+00:00';deleted['repositories'][0]['releases']=[]
        history=update_history(history,deleted)
        self.assertEqual(history['points'][-1]['packages']['moviebox-desktop'],12)
        reset=fixture(2);reset['observedAt']='2026-11-24T12:00:00+00:00'
        self.assertEqual(update_history(history,reset)['points'][-1]['packages']['moviebox-desktop'],12)
        reset['repositories'][0]['releases'][0]['assets'][0]['id']=2
        self.assertEqual(update_history(history,reset)['points'][-1]['packages']['moviebox-desktop'],14)
    def test_first_observation_is_a_baseline_not_invented_daily_growth(self):
        snapshot=fixture();history=update_history({},snapshot)
        self.assertEqual(history['points'][0]['packages']['moviebox-desktop'],10)
        self.assertEqual(history['trackingStartedAt'],snapshot['observedAt'])
        self.assertEqual(update_history(history,snapshot),history)
    def test_snapshot_excludes_drafts_and_rejects_foreign_download_origins(self):
        self.assertEqual(normalise('moviebox-desktop','Windows',[{'draft':True}])['allAssets'],0)
        asset={'id':1,'name':'x','download_count':2,'browser_download_url':'https://evil.invalid/x','size':1,'created_at':'2026-01-01'}
        with self.assertRaises(ValueError): normalise('moviebox-desktop','Windows',[{'draft':False,'assets':[asset]}])
