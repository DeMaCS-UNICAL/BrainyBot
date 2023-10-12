import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
SCREENSHOT_PATH = os.path.join(RESOURCES_PATH, 'screenshot')
SCREENSHOT_FILENAME = 'screenshot.png'
SCREENSHOT_FULLPATH = os.path.join(SCREENSHOT_PATH, SCREENSHOT_FILENAME)
CLIENT_PATH = os.path.join(SRC_PATH, '../../../tappy-client/clients/python')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
# change IP addresses to your needs.
SCREENSHOT_SERVER_IP = '192.168.0.30'     # IP of the mobile phone with Screenshotserver on board
TAPPY_ORIGINAL_SERVER_IP = '127.0.0.1'  # IP of the server where the robot is attached to
USE_ADB = True                            # True if you want to use adb to get the screenshot, False if you want to use the Screenshotserver

