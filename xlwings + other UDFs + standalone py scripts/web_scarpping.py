import requests
import json
import datetime
import xlwings as xw

@xw.func
def get_url_data(country, symbol, from_date, to_date):
    from_date = datetime.datetime.strptime(from_date, "%d/%m/%Y").strftime("%m/%d/%Y")
    to_date = datetime.datetime.strptime(to_date, "%d/%m/%Y").strftime("%m/%d/%Y")
    url = f'http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com&type=historical_data&product=stocks&country={country}&symbol={symbol}&from_date={from_date}&to_date={to_date}'
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

