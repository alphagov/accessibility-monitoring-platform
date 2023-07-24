import json


def import_json_data():
    with open("aws_tools/copilot_settings.json", "r", encoding="UTF-8") as f:
        data = json.load(f)
    return data
