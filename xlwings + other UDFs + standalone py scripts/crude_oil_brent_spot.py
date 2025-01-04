import xlwings as xw
import pandas as pd
import requests
import json

@xw.func
def fetch_data(start_date, end_date):
    # Read the API key from the file
    with open('d:\\dev\\apikey.txt', 'r') as file:
        api_key = file.read().replace('\n', '')

    # Define the API URL
    url = f"https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[product][]=EPCBRENT&start={start_date}&end={end_date}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000&api_key={api_key}"

    # Send a GET request to the API
    response = requests.get(url)

    # Convert the response to JSON
    data = json.loads(response.text)

    # Convert the JSON data to a pandas DataFrame
    df = pd.json_normalize(data)

    return df

