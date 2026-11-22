"""Check the deployed public site; this cannot confirm Google's indexing state."""
import argparse,json,sys,time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from pathlib import Path

BASE='https://emransm877.github.io/moviebox-projects/'
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.h1=0;self.canonical=[];self.description='';self.robots='';self.title='';self.in_title=False;self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='link' and attrs.get('rel')=='canonical':self.canonical.append(attrs.get('href'))
        if tag=='meta' and attrs.get('name')=='description':self.description=attrs.get('content','')
        if tag=='meta' and attrs.get('name')=='robots':self.robots=attrs.get('content','')
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title+=data

def get(url):
    request=Request(url,headers={'User-Agent':'MovieBox-Project-SEO-Audit/1.0','Cache-Control':'no-cache'})
    try:
        with urlopen(request,timeout=25) as response:return response.status,response.read(),dict(response.headers)
    except HTTPError as error:return error.code,error.read(),dict(error.headers)

def audit():
    status,body,_=get(BASE+'sitemap.xml');assert status==200,('sitemap',status)
    urls=[element.text for element in ET.fromstring(body).iter() if element.tag.endswith('loc')]
    required={BASE,BASE+'windows/',BASE+'android/',BASE+'samsung-tv/',BASE+'help/',BASE+'android-tv/'}
    assert required.issubset(urls) and set(urls).issubset(required|{BASE+'android-app/'})
    def inspect(url):
        status,body,headers=get(url);assert status==200,(url,status)
        page=Page(body.decode('utf-8'));assert page.canonical==[url],(url,page.canonical)
        assert page.h1==1 and page.description and page.title,url
        assert 'noindex' not in page.robots.lower() and 'noindex' not in headers.get('X-Robots-Tag','').lower(),url
        return {'url':url,'status':status,'title':page.title,'canonical':page.canonical[0],'bytes':len(body)}
    with ThreadPoolExecutor(max_workers=5) as pool:pages=list(pool.map(inspect,urls))
    assert len({page['title'] for page in pages})==len(urls)
    missing_status,_,_=get(BASE+'seo-audit-page-that-does-not-exist/')
    assert missing_status==404,('soft404',missing_status)
    status,body,_=get('https://emransm877.github.io/moviebox-desktop/')
    old=Page(body.decode('utf-8'));assert status==200 and old.canonical==[BASE]
    assert 'http-equiv="refresh"' in body.decode('utf-8')
    files=list((Path(__file__).resolve().parents[1]/'site').glob('google*.html'))
    for verification in files:
        status,body,_=get(BASE+verification.name)
        assert status==200 and body==verification.read_bytes(),('verification-file',status)
    return {'pages':pages,'sitemap':'passed','missing_page_http_404':'passed','old_url_canonical_and_redirect':'passed','google_verification_file':'reachable' if files else 'not-configured','google_ownership_and_indexing':'Requires confirmation in the owner Google Search Console account; not inferred from public HTTP checks.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--attempts',type=int,default=1);parser.add_argument('--output');args=parser.parse_args()
    for attempt in range(max(1,args.attempts)):
        try:result=audit();break
        except (AssertionError,OSError) as error:
            if attempt+1>=args.attempts:raise
            print('Waiting for the published files to propagate.',file=sys.stderr);time.sleep(10)
    rendered=json.dumps(result,indent=2)
    if args.output:Path(args.output).write_text(rendered+'\n',encoding='utf-8')
    print(rendered)
