from astropy.time import Time
from astropy.coordinates import get_body
from datetime import datetime
def calculate_tithi(date_time_str):
    # Parse the input date and time string
    date_time = datetime.strptime(date_time_str, "%d/%m/%Y %H:%M:%S")
    # Convert to an ISO 8601 format string for astropy
    date_time_iso = date_time.isoformat()
    # Create an Astropy Time object
    time = Time(date_time_iso)
    # Get the Sun and Moon positions using get_body
    sun = get_body('sun', time)
    moon = get_body('moon', time)
    # Calculate the ecliptic longitudes of the Sun and Moon
    sun_longitude = sun.geocentrictrueecliptic.lon.deg
    moon_longitude = moon.geocentrictrueecliptic.lon.deg
    # Calculate the difference in longitude
    longitude_difference = moon_longitude - sun_longitude
    # If the difference is negative, add 360 to make it positive
    if longitude_difference < 0:
        longitude_difference += 360
    # Calculate the tithi number
    tithi_number = int(longitude_difference // 12) + 1
    # Determine the paksha and tithi name
    if tithi_number <= 15:
        paksha = 'Shukla'
    else:
        paksha = 'Krishna'
    tithi_names = [
        'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
        'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
        'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima', 'Amavasya'
    ]
    # Adjust the tithi index for Krishna Paksha
    tithi_index = (tithi_number - 1) % 15
    # Special case for Amavasya in Krishna Paksha
    if paksha == 'Krishna' and tithi_number == 30:
        tithi_name = tithi_names[-1]  # Amavasya
    else:
        tithi_name = tithi_names[tithi_index]
    # Print debug information
    print(f"Sun Longitude: {sun_longitude:.2f}°")
    print(f"Moon Longitude: {moon_longitude:.2f}°")
    print(f"Longitude Difference: {longitude_difference:.2f}°")
    print(f"Tithi Number: {tithi_number}")
    return f"{paksha} {tithi_name}"

