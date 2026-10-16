#!/usr/bin/env python3
"""Record the pre-perturbation r04 setup-path correction without touching raw data."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "rtc_time_counting-r04"
ORIGINAL = ROOT / "analysis/phase2_oracle_decisions_luna_rtc_extension.json"
AMENDED = ROOT / "analysis/luna_rtc_extension_functional_decisions.json"


def main() -> None:
    nominal = [json.loads(line) for line in
               (ROOT / "results/luna_rtc_extension/nominal_runs.jsonl").read_text().splitlines()]
    record = next(x for x in nominal if x["run_id"] == RUN_ID)
    uart = (ROOT / record["uart_path"]).read_text(errors="replace")
    source = (ROOT / "generated/luna_rtc_extension/suites/rtc_time_counting/r04/test.c").read_text()
    driver = (ROOT / "subjects/upstream/zephyr/drivers/rtc/rtc_ll_stm32.c").read_text()
    if (record["outcome"] != "fail" or "test.c:34" not in uart or
            ".tm_wday = -1" not in source or "if (timeptr->tm_wday == -1)" not in driver):
        raise ValueError("Nominal/source/driver evidence changed")
    original = json.loads(ORIGINAL.read_text())
    row = original["decisions"][RUN_ID]
    if row["feature_path_exercised"] != "met" or row["oracles"][0]["judgment"] != "met":
        raise ValueError("Original review is not the expected pre-nominal state")
    evidence = ("Frozen nominal UART fails rtc_set_time at test.c:34. Source sets "
                "tm_wday=-1; pinned rtc_ll_stm32.c returns -EINVAL for that value. "
                "Calendar counting is not reached.")
    row["feature_path_exercised"] = "not_met"
    row["feature_path_evidence"] = evidence
    for oracle in row["oracles"]:
        oracle["judgment"] = "not_met"
        oracle["evidence"] = evidence + " This intended check has no executable passing path."
    row["reviewer"] += "; nominal-path adjudication in notes/RTC_LUNA_NOMINAL_ADJUDICATION.md"
    ORIGINAL.write_text(json.dumps(original, sort_keys=True, indent=2) + "\n")

    amended = json.loads(AMENDED.read_text())
    functional = amended["decisions"][RUN_ID]
    if functional["functional"] != "met":
        raise ValueError("Amended review is not the expected pre-nominal state")
    functional["functional"] = "not_evaluable"
    functional["evidence"] = evidence
    functional["reviewer"] += "; nominal-path adjudication in notes/RTC_LUNA_NOMINAL_ADJUDICATION.md"
    AMENDED.write_text(json.dumps(amended, sort_keys=True, indent=2) + "\n")
    print("Recorded RTC counting r04 nominal-path source-gate correction")


if __name__ == "__main__":
    main()
