import requests
from bs4 import BeautifulSoup
import xlwings as xw
@xw.func
def get_sanskrit_mantras(url):
    # Send a GET request to the webpage
    response = requests.get(url)
    # Parse the HTML content of the webpage
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all article tags with the specified class
    articles = soup.find_all('article', class_='dpLyricsWrapper')
    # Initialize a list to store the mantras
    mantras = []
    # Iterate over each article tag
    for article in articles:
        # Find all div tags with the specified class within the article
        divs = article.find_all('div', class_='dpNameCardMantra dpFlexEqual')
        for div in divs:
            # Find the div containing the Sanskrit mantra
            mantra_div = div.find('div', class_='dpListPrimaryTitle')
            if mantra_div:
                # Extract the text and add it to the list
                mantras.append(mantra_div.get_text(strip=True))
    # Return the list of mantras in a vertical format
    return [[mantra] for mantra in mantras]

