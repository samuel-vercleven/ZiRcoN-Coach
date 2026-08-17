from analysis.itemization_analyzer import (
    ItemCatalog,
    _summarize_destroyed_audit,
    _summarize_intermediate_contradictions,
    reconstruct_item_timeline,
)


RAW_ITEMS = {
    "1001": {
        "name": "Boots",
        "gold": {"total": 300, "base": 300, "purchasable": True},
        "tags": ["Boots"],
        "into": ["3001"],
    },
    "1029": {
        "name": "Cloth Armor",
        "gold": {"total": 300, "base": 300, "purchasable": True},
        "tags": ["Armor"],
        "into": ["3047"],
    },
    "1036": {
        "name": "Long Sword",
        "gold": {"total": 350, "base": 350, "purchasable": True},
        "tags": ["Damage"],
        "into": ["3000"],
    },
    "1042": {
        "name": "Dagger",
        "gold": {"total": 250, "base": 250, "purchasable": True},
        "tags": ["AttackSpeed"],
        "into": ["3000"],
    },
    "2003": {
        "name": "Health Potion",
        "gold": {"total": 50, "base": 50, "purchasable": True},
        "tags": ["Consumable"],
        "consumed": True,
        "stacks": 5,
    },
    "2140": {
        "name": "Elixir",
        "gold": {"total": 500, "base": 500, "purchasable": True},
        "tags": ["Consumable"],
        "consumed": True,
        "consumeOnFull": True,
    },
    "2055": {
        "name": "Control Ward",
        "gold": {"total": 75, "base": 75, "purchasable": True},
        "tags": ["Consumable"],
        "consumed": True,
        "consumeOnFull": True,
        "stacks": 2,
    },
    "3000": {
        "name": "Synthetic Major",
        "gold": {"total": 1200, "base": 600, "purchasable": True},
        "tags": ["Damage"],
        "from": ["1036", "1042"],
    },
    "3001": {
        "name": "Synthetic Boots Upgrade",
        "gold": {"total": 900, "base": 600, "purchasable": True},
        "tags": ["Boots"],
        "from": ["1001"],
    },
    "3047": {
        "name": "Synthetic Steelcaps",
        "gold": {"total": 1000, "base": 400, "purchasable": True},
        "tags": ["Boots"],
        "from": ["1001", "1029"],
    },
    "4000": {
        "name": "Synthetic Charged Component",
        "gold": {"total": 900, "base": 550, "purchasable": True},
        "tags": ["Damage"],
        "from": ["1036"],
        "into": ["5000"],
    },
    "4001": {
        "name": "Synthetic Transformed Component",
        "gold": {"total": 900, "base": 550, "purchasable": False},
        "tags": ["Damage"],
        "from": ["1036"],
        "into": ["5000"],
    },
    "5000": {
        "name": "Synthetic Transformation Major",
        "gold": {"total": 1600, "base": 700, "purchasable": True},
        "tags": ["Damage"],
        "from": ["4000", "4001"],
    },
    "3340": {
        "name": "Warding Totem",
        "gold": {"total": 0, "base": 0, "purchasable": False},
        "tags": ["Trinket"],
    },
    "2422": {
        "name": "Slightly Magical Boots",
        "gold": {"total": 300, "base": 300, "purchasable": False},
        "tags": ["Boots"],
        "into": ["3001"],
    },
    "3364": {
        "name": "Oracle Lens",
        "gold": {"total": 0, "base": 0, "purchasable": False},
        "tags": ["Trinket"],
    },
    "1102": {
        "name": "Synthetic Jungle Pet",
        "gold": {"total": 450, "base": 450, "purchasable": True},
        "tags": ["Jungle"],
    },
}


def _event(timestamp, event_type, item_id=None, **raw):
    payload = {
        "timestamp": timestamp,
        "event_type": event_type,
        "type": event_type,
        "participant_id": 1,
        "item_id": item_id,
        "frame_index": timestamp // 60_000,
        "event_index": len(raw),
        "raw": {
            "timestamp": timestamp,
            "participantId": 1,
            "type": event_type,
        },
    }

    if item_id is not None:
        payload["raw"]["itemId"] = item_id

    payload["raw"].update(raw)
    return payload


def _meta(
    final_items=None,
    final_trinket=3340,
    champion="Synthetic",
    perk_selections=None,
    takedown_timestamps=None,
):
    return {
        "match_id": "SYNTHETIC",
        "game_creation": 1,
        "game_duration": 1800,
        "game_version": "synthetic",
        "champion": champion,
        "opponent_champion": "Opponent",
        "win": True,
        "my_participant_id": 1,
        "final_items": final_items or [],
        "final_trinket": final_trinket,
        "perk_selections": perk_selections or [],
        "takedown_timestamps": takedown_timestamps or [],
    }


