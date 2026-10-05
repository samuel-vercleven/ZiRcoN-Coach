from pathlib import Path

root = Path(SPECPATH).parent
staging = root / 'build' / 'release-resources'
a = Analysis([str(root / 'run_app.py')], pathex=[str(root)],
             datas=[(str(staging / 'catalogs'), 'resources/catalogs'),
                    (str(root / 'resources' / '*.svg'), 'resources'),
                    (str(root / 'ui' / 'quick' / 'qml'), 'ui/quick/qml')],
             hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=['pytest'], noarchive=False)
# Release inputs must be project assets, the chosen Python runtime or Windows.
import os
import sys
allowed = (root, Path(sys.base_prefix), Path(os.environ['SystemRoot']))
for _, source, _ in a.binaries:
    assert any(Path(source).resolve().is_relative_to(path.resolve()) for path in allowed), f'Unexpected external binary: {source}'
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ZiRcoN-Coach',
          debug=False, strip=False, upx=False, console=False,
          icon=str(staging / 'zircon.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ZiRcoN-Coach')
