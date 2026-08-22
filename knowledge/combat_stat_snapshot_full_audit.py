from collections import Counter

from knowledge.champion_attack_speed_source import load_attack_speed_ratio_catalog
from knowledge.champion_knowledge import build_champion_knowledge_catalog
from knowledge.combat_stat_snapshot import STATIC_STAT_RESOLVED, build_combat_snapshot
from knowledge.item_knowledge import build_item_knowledge_catalog

STRUCTURED_REPRESENTATIVES = ("attack_damage", "ability_power", "armor", "magic_resistance", "health", "attack_speed_percent")
EXCLUDED_REPRESENTATIVES = ("lethality", "ability_haste", "armor_penetration_percent", "magic_penetration_percent")
CANONICAL_OUTPUTS = {
    "health": ("health_bonus", "health_max"),
    "attack_damage": ("attack_damage_bonus", "attack_damage_total"),
    "armor": ("armor_bonus", "armor"),
    "magic_resistance": ("magic_resistance_bonus", "magic_resistance"),
    "flat_move_speed": ("move_speed",),
    "attack_speed_percent": ("attack_speed_percent", "attack_speed"),
}


def _representative_items(records):
    selected = {}
    for stat_name in STRUCTURED_REPRESENTATIVES:
        for item_id, item in sorted(records.items()):
            if item.get("applicability", {}).get("purchasable_on_summoners_rift") and any(row.get("stat") == stat_name and row.get("source") == "DDRAGON_STATS" for row in item.get("normalized_stats", [])):
                selected[f"structured:{stat_name}"] = {"item_id": item_id, "name": item.get("name")}
                break
    for stat_name in EXCLUDED_REPRESENTATIVES:
        for item_id, item in sorted(records.items()):
            if item.get("applicability", {}).get("purchasable_on_summoners_rift") and any(row.get("stat") == stat_name and row.get("source") != "DDRAGON_STATS" for row in item.get("normalized_stats", [])):
                selected[f"excluded:{stat_name}"] = {"item_id": item_id, "name": item.get("name")}
                break
    return selected


def build_audit(champion_catalog=None, item_catalog=None, attack_speed_catalog=None):
    champion_catalog = champion_catalog or build_champion_knowledge_catalog("16.16.1")
    item_catalog = item_catalog or build_item_knowledge_catalog("16.16.1")
    attack_speed_catalog = attack_speed_catalog or load_attack_speed_ratio_catalog(champion_catalog)
    selected = _representative_items(item_catalog["records"])
    unique_ids = list(dict.fromkeys(row["item_id"] for row in selected.values()))
    item_sets = [()] + [(item_id,) for item_id in unique_ids]
    statuses = Counter()
    excluded_facts = Counter()
    applied_facts = Counter()
    partial_outputs = Counter()
    silent_exact_exclusions = []
    failures = []
    snapshots = 0
    for champion_id, champion in champion_catalog["records"].items():
        ratio = attack_speed_catalog.get("records", {}).get(champion_id)
        for level in (1, 6, 11, 18):
            for item_ids in item_sets:
                try:
                    result = build_combat_snapshot(champion, level, item_catalog["records"], item_ids, ratio)
                except Exception as exc:
                    failures.append((champion_id, level, item_ids, type(exc).__name__))
                    continue
                snapshots += 1
                statuses[result["status"]] += 1
                partial_outputs.update(result["partial_outputs"])
                for fact in result["excluded_static_facts"]:
                    excluded_facts[(fact["stat"], fact["source"])] += 1
                    for output in CANONICAL_OUTPUTS.get(fact["stat"], (fact["stat"],)):
                        if result["stat_resolution"].get(output, {}).get("status") == STATIC_STAT_RESOLVED:
                            silent_exact_exclusions.append((champion_id, level, item_ids, output))
                for resolution in result["stat_resolution"].values():
                    applied_facts.update((fact["stat"], fact["source"]) for fact in resolution.get("applied_facts", []))
    expected_keys = {f"structured:{stat}" for stat in STRUCTURED_REPRESENTATIVES} | {f"excluded:{stat}" for stat in EXCLUDED_REPRESENTATIVES}
    return {
        "champion_catalog": champion_catalog,
        "item_catalog": item_catalog,
        "attack_speed_catalog": attack_speed_catalog,
        "representative_items": selected,
        "representatives_missing": sorted(expected_keys - set(selected)),
        "snapshots": snapshots,
        "statuses": statuses,
        "excluded_facts": excluded_facts,
        "applied_facts": applied_facts,
        "partial_outputs": partial_outputs,
        "silent_exact_exclusions": silent_exact_exclusions,
        "failures": failures,
    }


def main():
    audit = build_audit()
    print(f"Champions: {len(audit['champion_catalog']['records'])}")
    print(f"Representative items: {audit['representative_items']}")
    print(f"Snapshots: {audit['snapshots']}")
    print(f"Snapshot statuses: {dict(audit['statuses'])}")
    print(f"Excluded relevant static facts: {dict(audit['excluded_facts'])}")
    print(f"Exact applied item facts: {dict(audit['applied_facts'])}")
    print(f"Unresolved totals: {dict(audit['partial_outputs'])}")
    print(f"Silent exact exclusions: {audit['silent_exact_exclusions'][:10]}")
    print(f"Failures: {audit['failures'][:10]}")
    ok = len(audit["champion_catalog"]["records"]) == 173 and not audit["representatives_missing"] and not audit["failures"] and not audit["silent_exact_exclusions"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
