import subprocess
import sys
from pathlib import Path
from time import perf_counter


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace",
    )


PROJECT_ROOT = Path(__file__).resolve().parent
CURRENT_PHASE = (
    "Champion Spell Calculation Source Foundation Phase 2F"
)


TEST_COMMANDS = [
    (
        "Compilation Champion Spell Source",
        [
            sys.executable,
            "-m",
            "py_compile",
            "knowledge/champion_spell_source.py",
            "knowledge/champion_spell_source_synthetic_checks.py",
            "knowledge/champion_spell_source_precision_checks.py",
            "knowledge/champion_spell_source_full_audit.py",
        ],
    ),
    (
        "Tests synthétiques",
        [
            sys.executable,
            "-m",
            "knowledge.champion_spell_source_synthetic_checks",
        ],
    ),
    (
        "Tests de précision",
        [
            sys.executable,
            "-m",
            "knowledge.champion_spell_source_precision_checks",
        ],
    ),
    (
        "Audit complet Champion Spell Source",
        [
            sys.executable,
            "-m",
            "knowledge.champion_spell_source_full_audit",
        ],
    ),
]


FROZEN_FILES = {
    "analysis/death_cost_analyzer.py",
    "analysis/death_statistics.py",
    "analysis/jungle_tempo_analyzer.py",
    "analysis/tempo_statistics.py",
    "analysis/objective_analyzer.py",
    "analysis/objective_statistics.py",
    "analysis/reset_analyzer.py",
    "analysis/reset_statistics.py",
    "analysis/itemization_analyzer.py",
    "knowledge/item_knowledge.py",
    "knowledge/item_knowledge_synthetic_checks.py",
    "knowledge/item_knowledge_precision_checks.py",
    "knowledge/champion_knowledge.py",
    "knowledge/champion_knowledge_synthetic_checks.py",
    "knowledge/champion_knowledge_precision_checks.py",
    "knowledge/rune_knowledge.py",
    "knowledge/rune_knowledge_synthetic_checks.py",
    "knowledge/rune_knowledge_precision_checks.py",
    "knowledge/rune_knowledge_full_audit.py",
    "knowledge/champion_attack_speed_source.py",
    "knowledge/champion_level_stats.py",
    "knowledge/champion_level_stats_synthetic_checks.py",
    "knowledge/champion_level_stats_precision_checks.py",
    "knowledge/champion_level_stats_full_audit.py",
    "knowledge/combat_resistance_rules.py",
    "knowledge/combat_resistance_synthetic_checks.py",
    "knowledge/combat_resistance_precision_checks.py",
    "knowledge/combat_resistance_full_audit.py",
    "knowledge/champion_spell_source.py",
    "knowledge/champion_spell_source_synthetic_checks.py",
    "knowledge/champion_spell_source_precision_checks.py",
    "knowledge/champion_spell_source_full_audit.py",
}


def _run(title, command):
    start = perf_counter()
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration = perf_counter() - start

    stdout_lines = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    status_line = next(
        (
            line
            for line in reversed(stdout_lines)
            if line.startswith("STATUS :")
        ),
        "",
    )

    if result.returncode == 0:
        detail = ""

        if title == "Audit complet Champion Spell Source":
            if status_line:
                detail = f" | {status_line}"
        elif stdout_lines:
            detail = f" | {stdout_lines[-1]}"

        print(
            f"[PASS] {title} "
            f"({duration:.2f}s){detail}"
        )
        return True

    print(
        f"[FAIL] {title} "
        f"({duration:.2f}s)"
    )

    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())

    return False


def _git_changed_files():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        return []

    changed = []

    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue

        path = line[3:].strip()

        if " -> " in path:
            path = path.split(" -> ", 1)[1]

        changed.append(
            path.replace("\\", "/")
        )

    return sorted(set(changed))


def _check_frozen_files():
    changed = _git_changed_files()

    frozen_changed = [
        path
        for path in changed
        if path in FROZEN_FILES
    ]

    if frozen_changed:
        print("[FAIL] FROZEN guard")

        for path in frozen_changed:
            print(f"       {path}")

        return False

    print(
        "[PASS] FROZEN guard - "
        "aucun module gelé modifié"
    )
    return True


def main():
    print("=" * 60)
    print(
        "ZiRcoN Coach - "
        "validation de développement"
    )
    print("=" * 60)
    print(f"Phase : {CURRENT_PHASE}")
    print()

    start = perf_counter()

    for title, command in TEST_COMMANDS:
        if not _run(title, command):
            print()
            print("STATUS : REVIEW_REQUIRED")
            return 1

    if not _check_frozen_files():
        print()
        print("STATUS : REVIEW_REQUIRED")
        return 1

    changed = _git_changed_files()

    if changed:
        print()
        print("Fichiers locaux modifiés :")

        for path in changed:
            print(f"- {path}")

    print()
    print(
        f"Durée totale : "
        f"{perf_counter() - start:.2f}s"
    )
    print("STATUS : PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
