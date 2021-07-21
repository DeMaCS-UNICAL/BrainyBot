import os

import pip

SETUP_PATH = os.path.dirname(__file__)  # Where your .py file is located
SRC_PATH = os.path.join(SETUP_PATH, 'src')
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
MAP_PATH = os.path.join(RESOURCES_PATH, 'map')
SPRITE_PATH = os.path.join(RESOURCES_PATH, 'sprites')
TESTS_PATH = os.path.join(SETUP_PATH, 'tests')
LOGS_PATH = os.path.join(TESTS_PATH, 'logs')


def install_whl(path):
    pip.main(['install', path])


def setup():
    install_whl(os.path.join(DLV_PATH, "EmbASP-7.4.0-py2.py3-none-any.whl"))  # EMBASP INSTALLER
