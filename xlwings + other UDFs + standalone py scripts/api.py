import requests

url = "http://104.18.32.151/api/financialdata/historical/7"
params = {
    "start-date": "2022-09-29",
    "end-date": "2022-09-29",
    "time-frame": "Daily",
    "add-missing-rows": "false"
}
headers = {
    "Host": "api.investing.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Cookie": "CF_Authorization=tnHz_oRiCHCx8iLFfj2ixfkrLGK0aLM_RuE8wEgqX04-1713455508-1.0.1.1-2B9Ulo6XDzoRGLK8uKLVhnB2qJ586QwWgGSy9Z7jGnIXnfv3z_TqnGrIziU5XLC_of4vy6XuR05HgmvLLeqgOg"
    # Add any other required headers here
}

response = requests.get(url, params=params, headers=headers)
print(response.status_code)

