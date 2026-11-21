PYTHON ?= python3

.PHONY: tables
tables:
	$(PYTHON) -B analysis/final_submission_v1/reproduce.py $(if $(EVIDENCE_ARCHIVE),--archive "$(EVIDENCE_ARCHIVE)",)

.PHONY: course-tables
course-tables: tables counter-sweep
	$(PYTHON) -B notes/course_subjects_2026-11-04_v1/build_subject_tables.py
	$(PYTHON) -B notes/course_subjects_2026-11-04_v1/audit_paired_records.py
	$(PYTHON) -B notes/course_counter_2026-11-11_v1/build_counter_table.py
	$(PYTHON) -B notes/manuscript_v5_2026-11-21_v1/verify_manuscript_v5.py

.PHONY: counter-sweep
counter-sweep:
	$(PYTHON) -B notes/counter_natural_recovery_2026-11-20_v1/build_sweep_table.py
