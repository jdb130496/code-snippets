import PIL
from PIL import Image
img = Image.open(r'C:\Users\cos03\Desktop\IMG_20230206_084636285.jpg')
img.save(r'C:\Users\cos03\Desktop\IMG_20230206_084636285_reduced.jpg', "JPEG", optimize = True, quality = 40)
