import os
import cv2
from AI.src.monogram.constants import RESOURCES_PATH
from AI.src.abstraction.helpers import getImg
import numpy as np

# Resource paths
SPRITES_PATH = os.path.join(RESOURCES_PATH, 'sprites')
DISTANCE = [10000, 10000]

# Load template images for cell detection
CROSS_TEMPLATES = {}
EMPTY_TEMPLATES = {}
TEMPLATES = {}
THRESHOLDS = {}

print(f"[Constants] Looking for sprites in: {SPRITES_PATH}")

# Load cross templates
if os.path.exists(SPRITES_PATH):
    print(f"[Constants] Loading cross templates from: {SPRITES_PATH}")
    for file in os.listdir(SPRITES_PATH):
        filepath = os.path.join(SPRITES_PATH, file)
        if os.path.isfile(filepath) and file.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = getImg(filepath, color_conversion=cv2.COLOR_BGR2RGB)
                template_name = f"cross_{os.path.splitext(file)[0]}"
                CROSS_TEMPLATES[file] = img
                TEMPLATES[template_name] = img
                THRESHOLDS[template_name] = 0.75
                
                height, width = img.shape[:2]
                DISTANCE[0] = min(DISTANCE[0], width)
                DISTANCE[1] = min(DISTANCE[1], height)
                
                print(f"  ✓ Loaded: {file}")
            except Exception as e:
                print(f"  ✗ Error loading {file}: {e}")
else:
    print(f"[Constants] ⚠ Cross folder not found: {SPRITES_PATH}")

print(f"[Constants] Total templates loaded: {len(TEMPLATES)}")
print(f"[Constants] CROSS: {len(CROSS_TEMPLATES)}, EMPTY: {len(EMPTY_TEMPLATES)}")
