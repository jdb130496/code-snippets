import requests
import json
import datetime
import xlwings as xw
from bs4 import BeautifulSoup
import time

@xw.func
def convert_timestamps(timestamps):
    # Initialize an empty list to store the converted dates
    converted_dates = []
    # Check if timestamps is a list of lists
    if all(isinstance(i, list) for i in timestamps):
        # Iterate over each list in the input range
        for row in timestamps:
            # Iterate over each timestamp in the row
            for timestamp in row:
                # Convert the timestamp to an integer
                timestamp = int(timestamp)
                # Convert the Unix timestamp to a datetime object
                dt_object = datetime.datetime.fromtimestamp(timestamp)
                # Format the datetime object as a string in the format 'dd/mm/yyyy'
                date_string = dt_object.strftime('%d/%m/%Y')
                # Add the converted date to the converted_dates list as a single-item list
                converted_dates.append([date_string])
    else:
        # If timestamps is a list of floats, convert each timestamp
        for timestamp in timestamps:
            timestamp = int(timestamp)
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            date_string = dt_object.strftime('%d/%m/%Y')
            # Add the converted date to the converted_dates list as a single-item list
            converted_dates.append([date_string])
    # Return the list of lists with the converted dates
    return converted_dates

import pandas as pd
import xlwings as xw
import yfinance as yf
import datetime

@xw.func
def get_stock_data_yf(symbol, start_date, end_date):
    # Convert the date format from "dd/mm/yyyy" to "yyyy-mm-dd"
    start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")

    # Download historical market data
    hist = yf.Ticker(symbol).history(start=start_date, end=end_date)

    # Fill missing values with a default value (like 'N/A' or 0)
    hist.fillna('N/A', inplace=True)

    # Reset the index to include it in the output
    hist.reset_index(inplace=True)

    # Convert the DataFrame to a list of lists
    data = hist.values.tolist()

    # Add the column names as the first list in the output
    data.insert(0, hist.columns.tolist())

    return data

from datetime import datetime as dt
import re
@xw.func
def get_url_data_new(symbol, from_date, to_date):
    end_date_timestamp = int(dt.strptime(to_date, "%d/%m/%Y").timestamp())
    start_date_timestamp = int(dt.strptime(from_date, "%d/%m/%Y").timestamp())
    url = f'http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com&url=https%3A%2F%2Fin.investing.com%2Fequities%2F{symbol}-historical-data%3Fend_date%3D{end_date_timestamp}%26st_date%3D{start_date_timestamp}'
    Response = requests.get(url)
    time.sleep(5)
    soup = BeautifulSoup(Response.content, 'html.parser')
    div = soup.find('div', {'class': 'common-table-scroller js-table-scroller'})
    table = div.find('table', {'class': 'common-table medium js-table'})
    colgroup = table.find('colgroup')
    headers = [col.get('class')[0] for col in colgroup.find_all('col')]
    tbody = table.find('tbody')
    data = [
            [
                dt.strptime(" ".join([td.text.strip().rsplit(' ', 1)[0], re.sub(r'\D', '', td.text.strip().rsplit(' ', 1)[1])]), "%b %d, %Y") if i == 0 else float(td.text.replace(',', '')) if 1 <= i <= 4 else td.text.strip() 
                for i, td in enumerate(tr.find_all('td'))
                ]# .strftime("%d/%m/%Y") in dt.strptime(" ".join([td.text.strip().rsplit(' ', 1)[0], re.sub(r'\D', '', td.text.strip().rsplit(' ', 1)[1])]), "%b %d, %Y") at the end deleted to avoid date being converted to text.
            for tr in tbody.find_all('tr')
            ]
    result = [headers] + data
    return result
@xw.func
def get_url_data_id(investingid,from_date, to_date):
    from_date = datetime.datetime.strptime(from_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    to_date = datetime.datetime.strptime(to_date, "%d/%m/%Y").strftime("%Y-%m-%d")
#    investingid=int(investingid)
    url = f'http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com&url=https%3A%2F%2Fapi.investing.com%2Fapi%2Ffinancialdata%2Fhistorical%2F{investingid}%3Fstart-date%3D{from_date}%26end-date%3D{to_date}%26time-frame%3DDaily%26add-missing-rows%3Dfalse'
    response = requests.get(url)
    json_output = response.json()  # This is already a Python dictionary
    data_list = json_output['data']
    data = []
    if data_list:
        # Add headers as the first row in data
        headers = list(data_list[0].keys())
        data.append(headers)
        for item in data_list:
            if item is not None:
                data.append(list(item.values()))
    return data

import pandas as pd
import datetime
import requests
import xlwings as xw

@xw.func
def get_url_data_id_new(investingid, from_date, to_date):
    # Convert date strings to the required format
    from_date = datetime.datetime.strptime(from_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    to_date = datetime.datetime.strptime(to_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    
    # Construct the URL
    url = f'http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com&url=https%3A%2F%2Fapi.investing.com%2Fapi%2Ffinancialdata%2Fhistorical%2F{investingid}%3Fstart-date%3D{from_date}%26end-date%3D{to_date}%26time-frame%3DDaily%26add-missing-rows%3Dfalse'
    
    # Fetch data from the API
    response = requests.get(url)
    json_output = response.json()
    data_list = json_output['data']
    
    # Convert data_list into a pandas dataframe
    df = pd.DataFrame(data_list)
    
    # Remove commas from integer and float columns
    int_float_columns = ['last_close','last_open','last_max','last_min','change_precent','last_closeRaw', 'last_openRaw', 'last_maxRaw', 'last_minRaw', 'change_precentRaw']
    for col in int_float_columns:
        df[col] = df[col].astype(str).str.replace(',', '').astype('float')
    # Format columns
    df['direction_color'] = df['direction_color'].astype(str)
    df['rowDate'] = pd.to_datetime(df['rowDate'], format='%b %d, %Y').apply(lambda x: x.date())
    df['rowDateTimestamp'] = pd.to_datetime(df['rowDateTimestamp']).apply(lambda x: x.date())
    
    # Keep only the columns you want
#    columns_to_keep = ['direction_color', 'rowDate', 'rowDateRaw', 'rowDateTimestamp', 'last_close', 'last_open', 'last_max', 'last_min', 'volume', 'volumeRaw', 'change_precent']
#    df = df[columns_to_keep]
    
    # Create a matrix (list of lists) from the dataframe
    matrix = df.values.tolist()
    
    # Add headers at the beginning of the list
    headers = df.columns.tolist()
    matrix.insert(0, headers)

    return matrix


