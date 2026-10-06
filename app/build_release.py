"""Build and verify a credential-free Windows portable release."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from contextlib import closing

from app.paths import PROJECT_ROOT, CATALOG_ROOT, DEFAULT_DB_PATH, CACHE_ROOT
from app.version import VERSION
from build_optimizer.profiles import SUPPORTED_PATCHES


def main():
    if sys.platform != 'win32':
        raise SystemExit('Build on Windows for the Windows release.')
    staging = PROJECT_ROOT / 'build' / 'release-resources'
    staging.mkdir(parents=True, exist_ok=True)
    for patch in sorted(SUPPORTED_PATCHES):
        version = patch + '.1'
        target = staging / 'catalogs' / version
        target.mkdir(parents=True, exist_ok=True)
        for resource in ('item.json', 'champion.json'):
            source = CATALOG_ROOT / version / resource
            if json.loads(source.read_text(encoding='utf-8')).get('version') != version:
                raise AssertionError(f'Exact version missing: {version}/{resource}')
            shutil.copy2(source, target / resource)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    QSvgRenderer(str(PROJECT_ROOT / 'resources' / 'zircon.svg')).render(painter)
    painter.end()
    assert image.save(str(staging / 'zircon.ico'))
    # Do not collect unrelated/older DLLs from tools added to the host's PATH.
    windows = Path(os.environ['SystemRoot'])
    build_env = {**os.environ, 'PATH': os.pathsep.join(map(str, (Path(sys.base_prefix), Path(sys.executable).parent, windows / 'System32', windows)))}
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', str(PROJECT_ROOT / 'packaging' / 'zircon.spec')], cwd=PROJECT_ROOT, env=build_env, check=True)
    bundle = PROJECT_ROOT / 'dist' / 'ZiRcoN-Coach'
    executable = bundle / 'ZiRcoN-Coach.exe'
    shutil.copy2(PROJECT_ROOT / 'RELEASE_GUIDE.md', bundle / 'Lire avant de commencer.md')
    shutil.copy2(PROJECT_ROOT / 'THIRD_PARTY_NOTICES.md', bundle / 'THIRD_PARTY_NOTICES.md')
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    assert python_license.is_file(), 'Python license missing from the runtime'
    (bundle / 'licenses' / 'Python').mkdir(parents=True, exist_ok=True)
    shutil.copy2(python_license, bundle / 'licenses' / 'Python' / 'LICENSE.txt')
    for package in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6', 'requests', 'urllib3', 'certifi', 'charset-normalizer', 'idna', 'python-dotenv'):
        dist = importlib.metadata.distribution(package)
        for entry in dist.files or ():
            if 'licenses' in entry.parts and dist.locate_file(entry).is_file():
                target = bundle / 'licenses' / package / entry.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dist.locate_file(entry), target)
    results = []
    for mode in ('fresh', 'local-history'):
        if mode == 'local-history' and not DEFAULT_DB_PATH.exists():
            continue
        with tempfile.TemporaryDirectory(prefix='zircon-release-check-') as directory:
            data = Path(directory)
            if mode == 'local-history':
                db = data / 'database' / 'zircon.db'; db.parent.mkdir()
                with closing(sqlite3.connect(f'{DEFAULT_DB_PATH.resolve().as_uri()}?mode=ro', uri=True)) as source, closing(sqlite3.connect(db)) as target:
                    source.backup(target)
                settings_source = CACHE_ROOT / 'settings.json'
                if settings_source.exists():
                    settings = json.loads(settings_source.read_text(encoding='utf-8'))
                    safe = {key: settings[key] for key in ('game_name', 'tag_line', 'active_puuid', 'sync_scope') if key in settings}
                    target = data / '.cache' / 'zircon' / 'settings.json'; target.parent.mkdir(parents=True)
                    target.write_text(json.dumps(safe), encoding='utf-8')
            env = {**build_env, 'ZIRCON_DATA_DIR': str(data), 'QT_QPA_PLATFORM': 'offscreen'}
            env.pop('RIOT_API_KEY', None)
            output = data / 'result.json'
            args = [str(executable), '--smoke-check', '--smoke-output', str(output)]
            replay = PROJECT_ROOT / 'logs' / 'build_optimizer' / 'contextual_replay.json'
            if mode == 'local-history' and replay.exists():
                rows = json.loads(replay.read_text(encoding='utf-8')).get('rows', [])
                if rows: args.extend(['--smoke-match', rows[0]['match_id']])
            run = subprocess.run(args, env=env, cwd=data, timeout=240)
            result = json.loads(output.read_text(encoding='utf-8'))
            if run.returncode or not result.get('passed'):
                raise RuntimeError(f'Release {mode} smoke failed: {result.get("error", "unknown error")}')
            assert result['passed'] and result['initialized_pages'] == 5
            assert Path(result['database_path']).is_relative_to(data)
            captures = PROJECT_ROOT / 'logs' / 'release' / VERSION / mode
            captures.mkdir(parents=True, exist_ok=True)
            for capture_path in result.get('captures', []):
                capture = Path(capture_path)
                assert capture.resolve().is_relative_to(data.resolve())
                shutil.copy2(capture, captures / capture.name)
            classic_output = data / 'classic-result.json'
            classic_args = [str(executable), '--classic', '--smoke-check', '--smoke-output', str(classic_output)]
            classic_run = subprocess.run(classic_args, env=env, cwd=data, timeout=240)
            classic_result = json.loads(classic_output.read_text(encoding='utf-8'))
            assert not classic_run.returncode and classic_result.get('passed'), 'Packaged classic fallback smoke failed'
            results.append({'mode': mode, 'passed': True, 'presentation': result.get('presentation'),
                            'captures': len(result.get('captures', [])), 'classic_fallback': True,
                            'matches_opened': result.get('matches_opened', 0)})
    for path in bundle.rglob('*'):
        if path.is_file():
            assert path.name not in ('.env', 'settings.json') and path.suffix != '.db', f'Private file in release: {path.name}'
            if re.search(rb'RGAPI-[A-Za-z0-9-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}', path.read_bytes()):
                raise AssertionError(f'Credential pattern in release: {path.name}')
    manifest = {'version': VERSION, 'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, text=True).strip(),
        'source_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=PROJECT_ROOT, text=True).strip()),
        'smoke_checks': results, 'patches': sorted(SUPPORTED_PATCHES), 'contains_credentials': False, 'contains_player_history': False}
    (bundle / 'release-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = Path(shutil.make_archive(str(PROJECT_ROOT / 'dist' / f'ZiRcoN-Coach-{VERSION}-Windows-x64'), 'zip', bundle.parent, bundle.name))
    with archive.open('rb') as stream:
        manifest['archive_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    (archive.with_suffix('.json')).write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
    print(json.dumps({'status': 'PASS', 'archive': str(archive), 'size_mb': round(archive.stat().st_size / 1e6, 1), **manifest}, indent=2))


if __name__ == '__main__':
    main()
