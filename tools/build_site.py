"""Generate useful project pages and consistent search metadata from published data."""
from html import escape as e
import json,re,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
BASE='https://emransm877.github.io/moviebox-projects/'
OWNER={'@type':'Person','@id':BASE+'#maintainer','name':'Emran Hossain','url':'https://github.com/emransm877'}
PAGES={
 '':('MovieBox Projects | Windows, Android & Samsung TV','Explore independent MovieBox projects for Windows, Android and Samsung Tizen TV. Get published downloads, installation guides and transparent download counts.'),
 'windows/':('MovieBox for Windows: Downloads & Setup | Community Client','Download the independent MovieBox Windows client. Compare installer and portable ZIP downloads, Windows requirements, subtitles, saved lists and known limitations.'),
 'android/':('MovieBox Android APK Patch: Download & Installation Guide','Get the independent MovieBox Android patch for one known forced-update dialog. Read ARM64 compatibility, safe update steps and the limits of this APK.'),
 'samsung-tv/':('MovieBox for Samsung TV: Tizen Download & Setup Guide','Install the independent MovieBox Samsung Tizen TV client. Find the published bundle, remote features, tested TV model and certificate requirements.'),
 'help/':('MovieBox Installation Help & Troubleshooting | Community','Get installation help for independent MovieBox Windows, Android and Samsung TV projects. Resolve package, signature, saved-list and playback problems.')}

def product(data,name,kind):
    repo=next(r for r in data['repositories'] if r['name']==name)
    release=next(r for r in repo['releases'] if r['tag']==repo['latestTag'] and not r['prerelease'])
    asset=next(a for a in release['assets'] if a['kind']==kind)
    return repo,release,asset

