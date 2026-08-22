from knowledge.champion_spell_value_resolver import PINNED_RANK_0_TO_6, PINNED_RANK_1_TO_6, VALUE_RESOLVED, resolve_rank_value

CAST_STATS_VERSION="champion_spell_cast_stats_phase2g_v1"
CAST_VALUE_RESOLVED="CAST_VALUE_RESOLVED"
RESOURCE_TYPE_UNRESOLVED="RESOURCE_TYPE_UNRESOLVED"


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


def resolve_cast_stats(source_spell,rank,max_rank,ability_haste=0,resource_type=None):
    raw=(source_spell.get("raw_spell_object") or {}).get("mSpell") or {}
    cooldown=_ranked(raw,("cooldownTime","Cooldown"),rank,max_rank,PINNED_RANK_0_TO_6)
    adjusted=None
    if cooldown.get("status")==VALUE_RESOLVED and isinstance(ability_haste,(int,float)) and not isinstance(ability_haste,bool) and ability_haste>=0:
        adjusted=cooldown["value"]*100/(100+ability_haste)
    cost=_ranked(raw,("mana","manaValues"),rank,max_rank,PINNED_RANK_1_TO_6)
    resource_status=CAST_VALUE_RESOLVED if cost.get("status")==VALUE_RESOLVED and resource_type else RESOURCE_TYPE_UNRESOLVED
    cast_range=_ranked(raw,("castRange","castRangeValues"),rank,max_rank,PINNED_RANK_0_TO_6)
    return {"version":CAST_STATS_VERSION,"cooldown":cooldown,"base_cooldown":cooldown.get("value"),"adjusted_cooldown":adjusted,"ability_haste":ability_haste,"resource_cost":cost,"resource_type":resource_type,"resource_cost_status":resource_status,"cast_range":cast_range,"provenance":{"source_version":source_spell.get("champion_spell_source_version"),"source_commit":source_spell.get("source_commit"),"source_path":source_spell.get("object_path")}}
