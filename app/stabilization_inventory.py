"""Read-only structural inventory; prints Markdown for review, never imports production."""
import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory():
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
             'Initial structural audit at pre-stabilization-v1. No status below promotes a frozen methodology.',
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
        if not tree.body:
            status, note = 'STABLE', 'empty package marker'
        lines.append('| ' + ' | '.join(str(v).replace('|', '/') for v in
                     (name, role, contracts, 'return values / records' if public else 'module namespace',
                      ', '.join(imports[name]) or 'none', ', '.join(tests) or 'indirect / none identified', status, note)) + ' |')
    lines += ['', f'Python modules inventoried: {len(trees)}. Frozen paths: {len(frozen)}.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    print(inventory())
