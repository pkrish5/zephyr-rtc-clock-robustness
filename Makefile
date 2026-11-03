PYTHON ?= python3

.PHONY: tables
tables:
	$(PYTHON) -B analysis/final_submission_v1/reproduce.py $(if $(EVIDENCE_ARCHIVE),--archive "$(EVIDENCE_ARCHIVE)",)
