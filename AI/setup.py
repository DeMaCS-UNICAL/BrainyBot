# import os
#
# import conda.cli
# import pip
#
# from src.costants import DLV_PATH
#
#
# def install_whl(path):
#     pip.main(['install', path])
#
#
# def installConda():
#     conda.cli.main('conda', 'install', '-y', 'numpy')
#     conda.cli.main('conda', 'install', '-c', 'lfortran antlr4 - python3 - runtime')
#     conda.cli.main('conda', 'install', '-c', 'conda-forge matplotlib')
#     conda.cli.main('conda', 'install', '-c', 'conda-forge opencv')
#     conda.cli.main('conda', 'install', '-c', 'conda-forge networkx')
#     conda.cli.main('conda', 'install', '-c', 'conda-forge mahotas')
#
#
# def setup():
#     install_whl(os.path.join(DLV_PATH, "EmbASP-7.4.0-py2.py3-none-any.whl"))  # EMBASP INSTALLER
#     installConda()

from setuptools import setup

setup()
