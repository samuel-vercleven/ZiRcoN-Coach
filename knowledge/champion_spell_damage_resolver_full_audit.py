from collections import Counter

from knowledge.champion_spell_damage_evidence_full_audit import build_audit as build_evidence_audit
from knowledge.champion_spell_damage_resolver import resolve_damage_components


def build_audit(source_catalog=None,champion_catalog=None):
    evidence_audit=build_evidence_audit(source_catalog,champion_catalog); statuses=Counter(); failures=[]; total=0
    source_catalog=evidence_audit["source_catalog"]; champions=evidence_audit["champion_catalog"]
    semantic_records=champions["records"]
    from knowledge.champion_spell_damage_evidence import classify_damage_evidence
    for champion_id,source_champion in source_catalog["records"].items():
        semantic={row.get("inferred_slot"):row for row in semantic_records.get(champion_id,{}).get("spells",[])}
        for spell in source_champion["primary_spells"]:
            evidence=classify_damage_evidence(spell,semantic.get(spell["slot"]))
            try: rows=resolve_damage_components(spell,evidence,{"spell_rank":1,"max_rank":5})
            except Exception as exc: failures.append((champion_id,spell["slot"],type(exc).__name__)); continue
            for row in rows: total+=1; statuses[row["status"]]+=1
    return {"evidence_audit":evidence_audit,"total":total,"statuses":statuses,"failures":failures}


def main():
    audit=build_audit(); print(f"Damage candidates: {audit['total']}"); print(f"Resolver statuses: {dict(audit['statuses'])}"); print(f"Failures: {audit['failures'][:10]}")
    ok=not audit["failures"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}"); return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
