import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# The activity log is stored next to the program files.
LOG_FILE = Path(__file__).resolve().parent / "activity_log.json"


# Loads existing log entries or returns an empty list.
def _load_log() -> List[Dict]:
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open("r", encoding="utf-8") as file:
            entries = json.load(file)
        if not isinstance(entries, list):
            raise ValueError
        return entries
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        print("Warning: the activity log is unreadable. A new log will be used.")
        return []


# Adds one event to the activity log.
def log_event(event_type: str, description: str) -> None:
    entries = _load_log()
    entries.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "details": description,
        }
    )

    try:
        with LOG_FILE.open("w", encoding="utf-8") as file:
            json.dump(entries, file, indent=4)
    except OSError as error:
        print(f"Warning: activity could not be logged: {error}")
