import requests
from bs4 import BeautifulSoup
import os

url = "https://viewpoint.pwc.com/dt/us/en/fasb_financial_accou/asus_fulltext/2016/asu_201610revenue_fr/asu_201610revenue_fr_US/asu_201610revenue_fr_US.html#pwc-topic.dita_1940293703123410"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

with open(f"pwc.txt", "w", encoding="utf-8") as f:
    for tag_item in soup.find_all():
        if tag_item.text.strip():
            f.write(tag_item.text)

with open(f"pwc.txt", 'r+', encoding='latin1') as f:
    lines = [line for line in f.readlines() if line.strip()]
    f.seek(0)
    f.write(''.join(lines))
    f.truncate()
with open("pwc.txt", "rb") as f:
    contents = f.read().replace(b"\r", b"")
    
with open("pwc.txt", "wb") as f:
    f.write(contents)
