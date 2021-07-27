import os

from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService

from Application.costants import DLV_PATH


def chooseDLVSystem() -> DesktopHandler:
    if os.name == 'nt':
        return DesktopHandler(
            DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
    elif os.uname().sysname == 'Darwin':
        return DesktopHandler(
            DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
    else:
        return DesktopHandler(
            DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux-64_6")))
