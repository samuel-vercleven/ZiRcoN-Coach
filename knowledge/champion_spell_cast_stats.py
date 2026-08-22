from knowledge.champion_spell_value_resolver import PINNED_RANK_0_TO_6, PINNED_RANK_1_TO_6, VALUE_RESOLVED, resolve_rank_value
from knowledge.combat_stat_snapshot import STATIC_STAT_RESOLVED

CAST_STATS_VERSION="champion_spell_cast_stats_phase2g_v2"
CAST_VALUE_RESOLVED="CAST_VALUE_RESOLVED"
RESOURCE_TYPE_UNRESOLVED="RESOURCE_TYPE_UNRESOLVED"
ADJUSTED_COOLDOWN_RESOLVED="ADJUSTED_COOLDOWN_RESOLVED"
ADJUSTED_COOLDOWN_UNRESOLVED="ADJUSTED_COOLDOWN_UNRESOLVED"


def _ranked(raw,fields,rank,max_rank,indexing_contract):
    for field in fields:
        if field not in raw: continue
        value=raw[field]
        if isinstance(value,dict): value=value.get("values")
        if isinstance(value,(int,float)) and not isinstance(value,bool):
            return {"status":VALUE_RESOLVED,"value":value,"source_field":field}
        result=resolve_rank_value(value,rank,max_rank,indexing_contract)
        return {**result,"source_field":field}
    return resolve_rank_value(None,rank,max_rank,indexing_contract)


def resolve_cast_stats(
    source_spell,
    rank,
    max_rank,
    ability_haste=0,
    resource_type=None,
    ability_haste_resolution=None,
):
    raw=(source_spell.get("raw_spell_object") or {}).get("mSpell") or {}
    cooldown=_ranked(raw,("cooldownTime","Cooldown"),rank,max_rank,PINNED_RANK_0_TO_6)
    adjusted=None
    haste_is_exact = (
        isinstance(ability_haste, (int, float))
        and not isinstance(ability_haste, bool)
        and ability_haste >= 0
        and (
            ability_haste_resolution is None
            or ability_haste_resolution.get("status") == STATIC_STAT_RESOLVED
        )
    )
    if cooldown.get("status")==VALUE_RESOLVED and haste_is_exact:
        adjusted=cooldown["value"]*100/(100+ability_haste)
    adjusted_status = ADJUSTED_COOLDOWN_RESOLVED if adjusted is not None else ADJUSTED_COOLDOWN_UNRESOLVED
    adjusted_reasons = []
    if cooldown.get("status") != VALUE_RESOLVED:
        adjusted_reasons.append(cooldown.get("status"))
    if not haste_is_exact:
        adjusted_reasons.append(
            (ability_haste_resolution or {}).get("status", "ABILITY_HASTE_NOT_EXACT")
        )
    cost=_ranked(raw,("mana","manaValues"),rank,max_rank,PINNED_RANK_1_TO_6)
    resource_status=CAST_VALUE_RESOLVED if cost.get("status")==VALUE_RESOLVED and resource_type else RESOURCE_TYPE_UNRESOLVED
    cast_range=_ranked(raw,("castRange","castRangeValues"),rank,max_rank,PINNED_RANK_0_TO_6)
    return {"version":CAST_STATS_VERSION,"cooldown":cooldown,"base_cooldown":cooldown.get("value"),"adjusted_cooldown":adjusted,"adjusted_cooldown_status":adjusted_status,"adjusted_cooldown_unresolved_reasons":adjusted_reasons,"ability_haste":ability_haste,"ability_haste_resolution":ability_haste_resolution,"resource_cost":cost,"resource_type":resource_type,"resource_cost_status":resource_status,"cast_range":cast_range,"provenance":{"source_version":source_spell.get("champion_spell_source_version"),"source_commit":source_spell.get("source_commit"),"source_path":source_spell.get("object_path")}}
