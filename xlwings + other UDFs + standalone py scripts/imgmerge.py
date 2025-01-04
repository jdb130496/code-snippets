from PIL import Image, ImageChops

# Function to auto-crop footers or headers based on pixel color detection
def crop_white_space(img):
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        return img.crop(bbox)
    return img

# Load and crop white spaces from the images
def process_images(images_list):
    imgs = [Image.open(img_path) for img_path in images_list]
    
    # Crop white space from each image
    imgs = [crop_white_space(img) for img in imgs]

    # Resize all images to the same width (for better alignment)
    min_img_width = min(i.width for i in imgs)
    total_height = sum(i.height for i in imgs)

    # Create a new image for merging
    img_merge = Image.new('RGB', (min_img_width, total_height))

    # Merge the images together without gaps
    y_offset = 0
    for img in imgs:
        img_merge.paste(img, (0, y_offset))
        y_offset += img.height

    return img_merge

# Paths to the individual page images
images_list = [
    'D:\\DGB Personal Data\\juhi all documents\\Resume and Write Up Templates\\Juhi_Matrimonial_CV_170823_Page_1.jpg',
    'D:\\DGB Personal Data\\juhi all documents\\Resume and Write Up Templates\\Juhi_Matrimonial_CV_170823_Page_2.jpg'
]

# Process and merge the images
merged_image = process_images(images_list)

# Save the merged image
merged_image.save('D:\\DGB Personal Data\\juhi all documents\\Resume and Write Up Templates\\juhi_cv_matrimonial_merged_clean.png', format='PNG')

print("Footers removed and images merged without gaps.")

