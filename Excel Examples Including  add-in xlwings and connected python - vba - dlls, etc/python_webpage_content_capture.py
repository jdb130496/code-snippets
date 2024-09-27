import requests
from bs4 import BeautifulSoup

url = "https://viewpoint.pwc.com/dt/us/en/fasb_financial_accou/asus_fulltext/2016/asu_201610revenue_fr/asu_201610revenue_fr_US/asu_201610revenue_fr_US.html#pwc-topic.dita_1940293703123410"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
tags = ["div", "h4", "li"]
with open("pwc.txt", "w", encoding="utf-8") as f:
    for tag in tags:
        tag_list = soup.find_all(tag)
        for tag_item in tag_list:
            if tag_item.text.strip():
                f.write(tag_item.text + "\n")
with open('pwc.txt', 'r+',  encoding="utf-8") as f:
    lines = [line for line in f.readlines() if line.strip()]
    f.seek(0)
    f.write(''.join(lines))
    f.truncate()

