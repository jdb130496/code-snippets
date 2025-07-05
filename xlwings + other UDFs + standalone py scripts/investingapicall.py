import pandas as pd
from datetime import datetime
import requests
import xlwings as xw

@xw.func
def get_url_data_id_new_2(investingid, from_date, to_date):
    # Convert date strings to MM/DD/YYYY format
    from_date = datetime.strptime(from_date, "%d/%m/%Y").strftime("%m/%d/%Y")
    to_date = datetime.strptime(to_date, "%d/%m/%Y").strftime("%m/%d/%Y")

    # Construct the updated URL
    url = (
        f"http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com"
        f"&type=historical_data&product=stocks&country=india&id={investingid}"
        f"&from_date={from_date}&to_date={to_date}"
    )

    # Fetch data from the API
    response = requests.get(url)
    json_output = response.json()
    data_list = json_output['data']

    # Convert data_list into a pandas dataframe
    df = pd.DataFrame(data_list)

    # Remove commas from numeric columns
    int_float_columns = [
        'last_close','last_open','last_max','last_min',
        'change_precent','last_closeRaw', 'last_openRaw',
        'last_maxRaw', 'last_minRaw', 'change_precentRaw'
    ]
    for col in int_float_columns:
        df[col] = df[col].astype(str).str.replace(',', '').astype('float')

    # Format columns
    df['direction_color'] = df['direction_color'].astype(str)
    df['rowDate'] = pd.to_datetime(df['rowDate'], format='%b %d, %Y').dt.date
    df['rowDateTimestamp'] = pd.to_datetime(df['rowDateTimestamp']).dt.date

    # Create a matrix (list of lists) from the dataframe
    matrix = df.values.tolist()
    headers = df.columns.tolist()
    matrix.insert(0, headers)

    return matrix

