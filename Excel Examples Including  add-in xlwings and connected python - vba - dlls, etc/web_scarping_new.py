import requests
import json
import datetime
import xlwings as xw
from bs4 import BeautifulSoup
import time

@xw.func
def get_url_data_investingid(investingid,from_date, to_date):
    from_date = datetime.datetime.strptime(from_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    to_date = datetime.datetime.strptime(to_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    investingid=int(investingid)
    url = f'http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com&%2F{investingid}%3Fstart-date%3D{from_date}%26end-date%3D{to_date}%26time-frame%3DDaily%26add-missing-rows%3Dfalse'
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

import datetime
import xlwings as xw

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
