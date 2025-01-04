import requests
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup

# Define the Stellarium URL once at the beginning
STELLARIUM_URL = "http://192.168.1.214:8090/api"

# Function to convert a datetime object to Julian Day
#def datetime_to_julian_day(dt):
#    JD = dt.toordinal() + 1721424.5 + (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400
#    return JD
def datetime_to_julian_day(dt):
    # Add 5 hours and 30 minutes to the input datetime
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
    print(f"Request URL: {url}")
    print(f"Request Data: {data}")
    response = requests.post(url, data=data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    return {"status": "success"} if response.text.strip() == "ok" else {"status": "error"}

# Function to set time using Stellarium API
def set_time(julian_day, timerate):
    url = f"{STELLARIUM_URL}/main/time"
    data = {
        "time": float(julian_day),
        "timerate": float(timerate)
    }
    print(f"Request URL: {url}")
    print(f"Request Data: {data}")
    try:
        response = requests.post(url, data=data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        if response.text.strip() == "ok":
            return {"status": "success", "message": "Time set successfully"}
        else:
            return {"status": "error", "message": response.text}
    except requests.exceptions.RequestException as e:
        print(f"Error setting time: {e}")
        return {"status": "error", "message": str(e)}

# Function to get object information from Stellarium API
def get_object_info(obj_name):
    url = f"{STELLARIUM_URL}/objects/info?name={obj_name}"
    print(f"Request URL: {url}")
    try:
        response = requests.get(url)
        print(f"Response Status Code: {response.status_code}")
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching object info: {e}")
        return ""

# Function to parse the ecliptic longitude from HTML content using BeautifulSoup and convert to decimal degrees
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
def stelget(latitude, longitude, date_str, *objects):
    local_tz = pytz.timezone("Asia/Kolkata")
    local_date_time = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    local_date_time = local_tz.localize(local_date_time)
    julian_day = datetime_to_julian_day(local_date_time)
    print(f"Julian Day: {julian_day}")
    set_location_response = set_location(latitude, longitude)
    if set_location_response.get("status") != "success":
        print("Failed to set location.")
        return
    set_time_response = set_time(julian_day, 0)
    if set_time_response.get("status") != "success":
        print("Failed to set time.")
        return
    results = []
    for obj in objects:
        # Get the HTML content from Stellarium API
        html_content = get_object_info(obj)
        if html_content:
            # Parse the ecliptic longitude from the HTML content
            ecl_long = parse_ecl_lon(html_content)
            results.append(ecl_long)
            print(f"{obj.capitalize()} Ecliptic Longitude (J2000) in Decimal Degrees: {ecl_long}")
        else:
            print(f"Failed to get info for {obj}.")
            results.append(None)
    return results

# Test the function with provided inputs
results = stelget(22.3072, 73.1812, "31/03/2015 16:40:23", "Sun", "Moon")
print(results)

