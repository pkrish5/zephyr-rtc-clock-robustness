"""Compare persisted RTC replay traces, after JSON has normalized value types."""

import json
from pathlib import Path

TRACE_KEYS = ("lsi_frequency_hz", "observations", "cases", "outcome", "error")


def compare_persisted_traces(original_path: Path, replay_path: Path) -> bool:
    """Return exact equality of registered observable trace fields on disk."""
    original = json.loads(original_path.read_text())
    replay = json.loads(replay_path.read_text())
    return all(original[key] == replay[key] for key in TRACE_KEYS)
