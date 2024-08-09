from datetime import datetime
import pytz
import requests
# Define the Stellarium API URL
STELLARIUM_URL = "http://192.168.1.4:8090/api"  # Update with your IP address
def datetime_to_julian_day(date_time):
    """Convert a datetime object to Julian Day."""
    # Julian Day for 0:00 UT on January 1, 2000 (J2000 epoch)
    J2000_EPOCH = 2451545.0
    # Convert the datetime object to a UTC timestamp
    timestamp = date_time.timestamp()
    # Calculate Julian Day
    julian_day = J2000_EPOCH + (timestamp / 86400.0)
    print("Calculated Julian Day:", julian_day)  # Debugging output
    return julian_day
def set_time(date_time):
    # Convert datetime to Julian Day
    julian_day = datetime_to_julian_day(date_time)
    url = f"{STELLARIUM_URL}/main/time"
    data = {
        "time": float(julian_day),  # Ensure it's a float
        "timerate": 1.0  # Set timerate as a float
    }
#    data = {
#        "time": format(julian_day, ".16f"),
#        "timerate": format(1.0, ".16f")
#    }
#    data = {
#        "time": str(julian_day),
#        "timerate": str(1.0)
#    }
    print(f"Request URL: {url}")
    print(f"Request Data: {data}")
    headers = {
        "Content-Type": "application/json"
    }
    try:
#        response = requests.post(url, json=data)
#        response = requests.post(url, json={"time": julian_day, "timerate": 1.0})
        response = requests.post(url, json=data, headers=headers)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        # Ensure the response is JSON and return it
        if response.headers.get('Content-Type') == 'application/json':
            return response.json()
        else:
            print("Unexpected response format.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error setting time: {e}")
        return None
# Main test function
if __name__ == "__main__":
    # Example date and time string
    date_str = "25/09/2018 09:37:00"  # Local date and time
    # Convert the date string to a datetime object
    local_tz = pytz.timezone("Asia/Kolkata")  # Replace with your local timezone
    local_date_time = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    local_date_time = local_tz.localize(local_date_time)
    # Convert the localized datetime to UTC
    utc_date_time = local_date_time.astimezone(pytz.utc)
    # Test the set_time function
    set_time_response = set_time(utc_date_time)
    # Output the response
    print("Set Time Response:", set_time_response)
