"""Capture code-native social artwork; no synthetic app screenshots or reviews."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None,headless=True)
    page=browser.new_page(viewport={'width':1200,'height':630},device_scale_factor=1)
    page.goto((root/'site/assets/social-card.html').as_uri());page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
    page.screenshot(path=str(root/'site/assets/social-card.png'));browser.close()
    (root/'site/assets/community-share.png').write_bytes((root/'site/assets/social-card.png').read_bytes())
print('Rendered 1200×630 social preview from maintained HTML/CSS.')
