#!/usr/bin/env python3
"""Record source-backed original-oracle review before RTC-extension timing runs."""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "analysis/phase2_oracle_decisions_luna_rtc_extension.json"

COUNTING = {
    1: ("uncertain", "Calendar polling reaches +10 and crosses the year, but the 30 s host bound has no documented full scheduling margin beyond the ~18.824 s legal slow-clock calendar arrival."),
    2: ("uncertain", "Calendar polling reaches +10 within a 22 s host bound; the legal slow-clock calendar arrival is ~18.824 s, leaving an unproven scheduling margin."),
    3: ("not_met", "The 18 s loop cap is shorter than the ~18.824 s calendar arrival allowed at 17 kHz LSI, before polling or scheduling margin."),
    4: ("uncertain", "Calendar polling reaches +10 and checks year crossing, but the 30 s bound does not establish a worst-case scheduling margin."),
    5: ("uncertain", "The 30 s calendar polling bound exceeds the slow-clock arithmetic but its full scheduling margin is not established."),
}


def main() -> None:
    data = json.loads(REVIEW.read_text())
    if len(data["decisions"]) != 10:
        raise ValueError("Expected all ten frozen RTC-extension sources")
    timestamp = datetime.now(timezone.utc).isoformat()
    for run_id, row in data["decisions"].items():
        if row["feature_path_exercised"] != "pending" or any(
                oracle["judgment"] != "pending" for oracle in row["oracles"]):
            raise ValueError(f"Already reviewed: {run_id}")
        index = int(run_id.rsplit("r", 1)[1])
        if run_id.startswith("rtc_time_counting-"):
            row["feature_path_exercised"] = "met"
            row["feature_path_evidence"] = (
                "Build passed; source sets and reads the STM32 RTC calendar, polls RTC values, "
                "and asserts year-boundary progression to a +10-second target.")
            row["oracles"][0].update(judgment="met", evidence="rtc_set_time and initial rtc_get_time results are asserted successful, with readback checks.")
            row["oracles"][1].update(
                judgment="not_met" if index == 5 else "met",
                evidence=("Only comparisons against the initial RTC time are asserted; `previous` is assigned but never used to check each successive observation."
                          if index == 5 else
                          "Each polled RTC value is compared against the preceding observation before updating that observation."))
            judgment, evidence = COUNTING[index]
            row["oracles"][2].update(judgment=judgment, evidence=evidence)
        else:
            row["feature_path_exercised"] = "not_met"
            row["feature_path_evidence"] = (
                "The frozen source does not compile against pinned Zephyr RTC alarm API; "
                "the saved build log reports an incorrect rtc_alarm_get_time signature "
                "(and some versions have additional signature errors). No executable assertion reaches the path.")
            for oracle in row["oracles"]:
                oracle.update(judgment="not_met", evidence=(
                    "The alarm suite failed compilation, so this intended source-level check "
                    "has no executable assertion in the frozen test."))
        row["reviewer"] = "Codex source review before RTC-extension perturbation; original strict oracle rubric"
        row["reviewed_utc"] = timestamp
    REVIEW.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print("Recorded original-oracle decisions for ten frozen RTC-extension sources")


if __name__ == "__main__":
    main()
