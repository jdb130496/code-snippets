import xlwings as xw
import requests
import json
import numpy as np
from datetime import datetime
@xw.func
@xw.arg('input_data', np.array, ndim=2)
def get_panchang(input_data):
    # Read API key from file
    with open(r"D:\dev\api_key_freeastrologyapicom.txt", "r") as file:
        api_key = file.read().strip()
    # Set API endpoint
    url = "https://json.freeastrologyapi.com/complete-panchang"
    # Process input data
    date_time_int = input_data[0][0]
    latitude = input_data[0][1]
    longitude = input_data[0][2]
    timezone = input_data[0][3]
    # Convert Excel date to datetime object
    dt = datetime.fromordinal(int(date_time_int) + 693594)
    # Extract year, month, date, hours, minutes, seconds
    year = dt.year
    month = dt.month
    date = dt.day
    hours = dt.hour
    minutes = dt.minute
    seconds = dt.second
    # Set payload
    payload = json.dumps({
        "year": year,
        "month": month,
        "date": date,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "config": {
            "observation_point": "topocentric",
            "ayanamsha": "lahiri"
        }
    })
    # Set headers with API key
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key
    }
    # Send POST request
    response = requests.request("POST", url, headers=headers, data=payload)
    # Return response as JSON array
    panchang=json.loads(response.text)
    return panchang
