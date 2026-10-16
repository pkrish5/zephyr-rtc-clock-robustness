#!/usr/bin/env python3
"""Give every blind item the target ZTEST symbol, without a provenance cue."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/blind_rq1"
KEY = ROOT / "analysis/blind_rq1_key.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    key = json.loads(KEY.read_text())
    if sha(BASE / "PACKET.md") != key["packet_sha256"]:
        raise ValueError("Packet index changed")
    for item in key["items"]:
        path = BASE / "items" / f"{item['item_id']}.md"
        if sha(path) != item["packet_sha256"]:
            raise ValueError(f"Packet source changed: {item['item_id']}")
        source = "\n".join((ROOT / f["path"]).read_text() for f in item["source_files"])
        if item["kind"] == "agent":
            names = re.findall(r"\bZTEST(?:_F|_USER)?\s*\(\s*[^,]+\s*,\s*"
                               r"([A-Za-z_][A-Za-z_0-9]*)", source)
            if len(names) != 1:
                raise ValueError(f"Expected one agent ZTEST case: {item['item_id']}: {names}")
            target = names[0]
        else:
            target = item["decision_id"].split(".", 1)[-1]
        body = path.read_text()
        updated, count = re.subn(r"(?m)^Target case: `[^`]+`\.$",
                                 f"Target case: `{target}`.", body, count=1)
        if count != 1:
            raise ValueError(f"Missing target line: {item['item_id']}")
        if updated != body:
            path.write_text(updated)
            item["packet_sha256"] = sha(path)
    KEY.write_text(json.dumps(key, indent=2) + "\n")
    print(f"Uniform target-case labels for {len(key['items'])} blinded items")


if __name__ == "__main__":
    main()
