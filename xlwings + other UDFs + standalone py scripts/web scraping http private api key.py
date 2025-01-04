from zenrows import ZenRowsClient
from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import re  # Regular expression library

@xw.func
def get_historical_data(script_name, end_date, start_date, api_key_path):
    # Convert dates from dd/mm/yyyy to timestamp
    end_date_timestamp = int(datetime.strptime(end_date, "%d/%m/%Y").timestamp())
    start_date_timestamp = int(datetime.strptime(start_date, "%d/%m/%Y").timestamp())
    with open(api_key_path, 'r') as f:
        api_key = f.read().strip()
    # Create the URL
    url = f"https://in.investing.com/equities/{script_name}-historical-data?end_date={end_date_timestamp}&st_date={start_date_timestamp}"
    # Fetch the data
    client = ZenRowsClient(api_key)
    resp = client.get(url)
    # Parse the HTML
    soup = BeautifulSoup(resp.content, 'html.parser')
    div = soup.find('div', {'class': 'common-table-scroller js-table-scroller'})
    table = div.find('table', {'class': 'common-table medium js-table'})
    colgroup = table.find('colgroup')
    headers = [col.get('class')[0] for col in colgroup.find_all('col')]
    tbody = table.find('tbody')
    # Get the data using list comprehension
    data = [
        [
            datetime.strptime(" ".join([td.text.strip().rsplit(' ', 1)[0], re.sub(r'\D', '', td.text.strip().rsplit(' ', 1)[1])]), "%b %d, %Y") if i == 0 else float(td.text.replace(',', '')) if 1 <= i <= 4 else td.text.strip() 
            for i, td in enumerate(tr.find_all('td'))
        ]# .strftime("%d/%m/%Y") in datetime.strptime(" ".join([td.text.strip().rsplit(' ', 1)[0], re.sub(r'\D', '', td.text.strip().rsplit(' ', 1)[1])]), "%b %d, %Y") at the end deleted to avoid date being converted to text.
        for tr in tbody.find_all('tr')
    ]
    # Combine headers and data
    result = [headers] + data
    return result

