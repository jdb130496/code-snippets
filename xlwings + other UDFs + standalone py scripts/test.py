
def parse_ecl_lon(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tags = soup.find_all(text=True)
    for tag in tags:
        if "Ecl. long./lat. (J2000.0):" in tag:
            longitude_part = tag.split(":")[1].split("/")[0].strip()
            longitude_part = longitude_part.replace("°", "").replace("Â", "")
            return float(longitude_part)
    return "N/A"

def get_julian_datetime(date):
    """
    Convert a datetime object into julian float.
    Args:
        date: datetime-object of date in question
    Returns: float - Julian calculated datetime.
    Raises: 
        TypeError : Incorrect parameter type
        ValueError: Date out of range of equation
    """
    # Ensure correct format
	if not isinstance(date, datetime.datetime):
        raise TypeError('Invalid type for parameter "date" - expecting datetime')
    elif date.year < 1801 or date.year > 2099:
        raise ValueError('Datetime must be between year 1801 and 2099')
    # Perform the calculation
    julian_datetime = 367 * date.year - int((7 * (date.year + int((date.month + 9) / 12.0))) / 4.0) + int((275 * date.month) / 9.0) + date.day + 1721013.5 + (date.hour + date.minute / 60.0 + date.second / math.pow(60,1, 100 * date.year + date.month - 190002.5) + 0.5
                                                                                                                                                              
