from collections import Counter

from knowledge.champion_spell_cast_stats import resolve_cast_stats
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


def build_audit(catalog=None):
    catalog=catalog or get_pinned_spell_catalog(); cooldown=Counter(); cost=Counter(); ranges=Counter(); failures=[]; total=0
    for champion in catalog["records"].values():
        for spell in champion["primary_spells"]:
            total+=1
            try: result=resolve_cast_stats(spell,1,5)
            except Exception as exc: failures.append((spell.get("champion_id"),spell.get("slot"),type(exc).__name__)); continue
            cooldown[result["cooldown"]["status"]]+=1; cost[result["resource_cost"]["status"]]+=1; ranges[result["cast_range"]["status"]]+=1
    return {"total":total,"cooldown":cooldown,"cost":cost,"ranges":ranges,"failures":failures}


def main():
    audit=build_audit(); print(f"Primary spells: {audit['total']}"); print(f"Cooldown statuses: {dict(audit['cooldown'])}"); print(f"Cost statuses: {dict(audit['cost'])}"); print(f"Range statuses: {dict(audit['ranges'])}"); print(f"Failures: {audit['failures'][:10]}")
    ok=audit["total"]==692 and not audit["failures"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}"); return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
