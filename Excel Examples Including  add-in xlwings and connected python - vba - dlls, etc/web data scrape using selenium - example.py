from selenium import webdriver
from bs4 import BeautifulSoup
import xlsxwriter
import re

# Create a new instance of the Firefox driver
driver = webdriver.Firefox()

# Go to the website
driver.get("https://www.bankbazaar.com/gold-rate/gold-rate-trend-in-india.html")

# Get the HTML of the page
html = driver.page_source

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find the div with the class "hfm-table"
div = soup.find('div', {'class': 'hfm-table'})

# Find the table within the div
table = div.find('table', {'class': 'ui celled striped structured table'})

# Find all the rows in the table body
rows = table.tbody.find_all('tr')

# Initialize an empty list to store the data
data = []

# Iterate over each row
for row in rows:
    # Find all the cells in the row
    cells = row.find_all('td')
    
    # Get the text from each cell and add it to the data list
    data.append([cell.text for cell in cells])

# Clean up the escape sequences
#cleaned_data = [[item.replace('\\xa0', ' ') for item in sublist] for sublist in data]
cleaned_data = [data[0]] + [[int(re.sub(r'\xa0', '', item[:4])) if i == 0 else float(re.sub(r'Rs\.|,', '', re.sub(r'\xa0', ' ', item))) for i, item in enumerate(sublist)] for sublist in data[1:]]

# Create a new Excel file and add a worksheet
workbook = xlsxwriter.Workbook('gold_rate_trend.xlsx')
worksheet = workbook.add_worksheet()
worksheet.write('A1', 'Year')
worksheet.write('B1', 'Gold Rate')
# Iterate over the data and write it out row by row
for i, (year, gold_rate) in enumerate(cleaned_data, start=2):
    worksheet.write(f'A{i}', year)
    worksheet.write(f'B{i}', gold_rate)
workbook.close()
# Close the browser
driver.quit()

