"""Thin adapter over frozen Phase 2E; no resistance formula duplication."""
from knowledge.combat_resistance_rules import COMBAT_RESISTANCE_VERSION, apply_resistance_to_damage, resolve_armor, resolve_magic_resistance

MITIGATION_VERSION="spell_damage_mitigation_phase2g_v1"
def mitigate_component(component,attacker_snapshot,target_snapshot):
    if component.get("status")!="RAW_DAMAGE_RESOLVED": return {"status":"DAMAGE_UNRESOLVED","component":component}
    raw=component["raw_damage"]; kind=component["damage_type"]; attacker=attacker_snapshot["stats"]; target=target_snapshot["stats"]
    resistance=None
    if kind=="TRUE": resolution=apply_resistance_to_damage(raw,"TRUE")
    elif kind=="PHYSICAL":
        resistance=resolve_armor(target["armor"],base_armor=target.get("armor_native"),percentage_penetrations=(attacker.get("armor_penetration_percent",0),),flat_penetration=attacker.get("armor_penetration_flat",0),lethality=attacker.get("lethality",0)); resolution=apply_resistance_to_damage(raw,"PHYSICAL",effective_resistance=resistance.effective_resistance)
    elif kind=="MAGIC":
        resistance=resolve_magic_resistance(target["magic_resistance"],percentage_penetrations=(attacker.get("magic_penetration_percent",0),),flat_penetration=attacker.get("magic_penetration_flat",0)); resolution=apply_resistance_to_damage(raw,"MAGIC",effective_resistance=resistance.effective_resistance)
    else: return {"status":"DAMAGE_TYPE_UNRESOLVED","component":component}
    return {"status":"POST_MITIGATION_RESOLVED","component":component,"raw_damage":raw,"damage_type":kind,"original_resistance":None if resistance is None else resistance.original_resistance,"effective_resistance":resolution.effective_resistance,"penetration_inputs":{"armor_percent":attacker.get("armor_penetration_percent",0),"armor_flat":attacker.get("armor_penetration_flat",0),"lethality":attacker.get("lethality",0),"magic_percent":attacker.get("magic_penetration_percent",0),"magic_flat":attacker.get("magic_penetration_flat",0)},"post_mitigation_damage":resolution.post_mitigation_damage,"resistance_multiplier":resolution.resistance_multiplier,"phase2e_version":COMBAT_RESISTANCE_VERSION}
