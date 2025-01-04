import xlwings as xw
import requests
import json
from datetime import datetime, timedelta
@xw.func
@xw.arg('input_data_2', ndim=2)
def get_sunrise_sunset(input_data_2):
#    del date, latitude, longitude, timezone, response, payload, data, key_values
    # Read API endpoint
    print(input_data_2)
    url = "https://api.sunrisesunset.io/json"
    # Process input data
    date1 = input_data_2[0][0]
    latitude = input_data_2[0][1]
    longitude = input_data_2[0][2]
    timezone = input_data_2[0][3]
    if isinstance(date1, (int, float)):
        date = datetime(1899, 12, 30) + timedelta(days=date1)
    else:
        date = date1
    # Set payload
    payload = {
        "lat": latitude,
        "lng": longitude,
        "date": date,
        "timezone": timezone
    }
    # Send GET request
    response = requests.get(url, params=payload)
    # Load JSON response
    print(response.json())
    data = response.json()
    keys_values = data["results"]
    sunrise_key = next(key for key in keys_values if key == "sunrise")
    sunset_key = next(key for key in keys_values if key == "sunset")
    # Extract sunrise and sunset timings
    sunrise = data["results"]["sunrise"]
    sunset = data["results"]["sunset"]
    sunrise_time = datetime.strptime(sunrise, '%I:%M:%S %p').time()
    sunset_time = datetime.strptime(sunset, '%I:%M:%S %p').time()
        # Combine date and time
    if isinstance(date, str):
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date_obj = date.date()
    sunrise_dt = datetime.combine(date_obj, sunrise_time)
    sunset_dt = datetime.combine(date_obj, sunset_time)
     # Prepare the result
    resultnew1 = [
        ["Key", "Value"],
        [sunrise_key, sunrise_dt],
        [sunset_key, sunset_dt]
    ]
    return resultnew1
