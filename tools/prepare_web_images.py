"""Create smaller screenshot derivatives; retain the original device captures.

Requires the same Playwright browser used by check_site.py. Run only when a
source screenshot changes. No third-party image service or credentials used.
"""
import base64,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright

assets=Path(__file__).resolve().parents[1]/'site/assets'
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
    page=browser.new_page()
    for name,widths in [('desktop-home',[640,1280]),('android-home',[360,720])]:
        original=assets/(name+'.png')
        for width in widths:
            encoded=page.evaluate('''async ({source,width})=>{
                const image=new Image();image.src=source;await image.decode();
                const canvas=document.createElement('canvas');
                canvas.width=Math.min(width,image.naturalWidth);
                canvas.height=Math.round(image.naturalHeight*canvas.width/image.naturalWidth);
                canvas.getContext('2d').drawImage(image,0,0,canvas.width,canvas.height);
                return canvas.toDataURL('image/webp',0.88).split(',')[1];
            }''',{'source':'data:image/png;base64,'+base64.b64encode(original.read_bytes()).decode(),'width':width})
            target=assets/f'{name}-{width}.webp';target.write_bytes(base64.b64decode(encoded))
            print(json.dumps({'asset':target.name,'bytes':target.stat().st_size,'originalBytes':original.stat().st_size}))
    browser.close()
