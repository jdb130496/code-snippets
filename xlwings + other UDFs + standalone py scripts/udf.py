import xlwings as xw
import rdrand
from randomgen import RDRAND
import sys
import numpy as np
import dask.dataframe as dd
from dask.distributed import Client
from scipy.optimize import newton
import pandas as pd
from datetime import datetime, timedelta
import calendar
import numpy as np
import os
import csv
import time
print(sys.executable)
@xw.func
@xw.arg('Lst', ndim=2)
def multiply_elements(Lst):
    # Separate lists and multiply each by 5
    new_Lst = [[(element*5)+3 for element in sub_list] for sub_list in Lst]
    return new_Lst
@xw.func
@xw.arg('Lst', ndim=2)
def multiply_elements_2(Lst):
    # Separate lists and multiply each by 5
    new_Lst = [[(element*4)+8 for element in sub_list] for sub_list in Lst]
    return new_Lst
@xw.func
@xw.arg('days_amounts', ndim=2)
def aging_buckets(days_amounts):
    aging_list = [
        (lambda day, amount: amount < 0, "Advance"),
        (lambda day, amount: 0 <= day < 31, "Not Due"),
        (lambda day, amount: 31 <= day < 61, "31-60 Days"),
        (lambda day, amount: 61 <= day < 91, "61-90 Days"),
        (lambda day, amount: 91 <= day < 181, "91-180 Days"),
        (lambda day, amount: 181 <= day < 366, "6 Months to 1 year"),
        (lambda day, amount: 366 <= day, "More than 1 year")
    ]
    result = [[next((label for condition, label in aging_list if condition(day[0], day[1])), 'No Match')] for day in days_amounts if len(day) == 2]
    return result
@xw.func
@xw.arg('days_amounts', ndim=2)
def aging_buckets_parallel(days_amounts):
    client = Client(n_workers=6, threads_per_worker=4)
    df = pd.DataFrame(days_amounts, columns=['days', 'amount'])
    df['days'] = pd.to_numeric(df['days'], errors='coerce')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    ddf = dd.from_pandas(df, npartitions=4)
    aging_list = [
            (lambda day, amount: int(amount) < 0, "Advance"),
            (lambda day, amount: 0 <= int(day) < 31, "Not Due"),
            (lambda day, amount: 31 <= int(day) < 61, "31-60 Days"),
            (lambda day, amount: 61 <= int(day) < 91, "61-90 Days"),
            (lambda day, amount: 91 <= int(day) < 181, "91-180 Days"),
            (lambda day, amount: 181 <= int(day) < 366, "6 Months to 1 year"),
            (lambda day, amount: 366 <= int(day), "More than 1 year")
            ]
    ddf['age_bucket'] = ddf.map_partitions(lambda df: df.apply(lambda row: next((label for condition, label in aging_list if condition(row['days'], row['amount'])), None), axis=1), meta=('days', 'object'))
    result_df = ddf.compute()
    result = [[item] for item in result_df['age_bucket'].values]
    client.close()
    return result
@xw.func
@xw.arg('date_and_months', ndim=2)
def EOMONTHM(date_and_months):
    result = []
    for row in date_and_months:
        dt = row[0]
        month_offset = int(row[1])
        year, month = divmod(dt.month - 1 + month_offset, 12)
        _, last_day = calendar.monthrange(dt.year + year, month + 1)
        eomonth = datetime(dt.year + year, month + 1, last_day)
        result.append([(eomonth - datetime(1899, 12, 30)).days])
    return result
@xw.func
@xw.arg('date_and_months', ndim=2)
def EDATEM(date_and_months):
    result = []
    for row in date_and_months:
        # The date is already a datetime.datetime object
        dt = row[0]
        month_offset = int(row[1])
        # Add the month offset to the current month and adjust the year if necessary
        year, month = divmod(dt.month - 1 + month_offset, 12)
        edate = datetime(dt.year + year, month + 1, dt.day)
        # Convert the datetime.datetime object back to an Excel date (ordinal)
        result.append([(edate - datetime(1899, 12, 30)).days])
    return result
@xw.func
@xw.arg('numbers', ndim=2)
def check_duplicates(numbers):
    # Flatten the list of lists
    numbers = [num for sublist in numbers for num in sublist]
    if len(numbers) == len(set(numbers)):
        return "No duplicates found."
    else:
        return "Duplicates found."
@xw.func
def RandomGennp(n):
    # Convert n to an integer
    n = int(n)
    # Create a new RDRAND generator
    rg = RDRAND()
    # Generate n random numbers, each composed of three 5-digit numbers
    numbers = [int((rg.random_raw() % 90000 + 10000) * 1e10 + (rg.random_raw() % 90000 + 10000) * 1e5 + (rg.random_raw() % 90000 + 10000)) for _ in range(n)]
    # Convert the list to a list of lists for xlwings
    numbers_list = [[number] for number in numbers]
    # Return the list of lists
    return numbers_list
