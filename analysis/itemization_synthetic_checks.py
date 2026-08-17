from analysis.itemization_analyzer import (
    ItemCatalog,
    reconstruct_item_timeline,
)


RAW_ITEMS = {
    "1001": {
        "name": "Boots",
        "gold": {"total": 300, "base": 300, "purchasable": True},
        "tags": ["Boots"],
        "into": ["3001"],
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
    "3340": {
        "name": "Warding Totem",
        "gold": {"total": 0, "base": 0, "purchasable": False},
        "tags": ["Trinket"],
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


def _meta(final_items=None, final_trinket=3340, champion="Synthetic"):
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


def main():
    test_purchase()
    test_sell()
    test_undo_purchase()
    test_component_completion()
    test_special_jungle_trinket_consumable()
    test_consume_on_purchase_elixir()
    print("Synthetic itemization checks passed.")


if __name__ == "__main__":
    main()
