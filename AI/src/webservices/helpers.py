import json
import os

import requests

from src.costants import RESOURCES_PATH


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

    appendToJSON(json_obj, 'first', x, y)
    appendToJSON(json_obj, 'second', x1, y1)

    # Write the object to file.
    with open(os.path.join(RESOURCES_PATH, 'swap.json'), 'w') as jsonFile:
        json.dump(json_obj, jsonFile)

    return json_obj
