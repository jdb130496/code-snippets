import pandas as pd
import base64
import re

# Replace this with your Base64 encoded content
encoded_content =  "U2VyaWFsfEVNSXxQcmluY2lwYWx8SW50ZXJlc3R8T3V0c3RhbmRpbmcNCjB8MjM0OS42Mnw5NzY1MC4zOA0KMXwyMzQ5LjYyfDExMjguOTl8MTIyMC42M3w5NjUyMS4zOQ0KMnwyMzQ5LjYyfDExNDMuMTF8MTIwNi41MXw5NTM3OC4yOA0KM3wyMzQ5LjYyfDExNTcuNDB8MTE5Mi4yMnw5NDIyMC44OA0KNHwyMzQ5LjYyfDExNzEuODZ8MTE3Ny43Nnw5MzA0OS4wMg0KNXwyMzQ5LjYyfDExODYuNTF8MTE2My4xMXw5MTg2Mi41MQ0KNnwyMzQ5LjYyfDEyMDEuMzR8MTE0OC4yOHw5MDY2MS4xNw0KN3wyMzQ5LjYyfDEyMTYuMzZ8MTEzMy4yNnw4OTQ0NC44MQ0KOHwyMzQ5LjYyfDEyMzEuNTZ8MTExOC4wNlw4ODIxMy4yNQ0KOXwyMzQ5LjYyfDEyNDYuOTZ8MTEwMi42Nnw4Njk2Ni4yOQ0KMTB8MjM0OS42MnwxMjYyLjU1fDEwODcuMDd8ODU3MDMuNzQNCjExfDIzNDkuNjJ8MTI3OC4zM3wxMDcxLjI5fDg0NDI1LjQxDQoxMnwyMzQ5LjYyfDEyOTQuMzF8MTA1NS4zMXw4MzEzMS4xMA0KMTN8MjM0OS42MnwxMzEwLjQ5fDEwMzkuMTN8ODE4MjAuNjENCg=="

# Decode the content
decoded_content = base64.b64decode(encoded_content).decode('utf-8')

# Remove carriage return and newline characters followed by a digit from the decoded content
decoded_content = re.sub(r'\r\d', '', decoded_content)

# Split the content into rows
rows = decoded_content.split('\n')
decoded_content = re.sub(r'\r', '', decoded_content)

# Split each row into columns using the "|" separator
data = [row.split('|') for row in rows]

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Save the DataFrame as a CSV file
df.to_csv('output.csv', index=False, sep='|')

