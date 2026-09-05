"""Broad existing regression runner. Logs stay local; stdout contains status only."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def frozen_guard():
    tree = ast.parse((ROOT / 'main.py').read_text(encoding='utf-8'))
    paths = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'FROZEN_FILES' for t in n.targets))
    subprocess.run(['git', 'diff', '--quiet', 'pre-stabilization-v1', '--', *sorted(paths)], cwd=ROOT, check=True)
    return len(paths)


def secret_scan():
    import re
    paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    bad = []
    for name in paths:
        path = ROOT / name
        if not path.is_file():
            continue
        if path.name == '.env' or path.suffix == '.db' or name.startswith(('.venv/', '.cache/', 'logs/')):
            bad.append(name)
        data = path.read_bytes()
        if re.search(rb'RGAPI-[A-Za-z0-9-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', data):
            bad.append(name)
    if bad:
        raise AssertionError('Secret/local-only file scan failed; paths only: ' + ', '.join(sorted(set(bad))))
    return len(paths)


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'final'
    if label not in ('baseline', 'final'):
        raise SystemExit('Use baseline or final')
    log_dir = ROOT / 'logs' / 'stabilization' / label
    log_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONIOENCODING': 'utf-8'}
    modules = sorted({p.with_suffix('').as_posix().replace('/', '.')
                      for folder in ('analysis', 'knowledge') for p in Path(folder).glob('*checks.py')})
    modules += ['app.v01_alpha_checks', 'app.v01_account_scope_check', 'app.v01_ui_semantics_check',
                'app.v01_death_adapter_check', 'app.v01_remaining_adapters_check', 'app.v01_alpha_smoke']
    if label == 'final':
        modules += ['app.stabilization_regressions', 'app.stabilization_golden_checks']
    results = []
    for module in modules:
        start = time.monotonic()
        try:
            run = subprocess.run([sys.executable, '-X', 'utf8', '-m', module], cwd=ROOT, env=env,
                                 capture_output=True, timeout=300)
            (log_dir / (module + '.txt')).write_bytes(run.stdout + run.stderr)
            passed = run.returncode == 0
        except subprocess.TimeoutExpired:
            passed = False
        results.append({'module': module, 'pass': passed, 'seconds': round(time.monotonic() - start, 2)})
        print(('PASS ' if passed else 'FAIL ') + module, flush=True)
    run = subprocess.run([sys.executable, '-X', 'utf8', 'main.py'], cwd=ROOT, env=env, capture_output=True)
    (ROOT / 'logs' / 'latest_full_run.txt').write_bytes(run.stdout + run.stderr)
    results.append({'module': 'main.py', 'pass': run.returncode == 0})
    print('FROZEN unchanged paths:', frozen_guard(), flush=True)
    print('Secret scan files:', secret_scan(), flush=True)
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    (log_dir / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f"Passed {sum(r['pass'] for r in results)}/{len(results)} command suites", flush=True)
    return int(not all(r['pass'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
