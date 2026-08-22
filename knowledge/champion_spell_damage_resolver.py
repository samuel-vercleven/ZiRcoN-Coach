from math import isfinite
from knowledge.champion_spell_formula_evaluator import evaluate_calculation
from knowledge.combat_formula_types import RESOLVED
from knowledge.champion_spell_damage_evidence import DAMAGE_CALCULATION_HIGH_CONFIDENCE

DAMAGE_RESOLVER_VERSION="champion_spell_damage_resolver_phase2g_v1"
RAW_DAMAGE_RESOLVED="RAW_DAMAGE_RESOLVED"; DAMAGE_UNRESOLVED="DAMAGE_UNRESOLVED"
def resolve_damage_components(source_spell,evidence,context):
    results=[]
    for component in evidence.get("components",[]):
        formula=evaluate_calculation(source_spell,component["calculation_key"],context)
        activation=component.get("activation_condition_status")
        numeric=isinstance(formula.value,(int,float)) and not isinstance(formula.value,bool) and isfinite(formula.value) and formula.value>=0
        status=RAW_DAMAGE_RESOLVED if formula.status==RESOLVED and numeric and evidence.get("status")==DAMAGE_CALCULATION_HIGH_CONFIDENCE and activation in {"SATISFIED","NOT_REQUIRED"} else DAMAGE_UNRESOLVED
        warnings=[] if numeric or formula.value is None else ["NON_NEGATIVE_FINITE_DAMAGE_REQUIRED"]
        results.append({"champion_id":source_spell.get("champion_id"),"slot":source_spell.get("slot"),"spell_rank":context.get("spell_rank"),**component,"status":status,"raw_damage":formula.value if status==RAW_DAMAGE_RESOLVED else None,"formula_resolution_status":formula.status,"formula_result":formula,"semantic_evidence":evidence.get("evidence",{}),"warnings":warnings,"provenance":{"resolver_version":DAMAGE_RESOLVER_VERSION,"source_version":source_spell.get("champion_spell_source_version"),"source_commit":source_spell.get("source_commit"),"source_path":source_spell.get("object_path")}})
    return results
