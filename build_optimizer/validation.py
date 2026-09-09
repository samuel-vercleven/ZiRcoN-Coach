"""Complete reproducible gate. Exit 2 = review required, not an all-green freeze."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from app.stabilization_checks import frozen_guard, secret_scan

ROOT = Path(__file__).resolve().parents[1]


def product_zero_gate(checks, replay, diff_ok):
    """Separate executed invariant checks from the absent product contracts.

    A green command or an empty buy_now cannot establish gameplay validity.
    This assessment does not provide a flag to approve unimplemented contracts.
    """
    passed = {c['command']: c['passed'] is True for c in checks}

    def tested(*names):
        return 'PASS' if all(passed.get(name, False) for name in names) else 'FAIL'

    rows = replay.get('rows', [])
    outputs = [row['recommendation'] for row in rows]
    emitted = sum(out['target_item'] is not None or bool(out['buy_now']) for out in outputs)
    scored = sum(out['score'] is not None for out in outputs)
    replay_ok = tested('golden_replay', 'historical_batch') == 'PASS' and bool(rows)
    gates = {
        'Stable Base regression': tested('stable_base'),
        'Unit tests': tested('unit_scenarios', 'product_gate_checks'),
        'Integration invariants / serialization': tested('product_gate_checks'),
        'Integration product recommendations': 'BLOCKED',
        'Scenario invariants': tested('unit_scenarios'),
        'Scenario gameplay quality': 'BLOCKED',
        'Historical replay': 'PASS' if replay_ok else 'FAIL',
        'Temporal integrity': 'PASS' if replay_ok and replay.get('temporal_integrity') == 'PASS' else 'FAIL',
        'Recipe planning': tested('real_catalog_recipes', 'product_gate_checks', 'historical_batch'),
        'Scoring / final breakdown / explanation': 'BLOCKED',
        'Purchase feasibility (complete)': 'BLOCKED',
        'git diff --check': 'PASS' if diff_ok else 'FAIL',
    }
    return {
        'title': 'BUILD OPTIMIZER V1 ZERO GATE', 'gates': gates, 'freeze': 'NO FREEZE',
        'status': 'FAIL' if 'FAIL' in gates.values() else 'REVIEW_REQUIRED',
        'recommendations_observed': len(outputs), 'nonempty_recommendations': emitted,
        'final_scores_exercised': scored,
        'invalid_purchase_count': 0 if outputs and not emitted else None,
        'unexplained_recommendations': 0 if outputs and not emitted else None,
        'future_information_leakage': 0 if gates['Temporal integrity'] == 'PASS' else None,
        'fatal_scoring_errors': None,
        'counter_scope': 'Empty outputs are not purchase validation; final gameplay scoring is not exercised.',
        'blockers': [
            {'id': 'CONTEXTUAL_UTILITY_CONTRACT_MISSING', 'kind': 'MISSING_MODEL_CONTRACT',
             'evidence': 'scoring.py: eight factors UNMODELED; score=None; economy is diagnostic only.'},
            {'id': 'PURCHASE_LEGALITY_CONTRACT_MISSING', 'kind': 'MISSING_DATA_AND_MODEL_CONTRACT',
             'evidence': 'ItemView.restrictions_status=UNMODELED; shop_access/inventory_completeness unproven.'},
            {'id': 'PRODUCT_RECOMMENDATIONS_NOT_VALIDATED', 'kind': 'MISSING_PRODUCT_TEST_COVERAGE',
             'evidence': 'engine.py abstains; scenarios test invariants, not nonempty contextual recommendations.'},
        ],
    }


def main():
    folder = ROOT / 'logs/build_optimizer/final'
    folder.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONIOENCODING': 'utf-8'}
    commands = [
        ('stable_base', ['-m', 'app.stabilization_checks', 'final']),
        ('unit_scenarios', ['-m', 'build_optimizer.checks']),
        ('product_gate_checks', ['-m', 'build_optimizer.gate_checks']),
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
    replay = {}
    if technical:
        replay = json.loads((ROOT / 'logs/build_optimizer/batch_replay.json').read_text(encoding='utf-8'))
        result.update({'historical_counts': replay['counts'],
                       'contextual_recommendations_validated': replay['contextual_recommendations_validated'],
                       'invalid_buy_now': replay['invalid_buy_now'],
                       'invalid_buy_now_caveat': 'Empty buy_now; does not validate purchase legality.',
                       'future_leakage_in_tested_mutations': 0,
                       'fatal_errors_in_executed_checks': 0})
    result['product_zero_gate'] = product_zero_gate(checks, replay, diff)
    (folder / 'zero_gate.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    return 2 if technical else 1


if __name__ == '__main__':
    raise SystemExit(main())
