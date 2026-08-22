from knowledge.champion_spell_cast_stats import ADJUSTED_COOLDOWN_RESOLVED, ADJUSTED_COOLDOWN_UNRESOLVED, CAST_VALUE_RESOLVED, RESOURCE_TYPE_UNRESOLVED, resolve_cast_stats
from knowledge.combat_stat_snapshot import STATIC_STAT_PARTIAL


def main():
    spell={"raw_spell_object":{"mSpell":{"cooldownTime":[0,10,9,8,7,6,5],"mana":[40,45,50,55,60,65],"castRange":[0,600,600,600,600,600,600]}},"source_commit":"fixture"}
    result=resolve_cast_stats(spell,2,5,ability_haste=100,resource_type="Mana")
    assert result["base_cooldown"]==9 and result["adjusted_cooldown"]==4.5
    assert result["adjusted_cooldown_status"]==ADJUSTED_COOLDOWN_RESOLVED
    assert result["resource_cost"]["value"]==45 and result["resource_cost_status"]==CAST_VALUE_RESOLVED
    assert resolve_cast_stats(spell,1,5)["resource_cost_status"]==RESOURCE_TYPE_UNRESOLVED
    incomplete=resolve_cast_stats(spell,1,5,ability_haste=None,ability_haste_resolution={"status":STATIC_STAT_PARTIAL})
    assert incomplete["adjusted_cooldown"] is None and incomplete["adjusted_cooldown_status"]==ADJUSTED_COOLDOWN_UNRESOLVED
    assert incomplete["base_cooldown"]==10
    print("Spell cast stats synthetic checks: PASS (5/5)")


if __name__=="__main__": main()
