from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.combat_stat_snapshot_synthetic_checks import champion
from knowledge.spell_combat_runtime import (
    COMPOSABILITY_CALLER_ASSERTED,
    COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE,
    DAMAGE_UNRESOLVED,
    PROJECT_VALIDATED,
    TOTAL_DAMAGE_RESOLVED,
    resolve_spell_combat,
)


def _fixture():
    spell = {
        "champion_spell_source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "champion_id": "Test",
        "slot": "Q",
        "raw_data_values": [],
        "raw_calculation_names": ["QOutput"],
        "raw_m_spell_calculations": {"QOutput": {"~class": "NumberCalculationPart", "mNumber": 100}},
        "calculation_nodes": [],
    }
    semantic = {
        "raw_tooltip": "<magicDamage>{{ qoutput }}</magicDamage>",
        "effects": [{"effect_type": "MAGIC_DAMAGE"}],
    }
    return spell, semantic


def main():
    source = champion()
    target = champion()
    spell, semantic = _fixture()
    common = dict(source_level=1, target_level=1, spell_rank=1, max_rank=5)
    result = resolve_spell_combat(source, target, spell, semantic, **common)
    assert result["status"] == COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE and result["total_damage"] is None

    bare = resolve_spell_combat(source, target, spell, semantic, explicitly_composable=True, **common)
    assert bare["status"] == COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE
    assert bare["composability_decision"]["status"] == COMPOSABILITY_CALLER_ASSERTED

    caller_validated = {
        "status": "COMPOSABILITY_VALIDATED",
        "covered_component_ids": ["QOutput:MAGIC:0"],
        "reason": "caller assertion",
        "evidence": ["caller-only"],
        "provenance": {"origin": "CALLER_SUPPLIED", "source": "synthetic caller"},
    }
    caller = resolve_spell_combat(source, target, spell, semantic, composability_decision=caller_validated, **common)
    assert caller["status"] == COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE

    project_validated = {
        "status": "COMPOSABILITY_VALIDATED",
        "covered_component_ids": ["QOutput:MAGIC:0"],
        "reason": "single deterministic synthetic component",
        "evidence": ["fixture contains exactly one activated output"],
        "provenance": {"origin": PROJECT_VALIDATED, "source": "synthetic regression fixture"},
    }
    summed = resolve_spell_combat(source, target, spell, semantic, composability_decision=project_validated, **common)
    assert summed["status"] == TOTAL_DAMAGE_RESOLVED and summed["total_damage"] == 10000 / 132

    wrong_coverage = {**project_validated, "covered_component_ids": ["Other"]}
    withheld = resolve_spell_combat(source, target, spell, semantic, composability_decision=wrong_coverage, **common)
    assert withheld["status"] == COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE

    mixed_item = {
        1: {
            "item_id": 1,
            "name": "Structured AD, excluded lethality",
            "normalized_stats": [
                {"stat": "attack_damage", "value": 20, "source": "DDRAGON_STATS", "confidence": "STRUCTURED"},
                {"stat": "lethality", "value": 10, "source": "DDRAGON_DESCRIPTION_STATS", "confidence": "DESCRIPTION_EXPLICIT"},
            ],
        }
    }
    physical_semantic = {"raw_tooltip": "<physicalDamage>{{ qoutput }}</physicalDamage>", "effects": [{"effect_type": "PHYSICAL_DAMAGE"}]}
    physical = resolve_spell_combat(source, target, spell, physical_semantic, item_records=mixed_item, source_item_ids=(1,), **common)
    assert physical["raw_components"][0]["status"] == "RAW_DAMAGE_RESOLVED"
    assert physical["post_mitigation_components"][0]["status"] == "MITIGATION_INPUT_UNRESOLVED" and physical["status"] == DAMAGE_UNRESOLVED

    magic_with_unrelated_partial = resolve_spell_combat(source, target, spell, semantic, item_records=mixed_item, source_item_ids=(1,), **common)
    assert magic_with_unrelated_partial["post_mitigation_components"][0]["status"] == "POST_MITIGATION_RESOLVED"
    print("Spell combat runtime synthetic checks: PASS (11/11)")


if __name__ == "__main__":
    main()
