"""Generate useful project pages and consistent search metadata from published data."""
from html import escape as e
import json,re,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from release_info import browser_source, display_version, published_release, theme_count, tizen_scope, version_tuple
from screenshot_info import capture_for, figure, picture

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
BASE='https://emransm877.github.io/moviebox-projects/'
FACEBOOK_PAGE='https://www.facebook.com/profile.php?id=61596772531631'
NATIVE_AVAILABLE=False
OWNER={'@type':'Person','@id':BASE+'#maintainer','name':'Emran Hossain','url':'https://github.com/emransm877'}
PAGES={
 '':('MovieBox Projects | Windows, Android & TV Apps','Independent MovieBox apps for Windows, Android phones, Samsung Tizen and Android TV. Find published downloads, installation guides, compatibility and live counts.'),
 'android-app/':('MovieBox Android App: Native APK Download & Setup','The independent native MovieBox Android phone app. Find its published APK, touch playback, subtitles, installation steps and documented device compatibility.'),
 'android-tv/':('MovieBox for Android TV & Google TV: APK Download & Setup','Download the independent MovieBox Android TV / Google TV APK. Find remote controls, native playback, installation steps, updates and documented compatibility limits.'),
 'windows/':('MovieBox for Windows: Downloads & Setup | Community Client','Download the independent MovieBox Windows client. Compare installer and portable ZIP downloads, Windows requirements, subtitles, saved lists and known limitations.'),
 'android/':('MovieBox Android APK Patch: Download & Installation Guide','Get the independent MovieBox Android patch for one known forced-update dialog. Read ARM64 compatibility, safe update steps and the limits of this APK.'),
 'samsung-tv/':('MovieBox for Samsung TV: Tizen Download & Setup Guide','Install the independent MovieBox Samsung Tizen TV client. Find the published bundle, remote features, tested TV model and certificate requirements.'),
 'help/':('MovieBox Installation Help & Troubleshooting | Community','Get installation help for independent MovieBox Windows, Android phone, Android TV and Samsung Tizen projects. Resolve package, signature and playback problems.')}

def product(data,name,kind):
    repo=next(r for r in data['repositories'] if r['name']==name)
    release=published_release(repo)
    if release is None:raise ValueError('No complete published download set for '+name)
    asset=next(a for a in release['assets'] if a['kind']==kind)
    return repo,release,asset

def head(path,extra=None):
    title,description=PAGES[path];prefix='../' if path else ''
    # Sharing platforms cache image URLs separately from page HTML. Change the
    # preview URL only when its maintained artwork changes, just like CSS/JS.
    share_digest=hashlib.sha256((SITE/'assets/community-share.png').read_bytes()).hexdigest()[:12]
    share_image=BASE+'assets/community-share.png?v='+share_digest
    graph=[OWNER,{'@type':'WebSite','@id':BASE+'#website','url':BASE,'name':'MovieBox Projects','creator':{'@id':OWNER['@id']},'inLanguage':'en','sameAs':[FACEBOOK_PAGE]}]
    page={'@type':'CollectionPage' if not path else 'WebPage','@id':BASE+path+'#page','url':BASE+path,'name':title,'description':description,'isPartOf':{'@id':BASE+'#website'},'inLanguage':'en'}
    graph.append(page)
    if path:
        graph.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'MovieBox Projects','item':BASE},{'@type':'ListItem','position':2,'name':{'windows/':'Windows','android/':'Android patch','android-app/':'Android app','samsung-tv/':'Samsung TV','android-tv/':'Android TV','help/':'Installation help'}[path],'item':BASE+path}]})
    if extra:graph.append(extra);page['mainEntity']={'@id':extra['@id']}
    verification={}
    config=SITE/'verification.json'
    if config.exists():verification=json.loads(config.read_text(encoding='utf-8'))
    tags=''
    for key,name in [('google','google-site-verification'),('bing','msvalidate.01')]:
        if verification.get(key):
            if not re.fullmatch(r'[A-Za-z0-9_-]{8,200}',verification[key]):raise ValueError('Invalid public verification code')
            tags+=f'<meta name="{name}" content="{e(verification[key])}">\n'
    return f'''<meta name="description" content="{e(description)}">
<meta name="robots" content="{'noindex,follow' if path=='android-app/' and not NATIVE_AVAILABLE else 'index,follow,max-image-preview:large'}">
<meta name="author" content="Emran Hossain"><meta name="theme-color" content="#05060a">
<link rel="canonical" href="{BASE+path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="MovieBox Projects">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{BASE+path}"><meta property="og:locale" content="en_US">
<meta property="og:image" content="{share_image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/png">
<meta property="og:image:alt" content="MovieBox community projects for Windows, Android phones, Android TV and Samsung Tizen">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(description)}"><meta name="twitter:image" content="{share_image}"><meta name="twitter:image:alt" content="Independent MovieBox projects for Windows, Android phones, Android TV and Samsung Tizen">
<link rel="icon" href="{prefix}assets/cinema-favicon.svg" type="image/svg+xml"><link rel="icon" href="{prefix}assets/cinema-favicon.ico" sizes="16x16 32x32 48x48"><link rel="alternate icon" href="{prefix}assets/cinema-icon-32.png" type="image/png"><link rel="apple-touch-icon" href="{prefix}assets/cinema-apple-touch.png" sizes="180x180">
{tags}<title>{e(title)}</title>
<script type="application/ld+json">{json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<',chr(92)+'u003c')}</script>'''

