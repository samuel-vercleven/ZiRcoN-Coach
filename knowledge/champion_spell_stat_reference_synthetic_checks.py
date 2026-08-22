from knowledge.champion_spell_stat_reference import *

def main():
    assert resolve_stat_reference(2)["status"] == STAT_REFERENCE_UNRESOLVED
    assert resolve_stat_reference(2, mappings={2:"ABILITY_POWER"})["status"] == STAT_OWNER_UNRESOLVED
    result = resolve_stat_reference(2, owner="CASTER", mappings={2:"ABILITY_POWER"})
    assert result["status"] == STAT_REFERENCE_RESOLVED and result["stat"] == "ABILITY_POWER"
    print("Spell stat reference synthetic checks: PASS (3/3)")

if __name__ == "__main__": main()
