import sys
import urllib.request
from html.parser import HTMLParser

class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = ''
        self.links = []
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href', '')
    def handle_endtag(self, tag):
        if tag == 'a':
            self.href = ''
    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())
            if self.href:
                self.links.append((data.strip(), self.href))

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
url = sys.argv[1]
raw = opener.open(url, timeout=20).read()
encoding = 'gb18030' if 'sina.com' in url else 'utf-8'
p = Extract()
p.feed(raw.decode(encoding, 'replace'))
if len(sys.argv) < 3:
    for label, href in p.links:
        if any(t in label for t in ['2025', '2026', '年度报告', '半年度']):
            print(label, href)
else:
    text = '\n'.join(p.text)
    for term in sys.argv[2:]:
        start = 0
        count = 0
        while count < 8:
            pos = text.find(term, start)
            if pos < 0:
                break
            print('\n---', term, '---\n', text[max(0,pos-200):pos+2200])
            start = pos + len(term)
            count += 1
