"""Conservative single-cast orchestration across Phase 2G layers."""
from knowledge.champion_spell_damage_evidence import classify_damage_evidence
from knowledge.champion_spell_damage_resolver import resolve_damage_components
from knowledge.combat_stat_snapshot import build_combat_snapshot
from knowledge.spell_damage_mitigation import mitigate_component

SPELL_COMBAT_RUNTIME_VERSION="spell_combat_runtime_phase2g_v1"
TOTAL_DAMAGE_RESOLVED="TOTAL_DAMAGE_RESOLVED"
COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE="COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE"
PARTIAL_DAMAGE_ONLY="PARTIAL_DAMAGE_ONLY"
DAMAGE_UNRESOLVED="DAMAGE_UNRESOLVED"


def resolve_spell_combat(source_champion,target_champion,source_spell,semantic_spell,*,source_level,target_level,spell_rank,max_rank,item_records=None,source_item_ids=(),target_item_ids=(),attack_speed_records=None,source_current_health=None,target_current_health=None,calculation_keys=None,explicitly_composable=False,formula_context=None):
    ratios=attack_speed_records or {}
    source_snapshot=build_combat_snapshot(source_champion,source_level,item_records,source_item_ids,ratios.get(source_champion.get("champion_id")),source_current_health)
    target_snapshot=build_combat_snapshot(target_champion,target_level,item_records,target_item_ids,ratios.get(target_champion.get("champion_id")),target_current_health)
    evidence=classify_damage_evidence(source_spell,semantic_spell)
    if calculation_keys is not None:
        selected=set(calculation_keys); evidence={**evidence,"components":[row for row in evidence.get("components",[]) if row["calculation_key"] in selected]}
    context={"spell_rank":spell_rank,"max_rank":max_rank,"source_snapshot":source_snapshot,"target_snapshot":target_snapshot,**(formula_context or {})}
    raw=resolve_damage_components(source_spell,evidence,context)
    mitigated=[mitigate_component(row,source_snapshot,target_snapshot) for row in raw]
    resolved=[row for row in mitigated if row["status"]=="POST_MITIGATION_RESOLVED"]
    if not resolved: status=DAMAGE_UNRESOLVED; total=None
    elif len(resolved)!=len(mitigated): status=PARTIAL_DAMAGE_ONLY; total=None
    elif explicitly_composable: status=TOTAL_DAMAGE_RESOLVED; total=sum(row["post_mitigation_damage"] for row in resolved)
    else: status=COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE; total=None
    return {"runtime_version":SPELL_COMBAT_RUNTIME_VERSION,"status":status,"source_snapshot":source_snapshot,"target_snapshot":target_snapshot,"source_spell":source_spell,"damage_evidence":evidence,"raw_components":raw,"post_mitigation_components":mitigated,"total_damage":total,"explicitly_composable":explicitly_composable}
