"""Real-catalog gap probes plus non-circular arithmetic precision checks."""
from knowledge.champion_spell_damage_evidence import classify_damage_evidence
from knowledge.champion_spell_damage_resolver import resolve_damage_components
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog

REPRESENTATIVE_CHAMPIONS=("Ahri","Ezreal","Kayle","Chogath","Darius","Jayce","Singed","Shyvana","Belveth","DrMundo","Viego","Rammus")


def run_representative_checks(source_catalog=None,champion_catalog=None):
    source_catalog=source_catalog or get_pinned_spell_catalog(); probes=[]; failures=[]
    semantic_records=(champion_catalog or {}).get("records",{})
    for champion_id in REPRESENTATIVE_CHAMPIONS:
        source=source_catalog["records"].get(champion_id)
        if source is None: failures.append((champion_id,"SOURCE_RECORD_MISSING")); continue
        semantic={row.get("inferred_slot"):row for row in semantic_records.get(champion_id,{}).get("spells",[])}
        for spell in source["primary_spells"]:
            evidence=classify_damage_evidence(spell,semantic.get(spell["slot"])) if champion_catalog else {"status":"SEMANTIC_CATALOG_NOT_SUPPLIED","components":[],"evidence":{}}
            resolved=resolve_damage_components(spell,evidence,{"spell_rank":1,"max_rank":5})
            probes.append({"champion_id":champion_id,"slot":spell["slot"],"classes":spell.get("calculation_classes",[]),"evidence_status":evidence["status"],"candidate_count":len(evidence["components"]),"raw_resolved_count":sum(row["status"]=="RAW_DAMAGE_RESOLVED" for row in resolved)})

    fixture={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"champion_id":"ManualPinnedShape","slot":"Q","raw_data_values":[{"name":"BaseDamage","values":[0,25,50,75,100,125,150]}],"raw_m_spell_calculations":{"QDamage":{"~class":"GameCalculation","mFormulaParts":[{"~class":"NamedDataValueCalculationPart","mDataValue":"BaseDamage"},{"~class":"ProductOfSubPartsCalculationPart","mPart1":{"~class":"NumberCalculationPart","mNumber":2},"mPart2":{"~class":"NumberCalculationPart","mNumber":3.5}}]}}}
    evidence={"status":"DAMAGE_CALCULATION_HIGH_CONFIDENCE","evidence":{"source":"MANUAL_DERIVATION"},"components":[{"component_id":"QDamage","calculation_key":"QDamage","damage_type":"MAGIC","activation_condition_status":"NOT_REQUIRED"}]}
    manual=resolve_damage_components(fixture,evidence,{"spell_rank":2,"max_rank":5})[0]
    if abs((manual.get("raw_damage") or 0)-57.0)>1e-12: failures.append(("MANUAL_DERIVATION","EXPECTED_50_PLUS_2_TIMES_3_5"))
    return {"probes":probes,"manual_expected":57.0,"manual_result":manual.get("raw_damage"),"failures":failures}


def main():
    result=run_representative_checks(); print(f"Representative probes: {len(result['probes'])}"); print(f"Manual expected/result: {result['manual_expected']} / {result['manual_result']}"); print(f"Failures: {result['failures']}")
    ok=not result["failures"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}"); return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
