import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
SCREENSHOT_PATH = os.path.join(RESOURCES_PATH, 'screenshot')
VALIDATION_PATH = os.path.join(SRC_PATH, 'validation')
BENCHMARK_PATH = os.path.join(SRC_PATH, 'benchmark')
SCREENSHOT_FILENAME = 'screenshot.png'
SCREENSHOT_FULLPATH = os.path.join(SCREENSHOT_PATH, SCREENSHOT_FILENAME)
CLIENT_PATH = os.path.join(SRC_PATH, '../../../tappy-client/clients/python')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
# change IP addresses to your needs.
SCREENSHOT_SERVER_IP = '192.168.0.30'     # IP of the mobile phone with Screenshotserver on board
TAPPY_ORIGINAL_SERVER_IP = '127.0.0.1'  # IP of the server where the robot is attached to

# Which backend to use for screenshots and tap/swipe input.
# "adb"     -> Android device or emulator via adb (screenshot + input)
# "ios_sim" -> iOS Simulator via Appium/XCUITest (screenshot + input)
# "tappy"   -> Screenshotserver for screenshots + tappy-server robot arm for input
INPUT_BACKEND = 'ios_sim'

USE_ADB = INPUT_BACKEND == 'adb'          # kept for readability at call sites

APPIUM_SERVER_URL = 'http://127.0.0.1:4723'
IOS_SIMULATOR_UDID = 'FB9FD78D-8C2B-4B7F-8219-DC99CFC4F4CC'  # iPhone 17, iOS 26.5 (matches installed SDK)

