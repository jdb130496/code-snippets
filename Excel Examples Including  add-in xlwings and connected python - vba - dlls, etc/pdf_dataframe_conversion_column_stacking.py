from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
import pandas as pd
import numpy as np

def read_pdf(pdf_path):
    with open(pdf_path, 'rb') as fh:
        # Create a PDF resource manager object
        resource_manager = PDFResourceManager()
        
        # Create a buffer for the text converter
        fake_file_handle = StringIO()
        
        # Create a text converter object
        converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
        
        # Create a PDF page interpreter object
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        
        # Process each page in the PDF
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        
        # Get the text from the buffer
        text = fake_file_handle.getvalue()
        
        # Close the text converter and buffer
        converter.close()
        fake_file_handle.close()
    
    # Return the text as a list of lines
    return text.splitlines()

# Read the text from the PDF
text_list = read_pdf('EMI Finding Implicit Rate Of Interest - Sheet1.pdf')

# Remove empty strings from the text list
text_list = [x for x in text_list if x]


# Extract the column headers from the text list and delete first 5 elements
headers = text_list[:5]
text_list = text_list[5:]

# Insert empty strings into the text list for the missing data in the first row
text_list.insert(28, '')
text_list.insert(42, '')

# Number of rows and columns in the resulting DataFrame
num_rows = 14
num_cols = 5

# Split the text list into separate lists for each column
columns = []
for i in range(num_cols):
    start_index = i * num_rows
    end_index = start_index + num_rows
    col = text_list[start_index:end_index]
    columns.append(col)

# Stack the column lists horizontally and convert them into a list of lists
data = np.column_stack(columns).tolist()

# Create a DataFrame from the list of data
df = pd.DataFrame(data, columns=headers)

# Display the resulting DataFrame
print(df)
