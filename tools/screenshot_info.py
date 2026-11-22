"""Choose genuine captures appropriate to the published release, never future mockups."""
from html import escape
import json
from pathlib import Path
from release_info import version_tuple

ASSETS=Path(__file__).resolve().parents[1]/'site/assets'
CAPTURES=json.loads((ASSETS/'screenshots.json').read_text(encoding='utf-8'))['captures']


def capture_for(repo, release):
    version=version_tuple(release['tag'])
    candidates=[item for item in CAPTURES if item['repo']==repo and version and version_tuple(item['version'])<=version]
    return max(candidates,key=lambda item:version_tuple(item['version']),default=None)


def picture(capture,prefix='assets/',phone=False):
    if not capture:return ''
    file=Path(capture['file']);stem=file.stem
    sources=', '.join(prefix+stem+'-'+str(width)+'.webp '+str(width)+'w' for width in capture['webpWidths'])
    sizes='(max-width:720px) 180px, 280px' if phone else '(max-width:720px) calc(100vw - 48px), 640px'
    return '<picture><source type="image/webp" srcset="'+escape(sources)+'" sizes="'+sizes+'"><img class="guide-screen'+(' guide-phone-shot' if phone else '')+'" src="'+escape(prefix+capture['file'])+'" width="'+str(capture['width'])+'" height="'+str(capture['height'])+'" loading="lazy" alt="'+escape(capture['caption'])+'"></picture>'


def figure(capture,prefix='../assets/',phone=False):
    return '<figure class="guide-capture'+(' phone-capture' if phone else '')+'">'+picture(capture,prefix,phone)+'<figcaption class="fine-print">'+escape(capture['caption'])+'</figcaption></figure>' if capture else ''
