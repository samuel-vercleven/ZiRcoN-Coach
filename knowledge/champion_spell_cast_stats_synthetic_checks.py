from knowledge.champion_spell_cast_stats import CAST_VALUE_RESOLVED, RESOURCE_TYPE_UNRESOLVED, resolve_cast_stats


def main():
    spell={"raw_spell_object":{"mSpell":{"cooldownTime":[0,10,9,8,7,6,5],"mana":[40,45,50,55,60,65],"castRange":[0,600,600,600,600,600,600]}},"source_commit":"fixture"}
    result=resolve_cast_stats(spell,2,5,ability_haste=100,resource_type="Mana")
    assert result["base_cooldown"]==9 and result["adjusted_cooldown"]==4.5
    assert result["resource_cost"]["value"]==45 and result["resource_cost_status"]==CAST_VALUE_RESOLVED
    assert resolve_cast_stats(spell,1,5)["resource_cost_status"]==RESOURCE_TYPE_UNRESOLVED
    print("Spell cast stats synthetic checks: PASS (3/3)")


if __name__=="__main__": main()