def _final_ids(result):
    return sorted(result["final_state"]["slot_items"].elements())


def test_purchase():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[1036]),
        [_event(10_000, "ITEM_PURCHASED", 1036)],
        catalog,
    )
    assert _final_ids(result) == [1036]
    assert result["final_validation"]["status"] == "EXACT"


def test_sell():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[]),
        [
            _event(10_000, "ITEM_PURCHASED", 1036),
            _event(20_000, "ITEM_SOLD", 1036),
        ],
        catalog,
    )
    assert _final_ids(result) == []
    assert result["final_validation"]["status"] == "EXACT"


def test_undo_purchase():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[]),
        [
            _event(10_000, "ITEM_PURCHASED", 1036),
            _event(
                12_000,
                "ITEM_UNDO",
                beforeId=1036,
                afterId=0,
                goldGain=350,
            ),
        ],
        catalog,
    )
    assert _final_ids(result) == []
    assert result["final_validation"]["status"] == "EXACT"


def test_component_completion():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[3000]),
        [
            _event(10_000, "ITEM_PURCHASED", 1036),
            _event(20_000, "ITEM_PURCHASED", 1042),
            _event(30_000, "ITEM_DESTROYED", 1036),
            _event(30_000, "ITEM_DESTROYED", 1042),
            _event(30_000, "ITEM_PURCHASED", 3000),
        ],
        catalog,
    )
    assert _final_ids(result) == [3000]
    assert result["final_validation"]["status"] == "EXACT"


def test_special_jungle_trinket_consumable():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[], final_trinket=3364),
        [
            _event(10_000, "ITEM_PURCHASED", 1102),
            _event(15_000, "ITEM_DESTROYED", 1102),
            _event(20_000, "ITEM_PURCHASED", 2003),
            _event(25_000, "ITEM_DESTROYED", 2003),
            _event(30_000, "ITEM_PURCHASED", 3364),
            _event(40_000, "ITEM_DESTROYED", 3364),
        ],
        catalog,
    )
    assert _final_ids(result) == []
    assert result["final_state"]["trinket_id"] == 3364
    assert result["final_validation"]["status"] == "EXACT"


def test_consume_on_purchase_elixir():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[]),
        [
            _event(10_000, "ITEM_PURCHASED", 2140),
        ],
        catalog,
    )
    assert _final_ids(result) == []
    assert result["final_validation"]["status"] == "EXACT"


def test_magical_footwear_rune_grant():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(
            final_items=[2422],
            perk_selections=[
                {
                    "style": 8300,
                    "style_description": "subStyle",
                    "perk": 8304,
                    "var1": 9,
                    "var2": 4,
                    "var3": 5,
                }
            ],
            takedown_timestamps=[
                180_000,
                360_000,
                390_000,
                590_000,
            ],
        ),
        [],
        catalog,
    )
    validation = result["final_validation"]
    assert _final_ids(result) == []
    assert validation["status"] == "EXACT_WITH_EXPLAINED_GRANT"
    assert validation["explained_grants"][0]["source"] == "RUNE_GRANT"
    assert validation["explained_grants"][0]["purchase_event"] == "NONE"
    assert (
        validation["explained_grants"][0]["derived_status"]
        == "DERIVED_INFERRED"
    )


def test_missing_magical_boots_without_rune_stays_unexplained():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[2422]),
        [],
        catalog,
    )
    assert result["final_validation"]["status"] != "EXACT_WITH_EXPLAINED_GRANT"
    assert not result["final_validation"]["explained_grants"]


def _destroyed_classifications(result):
    return _summarize_destroyed_audit([result])["classification_counts"]


def test_undo_restores_consumed_components_for_later_sell():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[1001]),
        [
            _event(10_000, "ITEM_PURCHASED", 1001),
            _event(11_000, "ITEM_PURCHASED", 1029),
            _event(20_000, "ITEM_DESTROYED", 1001),
            _event(20_000, "ITEM_DESTROYED", 1029),
            _event(20_000, "ITEM_PURCHASED", 3047),
            _event(25_000, "ITEM_UNDO", beforeId=3047, afterId=0),
            _event(30_000, "ITEM_SOLD", 1029),
        ],
        catalog,
    )
    warning_codes = [
        warning["code"]
        for warning in result["invariant_warnings"]
    ]
    assert "SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD" not in warning_codes
    assert _final_ids(result) == [1001]
    assert result["final_validation"]["status"] == "EXACT"


