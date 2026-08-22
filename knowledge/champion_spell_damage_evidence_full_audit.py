from collections import Counter

from knowledge.champion_knowledge import build_champion_knowledge_catalog
from knowledge.champion_spell_damage_evidence import classify_damage_evidence
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


def build_audit(source_catalog=None,champion_catalog=None):
    source_catalog=source_catalog or get_pinned_spell_catalog(); champion_catalog=champion_catalog or build_champion_knowledge_catalog("16.16.1")
    statuses=Counter(); types=Counter(); components=0; failures=[]
    for champion_id,source_champion in source_catalog["records"].items():
        semantic={spell.get("inferred_slot"):spell for spell in champion_catalog["records"].get(champion_id,{}).get("spells",[])}
        for source_spell in source_champion["primary_spells"]:
            try: result=classify_damage_evidence(source_spell,semantic.get(source_spell["slot"]))
            except Exception as exc: failures.append((champion_id,source_spell["slot"],type(exc).__name__)); continue
            statuses[result["status"]]+=1; components+=len(result["components"]); types.update(row["damage_type"] for row in result["components"])
    return {"source_catalog":source_catalog,"champion_catalog":champion_catalog,"statuses":statuses,"types":types,"components":components,"failures":failures}


def main():
    audit=build_audit(); print(f"Primary spells: {sum(audit['statuses'].values())}"); print(f"Evidence statuses: {dict(audit['statuses'])}"); print(f"Damage types: {dict(audit['types'])}"); print(f"Candidate components: {audit['components']}"); print(f"Failures: {audit['failures'][:10]}")
    ok=sum(audit["statuses"].values())==692 and not audit["failures"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}"); return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
