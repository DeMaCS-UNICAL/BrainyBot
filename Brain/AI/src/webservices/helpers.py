import os
import requests
import subprocess

from AI.src.constants import SCREENSHOT_PATH, USE_ADB


def getScreenshot(url = None, port = None) -> bool:
    if USE_ADB:
        return require_image_from_adb()
    else:
        return require_image_from_url(url, port)

def require_image_from_url(url, port) -> None:
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    if response.status_code!=200:
        print("The screenshot can not be taken: is the ScreenshotServer running on the device?")
        return False
    file = open(os.path.join(SCREENSHOT_PATH, 'screenshot.png'), "wb")
    file.write(response.content)
    file.close()
    return True

def require_image_from_adb() -> bool:
    adb_command = f"adb exec-out screencap -p > {SCREENSHOT_PATH}/screenshot.png"
    try:
    # Execute the adb command
        subprocess.run(adb_command, shell=True, check=True)
        print(f"Screenshot saved to {SCREENSHOT_PATH}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing adb command: {e}")
        print(f"Is the device connected? Are the developer options enabled?")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False