#!/bin/bash -l
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
source "$script_dir/common.sh"
mkdir -p "$RTC_BASE/images" "$RTC_BASE/build-home"
test "$(uname -m)" = x86_64 || { echo 'STOP: definition is pinned for LS6 x86_64' >&2; exit 2; }
test ! -e "$RTC_IMAGE" || { echo 'STOP: image already exists; preserve it' >&2; exit 2; }
test ! -e "$RTC_BASE/images/image.json" || { echo 'STOP: sealed image already exists' >&2; exit 2; }
python3 "$script_dir/calibration.py" verify --bundle "$RTC_BUNDLE" --repo "$RTC_REPO"
cd "$RTC_REPO"
# Use a WORK-backed build home/cache/temp, including for unprivileged fakeroot.
apptainer build --fakeroot --bind "$RTC_BASE/build-home:/root" \
    "$RTC_IMAGE" "$script_dir/rtc-ls6.def" \
    > "$RTC_BASE/images/build.log" 2>&1
apptainer exec --cleanenv --containall --home "$RTC_BASE/build-home:/home/rtc" \
    "$RTC_IMAGE" /opt/rtc-python/bin/python - <<'PY' > "$RTC_BASE/images/software-inventory.json"
import json, subprocess
from pathlib import Path
def cmd(*x): return subprocess.check_output(x,text=True).strip()
print(json.dumps({'renode_version':cmd('/opt/renode/renode-pinned','--version'),
 'dotnet_runtimes':cmd('/usr/bin/dotnet','--list-runtimes'),
 'compiler_version':cmd('/opt/zephyr-sdk-0.17.4/arm-zephyr-eabi/bin/arm-zephyr-eabi-gcc','--version'),
 'zephyr_commit':cmd('git','-C','/opt/zephyrproject/zephyr','rev-parse','HEAD'),
 'python_packages':Path('/opt/rtc-pins/python-packages.txt').read_text(),
 'os_packages':Path('/opt/rtc-pins/os-packages.txt').read_text()},indent=2,sort_keys=True))
PY
python3 - "$RTC_IMAGE" "$RTC_BASE/images" "$RTC_BUNDLE" "$RTC_APPTAINER_VERSION" <<'PY'
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
image,folder,bundle=map(Path,sys.argv[1:4])
inventory=json.loads((folder/'software-inventory.json').read_text())
plan=json.loads((bundle/'calibration_plan.json').read_text())
if inventory['renode_version']!=plan['expected_renode_version']:
    raise SystemExit('STOP: built Renode version differs; retain image/log and report before any probe')
h=hashlib.sha256()
with image.open('rb') as f:
    for b in iter(lambda:f.read(1048576),b''): h.update(b)
record={'image_path':str(image),'container_sha256':h.hexdigest(),
 'apptainer_version':sys.argv[4],'apptainer_module':'tacc-apptainer/1.4.1',
 'launcher_module':'launcher/3.10','sealed_utc':datetime.now(timezone.utc).isoformat(),
 'calibration_plan_sha256':hashlib.sha256((bundle/'calibration_plan.json').read_bytes()).hexdigest(),
 'software_inventory_sha256':hashlib.sha256((folder/'software-inventory.json').read_bytes()).hexdigest()}
with (folder/'image.json').open('x') as f: json.dump(record,f,indent=2,sort_keys=True);f.write('\n')
with (folder/'rtc-ls6-v1.sif.sha256').open('x') as f: f.write(h.hexdigest()+'  '+image.name+'\n')
print(json.dumps(record,indent=2))
PY
