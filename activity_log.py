"""
activity_log.py

Keeps a permanent, append-only history of what happens in the system:
every registration, every allocation, every payment, and every save.

This is deliberately a separate file from hostel_data.json. That file
only ever holds the *current* state and gets overwritten completely on
every save - it can't tell you what changed or when. This file never
gets overwritten, only appended to, so opening it later shows the full
timeline of everything that's happened since the system went live.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

LOG_FILE = Path(__file__).resolve().parent / "activity_log.json"


def _load_log() -> List[Dict]:
    """
    Reads the existing log so a new entry can be appended to it.

    A missing file just means nothing has been logged yet. A corrupted
    file is handled the same way it is everywhere else in this project:
    reported, then treated as empty rather than crashing the program -
    losing old history to a bad write is unfortunate, but it should
    never stop new history from being recorded.
    """
    if not LOG_FILE.exists():
        return []
    try:
        with LOG_FILE.open("r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print("Warning: the activity log file is unreadable - starting a new one.")
        return []


def log_event(event_type: str, description: str) -> None:
    """
    Records one line of history: what kind of event it was, a plain
    description of what happened, and exactly when.

    Called from main.py right after an action succeeds, never from
    inside hostel.py / students.py / fees.py themselves - those modules
    only handle the business rules and shouldn't need to know that
    logging to disk even exists. Keeping that decision in main.py means
    the core modules stay easy to test without touching the filesystem.
    """
    entries = _load_log()
    entries.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "details": description,
    })
    with LOG_FILE.open("w") as file:
        json.dump(entries, file, indent=4)
