"""Build new repair ELFs without touching any original source or build tree."""
import os
import shutil
import subprocess
import time
from pathlib import Path
from support import save, sha, utc


def build(bundle, plan, vid, version, operator, provenance):
    study = bundle / 'study'
    out = study / plan['output_relative']
    unit = out / 'builds' / vid / operator
    unit.mkdir(parents=True, exist_ok=False)
    sources = version.get('offset_sources', version['sources']) if operator.startswith('offset_') else version['sources']
    conf = version.get('offset_conf', version['conf']) if operator.startswith('offset_') else version['conf']
    source_hash = version.get('offset_source_sha256', version['source_sha256']) if operator.startswith('offset_') else version['source_sha256']
    driver, macros = None, []
    if operator == 'nonarrival':
        driver = plan['drivers']['nonarrival']
        macros = ['QUALITY_DELAY_US=0','QUALITY_LATENCY_ALARM=0','QUALITY_LATENCY_COUNTING=0',
                  'QUALITY_NONARRIVAL_ALARM=' + str(int(version['family'] != 'rtc_time_counting')),
                  'QUALITY_NONARRIVAL_COUNTING=' + str(int(version['family'] == 'rtc_time_counting'))]
    elif operator.startswith('offset_'):
        driver = plan['drivers']['offset']
        macros = ['QUALITY_ALARM_OFFSET_SIGN=' + ('-1' if operator == 'offset_early' else '1')]
    files = [*sources, conf, *plan['overlays'], *version.get('support_inputs', {})]
    if driver:
        files.append(driver)
    for rel in files:
        if sha(study / rel) != plan['input_sha256']['study/' + rel]:
            raise RuntimeError('Build input changed: ' + rel)
    record = dict(version_id=vid, original_suite_id=version.get('original_suite_id'), operator=operator,
        variant=version['variant'], family=version['family'], source_sha256=source_hash,
        inputs={r: sha(study / r) for r in files}, macros=macros, timestamp_utc=utc(), **provenance)
    if operator == 'nominal' and version['reuse_nominal_elf']:
        elf = study / version['original_elf_path']
        if sha(elf) != version['original_elf_sha256']:
            raise RuntimeError('Frozen nominal ELF differs')
        record.update(status='pass', reused_frozen_elf=True, elf_path=str(elf.relative_to(study)),
                      elf_sha256=sha(elf), commands=[])
        save(unit / 'build_record.json', record)
        return record
    zephyr = Path('/opt/zephyrproject/zephyr')
    env = dict(os.environ, ZEPHYR_BASE=str(zephyr), ZEPHYR_TOOLCHAIN_VARIANT='zephyr',
               ZEPHYR_SDK_INSTALL_DIR='/opt/zephyr-sdk-0.17.4', CCACHE_DISABLE='1')
    safe = [str(zephyr), '/opt/zephyrproject/modules/hal/cmsis', '/opt/zephyrproject/modules/hal/cmsis_6',
            '/opt/zephyrproject/modules/hal/stm32']
    env['GIT_CONFIG_COUNT'] = str(len(safe))
    for i, path in enumerate(safe):
        env[f'GIT_CONFIG_KEY_{i}'] = 'safe.directory'
        env[f'GIT_CONFIG_VALUE_{i}'] = path
    commit = subprocess.check_output(['git','-C',str(zephyr),'rev-parse','HEAD'],env=env,text=True).strip()
    if commit != '3568e1b6d5cdd51a6b964a2a1d6d29200fea2056':
        raise RuntimeError('Zephyr commit differs')
    app, target = unit / 'app', unit / 'build'
    app.mkdir()
    cmake = ('cmake_minimum_required(VERSION 3.20.0)\nfind_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})\n'
             'project(rtc_mechanical_repair)\ntarget_sources(app PRIVATE ' +
             ' '.join(str(study / s) for s in sources) + ')\n')
    if version.get('app_define'):
        cmake += 'target_compile_definitions(app PRIVATE ' + version['app_define'] + ')\n'
    if driver:
        cmake += ('get_target_property(rtc_sources drivers__rtc SOURCES)\n'
                  'list(FILTER rtc_sources EXCLUDE REGEX "rtc_ll_stm32[.]c$")\n'
                  'set_property(TARGET drivers__rtc PROPERTY SOURCES "${rtc_sources}")\n'
                  f'target_sources(drivers__rtc PRIVATE {study / driver})\n'
                  f'target_include_directories(drivers__rtc PRIVATE {zephyr}/drivers/rtc)\n'
                  'target_compile_definitions(drivers__rtc PRIVATE ' + ' '.join(macros) + ')\n')
    (app / 'CMakeLists.txt').write_text(cmake)
    shutil.copyfile(study / conf, app / 'prj.conf')
    commands = [[shutil.which('cmake'),'-S',str(app),'-B',str(target),'-G','Ninja','-DBOARD=stm32f4_disco',
        '-DDTC_OVERLAY_FILE=' + ';'.join(str(study / o) for o in plan['overlays']),
        '-DZEPHYR_MODULES=' + ';'.join(safe[1:]), '-DPYTHON_EXECUTABLE=/opt/rtc-python/bin/python',
        '-DPython3_EXECUTABLE=/opt/rtc-python/bin/python'],
        [shutil.which('cmake'),'--build',str(target),'--parallel',str(plan['compiler_parallelism'])]]
    start = time.monotonic()
    rc, error = 0, None
    log = unit / 'build.log'
    with log.open('x') as stream:
        for command in commands:
            try:
                rc = subprocess.run(command,cwd=unit,env=env,stdout=stream,stderr=subprocess.STDOUT,
                    timeout=max(1,plan['build_timeout_sec']-(time.monotonic()-start))).returncode
            except subprocess.TimeoutExpired:
                rc, error = 124, 'build_timeout'
            if rc:
                break
    elf = target / 'zephyr/zephyr.elf'
    record.update(status='pass' if rc == 0 and elf.exists() else 'build_fail', returncode=rc,error=error,
        wall_seconds=round(time.monotonic()-start,3),commands=commands,zephyr_commit=commit,
        app_sha256={q.name:sha(q) for q in app.iterdir()},log_path=str(log.relative_to(study)),log_sha256=sha(log),
        elf_path=str(elf.relative_to(study)) if elf.exists() else None,elf_sha256=sha(elf) if elf.exists() else None)
    save(unit / 'build_record.json',record)
    return record
