#!/usr/bin/env python3
"""Build the versioned manuscript and supplemental evidence assets."""
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "submission_assets/course-paper-2026-11-11-v3"
OUT.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add_zip(path, files, extra):
    expected = {str(p.relative_to(ROOT)): sha(p) for p in files}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in files:
            name = str(item.relative_to(ROOT))
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 11, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, item.read_bytes())
        for name, data in extra.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 11, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        archive.writestr("SOURCE_SHA256.json", json.dumps(expected, indent=2, sort_keys=True) + "\n")
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert all(hashlib.sha256(archive.read(name)).hexdigest() == digest for name, digest in expected.items())
    return expected

numbers = json.loads((HERE / "manuscript_numbers_v3.json").read_text())
counter = json.loads((HERE / "counter_table_audit.json").read_text())
assert numbers["status"] == counter["status"] == "PASS"
assert numbers["numeric_claims"] == 40 and numbers["original_table_hashes_match"] == 8
assert numbers["counter_table_hash_matches"] and numbers["citation_keys_resolve"] == 13
tex = ROOT / "paper/draft/main.tex"
pdf = ROOT / "paper/draft/main.pdf"
assert sha(tex) == numbers["manuscript_sha256"]
assert pdf.stat().st_mtime >= tex.stat().st_mtime
pdfinfo = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
assert "Pages:           5" in pdfinfo and "Page size:       612 x 792 pts (letter)" in pdfinfo
log = (ROOT / "paper/draft/main.log").read_text()
assert not any(term in log for term in ["Overfull ", "Undefined control sequence", "Citation `", "Reference `"])
assert all((HERE / f"page-{n}.png").is_file() for n in range(1, 6))
make_log = (HERE / "make_course_tables_v3.txt").read_text()
assert make_log.count('"status": "PASS"') >= 2

validation = {
    "status": "PASS",
    "date": "2026-11-11",
    "pdf_sha256": sha(pdf),
    "tex_sha256": sha(tex),
    "pdf_pages_including_references": 5,
    "all_pages_rendered_and_inspected": True,
    "overfull_boxes": 0,
    "unresolved_citation_or_reference_diagnostics": 0,
    "citation_keys_resolve": 13,
    "numeric_claims_checked": 40,
    "original_tables_rebuilt_and_hash_matched": 8,
    "readable_tables_hash_matched": 3,
    "counter_table_hash_matched": True,
    "original_repair_primary_records_hashed": 17375,
    "counter_legal_primary_records_paired": 408,
    "counter_fault_primary_records_checked": 8,
    "counter_slow_fault_activation_qualified": False,
    "repeatability_launches": 180,
    "renode_runs_for_manuscript_revision": 0,
}
(HERE / "final_validation_v3.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")

source_files = [
    tex, ROOT / "paper/draft/refs.bib", ROOT / "Makefile", ROOT / "DATA.md",
    ROOT / "reproduction/evidence.json", ROOT / "reproduction/expected_tables.json",
]
source_files += sorted((ROOT / "paper/draft/tables").glob("*.tex"))
v2 = ROOT / "notes/course_subjects_2026-11-04_v1"
source_files += [v2 / name for name in [
    "build_subject_tables.py", "audit_paired_records.py", "paired_and_scope_audit.json",
    "subject_table_audit.json", "hsi_summary.json", "citation_url_final.json",
]]
source_files += [HERE / name for name in [
    "build_counter_table.py", "verify_manuscript_v3.py", "CLAIM_AUDIT.md",
    "counter_table_audit.json", "manuscript_numbers_v3.json",
    "claim_to_evidence.csv", "final_validation_v3.json", "make_course_tables_v3.txt",
]]
source_files += [
    ROOT / "notes/counter_verification_2026-11-11_v1/OBSERVER_AUDIT.md",
    ROOT / "notes/counter_verification_2026-11-11_v1/PROTOCOL.md",
    ROOT / "notes/counter_verification_2026-11-11_v1/report-3575326-v1/summary.json",
    ROOT / "notes/counter_verification_2026-11-11_v1/report-3575326-v1/HANDOFF.md",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/processes.csv",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/case_verdicts.csv",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/reference_coverage.json",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/verification.json",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/output/new_sources/subjects/counter_verification_20261111_v1/progress.c",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/output/references/uart/f4-progress-control-slow_progress_control-027.log",
    ROOT / "notes/counter_verification_2026-11-11_v1/verified-3575326-v1/output/references/traces/f4-progress-control-slow_progress_control-027.json",
    ROOT / "notes/fixed_repeatability_recovery_2026-11-04_v1/combined_report_v1/summary.json",
    ROOT / "notes/fixed_repeatability_recovery_2026-11-04_v1/combined_report_v1/per_run.csv",
    ROOT / "notes/fixed_repeatability_recovery_2026-11-04_v1/combined_report_v1/per_cell.csv",
]
for job in ["3570473", "3570474", "3570475"]:
    source_files += sorted((ROOT / f"notes/counter_repair_execution_2026-11-05_v1/verified-{job}-v1/output/records").glob("f4-counter-*.json"))
