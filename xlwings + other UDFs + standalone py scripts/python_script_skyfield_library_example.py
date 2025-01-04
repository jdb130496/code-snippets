from datetime import datetime
from skyfield.api import load
def calculate_tithi_skyfield(date_time_str):
    # Load ephemeris data
    ts = load.timescale()
    planets = load('de421.bsp')
    earth, moon, sun = planets['earth'], planets['moon'], planets['sun']
    # Parse the input date and time string
    date_time = datetime.strptime(date_time_str, "%d/%m/%Y %H:%M:%S")
    time = ts.utc(date_time.year, date_time.month, date_time.day, date_time.hour, date_time.minute, date_time.second)
    # Calculate positions
    observer = earth
    moon_position = observer.at(time).observe(moon).apparent()
    sun_position = observer.at(time).observe(sun).apparent()
    # Convert positions to ecliptic longitude
    moon_longitude = moon_position.ecliptic_latlon()[1].degrees
    sun_longitude = sun_position.ecliptic_latlon()[1].degrees
    # Print debugging information
    print(f"Sun Longitude: {sun_longitude:.2f}°")
    print(f"Moon Longitude: {moon_longitude:.2f}°")
    # Calculate the longitude difference
    longitude_difference = moon_longitude - sun_longitude
    if longitude_difference < 0:
        longitude_difference += 360
    print(f"Longitude Difference: {longitude_difference:.2f}°")
    # Calculate the tithi number
    tithi_number = int(longitude_difference // 12) + 1
    print(f"Tithi Number (Before Adjustments): {tithi_number}")
    # Tithi names array
    tithi_names = [
        'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
        'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
        'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima', 'Amavasya'
    ]
    # Determine the paksha and tithi name
    if tithi_number <= 15:
        paksha = 'Shukla'
        tithi_name = tithi_names[tithi_number - 1]
    else:
        paksha = 'Krishna'
        tithi_number -= 15  # Adjust tithi_number for Krishna Paksha
        # Handle boundary condition for Krishna Paksha
        if tithi_number == 15:  # Krishna Paksha's last tithi should be Amavasya
            tithi_name = 'Amavasya'
        else:
            tithi_name = tithi_names[tithi_number - 1]
    print(f"Tithi Number (After Adjustments): {tithi_number}")
    return f"{paksha} {tithi_name}"
