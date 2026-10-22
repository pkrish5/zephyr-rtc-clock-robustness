#!/usr/bin/env python3
"""Verify the sealed image and inputs once per job, before launching records."""
import argparse
import json
import os
import re
from pathlib import Path
from prepare import sha
from calibration import verify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--image-record", type=Path, required=True)
    args = p.parse_args()
    verify(args)
    d = json.loads(args.image_record.read_text())
    if sha(args.image) != d["container_sha256"]:
        raise ValueError("SIF hash differs from sealed image")
    if sha(args.bundle / "calibration_plan.json") != d["calibration_plan_sha256"]:
        raise ValueError("Image was sealed for another plan")
    if not re.search(r"\b1\.4\.1(?:\s|$)", os.environ["RTC_APPTAINER_VERSION"]):
        raise ValueError("Apptainer 1.4.1 required")
    if d["apptainer_module"] != "tacc-apptainer/1.4.1" or d["launcher_module"] != "launcher/3.10":
        raise ValueError("Pinned module record differs")
    print("Sealed image and bundle verified; SHA-256:", d["container_sha256"])


if __name__ == "__main__":
    main()
