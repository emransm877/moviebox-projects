"""Test-only archived analytics component; never copied into the public site.

Keeps cache/category/history component regressions useful after removal of the
history disclosure from the homepage. check_cinema tests the unmodified homepage.
"""
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

def with_history(content):
    text=content.decode('utf-8')
    if 'class="wrap history-wrap"' not in text:
        fixture=(Path(__file__).parent/'fixtures/download-history.html').read_text(encoding='utf-8')
        text=text.replace('<section class="reel" id="help"',fixture+'<section class="reel" id="help"',1)
    return text.encode('utf-8')

class HistoryFixtureHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path in ('/','/index.html'):
            content=with_history((Path(self.directory)/'index.html').read_bytes())
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
        else:super().do_GET()
