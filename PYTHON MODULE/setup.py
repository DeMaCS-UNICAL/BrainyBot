import os

import conda.cli
import pip

SETUP_PATH = os.path.dirname(__file__)  # Where your .py file is located
SRC_PATH = os.path.join(SETUP_PATH, 'src')
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
SPRITE_PATH = os.path.join(RESOURCES_PATH, 'sprites')
TESTS_PATH = os.path.join(SETUP_PATH, 'tests')
LOGS_PATH = os.path.join(TESTS_PATH, 'logs')
MAP_PATH = os.path.join(TESTS_PATH, 'map')


# # mapping
# ASPMapper.get_instance().register_class(Swap)
# ASPMapper.get_instance().register_class(Edge)
# ASPMapper.get_instance().register_class(Node)
# ASPMapper.get_instance().register_class(AtLeast3Adjacent)


def install_whl(path):
    pip.main(['install', path])


def installConda():
    conda.cli.main('conda', 'install', '-y', 'numpy')
    conda.cli.main('conda', 'install', '-c', 'lfortran antlr4 - python3 - runtime')
    conda.cli.main('conda', 'install', '-c', 'conda-forge matplotlib')
    conda.cli.main('conda', 'install', '-c', 'conda-forge opencv')
    conda.cli.main('conda', 'install', '-c', 'conda-forge networkx')
    conda.cli.main('conda', 'install', '-c', 'conda-forge mahotas')


def setup():
    install_whl(os.path.join(DLV_PATH, "EmbASP-7.4.0-py2.py3-none-any.whl"))  # EMBASP INSTALLER
    installConda()
