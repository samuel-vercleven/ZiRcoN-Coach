from collections import Counter

from knowledge.champion_attack_speed_source import load_attack_speed_ratio_catalog
from knowledge.champion_knowledge import build_champion_knowledge_catalog
from knowledge.combat_stat_snapshot import build_combat_snapshot
from knowledge.item_knowledge import build_item_knowledge_catalog


REPRESENTATIVE_STATS=("attack_damage","ability_power","armor","magic_resistance","health","attack_speed_percent")


def _representative_items(records):
    selected={}
    for stat_name in REPRESENTATIVE_STATS:
        for item_id,item in sorted(records.items()):
            if not item.get("applicability",{}).get("purchasable_on_summoners_rift"):
                continue
            if any(row.get("stat")==stat_name and row.get("source")=="DDRAGON_STATS" for row in item.get("normalized_stats",[])):
                selected[stat_name]=item_id; break
    return selected


def build_audit(champion_catalog=None,item_catalog=None,attack_speed_catalog=None):
    champion_catalog=champion_catalog or build_champion_knowledge_catalog("16.16.1")
    item_catalog=item_catalog or build_item_knowledge_catalog("16.16.1")
    attack_speed_catalog=attack_speed_catalog or load_attack_speed_ratio_catalog(champion_catalog)
    selected=_representative_items(item_catalog["records"])
    statuses=Counter(); failures=[]; snapshots=0
    item_sets=[()] + [(item_id,) for item_id in selected.values()]
    for champion_id,champion in champion_catalog["records"].items():
        ratio=attack_speed_catalog.get("records",{}).get(champion_id)
        for level in (1,6,11,18):
            for item_ids in item_sets:
                try: result=build_combat_snapshot(champion,level,item_catalog["records"],item_ids,ratio)
                except Exception as exc: failures.append((champion_id,level,item_ids,type(exc).__name__)); continue
                snapshots+=1; statuses[result["status"]]+=1
    return {"champion_catalog":champion_catalog,"item_catalog":item_catalog,"attack_speed_catalog":attack_speed_catalog,"representative_items":selected,"snapshots":snapshots,"statuses":statuses,"failures":failures}


def main():
    audit=build_audit()
    print(f"Champions: {len(audit['champion_catalog']['records'])}")
    print(f"Representative items: {audit['representative_items']}")
    print(f"Snapshots: {audit['snapshots']}")
    print(f"Statuses: {dict(audit['statuses'])}")
    print(f"Failures: {audit['failures'][:10]}")
    ok=len(audit['champion_catalog']['records'])==173 and len(audit['representative_items'])==6 and not audit['failures']
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
