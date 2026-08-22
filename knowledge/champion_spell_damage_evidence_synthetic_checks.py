from knowledge.champion_spell_damage_evidence import *
def main():
    source={"raw_calculation_names":["QDamage"]}; semantic={"effects":[{"effect_type":"MAGIC_DAMAGE"}]}
    assert classify_damage_evidence(source,semantic)["components"][0]["damage_type"]=="MAGIC"
    assert classify_damage_evidence({"raw_calculation_names":["Shield"]},semantic)["status"]==NOT_IDENTIFIED_AS_DAMAGE
    assert classify_damage_evidence(source,{"effects":[]})["status"]==DAMAGE_EVIDENCE_INSUFFICIENT
    print("Spell damage evidence synthetic checks: PASS (3/3)")
if __name__=="__main__": main()
