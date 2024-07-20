from selenium import webdriver
from bs4 import BeautifulSoup
import numpy as np
import re
import statsmodels.api as sm

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

# Assuming cleaned_data is your cleaned data
years = [item[0] for item in cleaned_data[1:]]
gold_rates = [item[1] for item in cleaned_data[1:]]

# Convert lists to numpy arrays
years = np.array(years)
gold_rates = np.array(gold_rates)

# Add a constant (intercept term) to the predictors
years = sm.add_constant(years)

# Create an OLS model
model = sm.OLS(gold_rates, years)

# Fit the model
results = model.fit()

# Print the summary statistics of the regression model
print(results.summary())

# Get the R-squared value
r_squared = results.rsquared
print(f'R-squared: {r_squared}')

# Close the browser
driver.quit()
