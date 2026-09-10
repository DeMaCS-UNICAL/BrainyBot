import os
import cv2
from AI.src.monogram.constants import RESOURCES_PATH
from AI.src.abstraction.helpers import getImg

# This file loads all template images at module import time

SPRITES_PATH = os.path.join(RESOURCES_PATH, 'sprites')
DISTANCE = [10000, 10000]

CROSS_TEMPLATES = {}
EMPTY_TEMPLATES = {}
TEMPLATES = {}
THRESHOLDS = {}

# Load cross templates
cross_folder = os.path.join(SPRITES_PATH, 'cross')
if os.path.exists(cross_folder):
    for file in os.listdir(cross_folder):
        filepath = os.path.join(cross_folder, file)
        if os.path.isfile(filepath) and file.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = getImg(filepath, color_conversion=cv2.COLOR_BGR2RGB)
                template_name = f"cross_{os.path.splitext(file)[0]}"
                CROSS_TEMPLATES[file] = img
                TEMPLATES[template_name] = img
                THRESHOLDS[template_name] = 0.75  # Default confidence threshold
                
                # Track smallest dimensions
                height, width = img.shape[:2]
                DISTANCE[0] = min(DISTANCE[0], width)
                DISTANCE[1] = min(DISTANCE[1], height)
                
                print(f"Loaded cross template: {file}")
            except Exception as e:
                print(f"Error loading cross template {file}: {e}")

# Load empty templates
empty_folder = os.path.join(SPRITES_PATH, 'empty')
if os.path.exists(empty_folder):
    for file in os.listdir(empty_folder):
        filepath = os.path.join(empty_folder, file)
        if os.path.isfile(filepath) and file.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = getImg(filepath, color_conversion=cv2.COLOR_BGR2RGB)
                template_name = f"empty_{os.path.splitext(file)[0]}"
                EMPTY_TEMPLATES[file] = img
                TEMPLATES[template_name] = img
                THRESHOLDS[template_name] = 0.70  # Default confidence threshold
                
                # Track smallest dimensions
                height, width = img.shape[:2]
                DISTANCE[0] = min(DISTANCE[0], width)
                DISTANCE[1] = min(DISTANCE[1], height)
                
                print(f"Loaded empty template: {file}")
            except Exception as e:
                print(f"Error loading empty template {file}: {e}")

print(f"Total templates loaded: {len(TEMPLATES)}")
print(f"Cross templates: {len(CROSS_TEMPLATES)}, Empty templates: {len(EMPTY_TEMPLATES)}")
print(f"Smallest template size (DISTANCE): {DISTANCE}")
