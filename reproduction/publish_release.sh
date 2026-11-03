#!/bin/bash
# Human authenticates gh beforehand; no password/token belongs in this script.
set -euo pipefail
cd "$(dirname "$0")/.."
tag="course-submission-2026-11-03-v1"
repo="pkrish5/zephyr-rtc-clock-robustness"
test -f submission_assets/rtc-submission-evidence-v1.tar.gz
gh release create "$tag" \
  submission_assets/rtc-submission-evidence-v1.tar.gz \
  submission_assets/rtc-submission-evidence-v1.tar.gz.sha256 \
  submission_assets/clean-clone-test.json \
  paper/draft/main.pdf \
  --repo "$repo" --verify-tag \
  --title "Course submission: RTC clock robustness" \
  --notes-file reproduction/RELEASE_NOTES.md
