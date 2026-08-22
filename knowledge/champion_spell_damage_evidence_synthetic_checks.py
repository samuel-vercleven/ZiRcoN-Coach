from knowledge.champion_spell_damage_evidence import *


def main():
    source = {"raw_calculation_names": ["QDamage"], "calculation_nodes": []}
    linked = {"raw_tooltip": "Inflige <magicDamage>{{ qdamage }} pts</magicDamage>.", "effects": [{"effect_type": "MAGIC_DAMAGE"}]}
    result = classify_damage_evidence(source, linked)
    assert result["status"] == DAMAGE_CALCULATION_HIGH_CONFIDENCE
    assert result["components"][0]["damage_type"] == DAMAGE_TYPE_MAGIC
    assert result["components"][0]["evidence_tier"] == COMPONENT_LOCAL_STRUCTURAL_LINKAGE

    key_only = classify_damage_evidence(source, {"effects": [{"effect_type": "MAGIC_DAMAGE"}]})
    assert key_only["status"] == DAMAGE_EVIDENCE_INSUFFICIENT
    assert key_only["components"][0]["evidence_tier"] == KEY_NAME_ONLY

    assert classify_damage_evidence({"raw_calculation_names": ["Shield"]}, {"effects": []})["status"] == NOT_IDENTIFIED_AS_DAMAGE

    mixed = classify_damage_evidence(
        {"raw_calculation_names": ["TotalDamage"], "calculation_nodes": []},
        {"raw_tooltip": "<magicDamage>{{ totaldamage }}</magicDamage><trueDamage>{{ totaldamage }}</trueDamage>", "effects": []},
    )
    assert mixed["status"] == DAMAGE_CALCULATION_MULTIPLE_CANDIDATES and len(mixed["components"]) == 2
    print("Spell damage evidence synthetic checks: PASS (7/7)")


if __name__ == "__main__":
    main()