def test_destroyed_audit_strong_temporary_requires_no_acquisition():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[]),
        [_event(10_000, "ITEM_DESTROYED", 1036)],
        catalog,
    )
    assert (
        _destroyed_classifications(result)[
            "CONFIRMED_OR_STRONG_TEMPORARY_STATE"
        ]
        == 1
    )


def test_destroyed_audit_final_inventory_is_not_temporary_proof():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[1036]),
        [
            _event(10_000, "ITEM_PURCHASED", 1036),
            _event(20_000, "ITEM_DESTROYED", 1036),
        ],
        catalog,
    )
    assert _destroyed_classifications(result)["UNRESOLVED"] == 1


def test_consumable_destroyed_not_held_is_riot_representation():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[]),
        [
            _event(10_000, "ITEM_PURCHASED", 2055),
            _event(20_000, "ITEM_DESTROYED", 2055),
        ],
        catalog,
    )
    classifications = _destroyed_classifications(result)
    assert (
        classifications[
            "CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION"
        ]
        == 1
    )
    assert classifications["UNRESOLVED"] == 0


def test_destroyed_audit_detects_missed_transformation():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[3001]),
        [
            _event(20_000, "ITEM_DESTROYED", 2422),
            _event(20_000, "ITEM_PURCHASED", 3001),
        ],
        catalog,
    )
    assert _destroyed_classifications(result)["MISSED_TRANSFORMATION"] == 1


def test_retained_missed_transformation_marks_unreliable_interval():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[5000]),
        [
            _event(10_000, "ITEM_PURCHASED", 4000),
            _event(20_000, "ITEM_DESTROYED", 4000),
            _event(30_000, "ITEM_DESTROYED", 4001),
            _event(30_000, "ITEM_PURCHASED", 5000),
        ],
        catalog,
    )
    audit = _summarize_destroyed_audit([result])
    assert audit["missed_transformation_root_cause_counts"][
        "REAL_MISSED_TRANSFORMATION"
    ] == 1
    assert result["inventory_reliability"]["interval_counts"][
        "UNRESOLVED_TRANSFORMATION"
    ] == 1


def test_component_contradiction_ignores_destroy_before_reacquisition():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[3000]),
        [
            _event(10_000, "ITEM_DESTROYED", 1036),
            _event(20_000, "ITEM_PURCHASED", 1036),
            _event(21_000, "ITEM_PURCHASED", 1042),
            _event(30_000, "ITEM_PURCHASED", 3000),
        ],
        catalog,
    )
    contradictions = _summarize_intermediate_contradictions([result])
    assert (
        contradictions["counts"][
            "component_consumed_after_ignored_destroy"
        ]
        == 0
    )


def test_destroyed_audit_detects_likely_real_removal():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[3000]),
        [
            _event(10_000, "ITEM_PURCHASED", 3000),
            _event(20_000, "ITEM_DESTROYED", 3000),
            _event(120_000, "ITEM_PURCHASED", 3000),
        ],
        catalog,
    )
    assert _destroyed_classifications(result)["LIKELY_REAL_REMOVAL"] == 1


def test_viego_destroyed_audit_does_not_use_champion_only():
    catalog = ItemCatalog.from_raw_items(RAW_ITEMS)
    result = reconstruct_item_timeline(
        _meta(final_items=[1036], champion="Viego"),
        [
            _event(10_000, "ITEM_PURCHASED", 1036),
            _event(20_000, "ITEM_DESTROYED", 1036),
        ],
        catalog,
    )
    assert (
        _destroyed_classifications(result)[
            "UNRESOLVED_TEMPORARY_POSSIBLE"
        ]
        == 1
    )
    assert result["inventory_reliability"]["interval_counts"][
        "AMBIGUOUS_TEMPORARY_STATE"
    ] == 1


def main():
    test_purchase()
    test_sell()
    test_undo_purchase()
    test_component_completion()
    test_special_jungle_trinket_consumable()
    test_consume_on_purchase_elixir()
    test_magical_footwear_rune_grant()
    test_missing_magical_boots_without_rune_stays_unexplained()
    test_undo_restores_consumed_components_for_later_sell()
    test_destroyed_audit_strong_temporary_requires_no_acquisition()
    test_destroyed_audit_final_inventory_is_not_temporary_proof()
    test_consumable_destroyed_not_held_is_riot_representation()
    test_destroyed_audit_detects_missed_transformation()
    test_retained_missed_transformation_marks_unreliable_interval()
    test_component_contradiction_ignores_destroy_before_reacquisition()
    test_destroyed_audit_detects_likely_real_removal()
    test_viego_destroyed_audit_does_not_use_champion_only()
    print("Synthetic itemization checks passed.")


if __name__ == "__main__":
    main()
