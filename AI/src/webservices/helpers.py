import json
import os

import requests

from AI.src.constants import RESOURCES_PATH


def requireImageFromURL(url, port) -> None:
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    file = open(os.path.join(RESOURCES_PATH, 'matrix.png'), "wb")
    file.write(response.content)
    file.close()


def appendToJSON(json_obj: {}, string, x, y) -> None:
    json_obj[string].append({
        "x": f"{x}",
        "y": f"{y}"
    })


def makeJson(x, y, x1, y1) -> {}:
    json_obj = {'first': [], 'second': []}

    # first movement
    appendToJSON(json_obj, 'first', x, y)

    # second movement
    appendToJSON(json_obj, 'second', x1, y1)

    # Write the object to file.
    with open(os.path.join(RESOURCES_PATH, 'swap.json'), 'w') as jsonFile:
        json.dump(json_obj, jsonFile)

    return json_obj


def sendJson(ip, json_obj: {}) -> int:
    r = requests.post(ip, json_obj)
    return r.status_code
