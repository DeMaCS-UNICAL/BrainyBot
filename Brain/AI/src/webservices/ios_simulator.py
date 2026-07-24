from PIL import Image

from appium import webdriver
from appium.options.ios import XCUITestOptions

from AI.src.constants import APPIUM_SERVER_URL, IOS_SIMULATOR_UDID

_driver = None
_scale = None  # screenshot pixels per Appium point, e.g. 3.0 on a Retina simulator


def get_driver():
    global _driver
    if _driver is None:
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.automation_name = "XCUITest"
        options.new_command_timeout = 300
        if IOS_SIMULATOR_UDID:
            options.udid = IOS_SIMULATOR_UDID
        _driver = webdriver.Remote(APPIUM_SERVER_URL, options=options)
    return _driver


def screenshot(path):
    get_driver().get_screenshot_as_file(path)
    global _scale
    with Image.open(path) as img:
        screenshot_width = img.width
    window_width = get_driver().get_window_size()["width"]
    _scale = screenshot_width / window_width


def _to_points(x, y):
    if _scale is None:
        raise RuntimeError("Call screenshot() at least once before tap()/swipe() to establish the pixel-to-point scale.")
    return x / _scale, y / _scale


def tap(x, y):
    px, py = _to_points(x, y)
    get_driver().execute_script("mobile: tap", {"x": px, "y": py})


def swipe(x1, y1, x2, y2, duration_s=0.1):
    px1, py1 = _to_points(x1, y1)
    px2, py2 = _to_points(x2, y2)
    get_driver().execute_script("mobile: dragFromToForDuration", {
        "duration": duration_s,
        "fromX": px1, "fromY": py1,
        "toX": px2, "toY": py2,
    })
