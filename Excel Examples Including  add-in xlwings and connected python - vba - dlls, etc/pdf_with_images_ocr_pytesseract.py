from pdf2image import convert_from_path
import os

# Set the path to the PDF file
pdf_path = r'D:\dgbdata\Mai Krupa Bank Statement 2023-24.pdf'

# Set the path to the output directory
output_dir = r'D:\dgbdata\bank statement images'

# Create the output directory if it doesn't already exist
os.makedirs(output_dir, exist_ok=True)

# Convert the PDF pages into images
images = convert_from_path(pdf_path)

# Loop through each image in the sequence
for i, image in enumerate(images):
    # Set the path to the output image file
    image_path = os.path.join(output_dir, f'image_{i}.png')
    # Save the image to the output directory
    image.save(image_path)


