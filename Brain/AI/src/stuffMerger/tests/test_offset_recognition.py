
from AI.src.stuffMerger.enums import *
from AI.src.stuffMerger.utils.resources_utility import *
from AI.src.stuffMerger.utils.image_processing_utility import *

from threading import Thread
import matplotlib.pyplot as plt
import subprocess

from AI.src.constants import logger

TOTAL = 400  # px
STAGES = 4 # The number of moves we want to make
STEP = TOTAL//STAGES  # px
CHECK_RANGE = 30  # px
CHECK_FREQUENCY = 1  # px
VERTICAL = False
HORIZONTAL = True
ORIENTATION = Orientation.DESCENDING # 0 = descending, 1 = ascending (0->100, 100->0)
PERFECT = False
CAPTURE = False


if __name__ == "__main__":
	if CAPTURE:
		get_image_set(
			perfect=PERFECT,
			vertical=VERTICAL,
			horizontal=HORIZONTAL,
			orientation=ORIENTATION,
			save_location="multiple_axis/"
		)
		
	image_prefix = f"{'i_' if not PERFECT else ''}{'v_' if VERTICAL else ''}{'h_' if HORIZONTAL else ''}{'r_' if ORIENTATION != Orientation.DESCENDING else ''}"
	
	images = [Image.open(f"multiple_axis/{image_prefix}screenshot_{index}.png")for index in range(5)]
	ignoreZone = make_alpha_mask_from_bw(Image.open("isandempire_mask.png"))
	
	# TOTAL*2 and TOTAL inside the desk gives us additional margin to paste the images without worrying about going out of bounds, while CHECK_RANGE gives us the necessary space to check for offsets in both directions.

	desk = Image.new("RGBA",
	                 (images[0].width + TOTAL*2 + CHECK_RANGE, images[0].height + TOTAL*2 + CHECK_RANGE),
	                 (255, 0, 0, 255))
	
	desk.paste(images[0].convert("RGBA"),
	           (0, 0) if ORIENTATION == Orientation.DESCENDING else (desk.width-images[0].width-TOTAL, desk.height-images[0].height-TOTAL),
	           ignoreZone)
	
	offsets = []
	
	
	
	logger.setLevel(logging.INFO)
