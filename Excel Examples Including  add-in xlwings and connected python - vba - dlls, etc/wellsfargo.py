import aspose.pdf as pdf
license = pdf.License()
pdfFile = pdf.Document(r"D:\dgbdata\06 Wells Fargo 4328 06 30 2023.pdf")
# Save the output XML file
pdfFile.save(r"d:\dgbdata\wellsfargo.xml", pdf.SaveFormat.PDF_XML)

