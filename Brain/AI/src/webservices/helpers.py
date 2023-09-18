import os
import requests
import subprocess

from AI.src.constants import SCREENSHOT_PATH, USE_ADB


def getScreenshot(url = None, port = None) -> None:
    if USE_ADB:
        return require_image_from_adb()
    else:
        return require_image_from_url(url, port)

def require_image_from_url(url, port) -> None:
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    file = open(os.path.join(SCREENSHOT_PATH, 'screenshot.png'), "wb")
    file.write(response.content)
    file.close()

def require_image_from_adb() -> None:
    adb_command = f"adb exec-out screencap -p > {SCREENSHOT_PATH}/screenshot.png"
    try:
    # Execute the adb command
        subprocess.run(adb_command, shell=True, check=True)
        print(f"Screenshot saved to {SCREENSHOT_PATH}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing adb command: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")