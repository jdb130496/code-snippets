from PIL import Image, ImageEnhance, ImageOps
import os

folder = r"D:\DGB Personal Data\Bina - documents"
src = os.path.join(folder, "20260703_102529.jpg")
dst = os.path.join(folder, "document_enhanced.jpg")


im = Image.open(src)
im2 = ImageOps.autocontrast(im, cutoff=1)
im3 = ImageEnhance.Contrast(im2).enhance(1.4)
im4 = ImageEnhance.Brightness(im3).enhance(0.92)
im5 = ImageEnhance.Sharpness(im4).enhance(1.5)
im5.save(dst, quality=95)
