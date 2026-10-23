#!/bin/bash
# Build an unprivileged helper in WORK on the allocated compute node.
set -euo pipefail
: "${SLURM_JOB_ID:?Build the helper only in a Slurm allocation}"
: "${RTC_BASE:?Source common.sh first}"
helper="$RTC_BASE/tools/fakeroot-1.37.1.1"
src="$RTC_BASE/tools/fakeroot-source"
test ! -e "$helper" || { echo 'STOP: preserve the existing helper build'; exit 2; }
test ! -e "$src" || { echo 'STOP: preserve the existing source/build logs'; exit 2; }
mkdir -p "$src"
curl -fL --retry 3 --max-time 180 \
    https://deb.debian.org/debian/pool/main/f/fakeroot/fakeroot_1.37.1.1.orig.tar.gz \
    -o "$src/source.tar.gz"
echo "86b0b75bf319ca42e525c098675b6ed10a06b76e69ec9ccf20ef5e03883b3a14  $src/source.tar.gz" | sha256sum -c -
tar -xzf "$src/source.tar.gz" -C "$src"
cd "$src/fakeroot-1.37.1.1"
CC=/usr/bin/gcc ./configure --prefix="$helper" --disable-static \
    > "$src/configure.log" 2>&1
make -j4 > "$src/make.log" 2>&1
make install > "$src/install.log" 2>&1
test "$("$helper/bin/fakeroot" --version)" = 'fakeroot version 1.37.1.1'
"$helper/bin/fakeroot" /usr/bin/id -u | /usr/bin/grep -qx 0
python3 - "$helper" "$SLURM_JOB_ID" <<'PY' > "$RTC_BASE/tools/fakeroot-inventory.json"
import hashlib,json,socket,subprocess,sys
from pathlib import Path
p=Path(sys.argv[1])
files={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()
       for f in sorted(p.rglob('*')) if f.is_file()}
print(json.dumps({'version':'1.37.1.1','prefix':str(p),
 'source_url':'https://deb.debian.org/debian/pool/main/f/fakeroot/fakeroot_1.37.1.1.orig.tar.gz',
 'source_sha256':'86b0b75bf319ca42e525c098675b6ed10a06b76e69ec9ccf20ef5e03883b3a14',
 'node_name':socket.gethostname(),'slurm_job_id':sys.argv[2],
 'compiler_version':subprocess.check_output(['/usr/bin/gcc','--version'],text=True).strip(),
 'files_sha256':files},indent=2,sort_keys=True))
PY
