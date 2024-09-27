import os
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as fh:
        # Create a PDF resource manager object that stores shared resources.
        resource_manager = PDFResourceManager()
        # Create a buffer for the text converter
        fake_file_handle = StringIO()
        # Create a text converter and connect it to the resource manager and buffer
        converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
        # Create a PDF page interpreter and connect it to the resource manager and text converter
        page_interpreter = PDFPageInterpreter(resource_manager, converter)

        # Process each page contained in the document.
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

        # Close the text converter and buffer
        converter.close()
        fake_file_handle.close()

    return text

# Extract text from the PDF starting from page 3
text = extract_text_from_pdf(r'D:\dgbdata\20221130-statements-5930-.pdf')

# Save the extracted text to a file
with open(os.path.join(os.path.dirname(r'D:\dgbdata\20221130-statements-5930-.pdf'), 'extracted_text.txt'), 'w') as f:
    f.write(text)

