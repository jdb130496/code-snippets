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

