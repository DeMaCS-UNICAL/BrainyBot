import json
import os
import requests

from AI.src_ball_sort_game.constants import RESOURCES_PATH, SCREENSHOT_PATH


def require_image_from_url(url, port) -> None:
    response = requests.get(f"http://{url}:{port}/?name=requestimage")
    file = open(os.path.join(SCREENSHOT_PATH, 'screenshot.png'), "wb")
    file.write(response.content)
    file.close()


def append_to_json(json_obj: [], x1, y1, x2, y2) -> None:
    json_obj.append({"first": {"x": f"{x1}", "y": f"{y1}"}, "second": {"x": f"{x2}", "y": f"{y2}"}})


def make_json(coordinates: []) -> []:
    json_obj = []

    for coordinate in coordinates:
        append_to_json(json_obj, coordinate['x1'], coordinate['y1'], coordinate['x2'], coordinate['y2'])

    # Write the object to file.
    with open(os.path.join(RESOURCES_PATH, 'moves.json'), 'w') as jsonFile:
        json.dump(json_obj, jsonFile)

    return json_obj


def send_json(ip, json_obj: {}) -> int:
    r = requests.post(ip, json_obj)
    return r.status_code
