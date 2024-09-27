import xlwings as xw
import datetime
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
# Excel UDF to calculate tithi
@xw.func(async_mode='threading', volatile=False)
def tithinew(date_input):
    # Convert Excel date to datetime object
#    date_as_datetime = datetime.datetime.fromordinal(int(date_input) + 693594)
    # Format datetime object as string
    date_string = date_input.strftime("%d/%m/%Y %H:%M:%S")
    # Replace date string in sun-moon-elongj2000.ssc file
    with open(r"D:\Programs\Stellarium\scripts\sun-moon-elongj2000.ssc", "r") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if 'var date1' in line:
            lines[i] = f'var date1 = "{date_string}";\n'
            break
    with open(r"D:\Programs\Stellarium\scripts\sun-moon-elongj2000.ssc", "w") as file:
        file.writelines(lines)
    # Change to the correct directory
    os.chdir(r"D:\Programs\Stellarium\scripts")
    # Run curl command
    os.system('curl -d "id=sun-moon-elongj2000.ssc" http://localhost:8090/api/scripts/run')
    time.sleep(4)
    # Parse JSON string from sun-moon.txt file
    with open(r"C:\Users\dhawal123\AppData\Roaming\Stellarium\sun-moon.txt", "r") as file:
        json_string = file.read()
    data = json.loads(json_string)
    time.sleep(2)
    # Extract Sun and Moon's parameters
    sun_longitude = data["Sun"]["elongJ2000"]
    moon_longitude = data["Moon"]["elongJ2000"]
    # Calculate tithi number and name
    longitude_difference = moon_longitude - sun_longitude
    if longitude_difference < 0:
        longitude_difference += 360
    tithi_number = int(longitude_difference // 12) + 1
    paksha = 'Shukla' if tithi_number <= 15 else 'Krishna'
    tithi_names = ['Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima', 'Amavasya']
    tithi_index = (tithi_number - 1) % 15
    # Special case for Amavasya in Krishna Paksha
    if paksha == 'Krishna' and tithi_number == 30:
        tithi_name = tithi_names[-1]  # Amavasya
    else:
        tithi_name = tithi_names[tithi_index]
#    tithi_name = tithi_names[tithi_index]
    return f"{paksha} {tithi_name}"
import requests
import json
from datetime import datetime, timedelta
@xw.func(volatile=False)
@xw.arg('input_data', ndim=2)
def lunar_month(input_data):
    print(input_data)
    # Read API key from file
    with open(r"D:\dev\api_key_freeastrologyapicom.txt", "r") as file:
        api_key = file.read().strip()
    # Set API endpoint
    url = "https://json.freeastrologyapi.com/lunarmonthinfo"
    # Process input data
    date_time_int = input_data[0][0]
    latitude = input_data[0][1]
    longitude = input_data[0][2]
    timezone = input_data[0][3]
    if isinstance(date_time_int, (int, float)):
        date_time_int = datetime(1899, 12, 30) + timedelta(days=date_time_int)
#    else:
#        date_time_int = date_time_int
    # Convert Excel date to datetime object
    dt = date_time_int
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
    print(response.json())
   # Create a dictionary mapping original month names to desired names
    month_name_mapping = {
        "Pushyam": "Paush",
        "Maagham": "Maha",
        "Phalgunam": "Phagan",
        "Chaitram": "Chitra",
        "Vaisakham": "Vaishakh",
        "Jyeshtam": "Jeth",
        "Ashadam": "Ashadh",
        "Sravanam": "Shravan",
        "Bhadrapadam": "Bhadarvo",
        "Ashweeyujam": "Aaso",
        "Karthikam": "Kartak",
        "Maargasiram": "Magshar"
    }
    month_index_mapping = {
        10: 3,
        11: 4,
        12: 5,
        1: 6,
        2: 7,
        3: 8,
        4: 9,
        5: 10,
        6: 11,
        7: 12,
        8: 1,
        9: 2
    }
    # Return response as JSON array
    intoutput=response.json()
    panchang = json.loads(intoutput["output"])
    panchang["lunar_month_name"] = month_name_mapping[panchang["lunar_month_name"]]
    panchang["lunar_month_number"] = month_index_mapping[panchang["lunar_month_number"]]
    panchang["lunar_month_full_name"] = panchang["lunar_month_name"]
    headings = list(panchang.keys())
    values = list(panchang.values())
    return [headings, values]


