from collections import Counter

from knowledge.champion_spell_formula_runtime import evaluate_spell_calculation
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


def build_audit(catalog=None):
    catalog=catalog or get_pinned_spell_catalog(); statuses=Counter(); failures=[]; total=0
    snapshot={"status":"AUDIT_NEUTRAL_STATIC_CONTEXT","stats":{}}
    for champion in catalog["records"].values():
        for spell in champion["primary_spells"]:
            for key in spell.get("raw_calculation_names",[]):
                total+=1
                try: statuses[evaluate_spell_calculation(spell,key,spell_rank=1,max_rank=5,source_snapshot=snapshot)["result"].status]+=1
                except Exception as exc: failures.append((spell.get("champion_id"),spell.get("slot"),key,type(exc).__name__))
    return {"total":total,"statuses":statuses,"failures":failures}


def main():
    audit=build_audit(); print(f"Runtime calculations: {audit['total']}"); print(f"Statuses: {dict(audit['statuses'])}"); print(f"Failures: {audit['failures'][:10]}")
    ok=audit["total"]==1443 and not audit["failures"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}"); return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
