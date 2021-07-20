import json
# Create a JSON Object
import os

from model.DLVClass import resource_path


def makeJson(coodinateType: []):
    json_obj = {}
    json_obj['coordinates'] = []

    for x, y, t in coodinateType:
        json_obj['coordinates'].append({
            f'{x},{y}': f'{t}'
        })

    # Write the object to file.
    with open(os.path.join(resource_path, 'coordinates.json'), 'w') as jsonFile:
        json.dump(json_obj, jsonFile)


coodinateType = [(i, i + 1, i + 2) for i in range(100)]
makeJson(coodinateType)
