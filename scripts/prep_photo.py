#!/usr/bin/env python3
"""
Step 1 — prep_photo.py
Prepares a source photo for ASCII art conversion:
  1. Background removal via rembg
  2. CLAHE contrast boost via OpenCV
  3. Composite onto pure white background
Output: grayscale source-prepped.png
"""

import sys
import pathlib
import numpy as np
import cv2
from PIL import Image
from rembg import remove

INPUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg")
OUTPUT = pathlib.Path("source-prepped.png")

print(f"[prep_photo] Loading {INPUT} ...")
with open(INPUT, "rb") as f:
    raw = f.read()

print("[prep_photo] Removing background ...")
rgba_bytes = remove(raw)
rgba = Image.open(__import__("io").BytesIO(rgba_bytes)).convert("RGBA")

# Composite onto pure white background
white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
composited = Image.alpha_composite(white, rgba).convert("RGB")

# Convert to numpy for OpenCV processing
img_bgr = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

# CLAHE contrast boost — critical for flat faces to read in ASCII
clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
gray_boosted = clahe.apply(gray)

out = Image.fromarray(gray_boosted)
out.save(OUTPUT)
print(f"[prep_photo] Saved -> {OUTPUT}  ({out.size[0]}x{out.size[1]}px)")
