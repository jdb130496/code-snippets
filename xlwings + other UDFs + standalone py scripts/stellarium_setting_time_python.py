import requests
STELLARIUM_URL='http://192.168.1.5:8090/api/main'
def set_time(julian_day,timerate):
    url = f"{STELLARIUM_URL}/time"
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