def head(path,extra=None):
    title,description=PAGES[path];prefix='../' if path else ''
    graph=[OWNER,{'@type':'WebSite','@id':BASE+'#website','url':BASE,'name':'MovieBox Projects','creator':{'@id':OWNER['@id']},'inLanguage':'en'}]
    page={'@type':'CollectionPage' if not path else 'WebPage','@id':BASE+path+'#page','url':BASE+path,'name':title,'description':description,'isPartOf':{'@id':BASE+'#website'},'inLanguage':'en'}
    graph.append(page)
    if path:
        graph.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'MovieBox Projects','item':BASE},{'@type':'ListItem','position':2,'name':{'windows/':'Windows','android/':'Android','samsung-tv/':'Samsung TV','help/':'Installation help'}[path],'item':BASE+path}]})
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
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="author" content="Emran Hossain"><meta name="theme-color" content="#0b1716">
<link rel="canonical" href="{BASE+path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="MovieBox Projects">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{BASE+path}"><meta property="og:locale" content="en_US">
<meta property="og:image" content="{BASE}assets/social-card.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/png">
<meta property="og:image:alt" content="MovieBox community projects for Windows, Android and Samsung Tizen TV">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(description)}"><meta name="twitter:image" content="{BASE}assets/social-card.png"><meta name="twitter:image:alt" content="Independent MovieBox projects for three platforms">
<link rel="icon" href="{prefix}assets/moviebox-logo.svg" type="image/svg+xml"><link rel="alternate icon" href="{prefix}assets/moviebox-icon.png">
{tags}<title>{e(title)}</title>
<script type="application/ld+json">{json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<',chr(92)+'u003c')}</script>'''

def shell(path,heading,intro,body,extra=None):
    prefix='../';label={'windows/':'Windows','android/':'Android','samsung-tv/':'Samsung TV','help/':'Installation help'}[path]
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{head(path,extra)}<link rel="stylesheet" href="../styles.css"></head><body>
<a class="skip" href="#main">Skip to content</a><header class="topbar wrap"><a class="brand" href="../"><img src="../assets/moviebox-logo.svg" alt="" width="34" height="36"><span>MovieBox Projects<span class="brand-note">INDEPENDENT COMMUNITY PROJECTS</span></span></a><nav aria-label="Main navigation"><a href="../windows/">Windows</a><a href="../android/">Android</a><a href="../samsung-tv/">Samsung TV</a><a href="../help/">Help</a></nav></header>
<main id="main" class="wrap guide"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../">MovieBox Projects</a><span aria-hidden="true"> / </span><span aria-current="page">{label}</span></nav><p class="eyebrow">PUBLISHED PROJECTS · DOCUMENTED LIMITS</p><h1>{heading}</h1><p class="lead">{intro}</p>{body}</main>
<footer class="wrap footer"><p>Independent projects maintained by <a href="https://github.com/emransm877">Emran Hossain</a>. Not affiliated with MovieBox, Google, Microsoft or Samsung.</p><div><a href="../">Project hub</a><a href="../#analytics">Download statistics</a><a href="../help/">Installation help</a></div></footer></body></html>'''

def software(path,name,version,asset,osname,description,screenshot=None):
    result={'@type':'SoftwareApplication','@id':BASE+path+'#application','name':name,'url':BASE+path,'softwareVersion':version.lstrip('v'),'applicationCategory':'MultimediaApplication','operatingSystem':osname,'description':description,'downloadUrl':asset['url'],'maintainer':{'@id':OWNER['@id']},'softwareHelp':BASE+'help/'}
    if screenshot:result['screenshot']=BASE+'assets/'+screenshot
    return result

def build():
    data=json.loads((SITE/'data/latest.json').read_text(encoding='utf-8'))
    w,wr,wa=product(data,'moviebox-desktop','installer');portable=next(a for a in wr['assets'] if a['kind']=='portable')
    a,ar,aa=product(data,'moviebox-android','apk');t,tr,ta=product(data,'moviebox-tizen','tv_bundle')
    window_body=f'''<div class="guide-actions"><a class="button primary" href="{wa['url']}">Download Windows installer {wr['tag']}</a><a class="button secondary" href="{portable['url']}">Portable ZIP</a><a class="text-link" href="{wr['url']}">Release checksums and notes</a></div>
<section><h2>Choose the right Windows download</h2><p>The setup EXE installs MovieBox with Start menu and optional Desktop shortcuts. Python and administrator access are not required. The portable ZIP is useful if you prefer an extracted application folder: extract the complete archive and keep <code>_internal</code> beside <code>MovieBox.exe</code>.</p><p>The published stable download is <strong>{wr['tag']}</strong>. Newer code on GitHub is not automatically included in this installer. Check the release tag when reporting a problem.</p><img class="guide-screen" src="../assets/desktop-home.png" alt="Actual MovieBox Windows 0.10.3 browsing interface" width="1440" height="940" loading="lazy"><p class="fine-print">Screenshot: packaged 0.10.3 interface. Catalogue content and artwork are third-party material.</p></section>
<section><h2>Windows requirements and tested scope</h2><p>The installer targets Windows 10 version 1809 or newer on x64-compatible systems. Native playback has been exercised on Windows 11 x64. Windows 10 and ARM emulation are not separately certified; this download is not a macOS, Linux or 32-bit Windows app.</p><p>The preview is not Authenticode signed. Download from the linked repository and compare its SHA-256 with the release checksum. Do not disable antivirus protections to run it.</p></section>
<section><h2>Playback, subtitles and your library</h2><p>The native Qt player supports available qualities, embedded audio tracks, compatible dubbed editions, fullscreen, seeking, subtitles and local SRT/WebVTT imports. My list and per-episode progress are stored locally. There are five themes and separate Movies and TV Shows catalogues.</p><p>Available video sources, languages, subtitles and resolution tiers come from the upstream service. A 1080 label is not a guarantee of 1080 vertical picture rows in every widescreen file. Downloading this project does not change memberships or service restrictions.</p></section>
<section><h2>Update without removing your saved list</h2><p>Back up <code>%LOCALAPPDATA%\\MovieBoxDesktop</code> before troubleshooting. Application files and user-library data are separate. Optional GitHub reminders can be deferred, skipped or disabled; updates are not forced or installed automatically.</p><p>If your list appears missing or navigation freezes, report the exact downloaded version, Windows version, installer or ZIP, and the actions before the failure. Keep session files, account information and signed video URLs out of public issues.</p><a href="../help/">Read installation troubleshooting</a> · <a href="{w['url']}">Windows source and documentation</a></section>'''
    android_body=f'''<div class="guide-actions"><a class="button primary" href="{aa['url']}">Download Android patch {ar['tag']}</a><a class="button secondary" href="{ar['url']}">Release notes and checksum</a></div>
<section><h2>What this Android patch changes</h2><p>This independent patch targets one reviewed English forced-update dialog in a specific upstream APK. It keeps the launcher label MovieBox and uses the separate package <code>com.community.mbox.in.popupfree</code>.</p><p><strong>General advertising removal is not implemented or verified.</strong> The original repository name contains “Adds”; that wording is not a verified ad-blocking claim. Memberships, login and available service access are unchanged.</p></section>
<section><h2>Install the APK on a supported phone</h2><ol><li>Use an ARM64 phone running Android 10/API 29 or newer.</li><li>Download the published APK above and compare its SHA-256 with the release checksum.</li><li>Open it using your browser or file manager. If Android requests installation permission, review the source and grant it only to the installer you are using.</li><li>Open MovieBox. Do not disable Play Protect or other device security protections.</li></ol><p>This is a sideloaded preview, not an official Google Play release. Older Android versions, other ABIs, every manufacturer and all 16 KB page-size devices have not been certified.</p></section>
<section><h2>Keep the existing app and data when updating</h2><p>An in-place Android update requires the same package and signing certificate. Do not uninstall a working copy just to bypass a signature conflict: doing so can erase local data. The separate patched package is not an update to an official installation with a different package name.</p><p>The upstream manifest version is preserved, so About/version text alone does not identify the patch. Use the downloaded release-file hash and signing identity. The published 0.2.0 APK has now been installed through a signature-matched in-place update on the maintainer's connected phone; launch, browsing and observed playback are bounded checks, not universal certification.</p></section>
<section><h2>Optional patch update notices</h2><p>The patch can check its public GitHub release metadata daily. Notices offer Download, Later, Skip and an opt-out. They open a validated release link and do not download or install APKs themselves. Notices are deferred during playback and uncertain activity states.</p><p>A translated or changed upstream dialog may need a new investigation. Report the exact prompt text, language, patch release, phone model and Android version without attaching APKs, credentials or device identifiers.</p><a href="{a['url']}">Android patch source and build requirements</a> · <a href="../help/">Installation help</a></section>'''
    tv_body=f'''<div class="guide-actions"><a class="button primary" href="{ta['url']}">Get Samsung TV bundle {tr['tag']}</a><a class="button secondary" href="{tr['url']}">Release notes and checksums</a></div>
<section><h2>Samsung Tizen TV is a separate platform</h2><p>This is a Samsung Tizen client, not an Android TV APK. It has remote-first browsing, native TV video playback, subtitles, available audio tracks, episode navigation and resume. The app runs independently on the TV after installation.</p><p>The published {tr['tag']} transport was exercised on a Samsung U8000F running Tizen 9. The project targets Tizen 7 or newer; other models remain unverified. Source-branch work is separate from that published package.</p></section>
<section><h2>What you need before installing</h2><ul><li>A supported Samsung Tizen TV with Developer Mode enabled.</li><li>A PC with official Tizen SDK tools and the Samsung TV certificate extension.</li><li>Your own Samsung TV certificate profile authorized for the target TV's device ID.</li><li>The complete published installation bundle and its instructions.</li></ul><p>There is no universal signed WGT that can be installed on every Samsung TV. Certificates and device authorizations are required by the platform. Keep certificate passwords and private keys local.</p></section>
<section><h2>Install the published TV bundle</h2><ol><li>Download and extract the bundle, then read its <code>INSTALL-TV.md</code>.</li><li>Confirm the TV's local IP, Developer Mode settings and the correct host PC address.</li><li>Use the included helper with your SDK path and authorized certificate profile to sign and install the unsigned widget.</li><li>Open MovieBox on the TV and test remote navigation, playback, pause/resume and seeking.</li></ol><p>The PC is needed for developer installation, not to host the application during normal TV use. This package is not for LG webOS, Roku, Apple TV or Android TV.</p></section>
<section><h2>Playback and remote behavior</h2><p>Auto mode uses the TV HTML video engine for MP4 with application-scoped media request headers. Samsung AVPlay remains available for alternate formats and embedded audio tracks. Arrows, OK, Return and supported transport keys operate the TV interface.</p><p>Network interruptions, source formats and model-specific decoders can affect playback. For problems, include the TV model, Tizen version, downloaded release and the actions leading to the failure. Do not share your device ID, certificate files or signed video URLs publicly.</p><a href="{t['url']}/blob/main/docs/hardware-validation.md">Read hardware validation evidence</a> · <a href="{t['url']}">TV source and installation documentation</a></section>'''
    help_body='''<section><h2>Windows installer or portable ZIP?</h2><p>The installer is the simplest Windows option. For a portable copy, extract every file and keep <code>_internal</code> next to the executable. Use the <a href="../windows/">Windows download guide</a> to identify the currently published release.</p><h3>My saved list or progress looks empty</h3><p>Close extra application windows and back up <code>%LOCALAPPDATA%\\MovieBoxDesktop</code> before changing files. Preserve <code>library.json</code> and its backup. Do not reset or delete a library just to troubleshoot an application update.</p></section>
<section><h2>Android signature or installation problems</h2><p>An update needs the same package and signing certificate. Keep a working copy installed; uninstalling to work around an identity mismatch can remove data. The <a href="../android/">Android patch guide</a> explains supported devices, the separate package and preserved upstream version fields.</p><h3>Ads or an update prompt still appear</h3><p>General ad removal is not implemented. The patch targets one identified English forced-update dialog. If a different prompt appears, report its exact text and language instead of assuming every dialog is covered.</p></section>
<section><h2>Samsung TV cannot install the package</h2><p>Confirm that the device runs Tizen, not another TV operating system. The WGT requires developer installation and a certificate authorized for that specific TV. Review the <a href="../samsung-tv/">Samsung TV installation guide</a> before changing developer settings.</p><h3>Why does video buffer or fail to seek?</h3><p>Compare another playable title and note whether the interface itself responds. Service availability, network conditions, transport and TV decoders can each cause failures. The project's tested TV model does not establish compatibility with every Samsung model.</p></section>
<section><h2>Report a useful bug safely</h2><p>Include the platform, device/OS version, downloaded release, installation type, expected result and repeatable steps. A source-branch version and a downloaded release can contain different fixes. Crop screenshots to the app and remove personal information.</p><ul><li><a href="https://github.com/emransm877/moviebox-desktop/issues/new/choose">Windows issue form</a></li><li><a href="https://github.com/emransm877/moviebox-android/issues/new/choose">Android issue form</a></li><li><a href="https://github.com/emransm877/moviebox-tizen/issues">Samsung TV issues</a></li></ul><p>Never post passwords, account sessions, signing keys, certificate files, private logs, original APKs or signed stream URLs. Read each repository's security policy for sensitive reports.</p></section>
<section><h2>Independent projects and licensing</h2><p>This hub is maintained by Emran Hossain and is not the official MovieBox website. Independently authored project source is MIT licensed. That does not grant rights to upstream applications, their assets, trademarks or catalogue content. The Android patch does not review or replace all components in the derived APK.</p><p>Published downloads are listed for Windows, the Android phone patch and Samsung Tizen TV. Android TV has a separate development-status card without a download. Experimental Apple builds are not presented as ready downloads.</p></section>'''
    pages={
      'windows/':shell('windows/','MovieBox for Windows','Published downloads and practical setup for the independent native Windows client.',window_body,software('windows/','MovieBox Desktop — independent Windows client',wr['tag'],wa,'Windows 10 1809+; x64',PAGES['windows/'][1],'desktop-home.png')),
      'android/':shell('android/','MovieBox Android APK patch','One reviewed dialog patch, a separate installation, and clear limits.',android_body,software('android/','MovieBox Android — independent patch distribution',ar['tag'],aa,'Android 10+; ARM64',PAGES['android/'][1],'android-home.png')),
      'samsung-tv/':shell('samsung-tv/','MovieBox for Samsung Tizen TV','A remote-first TV client with a documented developer-install process.',tv_body,software('samsung-tv/','MovieBox Samsung Tizen TV — independent client',tr['tag'],ta,'Samsung Tizen 7+; tested U8000F / Tizen 9',PAGES['samsung-tv/'][1])),
      'help/':shell('help/','Installation help & troubleshooting','Choose the correct package, preserve your data, and report a reproducible problem.',help_body)}
    for path,html in pages.items():
        (SITE/path).mkdir(exist_ok=True)
        html=html.replace('</head>','<link rel="stylesheet" href="../guides.css"></head>')
        (SITE/path/'index.html').write_text(html,encoding='utf-8')
    index=SITE/'index.html';text=index.read_text(encoding='utf-8')
    if '<!-- seo:start -->' in text:text=re.sub(r'<!-- seo:start -->.*?<!-- seo:end -->','<!-- seo:start -->\n'+head('')+'\n<!-- seo:end -->',text,flags=re.S)
    else:
        start=text.index('  <meta name="description"');end=text.index('</head>')
        text=text[:start]+'<!-- seo:start -->\n'+head('')+'\n<!-- seo:end -->\n<link rel="stylesheet" href="styles.css"><script src="app.js" defer></script>\n'+text[end:]
    text=text.replace('<script src="app.js" defer></script>','<script src="live-counts.js" defer></script><script src="app.js" defer></script>') if 'src="live-counts.js"' not in text else text
    if not re.search(r'href="guides\.css(?:\?[^" ]*)?"',text):text=text.replace('</head>','<link rel="stylesheet" href="guides.css"></head>')
    if 'id="refresh-live"' not in text:text=text.replace('<p id="snapshot-status"','<div class="live-refresh"><button type="button" id="refresh-live">Refresh live counts</button><p id="snapshot-status"').replace('Loading the last collected snapshot…</p></div>','Loading the last collected snapshot…</p></div></div>')
    text=text.replace('Snapshots are scheduled daily. GitHub may delay scheduled jobs; the timestamp above shows the actual collection time.','Live counts are checked every 10 seconds while this page is visible. GitHub caching and API rate limits can delay the source data; any pause and the last verified time are shown above. Hourly snapshots retain observed growth.')
    index.write_text(text,encoding='utf-8')
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9');xml=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for path in PAGES:
        node=ET.SubElement(xml,'url');ET.SubElement(node,'loc').text=BASE+path
    (SITE/'sitemap.xml').write_bytes(ET.tostring(xml,encoding='utf-8',xml_declaration=True))
    (SITE/'404.html').write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Page not found | MovieBox Projects</title><link rel="stylesheet" href="{BASE}styles.css"></head><body><main class="wrap guide"><p class="eyebrow">MOVIEBOX PROJECTS</p><h1>That page is not here.</h1><p>Find the published Windows, Android and Samsung TV projects in the shared hub.</p><a class="button primary" href="{BASE}">Go to the project hub</a></main></body></html>',encoding='utf-8')
    # Content fingerprints prevent cached CSS/JS from mismatching fresh HTML.
    # Keep responsive screenshots in the static HTML, independent of JavaScript.
    for page_path in SITE.rglob('*.html'):
        if page_path.parent.name=='assets':continue
        if re.fullmatch(r'google[a-f0-9]+\.html',page_path.name):continue
        html=page_path.read_text(encoding='utf-8')
        for name in ['styles.css','guides.css','app.js','live-counts.js']:
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
        page_path.write_text(html,encoding='utf-8')
    print('Built five canonical pages, responsive captures, fingerprinted assets and a noindex 404. No ratings or rankings are invented.')

if __name__=='__main__':build()
