import requests
import json
import pandas as pd

# Set the API key
api_key = 'Sn6sbX4OGrAW9iQyhzP2X6qJB04UPAkChBUoX7Tj'

# Set the endpoint URL
url = 'https://validator.extracttable.com/'

# Set the request headers
headers = {'x-api-key': api_key}

# Send a GET request to the endpoint
response = requests.get(url, headers=headers)

# Print the response
print(response.text)

trigger_url = 'https://trigger.extracttable.com/'

# Open the image file in binary mode
with open('D:\\dgbdata\\bank statement images\\image_0 - original.png', 'rb') as f:
    image_data = f.read()

# Set up the data for the POST request
data = {
    'input': ('D:\\dgbdata\\bank statement images\\image_0 - original.png', image_data)
}

response = requests.post(trigger_url, headers=headers, files=data)

data = json.loads(response.text)

df = pd.DataFrame(data['Lines'])

# Extract the text from the nested dictionaries in the 'LinesArray' column
lines = [line['Line'] for line_dict in df['LinesArray'] for line in line_dict]

# Create a new DataFrame with one row for each line of text
df2 = pd.DataFrame(lines, columns=['Text'])

# Save the DataFrame as a tab-delimited CSV file
df2.to_csv('bank_st.csv', sep='\t', index=False)

