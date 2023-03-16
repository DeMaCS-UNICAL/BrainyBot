import os
import requests

from AI.src.constants import SCREENSHOT_PATH

def require_image_from_url(url, port) -> None:
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    file = open(os.path.join(SCREENSHOT_PATH, 'screenshot.png'), "wb")
    file.write(response.content)
    file.close()