def presence_badge():
    return '<span class="presence-badge" id="live-presence" data-state="connecting" role="status" aria-live="polite" aria-label="Connecting to the live visitor count" title="Connecting to the live visitor count"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg><span id="presence-value">—</span><span class="presence-word">online</span></span>'

def shell(path,heading,intro,body,extra=None):
    prefix='../';label={'windows/':'Windows','android/':'Android patch','android-app/':'Android app','samsung-tv/':'Samsung TV','android-tv/':'Android TV','help/':'Installation help'}[path]
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{head(path,extra)}<link rel="stylesheet" href="../styles.css"></head><body>
<a class="skip" href="#main">Skip to content</a><header class="topbar wrap"><a class="brand" href="../"><img src="../assets/moviebox-logo.svg" alt="" width="34" height="36"><span>MovieBox Projects<span class="brand-note">INDEPENDENT COMMUNITY PROJECTS</span></span></a><nav aria-label="Main navigation"><a href="../windows/">Windows</a><a href="../android/">Android patch</a>{'<a href="../android-app/">Android app</a>' if NATIVE_AVAILABLE else ''}<a href="../samsung-tv/">Samsung TV</a><a href="../android-tv/">Android TV</a><a href="../help/">Help</a></nav><div class="header-meta">{presence_badge()}</div></header>
<main id="main" class="wrap guide"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../">MovieBox Projects</a><span aria-hidden="true"> / </span><span aria-current="page">{label}</span></nav><p class="eyebrow">PUBLISHED PROJECTS · DOCUMENTED LIMITS</p><h1>{heading}</h1><p class="lead">{intro}</p>{body}</main>
<footer class="wrap footer"><p>Independent projects maintained by <a href="https://github.com/emransm877">Emran Hossain</a>. Not affiliated with MovieBox, Google, Microsoft or Samsung.</p><div><a href="../">Project hub</a><a href="../#analytics">Download statistics</a><a href="../help/">Installation help</a></div></footer></body></html>'''

def software(path,name,version,asset,osname,description,screenshot=None):
    result={'@type':'SoftwareApplication','@id':BASE+path+'#application','name':name,'url':BASE+path,'softwareVersion':version.lstrip('v'),'applicationCategory':'MultimediaApplication','operatingSystem':osname,'description':description,'downloadUrl':asset['url'],'maintainer':{'@id':OWNER['@id']},'softwareHelp':BASE+'help/'}
    if screenshot:result['screenshot']=BASE+'assets/'+screenshot
    return result

def refresh_scene_capture(text, scene_class, capture, label, phone=False):
    """Use the same publication-matched capture for a project card and its link."""
    if not capture:return text
    # Keep responsive sources, but use the card's styles rather than guide margins.
    image=picture(capture,phone=phone).replace(' class="guide-screen'+(' guide-phone-shot' if phone else '')+'"','')
    markup='<div class="im'+(' ph' if phone else '')+'"><a href="assets/'+e(capture['file'])+'" aria-label="Open full '+e(label)+' screenshot">'+image+'</a></div>'
    pattern=r'(<article\b[^>]*class="[^\"]*\b'+re.escape(scene_class)+r'\b[^\"]*"[^>]*>)(.*?)(</article>)'
    def update(match):
        body=re.sub(r'<div class="im(?: ph)?">.*?</div>',lambda _:markup,match[2],count=1,flags=re.S)
        body=re.sub(r'<p class="capture-caption">.*?</p>',lambda _:'<p class="capture-caption">'+e(capture['caption'])+'</p>',body,count=1,flags=re.S)
        return match[1]+body+match[3]
    return re.sub(pattern,update,text,flags=re.S)

def native_maintenance_sections(release):
    """Describe maintenance features only after their actual release is selected.

    The release plan alone never promotes an APK or changes download counters.
    Exact validation counts belong only to the release that was checked.
    """
    version=version_tuple(release['tag'])
    if version is None or version < (0,1,1):return ''
    validation='<p>The current 0.1.1 build 4 passed 131 scoped scenarios and 29 unit tests on the maintainer\'s physical Android 17 phone. These checks do not establish compatibility with every phone, Android version, network or file provider. See the release validation record for the exact APK identity.</p>' if version==(0,1,1) else '<p>See the selected release\'s validation record for its exact APK identity, checks and known limits.</p>'
    return '''<section id="library-backup"><h2>Keep your saved titles safe</h2><p>In Me, choose Back up library to export My list and watch progress. Restore library backup merges a saved backup with your current library. It does not transfer account sessions, app settings or downloaded videos.</p><p>If saved data cannot be read, the recovery screen offers restoring a backup, saving the damaged data or starting a new library after confirmation. Do not uninstall or clear app data to repair a saved library.</p></section>
<section id="offline-downloads"><h2>Downloads and mobile data</h2><p>New downloads use Wi-Fi unless you explicitly allow mobile data for that file. Roaming is disabled. Downloads shows progress and useful failure messages; Retry requests a fresh source.</p><p>Only supported single-file videos can be saved. Offline HLS/DASH playlists are not supported, and the app does not turn every stream into an offline file. Format choices rely on the supplied source metadata; server and device behavior can vary.</p></section>
<section id="subtitle-storage"><h2>Subtitle storage stays bounded</h2><p>Cached subtitles have file, size and age limits. Me &rarr; Clear cached subtitles removes unused cached captions while keeping My list, history and the subtitle currently playing. It does not remove your downloaded videos.</p></section>
<section id="optional-updates"><h2>Updates are your choice</h2><p>Optional reminders check published release information while the app is in use. A reminder can wait until you leave the player. They are not instant push notifications, and the app does not silently download or install updates. You can turn reminders off or use Check for updates yourself.</p></section>
<section id="phone-validation"><h2>What was checked</h2>'''+validation+'''<p>Android 6.0/API 23 is the minimum target. The selected release's runtime evidence is from one physical phone; minimum-OS, low-end hardware, process-death restoration, whole-app accessibility and real carrier/OEM interruption coverage remain limited.</p></section>'''

