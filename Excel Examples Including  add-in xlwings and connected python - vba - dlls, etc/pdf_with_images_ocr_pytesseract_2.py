import pytesseract
from PIL import Image
import pandas as pd
from pdf2image import convert_from_path

# Set the path to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\Local Programs\tesseract\tesseract.exe'

# Set the path to the PDF file
pdf_path = r'D:\dgbdata\Mai Krupa Bank Statement 2023-24.pdf'

# Convert the PDF pages into images
images = convert_from_path(pdf_path)

# Initialize an empty list to store the extracted text data
data = []

# Loop through each image in the sequence
for image in images:
    # Extract the text from the image using pytesseract
    text = pytesseract.image_to_string(image)
    # Split the text into lines and loop through each line
    for line in text.split('\n'):
        # Split the line into fields using '|' as a separator
        fields = line.split('|')
        # Append the fields to the data list
        data.append(fields)

# Create a Pandas DataFrame from the data list
df = pd.DataFrame(data)

# Define a regular expression pattern to extract the desired fields
pattern = r'^(?P<Description>.+?)\s+(?P<Amount>\d+\.\d+)\s+(?P<TransactionType>DR)\s+(?P<Balance>\d+\.\d+)\s+(?P<Location>.+)$'

# Extract the fields from the second column using the str.extract method
fields = df.iloc[:, 2].str.extract(pattern)

# Concatenate the extracted fields with the original DataFrame
df = pd.concat([df.iloc[:, :-1], fields], axis=1)

# Delete the third column of the DataFrame
df = df.drop(df.columns[2], axis=1)

# Save the DataFrame to a CSV file using '|' as a separator
df.to_csv('bank_statement.csv', sep='|', index=False)

