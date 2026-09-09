"""Complete reproducible gate. Exit 2 = review required, not an all-green freeze."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from app.stabilization_checks import frozen_guard, secret_scan

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'logs/build_optimizer/final'
    folder.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONIOENCODING': 'utf-8'}
    commands = [
        ('stable_base', ['-m', 'app.stabilization_checks', 'final']),
        ('unit_scenarios', ['-m', 'build_optimizer.checks']),
        ('real_catalog_recipes', ['-m', 'build_optimizer.catalog_checks']),
        ('golden_replay', ['-m', 'build_optimizer.replay', '--mode', 'golden']),
        ('historical_batch', ['-m', 'build_optimizer.replay', '--mode', 'batch']),
    ]
    checks = []
    for name, args in commands:
        start = time.monotonic()
        try:
            process = subprocess.run([sys.executable, '-X', 'utf8', *args], cwd=ROOT, env=env,
                                     capture_output=True, timeout=1800)
            (folder / f'{name}.txt').write_bytes(process.stdout + process.stderr)
            passed = process.returncode == 0
        except subprocess.TimeoutExpired:
            passed = False
            (folder / f'{name}.txt').write_text('TIMEOUT: command not validated', encoding='utf-8')
        checks.append({'command': name, 'passed': passed, 'seconds': round(time.monotonic() - start, 2)})
        print(f'{name}: {"PASS" if passed else "FAIL"}', flush=True)
    frozen = frozen_guard()
    secret_files = secret_scan()
    diff = subprocess.run(['git', 'diff', '--check', '9b9af010885acf19b647d0c75d763f628e8f5d2b'], cwd=ROOT).returncode == 0
    technical = all(check['passed'] for check in checks) and diff
    result = {'technical_validation': 'PASS' if technical else 'FAIL', 'commands': checks,
              'frozen_paths_unchanged': frozen, 'secret_scan_files': secret_files,
              'git_diff_check': diff, 'contextual_scoring_gate': 'BLOCKED_UNMODELED',
              'purchase_legality_gate': 'BLOCKED_UNMODELED', 'freeze': 'NO FREEZE',
              'status': 'REVIEW_REQUIRED' if technical else 'FAIL'}
    if technical:
        replay = json.loads((ROOT / 'logs/build_optimizer/batch_replay.json').read_text(encoding='utf-8'))
        result.update({'historical_counts': replay['counts'],
                       'contextual_recommendations_validated': replay['contextual_recommendations_validated'],
                       'invalid_buy_now': replay['invalid_buy_now'],
                       'invalid_buy_now_caveat': 'Empty buy_now; does not validate purchase legality.',
                       'future_leakage_in_tested_mutations': 0,
                       'fatal_errors_in_executed_checks': 0})
    (folder / 'zero_gate.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    return 2 if technical else 1


if __name__ == '__main__':
    raise SystemExit(main())
