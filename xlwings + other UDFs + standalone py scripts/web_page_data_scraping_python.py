import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

url = 'https://insidepublicaccounting.com/top-firms/ipa-500/'

# Set the user agent in the request headers
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

# Send a GET request to the URL with the headers
response = requests.get(url, headers=headers)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find all the <table> tags that have the class "tablepress"
tables = soup.find_all('table', {'class': 'tablepress'})

# Create an empty list to store the dataframes
dfs = []

# Loop through each <table> tag and extract the table data
for table in tables:
    # Convert the <table> tag to a string and read it into a pandas dataframe
    html_string = str(table)
    df = pd.read_html(StringIO(html_string))[0]
    # Rename the "Firm Name / Headquarters" column to "Firm / Headquarters"
    df = df.rename(columns={'Firm Name / Headquarters': 'Firm / Headquarters'})
    # Append the dataframe to the list
    dfs.append(df)

# Concatenate all the dataframes in the list into a single dataframe
result = pd.concat(dfs)

# Save the resulting dataframe to a tab-delimited CSV file
result.to_csv('ipa-500.csv', sep='\t', index=False)


