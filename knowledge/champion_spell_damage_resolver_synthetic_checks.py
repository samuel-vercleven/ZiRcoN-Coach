from knowledge.champion_spell_damage_resolver import *
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
def main():
    spell={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"raw_data_values":[],"raw_m_spell_calculations":{"QDamage":{"~class":"NumberCalculationPart","mNumber":100}}}
    ev={"status":"DAMAGE_CALCULATION_HIGH_CONFIDENCE","components":[{"calculation_key":"QDamage","damage_type":"MAGIC","evidence_tier":"COMPONENT_LOCAL_STRUCTURAL_LINKAGE","activation_condition_status":"NOT_REQUIRED"}]}
    assert resolve_damage_components(spell,ev,{})[0]["raw_damage"]==100
    ev["components"][0]["activation_condition_status"]="UNRESOLVED"
    assert resolve_damage_components(spell,ev,{})[0]["status"]==DAMAGE_UNRESOLVED
    ev["components"][0].update({"activation_condition_status":"NOT_REQUIRED","evidence_tier":"KEY_NAME_ONLY"})
    assert resolve_damage_components(spell,ev,{})[0]["status"]==DAMAGE_UNRESOLVED
    print("Spell damage resolver synthetic checks: PASS (3/3)")
if __name__=="__main__": main()
