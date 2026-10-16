"""Check Card Harvester runtime dependencies without installing or modifying anything."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


MODULES = {'numpy': 'numpy', 'opencv-python-headless': 'cv2', 'Pillow': 'PIL',
           'openpyxl': 'openpyxl', 'XlsxWriter': 'xlsxwriter', 'phonenumbers': 'phonenumbers'}
MODES = {'video': set(MODULES), 'workbook': {'Pillow', 'openpyxl', 'XlsxWriter', 'phonenumbers'},
         'vcf': {'openpyxl'}}


def numeric_version(value):
    return tuple(int(part) for part in re.match(r'\d+(?:\.\d+)*', value).group().split('.'))


def package_check(name, module, minimum=None):
    result = {'name': name, 'minimum': minimum}
    try:
        # Import as well as inspect metadata: installed wheels may have missing shared libraries.
        importlib.import_module(module)
        result['version'] = importlib.metadata.version(name)
        result['ok'] = minimum is None or numeric_version(result['version']) >= numeric_version(minimum)
        if not result['ok']:
            result['error'] = 'Installed version is below the declared minimum'
    except Exception as error:
        result.update(ok=False, error=f'{type(error).__name__}: {error}')
    return result


def executable_check(name):
    result = {'name': name, 'path': shutil.which(name), 'ok': False}
    if not result['path']:
        result['error'] = 'Executable is not on PATH'
        return result
    try:
        process = subprocess.run([result['path'], '-version'], capture_output=True, text=True, timeout=15)
        result['ok'] = process.returncode == 0
        result['version'] = (process.stdout or process.stderr).splitlines()[0]
        if not result['ok']:
            result['error'] = f'Version command exited with {process.returncode}'
    except (OSError, subprocess.TimeoutExpired, IndexError) as error:
        result.update(ok=False, error=str(error))
    return result


def check(mode='video', hdr=False, qr=False):
    checks = [{'name': 'Python', 'version': sys.version.split()[0],
               'minimum': '3.11', 'ok': sys.version_info >= (3, 11)}]
    requirements = Path(__file__).parent / 'business_cards' / 'requirements.txt'
    for line in requirements.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, minimum = line.strip().split('>=', 1)
        if name in MODES[mode]:
            checks.append(package_check(name, MODULES[name], minimum))
    if mode == 'video':
        checks.extend(executable_check(name) for name in ('ffmpeg', 'ffprobe'))
    if hdr:
        result = {'name': 'ffmpeg HDR filters', 'ok': False}
        try:
            process = subprocess.run(['ffmpeg', '-hide_banner', '-filters'],
                                     capture_output=True, text=True, timeout=15)
            filters = {line.split()[1] for line in process.stdout.splitlines() if len(line.split()) >= 2}
            result['missing'] = sorted({'zscale', 'tonemap'} - filters)
            result['ok'] = process.returncode == 0 and not result['missing']
            if not result['ok']:
                result['error'] = 'Required HDR filters are unavailable'
        except (OSError, subprocess.TimeoutExpired) as error:
            result['error'] = str(error)
        checks.append(result)
    if qr:
        checks.append(package_check('zxing-cpp', 'zxingcpp'))
    return {'mode': mode, 'ok': all(item['ok'] for item in checks), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=tuple(MODES), default='video')
    parser.add_argument('--hdr', action='store_true', help='Require zscale and tonemap in video mode')
    parser.add_argument('--qr', action='store_true', help='Also require the optional QR decoder')
    args = parser.parse_args()
    if args.hdr and args.mode != 'video':
        parser.error('--hdr requires --mode video')
    report = check(args.mode, args.hdr, args.qr)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['ok'] else 1)


if __name__ == '__main__':
    main()
