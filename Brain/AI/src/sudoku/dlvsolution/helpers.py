import os

from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from AI.src.constants import DLV_PATH

from languages.predicate import Predicate


class Cell(Predicate):
    predicate_name = "cell"

    def __init__(self, row=None, col=None):
        Predicate.__init__(self, [("row", int), ("col", int)])
        self.__row = row
        self.__col = col

    def get_row(self):
        return self.__row

    def get_col(self):
        return self.__col

    def set_row(self, row):
        self.__row = row

    def set_col(self, col):
        self.__col = col


class Box(Predicate):
    predicate_name = "box"

    def __init__(self, row=None, col=None, box=None):
        Predicate.__init__(self, [("row", int), ("col", int), ("box", int)])
        self.__row = row
        self.__col = col
        self.__box = box

    def get_row(self):
        return self.__row

    def get_col(self):
        return self.__col

    def get_box(self):
        return self.__box

    def set_row(self, row):
        self.__row = row

    def set_col(self, col):
        self.__col = col

    def set_box(self, box):
        self.__box = box


class Given(Predicate):
    predicate_name = "given"

    def __init__(self, row=None, col=None, value=None):
        Predicate.__init__(self, [("row", int), ("col", int), ("value", int)])
        self.__row = row
        self.__col = col
        self.__value = value

    def get_row(self):
        return self.__row

    def get_col(self):
        return self.__col

    def get_value(self):
        return self.__value

    def set_row(self, row):
        self.__row = row

    def set_col(self, col):
        self.__col = col

    def set_value(self, value):
        self.__value = value


class Value(Predicate):
    predicate_name = "value"

    def __init__(self, row=None, col=None, value=None):
        Predicate.__init__(self, [("row", int), ("col", int), ("value", int)])
        self.__row = row
        self.__col = col
        self.__value = value

    def get_row(self):
        return self.__row

    def get_col(self):
        return self.__col

    def get_value(self):
        return self.__value

    def set_row(self, row):
        self.__row = row

    def set_col(self, col):
        self.__col = col

    def set_value(self, value):
        self.__value = value


def chooseDLVSystem() -> DesktopHandler:
    try:
        if os.name == 'nt':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
        elif os.uname().sysname == 'Darwin':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
        else:
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux")))
    except Exception as e:
        print(e)
