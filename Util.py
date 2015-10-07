import time
import re
import html.parser
import unicodedata

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print('%s function took %0.3f ms' % (f.__name__, (time2-time1)*1000.0))
        return ret
    return wrap

def remove_invisible_characters(s):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')
 
def to_unicode(obj):
    if isinstance(obj,(str,bytes)):
        if not isinstance(obj, str):
            return str(obj, 'utf-8')
    return obj
 
def process_string(s):
    s = to_unicode(s)
    s = remove_invisible_characters(s)
    s = s.replace('&nbsp;', '')
    s = html.parser.HTMLParser().unescape(s)
    return s.strip()
