import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
url = "https://insidepublicaccounting.com/top-firms/ipa-500/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"} # replace this with your desired user agent string
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')
tables = soup.find_all('table')
rows = []
for table in tables:
    rows += table.find_all('tr')
with open('ipa-500.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        writer.writerow(cols)
df = pd.read_csv('ipa-500.csv', delimiter='\t', encoding='ISO-8859-1')
df.to_csv('final_df.csv', sep='\t', index=False)
