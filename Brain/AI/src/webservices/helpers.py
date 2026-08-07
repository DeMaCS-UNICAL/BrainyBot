import gzip
import os
import struct
import subprocess

import numpy as np
import requests
from AI.src.constants import (
    CLIENT_PATH,
    SCREENSHOT_PATH,
    TAPPY_ORIGINAL_SERVER_IP,
    USE_ADB,
    logger,
)
from PIL import Image


def getScreenshot(url=None, port=None) -> bool:
    if USE_ADB:
        return require_image_from_adb()
    else:
        return require_image_from_url(url, port)


def get_screenshot(
    url=None,
    port=None,
    to_memory: bool = False,
    save_path: str = None,
    filename: str = "screenshot.png",
) -> bool | np.ndarray:
    """
    Retrieves a screenshot from the device using either adb or a web request

    Parameters:
        url: the url of the server
        port: the port of the server
        to_memory: if True, saves the screenshot to memory, else saves it to a file
        save_path: the path to save the screenshot if to_memory is False, if None, uses the default SCREENSHOT_PATH
        filename: the name of the screenshot file if to_memory is False, if None, uses "screenshot.png"
    Returns: a boolean with the state of the screenshot if to_memory is false, else an np.ndarray with the image data, empty or False is something went wrong
    """

    if save_path is not None and save_path[-1] != "/":
        save_path += "/"

    try:
        match (USE_ADB, to_memory):
            case (True, True):
                return run_adb_screencap_to_memory()
            case (True, False):
                return run_adb_screencap_to_memory(
                    file_path=SCREENSHOT_PATH if save_path is None else save_path,
                    filename=filename,
                )
            case (False, True):
                return require_image_from_url_to_memory(url=url, port=port)
            case (False, False):
                return require_image_from_url(
                    url=url,
                    port=port,
                    save_path=SCREENSHOT_PATH,
                    filename=filename,
                )
    except Exception as e:
        logger.info(f"Error getting screenshot: {e}")
        return False


def require_image_from_url(
    url, port, save_path: str = None, filename: str = "screenshot.png"
) -> bool:
    if save_path is None:
        save_path = SCREENSHOT_PATH
    if not os.path.exists(save_path):
        raise Exception(f"The directory {save_path} does not exist")
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    if response.status_code != 200:
        print(
            "The screenshot can not be taken: is the ScreenshotServer running on the device?"
        )
        return False
    file = open(os.path.join(save_path, filename), "wb")
    file.write(response.content)
    file.close()
    return True


def require_image_from_url_to_memory(url: str, port: str) -> np.ndarray | bool:
    """
    Takes a screenshot from the device using a web request [⚠️ UNTESTED]

    Parameters:
        url: the url of the server
        port: the port of the server
    """
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    if response.status_code != 200:
        print(
            "The screenshot can not be taken: is the ScreenshotServer running on the device?"
        )
        return False
    return np.array(response.content)


def require_image_from_adb(
    save_path: str = None, filename: str = "screenshot.png"
) -> bool:
    if save_path is None:
        save_path = SCREENSHOT_PATH
    if not os.path.exists(save_path):
        raise Exception(f"The directory {save_path} does not exist")
    adb_command = f"adb exec-out screencap -p > {save_path}/{filename}"
    try:
        # Execute the adb command
        subprocess.run(adb_command, shell=True, check=True)
        print(f"Screenshot saved to {save_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing adb command: {e}")
        print(f"Is the device connected? Are the developer options enabled?")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def run_adb_screencap_to_memory(
    slow_usb: bool = True, file_path: str = None, filename: str = "screenshot.png"
) -> np.ndarray:
    """
    Takes a screenshot from the device using adb
    https://stackoverflow.com/questions/43900380/faster-command-than-adb-shell-screencap

    Parameters:
        slow_usb: if True, uses adb exec-out screencap | gzip -1 to save bandwidth,
            otherwise uses adb exec-out screencap to save cpu cycles
        file_path: the path to save the screenshot
        filename: the name of the screenshot file
    Returns:
        np.ndarray: image data in RGBA format
    """

    if slow_usb:
        cmd = [
            "adb",
            "exec-out",
            'sh -c "screencap | gzip -2"',
        ]  # can be changed for each device, I found -2 to be the best
    else:
        cmd = ["adb", "exec-out", "screencap"]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if slow_usb:
        stream = gzip.GzipFile(fileobj=process.stdout, mode="rb")
    else:
        stream = process.stdout

    header = stream.read(12)
    if len(header) < 12:
        raise Exception("Failed to read image header")

    width, height, pixel_format = struct.unpack("<III", header)
    buffer_size = width * height * 4
    raw_data = stream.read(buffer_size)

    if len(raw_data) != buffer_size:
        raise Exception("Incomplete read of image data")

    image = np.frombuffer(raw_data, dtype=np.uint8)
    image = image.reshape((height, width, 4))

    if slow_usb:
        stream.close()
    process.stdout.close()
    process.wait()

    if file_path is not None:
        if not os.path.exists(file_path):
            raise Exception(f"The directory {file_path} does not exist")
        Image.fromarray(image).save(os.path.join(file_path, filename))

    return image


def swipe(start_x: int, start_y: int, end_x: int, end_y: int):
    """
    Executes a swipe gesture on the device using either adb or a web request

    Parameters:
        start_x: the x-coordinate of the start point
        start_y: the y-coordinate of the start point
        end_x: the x-coordinate of the end point
        end_y: the y-coordinate of the end point
    """
    if USE_ADB:
        os.system(f"adb shell input swipe {start_x} {start_y} {end_x} {end_y}")
    else:
        os.system(
            f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {start_x} {start_y} {end_x} {end_y}'"
        )


def tap(x: int, y: int):
    """
    Executes a tap gesture on the device using either adb or a web request

    Parameters:
        x: the x-coordinate of the tap point
        y: the y-coordinate of the tap point
    """
    if USE_ADB:
        os.system(f"adb shell input tap {x} {y}")
    else:
        os.system(
            f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'tap {x} {y}'"
        )


def tap_and_hold(x: int, y: int, duration: int):
    """
    Executes a tap and hold gesture on the device using either adb or a web request

    Parameters:
        x: the x-coordinate of the tap point
        y: the y-coordinate of the tap point
        duration: the duration of the tap and hold in milliseconds
    """
    if USE_ADB:
        os.system(f"adb shell input swipe {x} {y} {x} {y} {duration}")
    else:
        os.system(
            f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'long-tap {x} {y} {duration}'"
        )
