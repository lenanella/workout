import json

EXPORT_FILE = "export.json"


def export_to_json(workouts):
    keys = ("id", "date", "exercise", "duration", "notes")
    data = [dict(zip(keys, row)) for row in workouts]
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
