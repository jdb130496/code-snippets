import requests
import json
import numpy as np

url = 'http://api.scraperlink.com/investpy/?email=your@email.com&type=historical_data&product=stocks&country=india&symbol=TTPW&from_date=01/01/2023&to_date=12/31/2023'
response = requests.get(url)
json_output = response.json()
json_dict = json.loads(json_output)
#data_list = json_dict['data']
data = []
for item in json_output['data']:
    data.append(list(item.values()))
np_array = np.array(data)
numpy_array = np.array(data)

