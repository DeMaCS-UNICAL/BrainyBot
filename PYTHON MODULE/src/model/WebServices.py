import requests as requests


def requireImageFromURL(url, port):
    upLoads = {'name': 'requestimage'}
    receive = requests.get(f'{url}:{port}/', params=upLoads)
    # with open(os.path.join(res, 'screenshot.png'), 'wb') as f:
    #     f.write(receive.content)


def makeJson(coodinateType: []):
    json_obj = {}
    json_obj['coordinates'] = []

    for x, y, t in coodinateType:
        json_obj['coordinates'].append({
            f'{x},{y}': f'{t}'
        })

    # Write the object to file.
    # with open(os.path.join(resource_path, 'coordinates.json'), 'w') as jsonFile:
    #     json.dump(json_obj, jsonFile)
