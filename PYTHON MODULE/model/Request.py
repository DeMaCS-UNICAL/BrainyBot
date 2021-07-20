import os

import requests as requests

from DLVClass import resource_path


def requireImageFromURL(url, port):
    upLoads = {'name': 'requestimage'}
    receive = requests.get(f'{url}:{port}/', params=upLoads)
    with open(os.path.join(resource_path, 'screenshot.png'), 'wb') as f:
        f.write(receive.content)
