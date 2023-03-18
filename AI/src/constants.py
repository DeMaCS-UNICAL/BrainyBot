import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
SCREENSHOT_PATH = os.path.join(RESOURCES_PATH, 'screenshot')
CLIENT_PATH = os.path.join(SRC_PATH, '../../tapsterbot-original/clients/python')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
# TODO: change IP!
SCREENSHOT_SERVER_IP = '192.168.1.33'
TAPPY_ORIGINAL_SERVER_IP = '192.168.85.37'