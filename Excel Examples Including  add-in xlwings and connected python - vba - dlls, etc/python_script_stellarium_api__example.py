import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
# Stellarium API endpoint
STELLARIUM_URL = "http://192.168.1.3:8090/api"  # Update with your IP address
def set_location(latitude, longitude):
    url = f"{STELLARIUM_URL}/location/setlocationfields"
    data = {
        "latitude": latitude,
        "longitude": longitude,
        "altitude": 0,
        "name": "Custom Location",
        "country": "N/A"
    }
    print(f"Request URL: {url}")
    print(f"Request Data: {data}")
    try:
        response = requests.post(url, json=data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        # Check if the response indicates success
        response.raise_for_status()
        # Handle cases where the response is not JSON
        if response.text.strip() == "ok":
            return {"status": "success", "message": "Location set successfully"}
        else:
            print("Unexpected response content.")
            return {"status": "error", "message": response.text}
    except requests.exceptions.RequestException as e:
        print(f"Error setting location: {e}")
        return {"status": "error", "message": str(e)}
def datetime_to_julian_day(date_time):
    """Convert a datetime object to Julian Day."""
    # Julian Day for 0:00 UT on January 1, 2000 (J2000 epoch)
    J2000_EPOCH = 2451545.0
    # Convert the datetime object to a UTC timestamp
    timestamp = date_time.timestamp()
    # Calculate Julian Day
    julian_day = J2000_EPOCH + (timestamp / 86400.0)
    print(julian_day)
    return julian_day
def set_time(date_time):
    # Convert datetime to Julian Day
    julian_day = datetime_to_julian_day(date_time)
    url = f"{STELLARIUM_URL}/main/time"
    data = {
            "time": julian_day,
            "timerate": 1.0)
            }
    print(f"Request URL: {url}")
    print(f"Request Data: {data}")
    try:
        response = requests.post(url, json=data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error setting time: {e}")
        return None
def get_object_info(object_name):
    url = f"{STELLARIUM_URL}/objects/info?name={object_name}"
    print(f"Request URL: {url}")
    try:
        response = requests.get(url)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error getting object info for {object_name}: {e}")
        return None
def parse_ecl_lon(html_content):
    # Use BeautifulSoup to parse the HTML and extract the ecliptic longitude (J2000)
    soup = BeautifulSoup(html_content, 'html.parser')
    for line in soup.stripped_strings:
        if "Ecl. long./lat. (J2000.0)" in line:
            parts = line.split(":")
            if len(parts) > 1:
                ecl_long = parts[1].split("/")[0].strip()
                return ecl_long
    return "N/A"
def stelget(latitude, longitude, date_str, *objects):
    # Convert local date string to datetime object
    local_tz = pytz.timezone("Asia/Kolkata")
    local_date_time = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    local_date_time = local_tz.localize(local_date_time)
    # Convert local datetime to UTC
    utc_date_time = local_date_time.astimezone(pytz.utc)
    julian_day = datetime_to_julian_day(utc_date_time)
    print(f"Julian Day: {julian_day}")
    # Set location
    set_location_response = set_location(latitude, longitude)
    if set_location_response.get("status") != "success":
        print("Failed to set location.")
        return
    # Set time in UTC
    #set_time_response = set_time(utc_date_time)
    #if not set_time_response:
    #    print("Failed to set time.")
    #    return
    results = {}
    for obj in objects:
        # Get ecliptic longitude of the specified celestial object
        html_content = get_object_info(obj)
        if html_content:
            ecl_long = parse_ecl_lon(html_content)
            ecl_long = ecl_long.replace(r'Â°', '')
#            ecl_long_clean = ecl_long_clean.replace(r"\\'","")
            results[obj] = ecl_long
            print(f"{obj.capitalize()} Ecliptic Longitude (J2000): {ecl_long}")
        else:
            print(f"Failed to get info for {obj}.")
    return results
# Example usage
if __name__ == "__main__":
    # Example city coordinates: Baroda
    latitude = 22.3072
    longitude = 73.1812
    date_str = "25/09/2018 09:37:00"  # Example local date and time
    # Get ecliptic longitudes for the Sun and Moon
    longitudes = stelget(latitude, longitude, date_str, "Sun", "Moon")
    print(longitudes)
