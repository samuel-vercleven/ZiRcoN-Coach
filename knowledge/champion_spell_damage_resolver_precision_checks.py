from knowledge.champion_spell_damage_resolver import RAW_DAMAGE_RESOLVED, resolve_damage_components
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION


def main():
    spell={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"champion_id":"PinnedShape","slot":"Q","raw_data_values":[{"name":"Damage","values":[0,10.25,20.5,30.75,41,51.25,61.5]}],"raw_m_spell_calculations":{"QDamage":{"~class":"GameCalculation","mFormulaParts":[{"~class":"NamedDataValueCalculationPart","mDataValue":"Damage"},{"~class":"NumberCalculationPart","mNumber":0.125}]}}}
    evidence={"status":"DAMAGE_CALCULATION_HIGH_CONFIDENCE","evidence":{"source":"fixture"},"components":[{"component_id":"QDamage","calculation_key":"QDamage","damage_type":"MAGIC","evidence_tier":"COMPONENT_LOCAL_STRUCTURAL_LINKAGE","activation_condition_status":"NOT_REQUIRED"}]}
    result=resolve_damage_components(spell,evidence,{"spell_rank":2,"max_rank":5})[0]
    assert result["status"]==RAW_DAMAGE_RESOLVED and abs(result["raw_damage"]-20.625)<1e-12
    assert result["semantic_evidence"]["source"]=="fixture"
    print("Spell damage resolver precision checks: PASS (2/2)")


if __name__=="__main__": main()
