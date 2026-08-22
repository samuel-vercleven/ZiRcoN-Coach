"""Separate conservative evidence classifier; arithmetic is not evaluated here."""
DAMAGE_EVIDENCE_VERSION="champion_spell_damage_evidence_phase2g_v1"
DAMAGE_CALCULATION_HIGH_CONFIDENCE="DAMAGE_CALCULATION_HIGH_CONFIDENCE"
DAMAGE_CALCULATION_MULTIPLE_CANDIDATES="DAMAGE_CALCULATION_MULTIPLE_CANDIDATES"
DAMAGE_TYPE_PHYSICAL="PHYSICAL"; DAMAGE_TYPE_MAGIC="MAGIC"; DAMAGE_TYPE_TRUE="TRUE"
DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL="DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL"
DAMAGE_TYPE_UNRESOLVED="DAMAGE_TYPE_UNRESOLVED"
NOT_IDENTIFIED_AS_DAMAGE="NOT_IDENTIFIED_AS_DAMAGE"
DAMAGE_EVIDENCE_INSUFFICIENT="DAMAGE_EVIDENCE_INSUFFICIENT"

TYPE_TAGS={"PHYSICAL_DAMAGE":DAMAGE_TYPE_PHYSICAL,"MAGIC_DAMAGE":DAMAGE_TYPE_MAGIC,"TRUE_DAMAGE":DAMAGE_TYPE_TRUE}
CONDITIONAL_CLASSES={"GameCalculationConditional","BuffCounterByCoefficientCalculationPart","BuffCounterByNamedDataValueCalculationPart","PercentageOfBuffNameElapsed","HasBuffCastRequirement"}
def classify_damage_evidence(source_spell, champion_knowledge_spell):
    effects={row.get("effect_type") for row in (champion_knowledge_spell or {}).get("effects",[])}
    types=sorted({TYPE_TAGS[tag] for tag in effects if tag in TYPE_TAGS})
    keys=list(source_spell.get("raw_calculation_names",[]))
    candidates=[key for key in keys if "damage" in key.casefold()]
    if not candidates or not types:
        return {"status":NOT_IDENTIFIED_AS_DAMAGE if not candidates else DAMAGE_EVIDENCE_INSUFFICIENT,"components":[],"evidence":{"calculation_keys":candidates,"semantic_effects":sorted(effects)}}
    damage_type=types[0] if len(types)==1 else DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL
    status=DAMAGE_CALCULATION_HIGH_CONFIDENCE if len(candidates)==1 and len(types)==1 else DAMAGE_CALCULATION_MULTIPLE_CANDIDATES
    components=[]
    for key in candidates:
        prefix=f"mSpellCalculations/{key}"
        conditional=sorted({node.get("calculation_class") for node in source_spell.get("calculation_nodes",[]) if node.get("graph_path","").startswith(prefix) and node.get("calculation_class") in CONDITIONAL_CLASSES})
        components.append({"component_id":key,"calculation_key":key,"damage_type":damage_type,"activation_condition_status":"UNRESOLVED_UNLESS_EXPLICIT" if conditional else "NOT_REQUIRED","required_state":conditional})
    return {"status":status,"components":components,"evidence":{"semantic_effects":sorted(effects),"key_name_evidence":candidates,"source":"PINNED_KEY_PLUS_FROZEN_CHAMPION_KNOWLEDGE"}}
