"""Adapter from a caller-selected source calculation to combat snapshots."""
from knowledge.champion_spell_formula_evaluator import evaluate_calculation

FORMULA_RUNTIME_VERSION="champion_spell_formula_runtime_phase2g_v1"


def evaluate_spell_calculation(source_spell,calculation_key,*,spell_rank,max_rank,source_snapshot,target_snapshot=None,extra_context=None):
    context={"spell_rank":spell_rank,"max_rank":max_rank,"source_snapshot":source_snapshot,"target_snapshot":target_snapshot,**(extra_context or {})}
    result=evaluate_calculation(source_spell,calculation_key,context)
    return {"runtime_version":FORMULA_RUNTIME_VERSION,"champion_id":source_spell.get("champion_id"),"slot":source_spell.get("slot"),"spell_rank":spell_rank,"calculation_key":calculation_key,"source_spell":source_spell,"source_snapshot":source_snapshot,"target_snapshot":target_snapshot,"result":result,"dependencies":result.dependencies,"required_context":result.required_context,"provenance":{"source_version":source_spell.get("champion_spell_source_version"),"source_commit":source_spell.get("source_commit"),"source_path":source_spell.get("object_path")}}
