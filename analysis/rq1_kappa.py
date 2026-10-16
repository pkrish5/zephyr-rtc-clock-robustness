#!/usr/bin/env python3
"""Calculate three-category Cohen's kappa after independent labels are returned."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/blind_rq1"
CATEGORIES = ("unjustified", "none_found", "unknown")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    key_path = ROOT / "analysis/blind_rq1_key.json"
    key = json.loads(key_path.read_text())
    if sha(ROOT / "analysis/phase3_rq1_decisions.json") != key["source_review_sha256"]:
        raise ValueError("Original first-reviewer source ledger changed")
    extension_hash = key.get("rtc_extension_source_review_sha256")
    if extension_hash and sha(ROOT / "analysis/rtc_extension_rq1_decisions.json") != extension_hash:
        raise ValueError("RTC-extension first-reviewer source ledger changed")
    if sha(BASE / "PACKET.md") != key["packet_sha256"]:
        raise ValueError("Blind packet index changed")
    expected = {item["item_id"]: item for item in key["items"]}
    if len(expected) != len(key["items"]):
        raise ValueError("Duplicate key ID")
    for item in expected.values():
        path = BASE / "items" / f"{item['item_id']}.md"
        if sha(path) != item["packet_sha256"]:
            raise ValueError(f"Source packet changed: {path}")
    rows = list(csv.DictReader((BASE / "labels.csv").open(newline="")))
    second = {row["item_id"]: row for row in rows}
    if len(second) != len(rows) or set(second) != set(expected):
        raise ValueError("Missing, unexpected, or duplicate independent item IDs")
    if any(row["label"] not in CATEGORIES for row in rows):
        missing = [row["item_id"] for row in rows if row["label"] not in CATEGORIES]
        raise SystemExit(f"Independent review incomplete: {', '.join(missing)}")
    n = len(rows)
    pairs = [(expected[item]["first_reviewer_label"], second[item]["label"])
             for item in expected]
    counts = Counter(pairs)
    first = Counter(a for a, _ in pairs)
    independent = Counter(b for _, b in pairs)
    observed = sum(counts[(c, c)] for c in CATEGORIES) / n
    chance = sum(first[c] * independent[c] for c in CATEGORIES) / (n * n)
    kappa = (observed - chance) / (1 - chance) if chance != 1 else None
    print(json.dumps({
        "n": n, "categories": CATEGORIES,
        "first_reviewer": dict(first), "independent_reviewer": dict(independent),
        "confusion_rows_first_columns_independent": {
            a: {b: counts[(a, b)] for b in CATEGORIES} for a in CATEGORIES},
        "observed_agreement": observed, "chance_agreement": chance,
        "cohens_kappa": kappa,
        "disagreements": [
            {"item_id": item, "first_reviewer_label": expected[item]["first_reviewer_label"],
             "independent_reviewer_label": second[item]["label"],
             "independent_reason": second[item]["reason"],
             "recognized_source": second[item]["recognized_source"]}
            for item in expected
            if expected[item]["first_reviewer_label"] != second[item]["label"]
        ],
        "recognized_source_count": sum(bool(row["recognized_source"].strip()) for row in rows),
        "packet_key_sha256": sha(key_path),
        "independent_labels_sha256": sha(BASE / "labels.csv"),
    }, indent=2))


if __name__ == "__main__":
    main()
