import os

import pip

from AI.src.candy_crush.constants import RESOURCES_PATH


def install_whl(path):
    pip.main(['install', path])


def main():
    install_whl(os.path.join(RESOURCES_PATH, "EmbASP-7.4.0-py2.py3-none-any.whl"))  # EMBASP INSTALLER


if __name__ == '__main__':
    main()

# RUN TO INSTALL EMBASP
