"""Read-only structural inventory; prints Markdown for review, never imports production."""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory(final=False):
    paths = [Path(p) for p in subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '*.py'],
        cwd=ROOT, text=True).splitlines()]
    trees = {p.as_posix(): ast.parse((ROOT / p).read_text(encoding='utf-8-sig')) for p in paths}
    frozen = next(ast.literal_eval(n.value) for n in trees['main.py'].body
                  if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FROZEN_FILES' for t in n.targets))
    imports = {}
    for name, tree in trees.items():
        imports[name] = sorted({n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
                               | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
    lines = ['# Stabilization inventory', '',
             ('Final inventory after stabilization checks, 2026-09-06.' if final else 'Initial structural audit at pre-stabilization-v1.') + ' No status below promotes a frozen methodology.',
             'Inputs/outputs list the existing public contracts; test links are direct import evidence, not claims of execution.',
             'All untested/indirect contracts remain À VALIDER. See STABILIZATION_AUDIT.md for correctness findings.', '',
             '| Module / fichier | Rôle | Entrées / contrats | Sorties | Dépendances | Tests directs | Statut | Risque / notes |',
             '|---|---|---|---|---|---|---|---|']
    corrections = {'services/cache_repository.py', 'services/local_data.py', 'services/post_game_analysis.py'}
    for name, tree in sorted(trees.items()):
        module = name[:-3].replace('/', '.')
        tests = [p for p, deps in imports.items() if module in deps and any(t in p for t in ('check', 'audit', 'test'))]
        public = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith('_')]
        contracts = ', '.join(n.name for n in public) or 'package / constantes'
        role = (ast.get_docstring(tree) or name.rsplit('/', 1)[-1][:-3].replace('_', ' ')).splitlines()[0]
        status = 'À CORRIGER' if name in corrections else 'À VALIDER'
        note = 'FROZEN; invariants only, no retuning' if name in frozen else 'compatibility / missing-data review'
        if final:
            status = 'STABLE' if name in frozen or name.startswith(('services/', 'ui/', 'viewmodels/', 'app/')) or name in ('main.py', 'run_app.py') else 'À VALIDER'
            note = ('FROZEN baseline regression; raw/derived semantics unchanged' if name in frozen
                    else 'tested stabilization surface; not FROZEN')
            if name.startswith('database/'):
                note = 'HIGH: legacy SQL projections; require GameContext admission, golden snapshot verifies current data'
            if name in ('analysis/coaching_engine.py', 'analysis/event_explainer.py', 'riot/riot_api.py', 'config/settings.py'):
                status, note = 'LEGACY', 'not used by desktop service path; preserved, not deleted'
            if name in ('knowledge/champion_level_stats.py', 'knowledge/champion_level_stats_full_audit.py', 'knowledge/champion_attack_speed_source.py'):
                status, note = 'À VALIDER', '16.16 frozen baseline PASS; latest 16.17 ratio unavailable, explicit REVIEW_REQUIRED'
            if name == 'riot/data_dragon.py':
                status, note = 'À VALIDER', 'HIGH: legacy latest fallback; do not use for exact historical semantics without patch guard'
        if not tree.body:
            status, note = 'STABLE', 'empty package marker'
        lines.append('| ' + ' | '.join(str(v).replace('|', '/') for v in
                     (name, role, contracts, 'return values / records' if public else 'module namespace',
                      ', '.join(imports[name]) or 'none', ', '.join(tests) or 'indirect / none identified', status, note)) + ' |')
    lines += ['', f'Python modules inventoried: {len(trees)}. Frozen paths: {len(frozen)}.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    print(inventory('--final' in sys.argv))