import rdrand
rng = rdrand.RdRandom()
@xw.func
def generate_random_numbers_rdrand(num):
    # Generate the random numbers
    random_numbers = [[rng.randint(10**14, 10**15 - 1)] for _ in range(int(num))]
    return random_numbers
@xw.func
@xw.arg('x_values', ndim=2)
@xw.arg('z_values', ndim=2)
@xw.arg('target', numbers=float)
def wa_return(x_values, z_values, target):
    # Convert input lists of lists to numpy arrays
    x_values = np.array(x_values)
    z_values = np.array(z_values)
    # Define the function for which we want to find the root
    def func(y):
        return np.sum(x_values * ((1 + y / 4) ** z_values)) - target
    # Use the Newton-Raphson method to find the root
    y_initial_guess = 0.5
    y_solution = newton(func, y_initial_guess)
    return y_solution
#@xw.func
#def intel_rdrand_boost(NUM_NUMBERS, NUM_WORKERS, NUM_THREADS):
#    NUM_NUMBERS = int(NUM_NUMBERS)
#    NUM_WORKERS = int(NUM_WORKERS)
#    NUM_THREADS = int(NUM_THREADS)
#    numbers_ptr = dll.generateRandomNumbers(NUM_NUMBERS, NUM_WORKERS, NUM_THREADS)
#    numbers = [[int(numbers_ptr[i])] for i in range(NUM_NUMBERS)]
#    return numbers
import pandas as pd
@xw.func
@xw.arg('dates', ndim=2)
def date_buckets(dates):
    df = pd.DataFrame(dates, columns=['date'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    date_list = [
            (lambda date: (date.month == 4 and date.day >= 1) or (date.month == 5) or (date.month == 6 and date.day <= 15), "01/04 To 15/06"),
            (lambda date: (date.month == 6 and date.day >= 16) or (date.month == 7) or (date.month == 8) or (date.month == 9 and date.day <= 15), "16/06 To 15/09"),
            (lambda date: (date.month == 9 and date.day >= 16) or (date.month == 10) or (date.month == 11) or (date.month == 12 and date.day <= 15), "16/09 To 15/12"),
            (lambda date: (date.month == 12 and date.day >= 16) or (date.month == 1) or (date.month == 2) or (date.month == 3 and date.day <= 15), "16/12 To 15/03"),
            (lambda date: (date.month == 3 and date.day >= 16 and date.day <= 31), "16/03 To 31/03")
            ]
    df['bucket'] = df['date'].apply(lambda date: next((label for condition, label in date_list if condition(date)), None))
    result = [[item] for item in df['bucket'].values]
    return result
import requests
import json
from datetime import datetime
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
                dt_object = datetime.fromtimestamp(timestamp)
                # Format the datetime object as a string in the format 'dd/mm/yyyy'
                date_string = dt_object.strftime('%d/%m/%Y')
                # Add the converted date to the converted_dates list as a single-item list
                converted_dates.append([date_string])
    else:
        # If timestamps is a list of floats, convert each timestamp
        for timestamp in timestamps:
            timestamp = int(timestamp)
            dt_object = datetime.fromtimestamp(timestamp)
            date_string = dt_object.strftime('%d/%m/%Y')
            # Add the converted date to the converted_dates list as a single-item list
            converted_dates.append([date_string])
    # Return the list of lists with the converted dates
    return converted_dates
import pandas as pd
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
from datetime import datetime
import requests
@xw.func
def get_url_data_id_new(investingid, from_date, to_date):
    # Convert date strings to the required format
    from_date = datetime.strptime(from_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    to_date = datetime.strptime(to_date, "%d/%m/%Y").strftime("%Y-%m-%d")
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
import re
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
@xw.arg('replacement')
def REGEXREPLACE(excel_range, patterns, replacement):
    result = []
    if replacement is None:
        replacement = ""
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_result = cell
            for pattern in patterns:
                if re.search(pattern, cell_result):
                    cell_result = re.sub(pattern, replacement, cell_result)
            row_result.append(cell_result)
        result.append(row_result)
    return result
import pandas as pd
@xw.func
@xw.arg('dates', ndim=2)
def quarter_buckets(dates):
    df = pd.DataFrame(dates, columns=['date'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    quarter_list = [
            (lambda date: 4 <= date.month <= 6, "Q1"),
            (lambda date: 7 <= date.month <= 9, "Q2"),
            (lambda date: 10 <= date.month <= 12, "Q3"),
            (lambda date: 1 <= date.month <= 3, "Q4")
            ]
    df['quarter'] = df['date'].apply(lambda date: next((label for condition, label in quarter_list if condition(date)), None))
    result = [[item] for item in df['quarter'].values]
    return result
import re
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXFINDM(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            cell_result = []
            for pattern in patterns:
                match = re.search(pattern, cell_str,flags=re.UNICODE)
                if match:
                    cell_result.append(cell_str)  # Return the entire string
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("")
        result.append(row_result)
    return result
import pandas as pd
import requests
import json
from datetime import datetime
@xw.func
def fetch_crude_data(start_date, end_date):
    # Convert the dates from "dd/mm/yyyy" to "yyyy-mm-dd"
    start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    # Read the API key from the file
    with open('d:\\dev\\apikey.txt', 'r') as file:
        api_key = file.read().replace('\n', '')
    # Define the API URL
    url = f"https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[product][]=EPCBRENT&start={start_date}&end={end_date}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000&api_key={api_key}"
    # Send a GET request to the API
    response = requests.get(url)
    # Convert the response to JSON
    data = json.loads(response.text)
    # Extract the nested data under the "data" key
    nested_data = data['response']['data']
    # Convert the nested data to a pandas DataFrame
    df = pd.json_normalize(nested_data)
    # Convert the date to "dd/mm/yyyy" format
    df['period'] = pd.to_datetime(df['period']).dt.strftime('%d/%m/%Y')
    # Convert the 'value' column to float
    df['value'] = df['value'].astype(float)
    # Convert the DataFrame to a 2D list, including headers
    data_list = [df.columns.values.tolist()] + df.values.tolist()
    return data_list
@xw.func
def fetch_gold_data(start_date, end_date):
    # Convert the dates from "dd/mm/yyyy" to "yyyy-mm-dd"
    start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    # Read the API key from the file
    with open('d:\\dev\\apikey2.txt', 'r') as file:
        api_key = file.read().replace('\n', '')
    # Define the API URL
    url = f"https://api.metalpriceapi.com/v1/timeframe?api_key={api_key}&start_date={start_date}&end_date={end_date}&base=XAU&currencies=INR"
    # Send a GET request to the API
    response = requests.get(url)
    # Convert the response to JSON
    data = json.loads(response.text)
    # Extract the nested data under the "rates" key
    nested_data = data['rates']
    # Convert the nested data to a list of dictionaries
    data_list = [{'date': date, 'INR': rate['INR']} for date, rate in nested_data.items()]
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data_list)
    # Convert the date to "dd/mm/yyyy" format
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
    # Convert the 'INR' column to float
    df['INR'] = df['INR'].astype(float)
    # Convert the DataFrame to a 2D list, including headers
    data_list = [df.columns.values.tolist()] + df.values.tolist()
    return data_list
@xw.func
def fetch_commodity_data(base, start_date, end_date):
    # Convert the dates from "dd/mm/yyyy" to "yyyy-mm-dd"
    start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    # Read the API key from the file
    with open('d:\\dev\\apikey2.txt', 'r') as file:
        api_key = file.read().replace('\n', '')
    # Define the API URL
    url = f"https://api.metalpriceapi.com/v1/timeframe?api_key={api_key}&start_date={start_date}&end_date={end_date}&base={base}&currencies=INR"
    # Send a GET request to the API
    response = requests.get(url)
    # Convert the response to JSON
    data = json.loads(response.text)
    # Extract the nested data under the "rates" key
    nested_data = data['rates']
    # Convert the nested data to a list of dictionaries
    data_list = [{'date': date, 'INR': rate['INR']} for date, rate in nested_data.items()]
    # Convert the nested data to a list of dictionaries, skipping dates without 'INR'
    #data_list = [{'date': date, 'INR': rate['INR']} for date, rate in nested_data.items() if 'INR' in rate]
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data_list)
    # Convert the date to "dd/mm/yyyy" format
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
    # Convert the 'INR' column to float
    df['INR'] = df['INR'].astype(float)
    # Convert the DataFrame to a 2D list, including headers
    data_list = [df.columns.values.tolist()] + df.values.tolist()
    return data_list
from rdrand import RdSeedom
@xw.func
def generate_random_numbers_rdseed(n):
    s = RdSeedom()
    random_numbers = []
    n = int(n)
    while len(random_numbers) < n:
        # Generate a random integer with exactly 15 digits
        num = s.randint(100000000000000, 999999999999999)
        # Append the number as a list to create a list of lists
        random_numbers.append([num])
    return random_numbers
    return output_list
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import xlwings as xw
url='https://chartered.tax/fmv-of-equity-share-as-on-31st-january-2018/'
@xw.func
def get_shares_prices():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'tablepress-4'})
    table_io = StringIO(str(table))
    df = pd.read_html(table_io)[0]
    return df.values.tolist()
import re
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXLATEST(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            for pattern in patterns:
                if re.search(pattern, cell_str):
                    row_result.append(cell_str)
                    break
            else:
                row_result.append("")
        result.append(row_result)
    return result
import rdrand
import xlwings as xw

#@xw.func
#def RDSEED_EXCEL(min_val, max_val, count):
#    count=int(count)
#    random_numbers_rdseed = []
#    for _ in range(count):
#        random_number_rdseed = rdrand.RdSeedom().get_bits(64) % (max_val - min_val + 1) + min_val
#        random_numbers_rdseed.append(random_number_rdseed)
#    return [[random_number_rdseed_1] for random_number_rdseed_1 in random_numbers_rdseed]


