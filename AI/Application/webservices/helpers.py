import os

import requests

from Application.costants import RESOURCES_PATH


def requireImageFromURL(url, port):
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    file = open(os.path.join(RESOURCES_PATH, 'matrix.png'), "wb")
    file.write(response.content)
    file.close()


def makeJson(coodinateType: []):
    json_obj = {'coordinates': []}

    for x, y, t in coodinateType:
        json_obj['coordinates'].append({
            f'{x},{y}': f'{t}'
        })

    # Write the object to file.
    # with open(os.path.join(resource_path, 'coordinates.json'), 'w') as jsonFile:
    #     json.dump(json_obj, jsonFile)
