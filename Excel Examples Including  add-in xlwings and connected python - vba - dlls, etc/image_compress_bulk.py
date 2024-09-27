import PIL
import os
from PIL import Image
imgpath='C:/Users/cos03/Desktop/png/'
images = []
images=[file for file in  os.listdir(imgpath) if  file.endswith(".png")]
for image in images:
    image_name = image.rsplit('.',1)[0]
    image = Image.open(imgpath+image)
    image.save(imgpath+image_name+"_reduced.jpg","JPEG",optimize = True, quality = 40)

