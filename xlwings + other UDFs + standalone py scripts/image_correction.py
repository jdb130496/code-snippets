"""
Document Image Enhancer - Makes faded text look like a high-contrast xerox
Usage: python enhance_document.py

Requirements: pip install Pillow numpy
"""

from PIL import Image, ImageFilter
import numpy as np

# ============================================================
# CHANGE THESE TWO LINES ONLY
INPUT_FILE  = "20260311_160740.jpg"   # your input file name
OUTPUT_FILE = "20260311_160740_corrected.jpg"     # output file name
# ============================================================

img = Image.open(INPUT_FILE).convert("L")  # convert to grayscale
arr = np.array(img, dtype=np.float32)

# STEP 1: Histogram stretch
# Finds the actual ink-dark and paper-white values and remaps to full 0-255
p_low  = np.percentile(arr, 5)   # below this = pure black
p_high = np.percentile(arr, 92)  # above this = pure white
arr = (arr - p_low) / (p_high - p_low) * 255
arr = np.clip(arr, 0, 255)

# STEP 2: S-Curve (the xerox effect)
# Non-linear contrast: pushes darks darker and lights lighter simultaneously
arr = arr / 255.0
arr = np.where(arr < 0.5, 2 * arr**2, 1 - 2*(1 - arr)**2)
arr = arr * 255

# STEP 3: Unsharp Mask (sharpens text edges)
img2    = Image.fromarray(arr.astype(np.uint8))
blurred = img2.filter(ImageFilter.GaussianBlur(radius=1.5))
arr2      = np.array(img2,    dtype=np.float32)
arr_blur  = np.array(blurred, dtype=np.float32)
arr2 = arr2 + 1.5 * (arr2 - arr_blur)   # strength = 1.5, increase for more sharpness
arr2 = np.clip(arr2, 0, 255)

# STEP 4: Gamma correction (brightens paper background to clean white)
arr2 = (arr2 / 255.0) ** 0.7 * 255      # 0.7 = brightens; try 0.5 for more aggressive
arr2 = np.clip(arr2, 0, 255)

result = Image.fromarray(arr2.astype(np.uint8))
result.save(OUTPUT_FILE, dpi=(300, 300))
print(f"Saved to {OUTPUT_FILE}")
