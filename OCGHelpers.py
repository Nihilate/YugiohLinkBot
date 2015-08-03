import re
import HTMLParser
import unicodedata
 
 
def remove_invisible_characters(s):
    return u''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')
 
 
html_parser = HTMLParser.HTMLParser()
 
 
def to_unicode(obj):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            return unicode(obj, 'utf-8')
    return obj
 
 
def process_string(s):
    s = to_unicode(s)
    s = remove_invisible_characters(s)
    s = s.replace('&nbsp;', '')
    s = html_parser.unescape(s)
    return s.strip()
 
 
def slugify(s):
    s = process_string(s)
    s = s.lower()
    return re.sub(r'\s+', '-', s)
