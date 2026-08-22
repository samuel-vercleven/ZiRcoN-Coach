from knowledge.combat_resistance_rules import combine_percentages
from knowledge.combat_stat_snapshot import STATIC_STAT_PARTIAL, STATIC_STAT_RESOLVED
from knowledge.spell_damage_mitigation import MITIGATION_INPUT_UNRESOLVED, mitigate_component


def _resolution(status, value=None):
    return {"status": status, "exact_value": value if status == STATIC_STAT_RESOLVED else None}


def build_audit():
    attacker = {
        "stats": {
            "armor_penetration_percent": combine_percentages((0.30, 0.20)),
            "armor_penetration_percent_sources": [
                {"item_id": "SOURCE_A", "value": 0.30, "source": "AUDIT_FIXTURE"},
                {"item_id": "SOURCE_B", "value": 0.20, "source": "AUDIT_FIXTURE"},
            ],
            "armor_penetration_flat": 0.0,
            "lethality": 0.0,
            "magic_penetration_percent": 0.0,
            "magic_penetration_percent_sources": [],
            "magic_penetration_flat": 0.0,
        },
        "stat_resolution": {
            "armor_penetration_percent": _resolution(STATIC_STAT_RESOLVED, 0.44),
            "armor_penetration_flat": _resolution(STATIC_STAT_RESOLVED, 0.0),
            "lethality": _resolution(STATIC_STAT_RESOLVED, 0.0),
            "magic_penetration_percent": _resolution(STATIC_STAT_RESOLVED, 0.0),
            "magic_penetration_flat": _resolution(STATIC_STAT_RESOLVED, 0.0),
        },
    }
    target = {
        "stats": {"armor": 100.0, "armor_native": 100.0, "magic_resistance": 40.0},
        "stat_resolution": {
            "armor": _resolution(STATIC_STAT_RESOLVED, 100.0),
            "armor_native": _resolution(STATIC_STAT_RESOLVED, 100.0),
            "magic_resistance": _resolution(STATIC_STAT_RESOLVED, 40.0),
        },
    }
    physical = {"status": "RAW_DAMAGE_RESOLVED", "raw_damage": 100.0, "damage_type": "PHYSICAL"}
    magic = {"status": "RAW_DAMAGE_RESOLVED", "raw_damage": 100.0, "damage_type": "MAGIC"}
    regression = mitigate_component(physical, attacker, target)

    unknown_lethality = {**attacker, "stats": {**attacker["stats"], "lethality": None}, "stat_resolution": {**attacker["stat_resolution"], "lethality": _resolution(STATIC_STAT_PARTIAL)}}
    unknown_magic_pen = {**attacker, "stats": {**attacker["stats"], "magic_penetration_percent": None}, "stat_resolution": {**attacker["stat_resolution"], "magic_penetration_percent": _resolution(STATIC_STAT_PARTIAL)}}
    withheld_physical = mitigate_component(physical, unknown_lethality, target)
    withheld_magic = mitigate_component(magic, unknown_magic_pen, target)
    return {
        "sources": regression.get("penetration_inputs", {}).get("percentage_sources"),
        "combined": regression.get("penetration_inputs", {}).get("percentage_combined"),
        "effective_resistance": regression.get("effective_resistance"),
        "status": regression.get("status"),
        "unresolved_penetration_inputs": {
            "physical": withheld_physical.get("unresolved_inputs", []),
            "magic": withheld_magic.get("unresolved_inputs", []),
        },
        "withheld": {
            "physical": withheld_physical.get("status"),
            "magic": withheld_magic.get("status"),
        },
    }


def main():
    audit = build_audit()
    print(f"Percentage sources passed to Phase 2E: {audit['sources']}")
    print(f"Combined percentage: {audit['combined']}")
    print(f"Effective resistance: {audit['effective_resistance']}")
    print(f"Unresolved penetration inputs: {audit['unresolved_penetration_inputs']}")
    print(f"Components withheld for incomplete penetration: {audit['withheld']}")
    ok = (
        audit["status"] == "POST_MITIGATION_RESOLVED"
        and tuple(audit["sources"]) == (0.30, 0.20)
        and abs(audit["combined"] - 0.44) < 1e-12
        and abs(audit["effective_resistance"] - 56.0) < 1e-12
        and audit["withheld"] == {"physical": MITIGATION_INPUT_UNRESOLVED, "magic": MITIGATION_INPUT_UNRESOLVED}
    )
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
