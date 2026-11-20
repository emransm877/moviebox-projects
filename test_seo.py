"""Static contracts for indexable content, honest structured data and internal links."""
import json,unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import xml.etree.ElementTree as ET

SITE=Path(__file__).parent/'site';BASE='https://emransm877.github.io/moviebox-projects/'
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.meta={};self.links=[];self.title='';self.h1=0;self.canonical=[];self.json=[];self._title=False;self._json=False;self._buffer='';self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if tag=='title':self._title=True
        if tag=='h1':self.h1+=1
        if tag=='script' and a.get('type')=='application/ld+json':self._json=True;self._buffer=''
        if tag in ('a','link','script','img'):
            target=a.get('href') or a.get('src')
            if target:self.links.append(target)
        if tag=='img' and not a.get('alt') and a.get('alt')!='':raise AssertionError('Image without alt')
    def handle_data(self,data):
        if self._title:self.title+=data
        if self._json:self._buffer+=data
    def handle_endtag(self,tag):
        if tag=='title':self._title=False
        if tag=='script' and self._json:self.json.append(json.loads(self._buffer));self._json=False

class SEOTests(unittest.TestCase):
    def test_sitemap_canonical_pages_and_honest_schema(self):
        urls=[e.text for e in ET.parse(SITE/'sitemap.xml').getroot().iter() if e.tag.endswith('loc')]
        self.assertEqual(set(urls),{BASE,BASE+'windows/',BASE+'android/',BASE+'samsung-tv/',BASE+'help/',BASE+'android-tv/'})
        titles=[];descriptions=[]
        for url in urls:
            relative=url.removeprefix(BASE);path=SITE/relative/'index.html';page=Page(path.read_text(encoding='utf-8'))
            self.assertEqual(page.canonical,[url]);self.assertEqual(page.h1,1)
            self.assertIn('index,follow',page.meta['robots'])
            self.assertEqual(page.meta['og:url'],url);self.assertEqual(page.meta['twitter:card'],'summary_large_image')
            self.assertEqual(page.meta['og:image'],BASE+'assets/social-card.png')
            self.assertTrue(page.json);self.assertTrue(25<=len(page.title)<=75)
            self.assertTrue(90<=len(page.meta['description'])<=190)
            raw=json.dumps(page.json)
            self.assertNotIn('aggregateRating',raw);self.assertNotIn('ratingValue',raw)
            titles.append(page.title);descriptions.append(page.meta['description'])
            for link in page.links:
                if urlsplit(link).scheme or link.startswith('#'):continue
                target=(path.parent/unquote(urlsplit(link).path)).resolve()
                if target.is_dir():target=target/'index.html'
                self.assertTrue(target.exists(),str(target))
        self.assertEqual(len(set(titles)),6);self.assertEqual(len(set(descriptions)),6)
    def test_404_is_not_indexable_and_social_image_has_real_dimensions(self):
        self.assertIn('noindex',Page((SITE/'404.html').read_text(encoding='utf-8')).meta['robots'])
        import struct
        image=(SITE/'assets/social-card.png').read_bytes();self.assertEqual(image[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',image[16:24]),(1200,630))
    def test_only_four_published_projects_are_listed_as_downloads(self):
        text=(SITE/'index.html').read_text(encoding='utf-8')
        for name in ['windows-download','android-download','tv-download','androidtv-download']:self.assertIn('id="'+name+'"',text)
        self.assertNotIn('id="ios-download"',text);self.assertNotIn('id="macos-download"',text)
