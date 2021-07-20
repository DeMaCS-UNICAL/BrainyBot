import os

import pip

lib_path = os.path.dirname(__file__)  # Where your .py file is located


def install_whl(path):
    pip.main(['install', path])


def main():
    install_whl(os.path.join(lib_path, "EmbASP-7.4.0-py2.py3-none-any.whl"))  # EMBASP INSTALLER



if __name__ == '__main__':
    main()

# RUN TO INSTALL EMBASP
