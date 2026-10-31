#!/bin/bash
# Infrastructure coordinator for NEW approved jobs only.
# Usage: run_packed.sh LABEL command [args...]
# Slurm wrapper must request --signal=B:USR1@600 for packing reserve.
set -euo pipefail
label=${1:?archive label}
shift
test "$#" -gt 0
source "${RTC_REPO:?}/harness/tacc_storage/runtime.sh"
test -n "${RTC_CONTAINER_SHA256:?calibrated image hash}"
state=failed
child=
finalizing=0
finalize() {
    status=$?
    trap - EXIT USR1 TERM INT
    if [ "$finalizing" = 1 ]; then exit "$status"; fi
    finalizing=1
    # Stop writers before any inventory/archive is made. setsid below gives
    # this command and its local Launcher descendants their own process group.
    if [ -n "$child" ]; then
        kill -TERM -- "-$child" 2>/dev/null || true
        for ((i=0;i<30;i++)); do
            if ! kill -0 -- "-$child" 2>/dev/null; then break; fi
            sleep 1
        done
        kill -KILL -- "-$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
    if ! python3 "$RTC_REPO/harness/tacc_storage/protected_check.py" \
        --out "$RTC_JOB_OUTPUT/job_metadata/protected_after.json"; then
        state=failed
        status=2
    fi
    # Even failed/interrupted jobs preserve their existing partial bytes.
    # A failure to publish is an infrastructure failure, never a test verdict.
    if ! python3 "$RTC_REPO/harness/tacc_storage/publish.py" \
        --label "$label" --state "$state"; then
        status=3
    fi
    exit "$status"
}
trap finalize EXIT
trap 'state=interrupted; exit 124' USR1 TERM INT
python3 "$RTC_REPO/harness/tacc_storage/check_headroom.py"
python3 "$RTC_REPO/harness/tacc_storage/protected_check.py" \
    --out "$RTC_JOB_OUTPUT/job_metadata/protected_before.json"
setsid "$@" > "$RTC_JOB_OUTPUT/job_metadata/command.out" \
    2> "$RTC_JOB_OUTPUT/job_metadata/command.err" &
child=$!
set +e
wait "$child"
status=$?
set -e
# There must be no lingering group member when publication begins, even if
# the command leader exited first. finalize() terminates remaining writers.
if [ "$status" = 0 ]; then state=complete; fi
exit "$status"
