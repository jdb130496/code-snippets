import PyPDF2

pdf_file = open('/mnt/hdd/DGB Personal Data/juhi all documents/IT Return FY 2022-23/XXXXXXXXXXX7064-01-04-2022to31-03-2023.pdf', 'rb')
read_pdf = PyPDF2.PdfReader(pdf_file)
number_of_pages = len(read_pdf.pages)

with open('/home/admin/Downloads/output.txt', 'w') as f:
    for page_number in range(number_of_pages):
        page = read_pdf.pages[page_number]
        page_content = page.extract_text()
        f.write(page_content)
