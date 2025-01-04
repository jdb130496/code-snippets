import argparse
import requests
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup
import time

# Define the Stellarium URL once at the beginning
STELLARIUM_URL = "http://192.168.1.214:8090/api"

# Function to convert a datetime object to Julian Day
def datetime_to_julian_day(dt):
    dt_adjusted = dt + timedelta(hours=6, minutes=30)
    JD = dt_adjusted.toordinal() + 1721424.5 + (dt_adjusted.hour - 12) / 24 + dt_adjusted.minute / 1440 + dt_adjusted.second / 86400
    return JD

# Function to set location
def set_location(latitude, longitude):
    url = f"{STELLARIUM_URL}/location/setlocationfields"
    data = {
        'latitude': latitude,
        'longitude': longitude,
        'altitude': 0,
        'name': 'Custom Location',
        'country': 'N/A'
    }
    response = requests.post(url, data=data)
    return {"status": "success"} if response.text.strip() == "ok" else {"status": "error"}

# Function to set time using Stellarium API
def set_time(julian_day, timerate):
    url = f"{STELLARIUM_URL}/main/time"
    data = {
        "time": float(julian_day),
        "timerate": float(timerate)
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return {"status": "success", "message": "Time set successfully"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

# Function to get object information from Stellarium API
def get_object_info(obj_name):
    url = f"{STELLARIUM_URL}/objects/info?name={obj_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return ""

# Function to parse the ecliptic longitude from HTML content
def parse_ecl_lon(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tags = soup.find_all(string=True)
    for tag in tags:
        if "Ecl. long./lat. (J2000.0):" in tag:
            longitude_part = tag.split(":")[1].split("/")[0].strip()
            longitude_part = longitude_part.replace("°", "").replace("Â", "")
            return float(longitude_part)
    return "N/A"

# Main function to get the ecliptic longitudes
def stelget(latitude, longitude, date_str, objects):
    local_tz = pytz.timezone("Asia/Kolkata")
    local_date_time = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    local_date_time = local_tz.localize(local_date_time)
    julian_day = datetime_to_julian_day(local_date_time)
    set_location_response = set_location(latitude, longitude)
    if set_location_response.get("status") != "success":
        print("Failed to set location.")
        return
    set_time_response = set_time(julian_day, 0)
    time.sleep(2)
    if set_time_response.get("status") != "success":
        print("Failed to set time.")
        return
    results = []
    for obj in objects:
        html_content = get_object_info(obj)
        if html_content:
            ecl_long = parse_ecl_lon(html_content)
            results.append(ecl_long)
            print(f"{obj.capitalize()} Ecliptic Longitude (J2000) in Decimal Degrees: {ecl_long}")
        else:
            print(f"Failed to get info for {obj}.")
            results.append(None)
    return results

# If the script is being run directly, parse arguments and call stelget
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get ecliptic longitudes for celestial objects.')
    parser.add_argument('latitude', type=float, help='Latitude of the location')
    parser.add_argument('longitude', type=float, help='Longitude of the location')
    parser.add_argument('date_time', type=str, help='Date and time in the format "dd/mm/yyyy hh:mm:ss"')
    parser.add_argument('objects', nargs='+', help='Names of the celestial objects to retrieve')
    args = parser.parse_args()

    stelget(args.latitude, args.longitude, args.date_time, args.objects)
# From command line in Windows, run like this: py stelget.py 22.3072 73.1812 "26/09/2016 15:14:58" Sun Moon