def build():
    global NATIVE_AVAILABLE
    data=json.loads((SITE/'data/latest.json').read_text(encoding='utf-8'))
    (SITE/'release-info.js').write_text(browser_source(),encoding='utf-8')
    native_repo=next((repo for repo in data['repositories'] if repo['name']=='moviebox-android-native'),None)
    native_release=published_release(native_repo) if native_repo else None
    NATIVE_AVAILABLE=native_release is not None
    native_asset=next((asset for asset in native_release['assets'] if asset['kind']=='apk'),None) if native_release else None
    w,wr,wa=product(data,'moviebox-desktop','installer');portable=next(a for a in wr['assets'] if a['kind']=='portable')
    a,ar,aa=product(data,'moviebox-android','apk');t,tr,ta=product(data,'moviebox-tizen','tv_bundle')
    wshot=capture_for(w['name'],wr);ashot=capture_for(a['name'],ar);tshot=capture_for(t['name'],tr)
    window_body=f'''<div class="guide-actions"><a class="button primary" href="{wa['url']}">Download Windows installer {display_version(wr['tag'])}</a><a class="button secondary" href="{portable['url']}">Portable ZIP</a><a class="text-link" href="{wr['url']}">Release checksums and notes</a></div>
<section><h2>Choose the right Windows download</h2><p>The setup EXE installs MovieBox with Start menu and optional Desktop shortcuts. Python and administrator access are not required. The portable ZIP is useful if you prefer an extracted application folder: extract the complete archive and keep <code>_internal</code> beside <code>MovieBox.exe</code>.</p><p>The published stable download is <strong>{display_version(wr['tag'])}</strong>. Newer code on GitHub is not automatically included in this installer. Check the release tag when reporting a problem.</p>{figure(wshot)}<p class="fine-print">Catalogue content and artwork belong to their respective owners.</p></section>
<section><h2>Windows requirements and tested scope</h2><p>The installer targets Windows 10 version 1809 or newer on x64-compatible systems. Native playback has been exercised on Windows 11 x64. Windows 10 and ARM emulation are not separately certified; this download is not a macOS, Linux or 32-bit Windows app.</p><p>Use the project release links and compare the downloaded file with its published SHA-256 checksum. <a href="https://github.com/emransm877/moviebox-desktop/blob/main/docs/CODE_SIGNING.md">Windows signing and installation details</a>.</p></section>
<section><h2>Security and privacy</h2><p>Read the <a href="https://github.com/emransm877/moviebox-desktop/blob/main/docs/CODE_SIGNING.md">Windows signing and installation policy</a> and <a href="https://github.com/emransm877/moviebox-desktop/blob/main/docs/PRIVACY.md">privacy notice</a>. Historical previews remain available in the release archive; the primary buttons above use the complete published release.</p></section>
<section><h2>Playback, subtitles and your library</h2><p>The native Qt player supports available qualities, embedded audio tracks, compatible dubbed editions, fullscreen, seeking, subtitles and local SRT/WebVTT imports. My list and per-episode progress are stored locally. There are {theme_count(w,wr)} themes and separate Movies and TV Shows catalogues.</p><p>Available video sources, languages, subtitles and resolution tiers come from the upstream service. A 1080 label is not a guarantee of 1080 vertical picture rows in every widescreen file. Downloading this project does not change memberships or service restrictions.</p></section>
<section><h2>Update without removing your saved list</h2><p>Back up <code>%LOCALAPPDATA%\\MovieBoxDesktop</code> before troubleshooting. Application files and user-library data are separate. Optional GitHub reminders can be deferred, skipped or disabled; updates are not forced or installed automatically.</p><p>If your list appears missing or navigation freezes, report the exact downloaded version, Windows version, installer or ZIP, and the actions before the failure. Keep session files, account information and signed video URLs out of public issues.</p><a href="../help/">Read installation troubleshooting</a> · <a href="{w['url']}">Windows source and documentation</a></section>'''
    android_body=f'''<div class="guide-actions"><a class="button primary" href="{aa['url']}">Download Android patch {display_version(ar['tag'])}</a><a class="button secondary" href="{ar['url']}">Release notes and checksum</a></div>
{figure(ashot,phone=True)}<section><h2>What this Android patch changes</h2><p>This independent patch targets one reviewed English forced-update dialog in a specific upstream APK. It keeps the launcher label MovieBox and uses the separate package <code>com.community.mbox.in.popupfree</code>.</p><p><strong>General advertising removal is not implemented or verified.</strong> The original repository name contains “Adds”; that wording is not a verified ad-blocking claim. Memberships, login and available service access are unchanged.</p></section>
<section><h2>Install the APK on a supported phone</h2><ol><li>Use an ARM64 phone running Android 10/API 29 or newer.</li><li>Download the published APK above and compare its SHA-256 with the release checksum.</li><li>Open it using your browser or file manager. If Android requests installation permission, review the source and grant it only to the installer you are using.</li><li>Open MovieBox. Do not disable Play Protect or other device security protections.</li></ol><p>This is a sideloaded preview, not an official Google Play release. Older Android versions, other ABIs, every manufacturer and all 16 KB page-size devices have not been certified.</p></section>
<section><h2>Keep the existing app and data when updating</h2><p>An in-place Android update requires the same package and signing certificate. Do not uninstall a working copy just to bypass a signature conflict: doing so can erase local data. The separate patched package is not an update to an official installation with a different package name.</p><p>The upstream manifest version is preserved, so About/version text alone does not identify the patch. Use the downloaded release-file hash and signing identity. The published 0.2.0 APK has now been installed through a signature-matched in-place update on the maintainer's connected phone; launch, browsing and observed playback are bounded checks, not universal certification.</p></section>
<section><h2>Optional patch update notices</h2><p>The patch can check its public GitHub release metadata daily. Notices offer Download, Later, Skip and an opt-out. They open a validated release link and do not download or install APKs themselves. Notices are deferred during playback and uncertain activity states.</p><p>A translated or changed upstream dialog may need a new investigation. Report the exact prompt text, language, patch release, phone model and Android version without attaching APKs, credentials or device identifiers.</p><a href="{a['url']}">Android patch source and build requirements</a> · <a href="../help/">Installation help</a></section>'''
    tv_body=f'''<div class="guide-actions"><a class="button primary" href="{ta['url']}">Get Samsung TV bundle {display_version(tr['tag'])}</a><a class="button secondary" href="{tr['url']}">Release notes and checksums</a></div>
{figure(tshot)}<section><h2>Samsung Tizen TV is a separate platform</h2><p>This is a Samsung Tizen client, not an Android TV APK. It has remote-first browsing, native TV video playback, subtitles, available audio tracks, episode navigation and resume. The app runs independently on the TV after installation.</p><p>Published release: {display_version(tr['tag'])}. {('Recorded hardware check: '+tizen_scope(tr)+'.') if tizen_scope(tr) else 'Read the linked validation record for this release.'} The project targets Tizen 7 or newer; other models remain unverified. The downloaded package and its validation record define the tested scope.</p></section>
<section><h2>What you need before installing</h2><ul><li>A supported Samsung Tizen TV with Developer Mode enabled.</li><li>A PC with official Tizen SDK tools and the Samsung TV certificate extension.</li><li>Your own Samsung TV certificate profile authorized for the target TV's device ID.</li><li>The complete published installation bundle and its instructions.</li></ul><p>There is no universal signed WGT that can be installed on every Samsung TV. Certificates and device authorizations are required by the platform. Keep certificate passwords and private keys local.</p></section>
<section><h2>Install the published TV bundle</h2><ol><li>Download and extract the bundle, then read its <code>INSTALL-TV.md</code>.</li><li>Confirm the TV's local IP, Developer Mode settings and the correct host PC address.</li><li>Use the included helper with your SDK path and authorized certificate profile to sign and install the unsigned widget.</li><li>Open MovieBox on the TV and test remote navigation, playback, pause/resume and seeking.</li></ol><p>The PC is needed for developer installation, not to host the application during normal TV use. This package is not for LG webOS, Roku, Apple TV or Android TV.</p></section>
<section><h2>Playback and remote behavior</h2><p>Auto mode uses the TV HTML video engine for MP4 with application-scoped media request headers. Samsung AVPlay remains available for alternate formats and embedded audio tracks. Arrows, OK, Return and supported transport keys operate the TV interface.</p><p>Network interruptions, source formats and model-specific decoders can affect playback. For problems, include the TV model, Tizen version, downloaded release and the actions leading to the failure. Do not share your device ID, certificate files or signed video URLs publicly.</p><a href="{t['url']}/blob/main/docs/hardware-validation.md">Read hardware validation evidence</a> · <a href="{t['url']}">TV source and installation documentation</a></section>'''
    help_body='''<section><h2>Windows installer or portable ZIP?</h2><p>The installer is the simplest Windows option. For a portable copy, extract every file and keep <code>_internal</code> next to the executable. Use the <a href="../windows/">Windows download guide</a> to identify the currently published release.</p><h3>My saved list or progress looks empty</h3><p>Close extra application windows and back up <code>%LOCALAPPDATA%\\MovieBoxDesktop</code> before changing files. Preserve <code>library.json</code> and its backup. Do not reset or delete a library just to troubleshoot an application update.</p></section>
<section><h2>Android signature or installation problems</h2><p>An update needs the same package and signing certificate. Keep a working copy installed; uninstalling to work around an identity mismatch can remove data. The <a href="../android/">Android patch guide</a> explains supported devices, the separate package and preserved upstream version fields.</p><h3>Ads or an update prompt still appear</h3><p>General ad removal is not implemented. The patch targets one identified English forced-update dialog. If a different prompt appears, report its exact text and language instead of assuming every dialog is covered.</p></section>
<section><h2>Samsung TV cannot install the package</h2><p>Confirm that the device runs Tizen, not another TV operating system. The WGT requires developer installation and a certificate authorized for that specific TV. Review the <a href="../samsung-tv/">Samsung TV installation guide</a> before changing developer settings.</p><h3>Why does video buffer or fail to seek?</h3><p>Compare another playable title and note whether the interface itself responds. Service availability, network conditions, transport and TV decoders can each cause failures. The project's tested TV model does not establish compatibility with every Samsung model.</p></section>
<section><h2>Report a useful bug safely</h2><p>Include the platform, device/OS version, downloaded release, installation type, expected result and repeatable steps. A source-branch version and a downloaded release can contain different fixes. Crop screenshots to the app and remove personal information.</p><ul><li><a href="https://github.com/emransm877/moviebox-desktop/issues/new/choose">Windows issue form</a></li><li><a href="https://github.com/emransm877/moviebox-android/issues/new/choose">Android issue form</a></li><li><a href="https://github.com/emransm877/moviebox-tizen/issues">Samsung TV issues</a></li></ul><p>Never post passwords, account sessions, signing keys, certificate files, private logs, original APKs or signed stream URLs. Read each repository's security policy for sensitive reports.</p></section>
<section><h2>Independent projects and licensing</h2><p>This hub is maintained by Emran Hossain and is not the official MovieBox website. Independently authored project source is MIT licensed. That does not grant rights to upstream applications, their assets, trademarks or catalogue content. The Android patch does not review or replace all components in the derived APK.</p><p>Published downloads are listed for Windows, the Android phone patch, Samsung Tizen TV and Android TV / Google TV. Each has its own installation guide and compatibility limits.</p>{'<p>The separate <a href="../android-app/">native Android app</a> is also available; it is not an in-place update for the Android patch.</p>' if NATIVE_AVAILABLE else ''}<p>Experimental Apple builds are not presented as ready downloads.</p></section>'''
    atv,atvr,atva=product(data,'moviebox-android-tv','apk')
    atvshot=capture_for(atv['name'],atvr)
    androidtv_body=f'''<section><h2>Download MovieBox for Android TV</h2><p>The installed name is MovieBox. This is the independent Android TV / Google TV client, separate from the Android phone patch and Samsung Tizen widget.</p><div class="guide-actions"><a class="button primary" href="{atva['url']}">Download Android TV APK {display_version(atvr['tag'])}</a><a href="{atv['url']}/releases/tag/{atvr['tag']}">Release notes and checksum</a></div>{figure(atvshot)}</section><section><h2>Install on Android TV or Google TV</h2><ol><li>Download the APK from this project's release.</li><li>Transfer it to the TV and allow installation from your chosen file manager.</li><li>Open the APK and install. MovieBox appears in the TV launcher.</li></ol><p>A PC can use <code>adb -s YOUR_TV_SERIAL install -r MovieBox-Android-TV-{atvr['tag'].lstrip('v')}.apk</code> after you enable and approve your TV's developer connection. Root access is not required.</p><p>Minimum target: Android 6.0/API 23 with current Android System WebView. Older OS/WebView combinations and physical TV models are not universally certified. The APK has no architecture-specific application native libraries. Device codecs and network/source availability still matter.</p></section><section><h2>Features and remote controls</h2><p>Shared TV interface, {theme_count(atv,atvr)} themes, carousel, Movies/TV browsing, native Media3 playback, available subtitles and audio tracks, My list, resume and sparse episode autoplay.</p><p>Arrows move focus, OK selects and Back returns. In playback, OK pauses/resumes on the play control or unobstructed player; Left/Right seek from the hidden controls or seek bar. Up opens the episode drawer only when controls are hidden. Android provides the TV search keyboard.</p></section><section><h2>Updates and saved data</h2><p>Optional notices check published GitHub releases. They do not force installation or promise instant delivery while closed. Install newer public APKs with the same package and certificate to preserve the private library. A previous local debug prototype has a different signature; uninstalling it removes its data. Clearing data or uninstalling the public app also removes the library.</p></section><section><h2>Validation and known limits</h2><p>The exact signed, non-debuggable release passed generated 1080p native playback, remote pause/resume, repeated seeking, subtitles/audio, episode continuation, failure exit, navigation during playback and a separate cold-process library/theme/progress restore.</p><p>Full physical-device coverage, minimum-version coverage and complete live-service episodes are not certified. Background downloads, local file-picker integration and account flows are not complete desktop parity. Source qualities, captions and languages vary; no membership or DRM bypass is included.</p><a href="{atv['url']}/blob/main/docs/VALIDATION.md">Read exact validation evidence</a> · <a href="{atv['url']}/blob/main/docs/INSTALLATION.md">Full installation and update guide</a> · <a href="{atv['url']}/issues">Report an Android TV issue</a></section>'''
    help_body += '<section id="live-counter"><h2>What does the eye counter mean?</h2><p>It counts browser sessions active in the last 90 seconds across these project pages. Tabs share a random browser ID; hidden pages stop sending activity. No names, emails or page history are stored by the counter. Multiple devices, browser restrictions and simulated activity mean this is not an exact count of people. If the service is unavailable, a dash appears.</p><p>The short-lived ID and signed session are stored in your browser. After 30 minutes without activity a new ID is used. The server stores only the ID and expiry, and removes expired rows on later requests. Hosting providers process normal HTTP traffic. Add <code>?presence=off</code> to a page URL to exclude that visit.</p><a href="https://github.com/emransm877/moviebox-projects/blob/main/docs/LIVE_PRESENCE.md">Counter privacy and technical details</a></section>'
    nshot=capture_for(native_repo['name'],native_release) if NATIVE_AVAILABLE else None
    if NATIVE_AVAILABLE:
        native_body=f'''<section><h2>Download the native Android app</h2><p>This is MovieBox Android App, an independently authored phone client. The installed name is MovieBox. It is separate from the <a href="../android/">Android APK patch</a> and uses <code>org.emransm.moviebox.phone</code>.</p><div class="guide-actions"><a class="button primary" href="{e(native_asset['url'])}">Download Android App APK {display_version(native_release['tag'])}</a><a href="{e(native_release['url'])}">Release notes and checksum</a></div></section>
{figure(nshot,phone=True)}<section><h2>Install and keep your library</h2><ol><li>Use an Android phone running Android 6.0/API 23 or newer.</li><li>Download the APK from this project's release and compare its SHA-256 checksum.</li><li>Open the APK using your browser or file manager and approve installation from that source when Android asks.</li><li>Open MovieBox. Keep your device security protections enabled.</li></ol><p>Android 6.0/API 23 is the minimum target. Earlier app candidates were exercised on an Android 6 emulator. Those historical checks do not certify this selected APK on every Android version or phone; read its release validation record.</p><p>For later updates, install an APK with the same package and certificate over this one. Do not uninstall or clear data to troubleshoot an update: My list, progress and local downloads belong to this app's private storage.</p></section>
<section><h2>Playback made for touch</h2><p>Native Media3 playback, available audio and subtitles, per-episode resume, automatic episode continuation, touch seeking, volume and brightness gestures, screen-fit controls and ten selectable app icons. Tap a featured slider thumbnail to play that title.</p><p>Source availability, quality, languages and captions depend on the upstream service. Account login, live channels and complete upstream feature parity are not included. This app does not change memberships or protected service access.</p></section>
{native_maintenance_sections(native_release)}
<section><h2>Which Android download do I need?</h2><p><strong>Android App</strong> is this separate native phone client for Android 6 and newer. <strong>Android patch</strong> is a reviewed modification of a specific upstream APK, with Android 10/ARM64 requirements and a different package. They have separate release histories and libraries; one is not an in-place update for the other.</p><a href="{e(native_repo['url'])}">Source, validation and project documentation</a> &middot; <a href="{e(native_repo['url'])}/issues">Report an Android app issue</a></section>'''
    else:
        native_body='<section><h2>The first public APK is being prepared</h2><p>MovieBox Android App is a separate native phone client. Its download button will appear after a complete public release is available. The existing <a href="../android/">Android patch</a> remains available and is not replaced.</p></section>'
    pages={
      'android-app/':shell('android-app/','MovieBox Android App','An independent native phone app, separate from the Android patch.',native_body,software('android-app/','MovieBox Android App',native_release['tag'],native_asset,'Android 6.0+ / API 23+',PAGES['android-app/'][1],nshot['file'] if nshot else None) if NATIVE_AVAILABLE else None),
      'android-tv/':shell('android-tv/','MovieBox for Android TV & Google TV','A shared TV interface with native Android playback, remote controls and a signed APK.',androidtv_body,software('android-tv/','MovieBox Android TV — independent client',atvr['tag'],atva,'Android TV / Google TV; Android 6.0+ with current System WebView',PAGES['android-tv/'][1],atvshot['file'] if atvshot else None)),
      'windows/':shell('windows/','MovieBox for Windows','Published downloads and practical setup for the independent native Windows client.',window_body,software('windows/','MovieBox Desktop — independent Windows client',wr['tag'],wa,'Windows 10 1809+; x64',PAGES['windows/'][1],wshot['file'] if wshot else None)),
      'android/':shell('android/','MovieBox Android APK patch','One reviewed dialog patch, a separate installation, and clear limits.',android_body,software('android/','MovieBox Android — independent patch distribution',ar['tag'],aa,'Android 10+; ARM64',PAGES['android/'][1],ashot['file'] if ashot else None)),
      'samsung-tv/':shell('samsung-tv/','MovieBox for Samsung Tizen TV','A remote-first TV client with a documented developer-install process.',tv_body,software('samsung-tv/','MovieBox Samsung Tizen TV — independent client',tr['tag'],ta,'Samsung Tizen 7+',PAGES['samsung-tv/'][1],tshot['file'] if tshot else None)),
      'help/':shell('help/','Installation help & troubleshooting','Choose the correct package, preserve your data, and report a reproducible problem.',help_body)}
    for path,html in pages.items():
        (SITE/path).mkdir(exist_ok=True)
        html=html.replace('<body>','<body class="cinema-guide">').replace('src="../assets/moviebox-logo.svg"','src="../assets/cinema-favicon.svg"').replace('</head>','<link rel="stylesheet" href="../guides.css"><link rel="stylesheet" href="../cinema-guides.css"></head>')
        (SITE/path/'index.html').write_text(html,encoding='utf-8')
    index=SITE/'index.html';text=index.read_text(encoding='utf-8')
    if '<!-- seo:start -->' in text:text=re.sub(r'<!-- seo:start -->.*?<!-- seo:end -->','<!-- seo:start -->\n'+head('')+'\n<!-- seo:end -->',text,flags=re.S)
    else:
        start=text.index('  <meta name="description"');end=text.index('</head>')
        text=text[:start]+'<!-- seo:start -->\n'+head('')+'\n<!-- seo:end -->\n<link rel="stylesheet" href="styles.css"><script src="app.js" defer></script>\n'+text[end:]
    text=text.replace('<script src="app.js" defer></script>','<script src="live-counts.js" defer></script><script src="app.js" defer></script>') if 'src="live-counts.js"' not in text else text
    if not re.search(r'href="guides\.css(?:\?[^" ]*)?"',text):text=text.replace('</head>','<link rel="stylesheet" href="guides.css"></head>')
    if not re.search(r'src="release-info\.js(?:\?[^" ]*)?"',text):
        text=text.replace('</head>','<script src="release-info.js" defer></script></head>')
    # Defer execution order follows document order, so the release helper must precede app.js.
    helper=re.search(r'<script src="release-info\.js(?:\?[^" ]*)?" defer></script>',text)
    if helper:
        text=text.replace(helper[0],'')
        text=re.sub(r'(<script src="(?:live-counts|app)\.js(?:\?[^" ]*)?" defer></script>)',lambda match:helper[0]+match[0],text,count=1)
    text=text.replace('Snapshots are scheduled daily. GitHub may delay scheduled jobs; the timestamp above shows the actual collection time.','Live counts are checked every 10 seconds while this page is visible. GitHub caching and API rate limits can delay the source data; any pause and the last verified time are shown above. Hourly snapshots retain observed growth.')
    if NATIVE_AVAILABLE:
        text=re.sub(r'(<[^>]+data-published-project="moviebox-android-native")(?: hidden)?',lambda match:match[1],text)
        for identifier in ['native-version']:
            text=re.sub(r'(<span[^>]*id="'+identifier+r'">)[^<]*(</span>)',lambda match:match[1]+display_version(native_release['tag'])+match[2],text)
        text=re.sub(r'(<span[^>]*data-version-source="native">)[^<]*(</span>)',lambda match:match[1]+display_version(native_release['tag'])+match[2],text)
        for attribute in ['id','data-download-source']:
            text=re.sub(r'(<a\b[^>]*'+attribute+'="native-download")(?: href="[^"]*")?',lambda match:match[1]+' href="'+e(native_asset['url'])+'"',text)
    else:
        text=re.sub(r'(<[^>]+data-published-project="moviebox-android-native")(?! hidden)',lambda match:match[1]+' hidden',text)
        for attribute in ['id','data-download-source']:
            text=re.sub(r'(<a\b[^>]*'+attribute+'="native-download") href="[^"]*"',lambda match:match[1],text)
    # Project cards and the main preview share publication-matched captures.
    for scene,capture,label,phone in [('windows-scene',wshot,'Windows',False),('native-scene',nshot,'Android App',True),('android-scene',ashot,'Android patch',True),('tv-scene',tshot,'Samsung TV',False),('androidtv-scene',atvshot,'Android TV',False)]:
        text=refresh_scene_capture(text,scene,capture,label,phone)
    # The main preview uses genuine, publication-matched captures for each platform.
    shots=[('windows','Windows',wshot),('tv','Android TV',atvshot)]
    if tshot:shots.append(('samsung','Samsung TV',tshot))
    tabs='<div class="preview-tabs" role="tablist" aria-label="Application screenshots">'+''.join('<button type="button" role="tab" id="preview-'+key+'-tab" aria-controls="preview-'+key+'-panel" aria-selected="'+('true' if n==0 else 'false')+'"'+('' if n==0 else ' tabindex="-1"')+'>'+label+'</button>' for n,(key,label,shot) in enumerate(shots))+'</div>'
    panels=''.join('<div class="preview-panel" id="preview-'+key+'-panel" role="tabpanel" aria-labelledby="preview-'+key+'-tab"'+('' if n==0 else ' hidden')+'><a href="assets/'+e(shot['file'])+'" aria-label="View the full '+label+' application screenshot">'+picture(shot)+'</a><p>'+e(shot['caption'])+'</p></div>' for n,(key,label,shot) in enumerate(shots) if shot)
    text=re.sub(r'(<div class="preview-wide">).*?(</div>\s*<figure class="preview-phone">)',lambda match:match[1]+tabs+panels+match[2],text,count=1,flags=re.S)
    phone_shot=nshot if NATIVE_AVAILABLE and nshot else ashot
    if phone_shot:
        phone_label='Android app' if NATIVE_AVAILABLE else 'Android patch'
        preview='<figure class="preview-phone"><span>'+phone_label+'</span><a href="assets/'+e(phone_shot['file'])+'" aria-label="View the full '+phone_label+' screenshot">'+picture(phone_shot,phone=True)+'</a><figcaption>'+e(phone_shot['caption'])+'</figcaption></figure>'
        text=re.sub(r'<figure class="preview-phone">.*?</figure>',lambda match:preview,text,count=1,flags=re.S)
    total='Five' if NATIVE_AVAILABLE else 'Four'
    text=re.sub(r'(<span data-project-total>)[^<]*(</span>)',lambda match:match[1]+total+match[2],text)
    text=re.sub(r'(<option value="all" data-all-projects>)[^<]*(</option>)',lambda match:match[1]+'All '+total.lower()+' projects'+match[2],text)
    text=re.sub(r'(<div class="project-grid")(?: data-project-count="[45]")?',lambda match:match[1]+' data-project-count="'+str(5 if NATIVE_AVAILABLE else 4)+'"',text)
    text=re.sub(r'(<div class="stat-grid")(?: data-project-count="[45]")?',lambda match:match[1]+' data-project-count="'+str(5 if NATIVE_AVAILABLE else 4)+'"',text)
    for prefix,repo,release,mapping in [('windows',w,wr,{'installer':'windows-download','portable':'portable-download'}),('android',a,ar,{'apk':'android-download'}),('tv',t,tr,{'tv_bundle':'tv-download'}),('androidtv',atv,atvr,{'apk':'androidtv-download'})]:
        text=re.sub(r'(<span\b[^>]*id="'+prefix+r'-version"[^>]*>)[^<]*(</span>)',lambda match:match[1]+e(display_version(release['tag']))+match[2],text)
        text=re.sub(r'(<span\b[^>]*data-version-source="'+prefix+r'"[^>]*>)[^<]*(</span>)',lambda match:match[1]+e(display_version(release['tag']))+match[2],text)
        for kind,identifier in mapping.items():
            asset=next(asset for asset in release['assets'] if asset['kind']==kind)
            for attribute in ['id','data-download-source']:
                text=re.sub(r'(<a\b[^>]*'+attribute+'="'+identifier+r'"[^>]*href=")[^"]*(")',lambda match:match[1]+e(asset['url'])+match[2],text)
    for prefix,repo,release in [('windows',w,wr),('tv',t,tr),('androidtv',atv,atvr)]:
        count=theme_count(repo,release)
        text=re.sub(r'(<span data-theme-source="'+prefix+r'">)[^<]*(</span>)',lambda match:match[1]+str(count)+match[2],text)
    tizen_label=tizen_scope(tr) or 'See release validation'
    text=re.sub(r'(<span data-tizen-scope>)[^<]*(</span>)',lambda match:match[1]+e(tizen_label)+match[2],text)
    index.write_text(text,encoding='utf-8')
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9');xml=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for path in PAGES:
        if path=='android-app/' and not NATIVE_AVAILABLE:continue
        node=ET.SubElement(xml,'url');ET.SubElement(node,'loc').text=BASE+path
    (SITE/'sitemap.xml').write_bytes(ET.tostring(xml,encoding='utf-8',xml_declaration=True))
    (SITE/'404.html').write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Page not found | MovieBox Projects</title><link rel="stylesheet" href="{BASE}styles.css"></head><body><main class="wrap guide"><p class="eyebrow">MOVIEBOX PROJECTS</p><h1>That page is not here.</h1><p>Find the published Windows, Android phone, Android TV and Samsung Tizen projects in the shared hub.</p><a class="button primary" href="{BASE}">Go to the project hub</a></main></body></html>',encoding='utf-8')
    # Content fingerprints prevent cached CSS/JS from mismatching fresh HTML.
    # Keep responsive screenshots in the static HTML, independent of JavaScript.
    for page_path in SITE.rglob('*.html'):
        if page_path.parent.name=='assets':continue
        if re.fullmatch(r'google[a-f0-9]+\.html',page_path.name):continue
        html=page_path.read_text(encoding='utf-8')
        if page_path.name=='404.html':
            html=html.replace('<body>','<body class="cinema-guide">')
            if 'cinema-favicon.svg' not in html:
                html=html.replace('</head>','<link rel="icon" href="'+BASE+'assets/cinema-favicon.svg" type="image/svg+xml"><link rel="alternate icon" href="'+BASE+'assets/cinema-icon-32.png"><link rel="apple-touch-icon" href="'+BASE+'assets/cinema-apple-touch.png"><link rel="stylesheet" href="'+BASE+'cinema-guides.css"></head>')
        if '<footer class="wrap footer"' in html and 'data-community-facebook' not in html:
            link='<a data-community-facebook href="'+e(FACEBOOK_PAGE)+'">Facebook community</a>'
            html=re.sub(r'(<footer class="wrap footer">.*?)(</div></footer>)',lambda match:match[1]+link+match[2],html,count=1,flags=re.S)
        if 'id="live-presence"' in html and 'src="presence.js' not in html and 'src="../presence.js' not in html:
            prefix='../' if page_path.parent!=SITE else ''
            html=html.replace('</head>','<script src="'+prefix+'presence.js" defer></script></head>')
        if page_path.name=='index.html' and (page_path.parent==SITE or page_path.parent.name in ('windows','android','android-app','samsung-tv','android-tv','help')) and 'usage.js' not in html:
            prefix='../' if page_path.parent!=SITE else ''
            html=html.replace('</head>','<script src="'+prefix+'usage.js" defer></script></head>')
        for name in ['styles.css','guides.css','trends.css','cinema.css','cinema-guides.css','cinema.js','app.js','live-counts.js','presence.js','usage.js','release-info.js']:
            digest=hashlib.sha256((SITE/name).read_bytes()).hexdigest()[:12]
            html=re.sub(r'((?:href|src)="(?:[^"?]*/)?'+re.escape(name)+r')(?:\?v=[a-f0-9]+)?"',lambda m:m[1]+'?v='+digest+'"',html)
        for name,widths in [('desktop-home',[640,1280]),('android-home',[360,720])]:
            pattern=r'<img\b[^>]*\bsrc="(?P<prefix>(?:\.\./)?assets/)'+name+r'\.png"[^>]*>'
            def responsive(match):
                tag=match[0];prefix=match['prefix']
                sources=', '.join(f'{prefix}{name}-{width}.webp {width}w' for width in widths)
                sizes='(max-width:720px) calc(100vw - 48px), (max-width:1100px) 90vw, 640px' if name=='desktop-home' else '(max-width:720px) 180px, 220px'
                return '<picture><source type="image/webp" srcset="'+sources+'" sizes="'+sizes+'">'+tag+'</picture>'
            html=re.sub(pattern,responsive,html) if '<picture>' not in html else html
        # Local previews and automation must not contribute production traffic.
        beacon = """<script data-cf-analytics>if(location.hostname==='emransm877.github.io'&&location.pathname.startsWith('/moviebox-projects/')&&!navigator.webdriver){const beacon=document.createElement('script');beacon.type='module';beacon.src='https://static.cloudflareinsights.com/beacon.min.js';beacon.dataset.cfBeacon=JSON.stringify({token:'639c7f632e8b4d9fb5a4836e2a8a3117'});document.head.append(beacon);}</script>"""
        html = re.sub(r'<script[^>]*(?:data-cf-beacon|data-cf-analytics)[^>]*>.*?</script>', '', html, flags=re.S)
        if page_path.name == 'index.html':
            html = html.replace('</head>', beacon + '</head>', 1)
        page_path.write_text(html,encoding='utf-8')
    print('Built published canonical pages, a gated native-phone guide, responsive captures and a noindex 404. No download assets are invented.')

if __name__=='__main__':build()