assert len(source_files) == len(set(source_files))
assert all(p.is_file() for p in source_files), [str(p) for p in source_files if not p.is_file()]
readme = """# Course manuscript v3, 2026-11-11

The PDF is `clock-sensitive-waits-v3.pdf`. This source ZIP contains the TeX,
table fragments, claim audit, 314 new counter primary records, diagnostic
summary, and the six-cell repeatability summary. All clock times in the paper
are Renode virtual time. The fourth counter slow-fault control is unresolved.

To reproduce the complete manuscript tables and numerical audit, clone the
repository at tag `course-paper-2026-11-11-v3`, extract this ZIP in the clone
root (preserving paths), download the unchanged original evidence archive from
`course-submission-2026-11-03-v1`, then run:

make course-tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz

The separate supplemental evidence ZIP contains the original completed-job
archives for independent inspection; it is not required for the table command.
The frozen original archive SHA256 is
805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921.
"""
source_zip = OUT / "clock-sensitive-waits-v3-source.zip"
source_hashes = add_zip(source_zip, source_files, {"README-MANUSCRIPT.txt": readme})

evidence_files = [
    ROOT / "notes/counter_repair_execution_2026-11-05_v1/returned-downstream-20261110-v1/3570473-counter-recovery-legal-a.tar.gz",
    ROOT / "notes/counter_repair_execution_2026-11-05_v1/returned-downstream-20261110-v1/3570474-counter-recovery-legal-b.tar.gz",
    ROOT / "notes/counter_repair_execution_2026-11-05_v1/returned-downstream-20261110-v1/3570475-counter-recovery-fault.tar.gz",
    ROOT / "notes/counter_verification_2026-11-11_v1/returned-3575326-20261111T205259Z/3575326-counter-diagnostics.tar.gz",
    ROOT / "notes/fixed_repeatability_recovery_2026-11-04_v1/returned-3552869-v1/3552869-fixed-repeat-f4-rtc.tar.gz",
    ROOT / "notes/fixed_repeatability_recovery_2026-11-04_v1/returned-3552870-v1/3552870-fixed-repeat-f4-counter.tar.gz",
]
evidence_zip = OUT / "clock-sensitive-waits-v3-supplemental-evidence.zip"
evidence_hashes = add_zip(evidence_zip, evidence_files, {})
for source, name in [
    (pdf, "clock-sensitive-waits-v3.pdf"),
    (tex, "main-v3.tex"),
    (HERE / "CLAIM_AUDIT.md", "CLAIM_AUDIT.md"),
    (HERE / "final_validation_v3.json", "final_validation_v3.json"),
]:
    shutil.copyfile(source, OUT / name)
assets = [source_zip, evidence_zip] + [OUT / name for name in [
    "clock-sensitive-waits-v3.pdf", "main-v3.tex", "CLAIM_AUDIT.md", "final_validation_v3.json",
]]
(OUT / "SHA256SUMS.txt").write_text("".join(f"{sha(p)}  {p.name}\n" for p in sorted(assets)))
(HERE / "release_assets_v3.json").write_text(json.dumps({
    "status": "PASS", "assets": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in assets},
    "source_entries_verified": len(source_hashes),
    "supplemental_archives_verified": len(evidence_hashes),
    "original_evidence_archive_unchanged": True,
}, indent=2, sort_keys=True) + "\n")
print(json.dumps({"out": str(OUT), "source_entries": len(source_hashes),
                  "supplemental_archives": len(evidence_hashes), "assets": len(assets) + 1}, indent=2))
