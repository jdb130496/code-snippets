#!/bin/bash
wl-paste --type text/html | \
python3 -c "
import sys
from html.parser import HTMLParser
import re

html = sys.stdin.read()

# Remove colors and backgrounds
html = re.sub(r'color\s*:[^;\"}\)]*', '', html)
html = re.sub(r'background(-color)?\s*:[^;\"}\)]*', '', html)

# Remove duplicate preview divs (Claude.ai shows message preview + full message)
# Remove consecutive duplicate paragraphs
html = re.sub(r'(<p[^>]*>)(.*?)(</p>)\s*\1\2\3', r'\1\2\3', html, flags=re.DOTALL)

# Collapse multiple <br> tags
html = re.sub(r'(<br\s*/?>(\s*)){2,}', '<br>', html)

# Collapse multiple empty paragraphs
html = re.sub(r'(<p[^>]*>\s*</p>\s*){2,}', '', html)

print(html)
" | \
wl-copy --type text/html
