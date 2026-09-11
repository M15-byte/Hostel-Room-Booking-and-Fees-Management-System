
"""
Keeps a permanent record of important system activities.
The log is appended to instead of being overwritten, so it keeps
a timeline of events such as registrations, allocations, payments,
and saves.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

LOG_FILE = Path(__file__).resolve().parent / "activity_log.json"


# Load existing activity records
def _load_log() -> List[Dict]:
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open("r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print("Warning: the activity log file is unreadable - starting a new one.")
        return []


# Add a new event to the activity history
def log_event(event_type: str, description: str) -> None:
    entries = _load_log()

    # Create a timestamped activity record
    entries.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "details": description,
    })

    # Save the updated activity history
    with LOG_FILE.open("w") as file:
        json.dump(entries, file, indent=4)
