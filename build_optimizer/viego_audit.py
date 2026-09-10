"""Read-only provenance audit for Viego timeline observations.

The payload has no documented possession-state field.  The product therefore
uses a narrow, reproducible contract: PERMANENT_SHOP_INVENTORY is reconstructed
only from the player's ITEM_PURCHASED/ITEM_SOLD/ITEM_UNDO prefix, while every
other Viego item event belongs to unobserved possession/runtime state and is
excluded.  This is not a reconstruction of the possessed champion's items.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sqlite3

from analysis.itemization_analyzer import ITEM_EVENT_TYPES
from app.paths import DEFAULT_DB_PATH
from services.game_context import load_game_context
from services.local_data import LocalDataService
from services.runtime_settings import RuntimeSettingsService


ROOT = Path(__file__).resolve().parents[1]
SHOP_EVENT_TYPES = frozenset({"ITEM_PURCHASED", "ITEM_SOLD", "ITEM_UNDO"})


def _sources():
    local = LocalDataService(DEFAULT_DB_PATH, settings=RuntimeSettingsService())
    player = local.player()
    if not player.puuid:
        raise RuntimeError("LOCAL_PLAYER_UNAVAILABLE")
    with sqlite3.connect(DEFAULT_DB_PATH) as connection:
        rows = connection.execute(
            """SELECT m.match_id, m.game_creation
               FROM matches m JOIN participants p ON p.match_id=m.match_id
               WHERE p.puuid=? AND p.champion_name='Viego' AND m.queue_id=420
               ORDER BY m.game_creation, m.match_id""",
            (player.puuid,),
        ).fetchall()
    for match_id, game_creation in rows:
        yield match_id, game_creation, load_game_context(DEFAULT_DB_PATH, match_id, player.puuid)


def run():
    """Return reproducible observations, never a possession inference."""
    counts = Counter()
    own_item_types = Counter()
    event_keys: set[str] = set()
    frame_keys: set[str] = set()
    stat_keys: set[str] = set()
    examples = []
    non_shop_examples = []
    candidate_kills = []
    for match_id, creation, game in _sources():
        counts["viego_games_found"] += 1
        own_pid = game.player["participantId"]
        own_item_events = []
        for event in game.events:
            event_type = event.get("type")
            event_keys.update(event.keys())
            if event_type in ITEM_EVENT_TYPES:
                counts["all_item_events"] += 1
            if event_type in SHOP_EVENT_TYPES and event.get("participantId") == own_pid:
                counts["own_permanent_shop_events"] += 1
                own_item_events.append(event)
                if type(event.get("itemId")) is int and event["itemId"] > 0:
                    counts["own_shop_events_with_item_id"] += 1
                else:
                    counts["own_shop_events_missing_item_id"] += 1
            if event_type in ITEM_EVENT_TYPES and event.get("participantId") == own_pid:
                counts["own_all_item_events"] += 1
                own_item_types[event_type] += 1
                if event_type not in SHOP_EVENT_TYPES:
                    counts["own_non_shop_item_events"] += 1
                    if len(non_shop_examples) < 12:
                        non_shop_examples.append({
                            "match_id": match_id,
                            "timestamp": event.get("timestamp"),
                            "type": event_type,
                            "item_id": event.get("itemId"),
                            "before_id": event.get("beforeId"),
                            "after_id": event.get("afterId"),
                        })
            # A champion kill by Viego is only a possible possession opportunity.
            # It does not identify a start/end interval and is never a state proof.
            if event_type == "CHAMPION_KILL" and event.get("killerId") == own_pid:
                counts["candidate_possession_kills"] += 1
                if len(candidate_kills) < 8:
                    candidate_kills.append({"match_id": match_id, "timestamp": event.get("timestamp"),
                                            "victim_id": event.get("victimId")})
        for frame in game.timeline:
            values = (frame.get("participantFrames") or {}).get(str(own_pid)) or {}
            frame_keys.update(values.keys())
            stat_keys.update((values.get("championStats") or {}).keys())
            counts["own_frames"] += 1
        if own_item_events and len(examples) < 8:
            examples.append({
                "match_id": match_id,
                "game_creation": creation,
                "shop_events": [
                    {key: event.get(key) for key in ("timestamp", "type", "participantId", "itemId", "beforeId", "afterId")
                     if key in event}
                    for event in own_item_events[:4]
                ],
            })
    possession_keys = sorted(key for key in event_keys | frame_keys | stat_keys if "posses" in key.lower())
    result = {
        "version": "viego_timeline_provenance_audit_v1",
        "counts": dict(counts),
        "own_item_event_types": dict(own_item_types),
        "event_keys": sorted(event_keys),
        "player_frame_keys": sorted(frame_keys),
        "champion_stat_keys": sorted(stat_keys),
        "possession_named_fields": possession_keys,
        "candidate_possession_kill_examples": candidate_kills,
        "shop_event_examples": examples,
        "non_shop_item_event_examples": non_shop_examples,
        "permanent_shop_inventory": {
            "status": "PERMANENT_SHOP_INVENTORY_PREFIX_SUPPORTED",
            "observed_contract": "Only own ITEM_PURCHASED/ITEM_SOLD/ITEM_UNDO events are admitted to the prefix reconstruction. ITEM_DESTROYED is explicitly excluded.",
            "evidence": "The local Viego sample records player-scoped shop transaction events separately from a high-volume ITEM_DESTROYED stream.",
            "limitation": "This contract proves only an observed shop-event prefix, not shop access or an in-possession runtime inventory.",
        },
        "possession_runtime_state": {
            "status": "UNOBSERVED",
            "limitation": "A Viego CHAMPION_KILL is only a candidate opportunity, not proof of possession state or duration.",
        },
        "frame_champion_stats": {
            "status": "VIEGO_FRAME_STATS_POSSESSION_SENSITIVE",
            "limitation": "Frames contain championStats but no observable possession identity/state; personal Viego championStats are not admitted to scoring.",
        },
        "optimizer_disposition": "VIEGO_PROFILE_ALLOWED_WITH_PERMANENT_SHOP_INVENTORY_ONLY",
    }
    folder = ROOT / "logs" / "build_optimizer"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "viego_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    run()
