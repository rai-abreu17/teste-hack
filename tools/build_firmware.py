"""Compile only the ESP32 firmware, keeping custom-chip C out of Arduino build.

The ESP32 3.3.0 Windows toolchain fails when either the sketch or Arduino data
path contains non-ASCII characters.  The repository lives below ``Raí``, so a
real compile needs an ASCII staging directory and a temporary ``subst`` drive
for Arduino15.  The workaround is local to this process and is removed on exit.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cli',default='arduino-cli')
p.add_argument('--stage-only',action='store_true',help='prepare the Arduino sketch without compiling it')
args=p.parse_args()

SOURCES = ('config.h','ITofSensor.h','SimTofSensor.h','SimTofSensor.cpp')


def stage_sources(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/'wokwi'/'sketch.ino', destination/'BoxFlow.ino')
    for name in SOURCES:
        shutil.copyfile(ROOT/'wokwi'/name, destination/name)


def non_ascii(value: Path) -> bool:
    try:
        str(value).encode('ascii')
    except UnicodeEncodeError:
        return True
    return False


stage=ROOT/'build'/'arduino'/'BoxFlow'
out=ROOT/'build'/'firmware'
out.mkdir(parents=True,exist_ok=True)
stage_sources(stage)
if args.stage_only:
    print(f'Sketch Arduino preparado em {stage}')
    raise SystemExit(0)

compile_stage = stage
compile_out = out
environment = os.environ.copy()
subst_drive = None

if os.name == 'nt' and non_ascii(ROOT):
    token = hashlib.sha256(str(ROOT).encode('utf-8')).hexdigest()[:10]
    portable = Path(environment.get('SystemDrive', 'C:')) / 'BoxFlowArduinoBuild' / token
    compile_stage = portable / 'BoxFlow'
    compile_out = portable / 'firmware'
    compile_out.mkdir(parents=True, exist_ok=True)
    stage_sources(compile_stage)

    data = Path(environment.get(
        'ARDUINO_DIRECTORIES_DATA',
        str(Path(environment['LOCALAPPDATA']) / 'Arduino15'),
    ))
    if non_ascii(data):
        home = Path.home()
        relative_data = data.relative_to(home)
        occupied = {p.drive.upper() for p in Path('/').glob('*') if p.drive}
        for letter in 'ZYXWVUTSRQPONMLKJIHGFED':
            candidate = f'{letter}:'
            if candidate.upper() not in occupied and not Path(candidate + '\\').exists():
                subprocess.run(['subst', candidate, str(home)], check=True)
                subst_drive = candidate
                environment['ARDUINO_DIRECTORIES_DATA'] = str(Path(candidate + '\\') / relative_data)
                break
        if subst_drive is None:
            raise RuntimeError('No free drive letter for the Arduino Unicode-path workaround')

try:
    subprocess.run(
        [args.cli,'compile','--fqbn','esp32:esp32:esp32','--output-dir',str(compile_out),str(compile_stage)],
        check=True,
        env=environment,
    )
    if compile_out != out:
        for artifact in compile_out.glob('BoxFlow.ino.*'):
            shutil.copyfile(artifact, out/artifact.name)
finally:
    if subst_drive is not None:
        subprocess.run(['subst', subst_drive, '/D'], check=False)

print(f'Firmware compilado em {out}')
