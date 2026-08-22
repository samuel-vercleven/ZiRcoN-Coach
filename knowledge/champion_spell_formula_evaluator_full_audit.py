from collections import Counter
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.champion_spell_formula_evaluator import evaluate_calculation

def build_audit():
    catalog=get_pinned_spell_catalog(); counts=Counter(); total=0; examples=[]
    for champ in catalog["records"].values():
        for spell in champ["primary_spells"]:
            for key in spell.get("raw_calculation_names",[]):
                total+=1
                try: result=evaluate_calculation(spell,key,{"spell_rank":1,"max_rank":5})
                except Exception as exc:
                    counts["UNEXPECTED_EXCEPTION"]+=1; examples.append((spell.get("champion_id"),spell.get("slot"),key,type(exc).__name__)); continue
                counts[result.status]+=1
    return {"total":total,"counts":counts,"examples":examples,"catalog":catalog}

def main():
    audit=build_audit(); print(f"Total calculations: {audit['total']}"); print(f"Statuses: {dict(audit['counts'])}"); print(f"Unexpected examples: {audit['examples'][:5]}")
    ok=audit['total']==1443 and not audit['examples']; print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}"); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
