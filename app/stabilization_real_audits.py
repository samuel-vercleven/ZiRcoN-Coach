"""Run retained real knowledge audits without changing their frozen contracts."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    logs = ROOT / 'logs/stabilization/real-audits'
    logs.mkdir(parents=True, exist_ok=True)
    modules = sorted('knowledge.' + p.stem for p in (ROOT / 'knowledge').glob('*_full_audit.py'))
    modules += ['knowledge.item_knowledge', 'knowledge.champion_knowledge', 'knowledge.rune_knowledge']
    results = []
    for module in modules:
        start = time.monotonic()
        try:
            run = subprocess.run([sys.executable, '-X', 'utf8', '-m', module], cwd=ROOT, capture_output=True, timeout=900)
            (logs / (module + '.txt')).write_bytes(run.stdout + run.stderr)
            passed = run.returncode == 0
        except subprocess.TimeoutExpired:
            passed = False
        results.append({'module': module, 'pass': passed, 'seconds': round(time.monotonic() - start, 2)})
        print(('PASS ' if passed else 'FAIL ') + module, flush=True)
    (logs / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return int(not all(row['pass'] for row in results))


if __name__ == '__main__':
    raise SystemExit(main())
