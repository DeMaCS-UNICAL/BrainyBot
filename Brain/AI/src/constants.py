import logging
import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
SCREENSHOT_PATH = os.path.join(RESOURCES_PATH, 'screenshot')
VALIDATION_PATH = os.path.join(SRC_PATH, 'validation')
BENCHMARK_PATH = os.path.join(SRC_PATH, 'benchmark')
MOTION_MODULE = os.path.join(SRC_PATH, 'motion_module')
MOTION_CALIBRATION_PATH = os.path.join(MOTION_MODULE, 'calibrations')
SCREENSHOT_FILENAME = 'screenshot.png'
SCREENSHOT_FULLPATH = os.path.join(SCREENSHOT_PATH, SCREENSHOT_FILENAME)
CLIENT_PATH = os.path.join(SRC_PATH, '../../../tappy-client/clients/python')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
# change IP addresses to your needs.
SCREENSHOT_SERVER_IP = '192.168.0.30'               # IP of the mobile phone with Screenshotserver on board
TAPPY_ORIGINAL_SERVER_IP = 'http://127.0.0.1:8000'  # IP of the server where the robot is attached to
USE_ADB = True                                      # True if you want to use adb to get the screenshot, False if you want to use the Screenshotserver


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # Niente, colori, non sono riuscito a farli funzionare bene... se ho tempo (voglia) ci metto le emoji
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

