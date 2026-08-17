import json
from collections import Counter, defaultdict
from dataclasses import dataclass

from analysis.reset_analyzer import (
    SHOP_CLUSTER_GAP_SECONDS,
    SHOP_EVENT_TYPES,
)
from database.database import (
    get_connection,
    get_local_account_by_riot_id,
)
from riot.data_dragon import (
    get_ddragon_versions,
    get_items,
)


ITEM_EVENT_TYPES = {
    "ITEM_PURCHASED",
    "ITEM_SOLD",
    "ITEM_UNDO",
    "ITEM_DESTROYED",
}

DEFAULT_TRINKET_ID = 3340
TARGET_MATCH_ID = "EUW1_7951911875"
GRANT_TARGET_MATCH_ID = "EUW1_7836627546"
TARGET_MATCH_IDS = (
    TARGET_MATCH_ID,
    GRANT_TARGET_MATCH_ID,
)

MAGICAL_FOOTWEAR_PERK_ID = 8304
SLIGHTLY_MAGICAL_BOOTS_ITEM_ID = 2422
MAGICAL_FOOTWEAR_BASE_GRANT_MS = 12 * 60 * 1000
MAGICAL_FOOTWEAR_TAKEDOWN_REDUCTION_MS = 45 * 1000

EXACT_FINAL_STATUSES = {
    "EXACT",
    "EXACT_WITH_EXPLAINED_GRANT",
}

INVENTORY_RELIABLE = "RELIABLE"
INVENTORY_AMBIGUOUS_TEMPORARY_STATE = "AMBIGUOUS_TEMPORARY_STATE"
INVENTORY_UNRESOLVED_TRANSFORMATION = "UNRESOLVED_TRANSFORMATION"

KNOWN_TRINKET_IDS = {
    3340,
    3363,
    3364,
}

KNOWN_JUNGLE_ITEM_IDS = {
    1101,
    1102,
    1103,
}

SQL_CHUNK_SIZE = 250


@dataclass(frozen=True)
class ItemMeta:
    item_id: int
    name: str
    total_gold: int | None
    base_gold: int | None
    purchasable: bool | None
    tags: tuple
    from_items: tuple
    into_items: tuple
    plaintext: str
    description: str
    consumed: bool
    consume_on_full: bool
    stacks: int
    raw: dict


class ItemCatalog:
    def __init__(self, version, raw_items=None, warnings=None):
        self.version = version or "UNKNOWN"
        self.warnings = list(warnings or [])
        self.items = {}

        for key, raw in (raw_items or {}).items():
            try:
                item_id = int(key)
            except (TypeError, ValueError):
                continue

            gold = raw.get("gold") or {}
            self.items[item_id] = ItemMeta(
                item_id=item_id,
                name=raw.get("name") or f"UNKNOWN_ITEM_{item_id}",
                total_gold=gold.get("total"),
                base_gold=gold.get("base"),
                purchasable=gold.get("purchasable"),
                tags=tuple(raw.get("tags") or ()),
                from_items=tuple(
                    int(value)
                    for value in raw.get("from", []) or []
                    if str(value).isdigit()
                ),
                into_items=tuple(
                    int(value)
                    for value in raw.get("into", []) or []
                    if str(value).isdigit()
                ),
                plaintext=raw.get("plaintext") or "",
                description=raw.get("description") or "",
                consumed=bool(raw.get("consumed")),
                consume_on_full=bool(raw.get("consumeOnFull")),
                stacks=int(raw.get("stacks") or 1),
                raw=raw,
            )

    @classmethod
    def from_raw_items(cls, raw_items, version="synthetic"):
        return cls(version=version, raw_items=raw_items)

    def meta(self, item_id):
        return self.items.get(item_id)

    def name(self, item_id):
        if item_id in (None, 0):
            return "EMPTY"

        meta = self.meta(item_id)
        if meta:
            return meta.name

        return f"UNKNOWN_ITEM_{item_id}"

    def category(self, item_id):
        if item_id in (None, 0):
            return "EMPTY"

        meta = self.meta(item_id)

        if item_id in KNOWN_TRINKET_IDS:
            return "TRINKET"

        if item_id in KNOWN_JUNGLE_ITEM_IDS:
            return "JUNGLE_ITEM"

        if meta is None:
            return "UNKNOWN"

        tags = set(meta.tags)

        if "Trinket" in tags:
            return "TRINKET"

        if meta.consumed or "Consumable" in tags:
            return "CONSUMABLE"

        if "Boots" in tags:
            if meta.from_items:
                return "BOOTS_UPGRADE"
            return "BOOTS"

        if meta.from_items and not meta.into_items:
            return "COMPLETED_MAJOR"

        if meta.from_items and meta.into_items:
            return "INTERMEDIATE"

        if meta.into_items:
            return "COMPONENT"

        if meta.purchasable:
            return "COMPONENT"

        return "SPECIAL"

    def is_stackable_for_slots(self, item_id):
        meta = self.meta(item_id)
        if not meta:
            return False

        return meta.stacks > 1 or self.category(item_id) == "CONSUMABLE"


class DataDragonCatalogProvider:
    def __init__(self):
        self._versions = None
        self._catalogs = {}

    def _resolve_version(self, game_version):
        if not game_version:
            return None

        if self._versions is None:
            self._versions = get_ddragon_versions()

        parts = str(game_version).split(".")
        if len(parts) < 2:
            return self._versions[0] if self._versions else None

        patch = f"{parts[0]}.{parts[1]}"

        for version in self._versions:
            if version.startswith(patch + "."):
                return version

        return self._versions[0] if self._versions else None

    def for_game_version(self, game_version):
        warnings = []

        try:
            ddragon_version = self._resolve_version(game_version)
        except Exception as exc:
            return ItemCatalog(
                version="UNKNOWN",
                raw_items={},
                warnings=[
                    (
                        "DATA_DRAGON_VERSION_UNAVAILABLE",
                        str(exc),
                    )
                ],
            )

        if not ddragon_version:
            return ItemCatalog(
                version="UNKNOWN",
                raw_items={},
                warnings=[("DATA_DRAGON_VERSION_UNKNOWN", game_version)],
            )

        if ddragon_version in self._catalogs:
            return self._catalogs[ddragon_version]

        try:
            raw_items = get_items(ddragon_version)
        except Exception as exc:
            warnings.append(
                (
                    "DATA_DRAGON_ITEMS_UNAVAILABLE",
                    f"{ddragon_version}: {exc}",
                )
            )
            raw_items = {}

        catalog = ItemCatalog(
            version=ddragon_version,
            raw_items=raw_items,
            warnings=warnings,
        )
        self._catalogs[ddragon_version] = catalog
        return catalog


def _chunks(values, size=SQL_CHUNK_SIZE):
    values = list(values)
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _format_time(timestamp_ms):
    total_seconds = int((timestamp_ms or 0) / 1000)
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def _event_key(event):
    return (
        event.get("timestamp") or 0,
        event.get("frame_index") or 0,
        event.get("event_index") or 0,
        event.get("event_type") or event.get("type") or "",
        event.get("item_id")
        or event.get("raw", {}).get("itemId")
        or event.get("raw", {}).get("beforeId")
        or event.get("raw", {}).get("afterId")
        or 0,
    )


def _counter_from_items(items):
    return Counter(
        int(item_id)
        for item_id in items
        if item_id not in (None, 0)
    )


def _counter_to_ids(counter, catalog=None, collapse_stackables=False):
    values = []

    for item_id in sorted(counter):
        count = counter[item_id]
        if count <= 0:
            continue

        if (
            collapse_stackables
            and catalog is not None
            and catalog.is_stackable_for_slots(item_id)
        ):
            count = 1

        values.extend([item_id] * count)

    return values


def _names_from_ids(item_ids, catalog):
    if not item_ids:
        return "EMPTY"

    return ", ".join(
        f"{catalog.name(item_id)} ({item_id})"
        for item_id in item_ids
    )


def _counter_names(counter, catalog):
    return _names_from_ids(
        _counter_to_ids(counter, catalog),
        catalog,
    )


def _counter_overlap(left, right):
    return sum((left & right).values())


def _slot_count(counter, catalog):
    count = 0

    for item_id, amount in counter.items():
        if amount <= 0:
            continue

        if catalog.is_stackable_for_slots(item_id):
            count += 1
        else:
            count += amount

    return count


def _known_inventory_gold(counter, catalog):
    total = 0
    unknown = False

    for item_id, count in counter.items():
        meta = catalog.meta(item_id)
        if not meta or meta.total_gold is None:
            unknown = True
            continue

        amount = 1 if catalog.is_stackable_for_slots(item_id) else count
        total += meta.total_gold * amount

    return None if unknown else total


def _add_item(counter, item_id):
    if item_id in (None, 0):
        return

    counter[item_id] += 1


def _remove_item(counter, item_id):
    if item_id in (None, 0):
        return True

    if counter[item_id] <= 0:
        return False

    counter[item_id] -= 1
    if counter[item_id] <= 0:
        del counter[item_id]
    return True


def _component_tree(item_id, catalog):
    meta = catalog.meta(item_id)
    if not meta or not meta.from_items:
        return []

    values = []
    for component_id in meta.from_items:
        values.append(component_id)
        values.extend(_component_tree(component_id, catalog))

    return values


def _consume_component_tree(counter, item_id, catalog, consumed):
    if _remove_item(counter, item_id):
        consumed.append(item_id)
        return True

    meta = catalog.meta(item_id)
    if not meta or not meta.from_items:
        return False

    removed_any = False
    for component_id in meta.from_items:
        if _consume_component_tree(
            counter,
            component_id,
            catalog,
            consumed,
        ):
            removed_any = True

    return removed_any


def _copy_counter(counter):
    return Counter(
        {
            item_id: count
            for item_id, count in counter.items()
            if count > 0
        }
    )


def _position_of(player):
    return (
        player.get("teamPosition")
        or player.get("individualPosition")
        or ""
    )


def _extract_perk_selections(player):
    selections = []
    perks = player.get("perks") or {}

    for style in perks.get("styles", []) or []:
        style_id = style.get("style")
        style_description = style.get("description")

        for selection in style.get("selections", []) or []:
            perk_id = selection.get("perk")
            if perk_id is None:
                continue

            selections.append(
                {
                    "style": style_id,
                    "style_description": style_description,
                    "perk": perk_id,
                    "var1": selection.get("var1"),
                    "var2": selection.get("var2"),
                    "var3": selection.get("var3"),
                }
            )

    return selections


def _has_perk(meta, perk_id):
    return any(
        selection.get("perk") == perk_id
        for selection in meta.get("perk_selections", [])
    )


def _perk_selection(meta, perk_id):
    for selection in meta.get("perk_selections", []):
        if selection.get("perk") == perk_id:
            return selection

    return None


def _build_match_meta(row, puuid, requested_position):
    (
        match_id,
        game_creation,
        game_duration,
        game_version,
        champion_name,
        win,
        item0,
        item1,
        item2,
        item3,
        item4,
        item5,
        item6,
        raw_json,
    ) = row

    try:
        match = json.loads(raw_json)
    except Exception:
        return None

    participants = match.get("info", {}).get("participants", [])
    my_player = None

    for player in participants:
        if player.get("puuid") == puuid:
            my_player = player
            break

    if not my_player:
        return None

    my_id = my_player.get("participantId")
    my_team_id = my_player.get("teamId")
    my_position = _position_of(my_player) or requested_position
    opponent = None

    for player in participants:
        if (
            player.get("teamId") != my_team_id
            and _position_of(player) == my_position
        ):
            opponent = player
            break

    players = {}
    for player in participants:
        participant_id = player.get("participantId")
        if participant_id is None:
            continue

        players[participant_id] = {
            "participant_id": participant_id,
            "team_id": player.get("teamId"),
            "position": _position_of(player),
            "champion": player.get("championName"),
            "puuid": player.get("puuid"),
        }

    return {
        "match_id": match_id,
        "game_creation": game_creation or 0,
        "game_duration": game_duration or 0,
        "game_version": game_version,
        "champion": champion_name or my_player.get("championName"),
        "win": bool(win),
        "my_participant_id": my_id,
        "opponent_participant_id": (
            opponent.get("participantId")
            if opponent
            else None
        ),
        "opponent_champion": (
            opponent.get("championName")
            if opponent
            else None
        ),
        "final_items": [
            item0,
            item1,
            item2,
            item3,
            item4,
            item5,
        ],
        "final_trinket": item6,
        "perk_selections": _extract_perk_selections(my_player),
        "players": players,
    }


def _load_match_metas(puuid, position, queue_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            m.match_id,
            m.game_creation,
            m.game_duration,
            m.game_version,
            p.champion_name,
            p.win,
            p.item0,
            p.item1,
            p.item2,
            p.item3,
            p.item4,
            p.item5,
            p.item6,
            m.raw_json
        FROM participants AS p
        JOIN matches AS m
            ON m.match_id = p.match_id
        WHERE p.puuid = ?
          AND p.position = ?
          AND m.queue_id = ?
        ORDER BY
            m.game_creation ASC,
            m.match_id ASC
        """,
        (
            puuid,
            position,
            queue_id,
        ),
    )

    metas = []

    for row in cursor.fetchall():
        meta = _build_match_meta(
            row=row,
            puuid=puuid,
            requested_position=position,
        )
        if meta and meta["my_participant_id"] is not None:
            metas.append(meta)

    connection.close()
    return metas


def _load_item_events(metas):
    match_ids = [meta["match_id"] for meta in metas]
    participant_by_match = {
        meta["match_id"]: meta["my_participant_id"]
        for meta in metas
    }
    events_by_match = defaultdict(list)

    if not match_ids:
        return events_by_match

    connection = get_connection()
    cursor = connection.cursor()

    for chunk in _chunks(match_ids):
        placeholders = ",".join("?" for _ in chunk)

        cursor.execute(
            f"""
            SELECT
                match_id,
                timestamp,
                event_type,
                participant_id,
                item_id,
                position_x,
                position_y,
                frame_index,
                event_index,
                raw_json
            FROM timeline_events
            WHERE match_id IN ({placeholders})
              AND event_type LIKE 'ITEM_%'
            ORDER BY
                match_id,
                timestamp,
                frame_index,
                event_index
            """,
            tuple(chunk),
        )

        for row in cursor.fetchall():
            match_id = row[0]
            raw = {}

            if row[9]:
                try:
                    raw = json.loads(row[9])
                except Exception:
                    raw = {}

            participant_id = row[3]
            if participant_id is None:
                participant_id = raw.get("participantId")

            if participant_id != participant_by_match.get(match_id):
                continue

            event_type = row[2]
            if event_type not in ITEM_EVENT_TYPES:
                event_type = event_type or "UNKNOWN_ITEM_EVENT"

            events_by_match[match_id].append(
                {
                    "match_id": match_id,
                    "timestamp": row[1] or raw.get("timestamp") or 0,
                    "event_type": event_type,
                    "type": event_type,
                    "participant_id": participant_id,
                    "item_id": row[4] or raw.get("itemId"),
                    "x": row[5],
                    "y": row[6],
                    "frame_index": row[7],
                    "event_index": row[8],
                    "raw": raw,
                }
            )

    connection.close()

    for events in events_by_match.values():
        events.sort(
            key=lambda event: (
                event.get("timestamp") or 0,
                event.get("frame_index") or 0,
                event.get("event_index") or 0,
            )
        )

    return events_by_match


def _load_takedown_timestamps(metas):
    match_ids = [meta["match_id"] for meta in metas]
    participant_by_match = {
        meta["match_id"]: meta["my_participant_id"]
        for meta in metas
    }
    takedowns_by_match = defaultdict(list)

    if not match_ids:
        return takedowns_by_match

    connection = get_connection()
    cursor = connection.cursor()

    for chunk in _chunks(match_ids):
        placeholders = ",".join("?" for _ in chunk)

        cursor.execute(
            f"""
            SELECT
                match_id,
                timestamp,
                killer_id,
                assisting_ids_json
            FROM timeline_events
            WHERE match_id IN ({placeholders})
              AND event_type = 'CHAMPION_KILL'
            ORDER BY
                match_id,
                timestamp,
                frame_index,
                event_index
            """,
            tuple(chunk),
        )

        for match_id, timestamp, killer_id, assists_json in cursor.fetchall():
            participant_id = participant_by_match.get(match_id)
            if participant_id is None:
                continue

            assists = []
            if assists_json:
                try:
                    assists = json.loads(assists_json)
                except Exception:
                    assists = []

            if killer_id == participant_id or participant_id in assists:
                takedowns_by_match[match_id].append(timestamp or 0)

    connection.close()
    return takedowns_by_match


def _assign_shop_visits(events):
    relevant = [
        event
        for event in events
        if event.get("event_type") in SHOP_EVENT_TYPES
    ]
    relevant.sort(
        key=lambda event: (
            event.get("timestamp") or 0,
            event.get("frame_index") or 0,
            event.get("event_index") or 0,
        )
    )

    visit_by_key = {}
    current = []
    visit_index = 0

    def flush():
        nonlocal current
        nonlocal visit_index

        if not current:
            return

        if any(
            event.get("event_type") == "ITEM_PURCHASED"
            for event in current
        ):
            visit_index += 1
            for event in current:
                visit_by_key[_event_key(event)] = visit_index

        current = []

    for event in relevant:
        if not current:
            current = [event]
            continue

        gap_seconds = (
            (event.get("timestamp") or 0)
            - (current[-1].get("timestamp") or 0)
        ) / 1000

        if gap_seconds <= SHOP_CLUSTER_GAP_SECONDS:
            current.append(event)
        else:
            flush()
            current = [event]

    flush()
    return visit_by_key


def _group_events_by_timestamp(events):
    groups = []
    current_key = None
    current = []

    for event in events:
        key = event.get("timestamp") or 0
        if current_key is None or key == current_key:
            current_key = key
            current.append(event)
            continue

        groups.append(current)
        current_key = key
        current = [event]

    if current:
        groups.append(current)

    return groups


def _mark_component_destroy_events(group, catalog):
    needed = Counter()

    for event in group:
        if event.get("event_type") != "ITEM_PURCHASED":
            continue

        item_id = event.get("item_id")
        meta = catalog.meta(item_id)
        if not meta:
            continue

        needed.update(meta.from_items)
        needed.update(_component_tree(item_id, catalog))

    marks = {}

    for event in group:
        if event.get("event_type") != "ITEM_DESTROYED":
            continue

        item_id = event.get("item_id")
        if needed[item_id] <= 0:
            continue

        needed[item_id] -= 1
        marks[_event_key(event)] = "COMPONENT_CONSUMED_BY_PURCHASE"

    return marks


def _inventory_view(slot_items, trinket_id, catalog):
    ids = _counter_to_ids(slot_items, catalog)
    return {
        "slot_item_ids": ids,
        "slot_items": _names_from_ids(ids, catalog),
        "major_item_ids": [
            item_id
            for item_id in ids
            if catalog.category(item_id) == "COMPLETED_MAJOR"
        ],
        "component_item_ids": [
            item_id
            for item_id in ids
            if catalog.category(item_id) in {
                "COMPONENT",
                "INTERMEDIATE",
            }
        ],
        "boots_item_ids": [
            item_id
            for item_id in ids
            if catalog.category(item_id) in {
                "BOOTS",
                "BOOTS_UPGRADE",
            }
        ],
        "jungle_item_ids": [
            item_id
            for item_id in ids
            if catalog.category(item_id) == "JUNGLE_ITEM"
        ],
        "trinket_id": trinket_id,
        "trinket": catalog.name(trinket_id) if trinket_id else "UNKNOWN",
        "known_inventory_gold": _known_inventory_gold(slot_items, catalog),
    }


def _base_transaction_row(
    meta,
    event,
    catalog,
    visit_by_key,
    slot_items,
    trinket_id,
):
    raw = event.get("raw") or {}
    event_type = event.get("event_type")
    item_id = event.get("item_id")

    if event_type == "ITEM_UNDO" and item_id is None:
        item_id = raw.get("beforeId")

    timestamp = event.get("timestamp") or 0
    item_meta = catalog.meta(item_id)
    view = _inventory_view(slot_items, trinket_id, catalog)
    slot_count_before = _slot_count(slot_items, catalog)

    row = {
        "match_id": meta["match_id"],
        "game_creation": meta["game_creation"],
        "champion": meta["champion"],
        "opponent_champion": meta.get("opponent_champion"),
        "win": meta["win"],
        "timestamp": timestamp,
        "minute": timestamp / 60_000,
        "time": _format_time(timestamp),
        "event_type": event_type,
        "item_id": item_id,
        "item_name": catalog.name(item_id),
        "item_category": catalog.category(item_id),
        "item_cost": item_meta.total_gold if item_meta else None,
        "item_base_cost": item_meta.base_gold if item_meta else None,
        "item_purchasable": item_meta.purchasable if item_meta else None,
        "item_tags": list(item_meta.tags) if item_meta else [],
        "item_from": list(item_meta.from_items) if item_meta else [],
        "item_into": list(item_meta.into_items) if item_meta else [],
        "frame_index": event.get("frame_index"),
        "event_index": event.get("event_index"),
        "x": event.get("x"),
        "y": event.get("y"),
        "shop_visit_id": visit_by_key.get(_event_key(event)),
        "reconstruction_status": "OK",
        "reconstruction_warnings": [],
        "inventory_before_slot_item_ids": list(view["slot_item_ids"]),
        "inventory_before_slot_items": list(view["slot_items"]),
        "inventory_before_trinket_id": trinket_id,
        "inventory_before_trinket": view["trinket"],
        "slot_count_before": slot_count_before,
        "raw_event": raw,
    }
    row.update(view)
    return row


def _append_warning(row, code, detail=None):
    warning = {
        "code": code,
        "detail": detail,
    }
    row["reconstruction_warnings"].append(warning)


def _apply_capacity_invariant(row, slot_items, catalog):
    slot_count = _slot_count(slot_items, catalog)

    if slot_count > 6:
        row["reconstruction_status"] = "RECONSTRUCTION_WARNING"
        _append_warning(
            row,
            "INVENTORY_CAPACITY_EXCEEDED",
            f"{slot_count} inferred slots",
        )


def _finalize_row_inventory(row, slot_items, trinket_id, catalog):
    view = _inventory_view(slot_items, trinket_id, catalog)
    row["inventory_after_slot_item_ids"] = list(view["slot_item_ids"])
    row["inventory_after_slot_items"] = list(view["slot_items"])
    row["inventory_after_trinket_id"] = trinket_id
    row["inventory_after_trinket"] = view["trinket"]
    row["slot_count_after"] = _slot_count(slot_items, catalog)
    row.update(view)


def reconstruct_item_timeline(meta, events, catalog):
    events = sorted(
        events,
        key=lambda event: (
            event.get("timestamp") or 0,
            event.get("frame_index") or 0,
            event.get("event_index") or 0,
        ),
    )

    slot_items = Counter()
    trinket_id = DEFAULT_TRINKET_ID
    visit_by_key = _assign_shop_visits(events)
    transactions = []
    milestones = {
        "first_meaningful_purchase": None,
        "boots_purchase": None,
        "boots_upgrade": None,
        "completed_major_items": [],
    }
    event_type_counts = Counter()
    special_case_counts = Counter()
    undoable_purchases = []

    for warning in catalog.warnings:
        special_case_counts[warning[0]] += 1

    for group in _group_events_by_timestamp(events):
        component_destroy_marks = _mark_component_destroy_events(
            group,
            catalog,
        )

        for event in group:
            event_type = event.get("event_type")
            event_type_counts[event_type] += 1
            row = _base_transaction_row(
                meta=meta,
                event=event,
                catalog=catalog,
                visit_by_key=visit_by_key,
                slot_items=slot_items,
                trinket_id=trinket_id,
            )
            raw = event.get("raw") or {}
            item_id = row["item_id"]
            category = catalog.category(item_id)

            if catalog.meta(item_id) is None and item_id not in (None, 0):
                row["reconstruction_status"] = "RECONSTRUCTION_WARNING"
                _append_warning(
                    row,
                    "UNKNOWN_ITEM_METADATA",
                    item_id,
                )
                special_case_counts["UNKNOWN_ITEM_METADATA"] += 1

            if event_type == "ITEM_PURCHASED":
                consumed_components = []
                missing_components = []
                meta_item = catalog.meta(item_id)

                if meta_item:
                    for component_id in meta_item.from_items:
                        if not _consume_component_tree(
                            slot_items,
                            component_id,
                            catalog,
                            consumed_components,
                        ):
                            missing_components.append(component_id)

                row["components_consumed"] = consumed_components
                row["components_not_held"] = missing_components

                if category == "TRINKET":
                    trinket_id = item_id
                    special_case_counts["TRINKET_PURCHASE_OR_SWAP"] += 1
                elif (
                    category == "CONSUMABLE"
                    and meta_item
                    and meta_item.consume_on_full
                ):
                    row["purchase_interpretation"] = (
                        "CONSUMED_ON_PURCHASE"
                    )
                    special_case_counts[
                        "CONSUMABLE_CONSUMED_ON_PURCHASE"
                    ] += 1
                else:
                    _add_item(slot_items, item_id)

                if (
                    milestones["first_meaningful_purchase"] is None
                    and category not in {
                        "CONSUMABLE",
                        "TRINKET",
                        "JUNGLE_ITEM",
                        "EMPTY",
                    }
                ):
                    milestones["first_meaningful_purchase"] = {
                        "timestamp": row["timestamp"],
                        "time": row["time"],
                        "item_id": item_id,
                        "item_name": row["item_name"],
                    }

                if (
                    milestones["boots_purchase"] is None
                    and category == "BOOTS"
                ):
                    milestones["boots_purchase"] = {
                        "timestamp": row["timestamp"],
                        "time": row["time"],
                        "item_id": item_id,
                        "item_name": row["item_name"],
                    }

                if (
                    milestones["boots_upgrade"] is None
                    and category == "BOOTS_UPGRADE"
                ):
                    milestones["boots_upgrade"] = {
                        "timestamp": row["timestamp"],
                        "time": row["time"],
                        "item_id": item_id,
                        "item_name": row["item_name"],
                    }

                if category == "COMPLETED_MAJOR":
                    milestones["completed_major_items"].append(
                        {
                            "timestamp": row["timestamp"],
                            "time": row["time"],
                            "item_id": item_id,
                            "item_name": row["item_name"],
                        }
                    )

                if category not in {"TRINKET", "CONSUMABLE"}:
                    undoable_purchases.append(
                        {
                            "item_id": item_id,
                            "consumed_components": list(
                                consumed_components
                            ),
                            "timestamp": row["timestamp"],
                            "undone": False,
                        }
                    )

                _apply_capacity_invariant(row, slot_items, catalog)

            elif event_type == "ITEM_SOLD":
                if category == "TRINKET" and trinket_id == item_id:
                    trinket_id = None
                    special_case_counts["TRINKET_SOLD_OR_REMOVED"] += 1
                elif not _remove_item(slot_items, item_id):
                    row["reconstruction_status"] = "RECONSTRUCTION_WARNING"
                    _append_warning(
                        row,
                        "SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD",
                        item_id,
                    )

                _apply_capacity_invariant(row, slot_items, catalog)

            elif event_type == "ITEM_UNDO":
                before_id = raw.get("beforeId")
                after_id = raw.get("afterId")
                row["undo_before_id"] = before_id
                row["undo_after_id"] = after_id
                row["item_id"] = before_id
                row["item_name"] = catalog.name(before_id)
                row["item_category"] = catalog.category(before_id)
                row["undo_restored_components"] = []

                if before_id not in (None, 0):
                    if (
                        catalog.category(before_id) == "TRINKET"
                        and trinket_id == before_id
                    ):
                        trinket_id = None
                    elif not _remove_item(slot_items, before_id):
                        row["reconstruction_status"] = (
                            "RECONSTRUCTION_WARNING"
                        )
                        _append_warning(
                            row,
                            "UNDO_BEFORE_ITEM_NOT_RECONSTRUCTED_AS_HELD",
                            before_id,
                        )
                    else:
                        for purchase in reversed(undoable_purchases):
                            if purchase["undone"]:
                                continue
                            if purchase["item_id"] != before_id:
                                continue

                            purchase["undone"] = True

                            if after_id in (None, 0):
                                for component_id in purchase[
                                    "consumed_components"
                                ]:
                                    _add_item(slot_items, component_id)
                                    row["undo_restored_components"].append(
                                        component_id
                                    )

                                if row["undo_restored_components"]:
                                    special_case_counts[
                                        "UNDO_CONSUMED_COMPONENTS_RESTORED"
                                    ] += len(
                                        row["undo_restored_components"]
                                    )
                            break

                if after_id not in (None, 0):
                    if catalog.category(after_id) == "TRINKET":
                        trinket_id = after_id
                    else:
                        _add_item(slot_items, after_id)

                if before_id in (None, 0) and after_id in (None, 0):
                    row["reconstruction_status"] = "AMBIGUOUS"
                    _append_warning(
                        row,
                        "UNDO_WITHOUT_BEFORE_OR_AFTER_ITEM",
                        raw,
                    )

                if after_id not in (None, 0):
                    special_case_counts["UNDO_AFTER_ID_RESTORED"] += 1

                _apply_capacity_invariant(row, slot_items, catalog)

            elif event_type == "ITEM_DESTROYED":
                mark = component_destroy_marks.get(_event_key(event))

                if mark:
                    row["reconstruction_status"] = "OK"
                    row["destroyed_interpretation"] = mark
                    special_case_counts[mark] += 1

                elif category in {"CONSUMABLE", "JUNGLE_ITEM"}:
                    if _remove_item(slot_items, item_id):
                        row["destroyed_interpretation"] = (
                            "REMOVED_FROM_HELD_INVENTORY"
                        )
                        special_case_counts[
                            f"{category}_DESTROYED_REMOVED"
                        ] += 1
                    else:
                        row["reconstruction_status"] = (
                            "RECONSTRUCTION_WARNING"
                        )
                        _append_warning(
                            row,
                            f"{category}_DESTROYED_NOT_HELD",
                            item_id,
                        )
                        special_case_counts[
                            f"{category}_DESTROYED_NOT_HELD"
                        ] += 1

                elif category == "TRINKET":
                    row["destroyed_interpretation"] = (
                        "TRINKET_USE_EVENT_IGNORED_FOR_INVENTORY"
                    )
                    special_case_counts["TRINKET_DESTROYED_IGNORED"] += 1

                else:
                    row["reconstruction_status"] = "AMBIGUOUS"
                    row["destroyed_interpretation"] = (
                        "NORMAL_OR_UNKNOWN_DESTROYED_EVENT_IGNORED"
                    )
                    if slot_items[item_id] > 0:
                        _append_warning(
                            row,
                            "DESTROYED_NORMAL_HELD_IGNORED_AS_AMBIGUOUS",
                            item_id,
                        )
                        special_case_counts[
                            "DESTROYED_NORMAL_HELD_IGNORED"
                        ] += 1
                    else:
                        _append_warning(
                            row,
                            "DESTROYED_NORMAL_NOT_HELD_IGNORED_AS_AMBIGUOUS",
                            item_id,
                        )
                        special_case_counts[
                            "DESTROYED_NORMAL_NOT_HELD_IGNORED"
                        ] += 1

                    if str(meta.get("champion", "")).lower() == "viego":
                        _append_warning(
                            row,
                            "VIEGO_TEMPORARY_ITEM_OR_POSSESSION_POSSIBLE",
                            item_id,
                        )
                        special_case_counts[
                            "VIEGO_TEMPORARY_ITEM_DESTROY_EVENTS"
                        ] += 1

            else:
                row["reconstruction_status"] = "AMBIGUOUS"
                _append_warning(
                    row,
                    "UNKNOWN_ITEM_EVENT_TYPE",
                    event_type,
                )

            _finalize_row_inventory(
                row,
                slot_items,
                trinket_id,
                catalog,
            )
            transactions.append(row)

    final_state = {
        "slot_items": _copy_counter(slot_items),
        "trinket_id": trinket_id,
    }
    validation = _validate_final_inventory(meta, final_state, catalog)

    invariant_warnings = []
    for row in transactions:
        for warning in row["reconstruction_warnings"]:
            invariant_warnings.append(
                {
                    "match_id": row["match_id"],
                    "time": row["time"],
                    "event_type": row["event_type"],
                    "item_id": row["item_id"],
                    "item_name": row["item_name"],
                    "code": warning["code"],
                    "detail": warning["detail"],
                }
            )

    result = {
        "match_id": meta["match_id"],
        "game_creation": meta["game_creation"],
        "game_duration": meta["game_duration"],
        "game_version": meta["game_version"],
        "ddragon_version": catalog.version,
        "champion": meta["champion"],
        "opponent_champion": meta.get("opponent_champion"),
        "win": meta["win"],
        "perk_selections": meta.get("perk_selections", []),
        "takedown_timestamps": meta.get("takedown_timestamps", []),
        "transactions": transactions,
        "event_type_counts": event_type_counts,
        "special_case_counts": special_case_counts,
        "milestones": milestones,
        "final_state": final_state,
        "final_validation": validation,
        "invariant_warnings": invariant_warnings,
        "catalog_warnings": catalog.warnings,
        "catalog": catalog,
    }
    _annotate_inventory_reliability(result)
    return result


def _normalize_final_counter(counter, catalog):
    normalized = Counter()

    for item_id, count in counter.items():
        if catalog.is_stackable_for_slots(item_id):
            normalized[item_id] = 1
        else:
            normalized[item_id] = count

    return normalized


def _derive_magical_footwear_timestamp(takedown_timestamps):
    if takedown_timestamps is None:
        return {
            "derived_timestamp": None,
            "derived_time": "UNKNOWN",
            "derived_status": "UNKNOWN",
            "takedowns_used": None,
            "rule": (
                "Magical Footwear base grant at 12:00, reduced by "
                "45s per takedown; no Riot item event is observed."
            ),
        }

    takedowns = sorted(
        timestamp
        for timestamp in takedown_timestamps
        if timestamp is not None
    )
    grant_timestamp = MAGICAL_FOOTWEAR_BASE_GRANT_MS

    for _ in range(len(takedowns) + 2):
        takedowns_before_grant = sum(
            timestamp <= grant_timestamp
            for timestamp in takedowns
        )
        next_timestamp = (
            MAGICAL_FOOTWEAR_BASE_GRANT_MS
            - (
                takedowns_before_grant
                * MAGICAL_FOOTWEAR_TAKEDOWN_REDUCTION_MS
            )
        )

        if next_timestamp == grant_timestamp:
            return {
                "derived_timestamp": grant_timestamp,
                "derived_time": _format_time(grant_timestamp),
                "derived_status": "DERIVED_INFERRED",
                "takedowns_used": takedowns_before_grant,
                "rule": (
                    "Magical Footwear base grant at 12:00, reduced by "
                    "45s per takedown; no Riot item event is observed."
                ),
            }

        grant_timestamp = next_timestamp

    return {
        "derived_timestamp": None,
        "derived_time": "UNKNOWN",
        "derived_status": "UNKNOWN",
        "takedowns_used": None,
        "rule": (
            "Magical Footwear timing could not be derived to a stable "
            "timestamp from the observed takedown list."
        ),
    }


def _grant_for_missing_final_item(meta, item_id, catalog):
    item_meta = catalog.meta(item_id)

    if (
        item_id == SLIGHTLY_MAGICAL_BOOTS_ITEM_ID
        and _has_perk(meta, MAGICAL_FOOTWEAR_PERK_ID)
    ):
        timing = _derive_magical_footwear_timestamp(
            meta.get("takedown_timestamps")
        )
        perk = _perk_selection(meta, MAGICAL_FOOTWEAR_PERK_ID)

        return {
            "item_id": item_id,
            "item_name": catalog.name(item_id),
            "source": "RUNE_GRANT",
            "grant_type": "MAGICAL_FOOTWEAR",
            "purchase_event": "NONE",
            "observed_timestamp": None,
            "observed_time": "NONE",
            "derived_timestamp": timing["derived_timestamp"],
            "derived_time": timing["derived_time"],
            "derived_status": timing["derived_status"],
            "confidence": "HIGH_RUNE_CONFIRMED",
            "evidence": [
                f"perk {MAGICAL_FOOTWEAR_PERK_ID} present",
                f"final item {item_id} present",
                "no ITEM_PURCHASED/ITEM_UNDO event for this item",
                timing["rule"],
            ],
            "perk_selection": perk,
            "takedowns_used": timing["takedowns_used"],
        }

    if item_meta and item_meta.purchasable is False:
        return {
            "item_id": item_id,
            "item_name": catalog.name(item_id),
            "source": "UNKNOWN_GRANT",
            "grant_type": "NON_PURCHASABLE_FINAL_ITEM",
            "purchase_event": "NONE",
            "observed_timestamp": None,
            "observed_time": "NONE",
            "derived_timestamp": None,
            "derived_time": "UNKNOWN",
            "derived_status": "UNKNOWN",
            "confidence": "UNRESOLVED",
            "evidence": [
                "final item is not purchasable in Data Dragon",
                "no matching reconstructed transaction explained it",
            ],
            "perk_selection": None,
            "takedowns_used": None,
        }

    return None


def _explain_missing_final_grants(meta, missing, catalog):
    grants = []

    for item_id, count in missing.items():
        for _ in range(count):
            grant = _grant_for_missing_final_item(
                meta,
                item_id,
                catalog,
            )
            if grant:
                grants.append(grant)

    return grants


def _grant_counter(grants, explained_only=False):
    counter = Counter()

    for grant in grants:
        if explained_only and grant.get("source") == "UNKNOWN_GRANT":
            continue
        counter[grant["item_id"]] += 1

    return counter


def _validate_final_inventory(meta, final_state, catalog):
    riot_counter = _counter_from_items(meta.get("final_items") or [])
    reconstructed_counter = _normalize_final_counter(
        final_state["slot_items"],
        catalog,
    )
    riot_counter = _normalize_final_counter(riot_counter, catalog)

    riot_trinket = meta.get("final_trinket") or None
    reconstructed_trinket = final_state.get("trinket_id")

    normal_exact = reconstructed_counter == riot_counter
    trinket_exact = reconstructed_trinket == riot_trinket

    missing = riot_counter - reconstructed_counter
    extra = reconstructed_counter - riot_counter
    grants = _explain_missing_final_grants(
        meta,
        missing,
        catalog,
    )
    explained_grant_counter = _grant_counter(
        grants,
        explained_only=True,
    )
    unexplained_grants = [
        grant
        for grant in grants
        if grant.get("source") == "UNKNOWN_GRANT"
    ]
    effective_reconstructed_counter = (
        reconstructed_counter
        + explained_grant_counter
    )
    missing_after_grants = riot_counter - effective_reconstructed_counter
    overlap = _counter_overlap(reconstructed_counter, riot_counter)
    smaller_size = min(
        sum(reconstructed_counter.values()),
        sum(riot_counter.values()),
    )

    causes = []

    if grants:
        causes.append("NON_PURCHASE_FINAL_ITEM_GRANT")
        for grant in grants:
            causes.append(grant["source"])
            causes.append(grant["grant_type"])

    if missing_after_grants:
        causes.append("FINAL_ITEMS_MISSING_FROM_RECONSTRUCTION")
        for item_id in missing_after_grants:
            item_meta = catalog.meta(item_id)
            if item_meta and item_meta.purchasable is False:
                causes.append(
                    "UNOBSERVED_NON_PURCHASABLE_FINAL_ITEM_GRANT"
                )
    if extra:
        causes.append("EXTRA_RECONSTRUCTED_FINAL_ITEMS")
    if not trinket_exact:
        causes.append("FINAL_TRINKET_MISMATCH")

    if normal_exact and trinket_exact:
        status = "EXACT"
    elif (
        effective_reconstructed_counter == riot_counter
        and trinket_exact
        and not extra
        and explained_grant_counter
        and not unexplained_grants
    ):
        status = "EXACT_WITH_EXPLAINED_GRANT"
    elif normal_exact or (
        smaller_size > 0
        and overlap >= max(1, smaller_size // 2)
    ):
        status = "PARTIAL"
    elif not riot_counter and reconstructed_counter:
        status = "UNKNOWN"
    else:
        status = "MISMATCH"

    return {
        "status": status,
        "definition": (
            "EXACT = reconstructed six-slot multiset and trinket match "
            "Riot final inventory from observed item transactions; "
            "EXACT_WITH_EXPLAINED_GRANT = remaining final difference is "
            "explained by a non-purchase grant such as a confirmed rune "
            "grant, without fabricating a Riot event; PARTIAL = normal "
            "inventory matches or meaningful overlap remains; MISMATCH = "
            "material disagreement; UNKNOWN = final reference cannot be "
            "exploited."
        ),
        "normal_exact": normal_exact,
        "trinket_exact": trinket_exact,
        "riot_final_counter": riot_counter,
        "reconstructed_final_counter": reconstructed_counter,
        "effective_reconstructed_final_counter": (
            effective_reconstructed_counter
        ),
        "riot_trinket": riot_trinket,
        "reconstructed_trinket": reconstructed_trinket,
        "missing_counter": missing,
        "missing_after_grants_counter": missing_after_grants,
        "extra_counter": extra,
        "explained_grants": [
            grant
            for grant in grants
            if grant.get("source") != "UNKNOWN_GRANT"
        ],
        "unexplained_grants": unexplained_grants,
        "causes": causes,
    }


def build_itemization_history(
    puuid,
    position="JUNGLE",
    queue_id=420,
):
    metas = _load_match_metas(
        puuid=puuid,
        position=position,
        queue_id=queue_id,
    )
    events_by_match = _load_item_events(metas)
    takedowns_by_match = _load_takedown_timestamps(metas)
    provider = DataDragonCatalogProvider()
    matches = []
    transactions = []
    load_warnings = []

    for meta in metas:
        meta["takedown_timestamps"] = takedowns_by_match.get(
            meta["match_id"],
            [],
        )
        catalog = provider.for_game_version(meta.get("game_version"))
        if catalog.warnings:
            load_warnings.extend(
                {
                    "match_id": meta["match_id"],
                    "warning": warning,
                }
                for warning in catalog.warnings
            )

        match_result = reconstruct_item_timeline(
            meta=meta,
            events=events_by_match.get(meta["match_id"], []),
            catalog=catalog,
        )
        matches.append(match_result)
        transactions.extend(match_result["transactions"])

    summary = _summarize_history(matches, transactions)

    return {
        "matches": matches,
        "transactions": transactions,
        "summary": summary,
        "load_warnings": load_warnings,
    }


def _summarize_history(matches, transactions):
    status_counts = Counter()
    event_type_counts = Counter()
    warning_counts = Counter()
    cause_counts = Counter()
    special_case_counts = Counter()
    champion_status = defaultdict(Counter)
    grant_source_counts = Counter()
    grant_type_counts = Counter()
    grant_derived_status_counts = Counter()
    grant_match_count = 0

    for row in matches:
        validation = row["final_validation"]
        status = validation["status"]
        status_counts[status] += 1
        champion_status[row["champion"]][status] += 1
        event_type_counts.update(row["event_type_counts"])
        special_case_counts.update(row["special_case_counts"])

        for cause in validation["causes"]:
            cause_counts[cause] += 1

        grants = (
            validation.get("explained_grants", [])
            + validation.get("unexplained_grants", [])
        )
        if grants:
            grant_match_count += 1

        for grant in grants:
            grant_source_counts[grant["source"]] += 1
            grant_type_counts[grant["grant_type"]] += 1
            grant_derived_status_counts[grant["derived_status"]] += 1

        for warning in row["invariant_warnings"]:
            warning_counts[warning["code"]] += 1

    exact = status_counts["EXACT"]
    explained_exact = status_counts["EXACT_WITH_EXPLAINED_GRANT"]
    total = len(matches)

    return {
        "games_processed": total,
        "item_events_processed": len(transactions),
        "status_counts": status_counts,
        "event_type_counts": event_type_counts,
        "warning_counts": warning_counts,
        "cause_counts": cause_counts,
        "special_case_counts": special_case_counts,
        "champion_status": champion_status,
        "exact_match_rate": exact / total if total else None,
        "exact_or_explained_rate": (
            (exact + explained_exact) / total
            if total
            else None
        ),
        "grant_match_count": grant_match_count,
        "grant_source_counts": grant_source_counts,
        "grant_type_counts": grant_type_counts,
        "grant_derived_status_counts": grant_derived_status_counts,
        "destroyed_audit": _summarize_destroyed_audit(matches),
        "viego_audit": _summarize_viego_audit(matches),
        "sell_warning_audit": _summarize_sell_warning_audit(matches),
        "intermediate_contradictions": (
            _summarize_intermediate_contradictions(matches)
        ),
        "inventory_reliability_audit": (
            _summarize_inventory_reliability(matches)
        ),
        "warning_buckets": _summarize_warning_buckets(warning_counts),
        "major_milestone_audit": _summarize_major_milestones(matches),
    }


def _format_counter(counter, catalog=None):
    if not counter:
        return "none"

    parts = []
    for item_id, count in sorted(counter.items()):
        label = catalog.name(item_id) if catalog else str(item_id)
        if count == 1:
            parts.append(f"{label} ({item_id})")
        else:
            parts.append(f"{label} ({item_id}) x{count}")

    return ", ".join(parts)


def _warning_codes(row):
    return {
        warning["code"]
        for warning in row.get("reconstruction_warnings", [])
    }


def _same_timestamp_item_events(match, row):
    timestamp = row.get("timestamp")
    return [
        transaction
        for transaction in match["transactions"]
        if transaction is not row
        and transaction.get("timestamp") == timestamp
        and transaction.get("event_type", "").startswith("ITEM_")
    ]


def _transaction_mentions_item(transaction, item_id):
    raw = transaction.get("raw_event") or {}
    return item_id in (
        transaction.get("item_id"),
        raw.get("itemId"),
        raw.get("beforeId"),
        raw.get("afterId"),
    )


def _is_acquisition_transaction(transaction, item_id):
    raw = transaction.get("raw_event") or {}

    if (
        transaction.get("event_type") == "ITEM_PURCHASED"
        and transaction.get("item_id") == item_id
    ):
        return True

    return (
        transaction.get("event_type") == "ITEM_UNDO"
        and raw.get("afterId") == item_id
    )


def _item_acquisition_transactions(match, item_id):
    return [
        transaction
        for transaction in match["transactions"]
        if _is_acquisition_transaction(transaction, item_id)
    ]


def _previous_item_transactions(match, row):
    item_id = row.get("item_id")
    timestamp = row.get("timestamp") or 0
    previous = []

    for transaction in match["transactions"]:
        if (transaction.get("timestamp") or 0) >= timestamp:
            continue

        if _transaction_mentions_item(transaction, item_id):
            previous.append(transaction)

    return previous


def _later_item_transactions(match, row):
    item_id = row.get("item_id")
    timestamp = row.get("timestamp") or 0
    later = []

    for transaction in match["transactions"]:
        if (transaction.get("timestamp") or 0) <= timestamp:
            continue

        if _transaction_mentions_item(transaction, item_id):
            later.append(transaction)

    return later


def _nearby_item_events(match, row, window_ms=5_000):
    timestamp = row.get("timestamp") or 0
    return [
        transaction
        for transaction in match["transactions"]
        if transaction is not row
        and transaction.get("event_type", "").startswith("ITEM_")
        and abs((transaction.get("timestamp") or 0) - timestamp)
        <= window_ms
    ]


def _component_or_upgrade_relation(catalog, source_item_id, target_item_id):
    source_meta = catalog.meta(source_item_id)
    target_meta = catalog.meta(target_item_id)

    if not source_meta or not target_meta:
        return False

    if source_item_id in target_meta.from_items:
        return True

    if source_item_id in _component_tree(target_item_id, catalog):
        return True

    if target_item_id in source_meta.into_items:
        return True

    return False


def _same_item_family(catalog, first_item_id, second_item_id):
    first_meta = catalog.meta(first_item_id)
    second_meta = catalog.meta(second_item_id)

    if not first_meta or not second_meta:
        return False

    if (
        first_meta.from_items
        and second_meta.from_items
        and Counter(first_meta.from_items) == Counter(second_meta.from_items)
    ):
        return True

    return False


def _summarize_transaction(transaction):
    if not transaction:
        return None

    raw = transaction.get("raw_event") or {}
    return {
        "time": transaction.get("time"),
        "timestamp": transaction.get("timestamp"),
        "event_type": transaction.get("event_type"),
        "item_id": transaction.get("item_id"),
        "item_name": transaction.get("item_name"),
        "before_id": raw.get("beforeId"),
        "after_id": raw.get("afterId"),
    }


def _find_transformation_purchase(match, row, catalog):
    item_id = row.get("item_id")

    for transaction in _nearby_item_events(match, row):
        if transaction.get("event_type") != "ITEM_PURCHASED":
            continue

        target_item_id = transaction.get("item_id")
        if _component_or_upgrade_relation(
            catalog,
            item_id,
            target_item_id,
        ):
            return transaction

    return None


def _find_later_unobserved_replacement(match, row, catalog):
    item_id = row.get("item_id")
    timestamp = row.get("timestamp") or 0

    for transaction in match["transactions"]:
        if (transaction.get("timestamp") or 0) <= timestamp:
            continue
        if transaction.get("event_type") != "ITEM_DESTROYED":
            continue

        replacement_id = transaction.get("item_id")
        if replacement_id == item_id:
            continue
        if not _same_item_family(catalog, item_id, replacement_id):
            continue

        previous_replacement_acquisitions = [
            acquisition
            for acquisition in _item_acquisition_transactions(
                match,
                replacement_id,
            )
            if (acquisition.get("timestamp") or 0)
            < (transaction.get("timestamp") or 0)
        ]
        if previous_replacement_acquisitions:
            continue

        return transaction

    return None


def _find_later_repurchase(match, row):
    item_id = row.get("item_id")
    timestamp = row.get("timestamp") or 0

    for transaction in match["transactions"]:
        if (transaction.get("timestamp") or 0) <= timestamp:
            continue
        if _is_acquisition_transaction(transaction, item_id):
            return transaction

    return None


def _has_previous_same_item_destroyed(match, row):
    item_id = row.get("item_id")
    timestamp = row.get("timestamp") or 0

    for transaction in match["transactions"]:
        if transaction is row:
            break
        if (transaction.get("timestamp") or 0) >= timestamp:
            continue
        if transaction.get("event_type") != "ITEM_DESTROYED":
            continue
        if transaction.get("item_id") == item_id:
            return True

    return False


def _purchase_consumes_related_component(catalog, purchase, item_id):
    if not purchase:
        return False

    consumed_components = purchase.get("components_consumed") or []
    for component_id in consumed_components:
        if component_id == item_id:
            return True
        if _same_item_family(catalog, component_id, item_id):
            return True
        if _component_or_upgrade_relation(catalog, component_id, item_id):
            return True
        if _component_or_upgrade_relation(catalog, item_id, component_id):
            return True

    return False


def _classify_destroyed_root_cause(
    match,
    row,
    catalog,
    classification,
    transformation_purchase,
    later_replacement,
    held_before,
    retained_after,
    is_viego,
    magical_footwear_context,
):
    if classification == "CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION":
        return "TEMPORARY_MECHANIC"

    if classification != "MISSED_TRANSFORMATION":
        if is_viego and classification == "UNRESOLVED_TEMPORARY_POSSIBLE":
            return "VIEGO_TEMPORARY_POSSIBLE"
        if classification == "CONFIRMED_OR_STRONG_TEMPORARY_STATE":
            return "TEMPORARY_MECHANIC"
        return "UNRESOLVED"

    if magical_footwear_context:
        if _has_previous_same_item_destroyed(match, row):
            return "EVENT_ORDER_DUPLICATE"
        return "TEMPORARY_MECHANIC"

    if is_viego:
        return "VIEGO_TEMPORARY_POSSIBLE"

    if held_before and retained_after:
        return "REAL_MISSED_TRANSFORMATION"

    if _purchase_consumes_related_component(
        catalog,
        transformation_purchase,
        row.get("item_id"),
    ):
        return "ALREADY_HANDLED_BY_PURCHASE_COMPONENT_CONSUMPTION"

    if transformation_purchase or later_replacement:
        return "EVENT_ORDER_DUPLICATE"

    return "UNRESOLVED"


def _final_effective_counter(match):
    return match["final_validation"].get(
        "effective_reconstructed_final_counter",
        match["final_validation"]["riot_final_counter"],
    )


def _destroyed_evidence_context(match, row):
    catalog = _catalog_for_match(match)
    codes = _warning_codes(row)
    item_id = row.get("item_id")
    timestamp = row.get("timestamp") or 0
    is_viego = str(match.get("champion", "")).lower() == "viego"
    before_ids = row.get("inventory_before_slot_item_ids") or []
    after_ids = row.get("inventory_after_slot_item_ids") or []
    held_before = item_id in before_ids
    retained_after = item_id in after_ids
    same_events = _same_timestamp_item_events(match, row)
    same_purchases = [
        event for event in same_events
        if event.get("event_type") == "ITEM_PURCHASED"
    ]
    same_sells = [
        event for event in same_events
        if event.get("event_type") == "ITEM_SOLD"
    ]
    same_undos = [
        event for event in same_events
        if event.get("event_type") == "ITEM_UNDO"
    ]
    previous_item_transactions = _previous_item_transactions(match, row)
    later_item_transactions = _later_item_transactions(match, row)
    acquisitions = _item_acquisition_transactions(match, item_id)
    previous_acquisitions = [
        transaction
        for transaction in acquisitions
        if (transaction.get("timestamp") or 0) < timestamp
    ]
    later_repurchase = _find_later_repurchase(match, row)
    transformation_purchase = _find_transformation_purchase(
        match,
        row,
        catalog,
    )
    later_replacement = _find_later_unobserved_replacement(
        match,
        row,
        catalog,
    )
    final_counter = _final_effective_counter(match)
    final_count = final_counter.get(item_id, 0)
    item_category = catalog.category(item_id)
    magical_footwear_context = (
        item_id == SLIGHTLY_MAGICAL_BOOTS_ITEM_ID
        and _has_perk(match, MAGICAL_FOOTWEAR_PERK_ID)
    )
    evidence = []
    classification = "UNRESOLVED"

    if (
        item_category == "CONSUMABLE"
        and "CONSUMABLE_DESTROYED_NOT_HELD" in codes
    ):
        classification = "CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION"
        evidence.append(
            "consumable destroy/use event was observed after a consumed-on-purchase item was not kept in the durable slot model"
        )
    elif transformation_purchase:
        classification = "MISSED_TRANSFORMATION"
        evidence.append(
            "nearby purchase is connected by Data Dragon component/upgrade graph"
        )
    elif later_replacement:
        classification = "MISSED_TRANSFORMATION"
        evidence.append(
            "later unpurchased sibling item appears in the same upgrade family"
        )
    elif held_before and later_repurchase and item_category in {
        "BOOTS",
        "BOOTS_UPGRADE",
        "COMPLETED_MAJOR",
        "INTERMEDIATE",
    }:
        classification = "LIKELY_REAL_REMOVAL"
        evidence.append(
            "item was held, ignored by production, and later reacquired"
        )
    elif (
        not previous_acquisitions
        and not acquisitions
        and final_count == 0
        and not magical_footwear_context
    ):
        classification = "CONFIRMED_OR_STRONG_TEMPORARY_STATE"
        evidence.append(
            "item has no observed acquisition/restoration and is absent from effective final inventory"
        )
    elif is_viego:
        classification = "UNRESOLVED_TEMPORARY_POSSIBLE"
        evidence.append(
            "Viego may expose copied inventory, but no possession window is observable here"
        )

    if held_before:
        evidence.append("item was reconstructed as held before destroy")
    else:
        evidence.append("item was not reconstructed as held before destroy")

    if retained_after:
        evidence.append("current production retains item after destroy")

    if magical_footwear_context:
        evidence.append(
            "Magical Footwear rune 8304 confirms item 2422 can be granted without purchase"
        )

    if final_count:
        evidence.append(
            "item appears in effective final inventory, used only as context"
        )

    root_cause = _classify_destroyed_root_cause(
        match=match,
        row=row,
        catalog=catalog,
        classification=classification,
        transformation_purchase=transformation_purchase,
        later_replacement=later_replacement,
        held_before=held_before,
        retained_after=retained_after,
        is_viego=is_viego,
        magical_footwear_context=magical_footwear_context,
    )

    return {
        "match_id": match["match_id"],
        "champion": match["champion"],
        "timestamp": timestamp,
        "time": row["time"],
        "item_id": item_id,
        "item_name": row.get("item_name"),
        "item_category": item_category,
        "classification": classification,
        "root_cause": root_cause,
        "classification_evidence": evidence,
        "warning_codes": sorted(codes),
        "held_before": held_before,
        "retained_after": retained_after,
        "inventory_before": list(before_ids),
        "inventory_before_names": list(
            row.get("inventory_before_slot_items") or []
        ),
        "inventory_after": list(after_ids),
        "inventory_after_names": list(
            row.get("inventory_after_slot_items") or []
        ),
        "slot_count_before": row.get("slot_count_before"),
        "slot_count_after": row.get("slot_count_after"),
        "same_timestamp_purchases": [
            _summarize_transaction(transaction)
            for transaction in same_purchases
        ],
        "same_timestamp_sells": [
            _summarize_transaction(transaction)
            for transaction in same_sells
        ],
        "same_timestamp_undos": [
            _summarize_transaction(transaction)
            for transaction in same_undos
        ],
        "previous_item_transaction": _summarize_transaction(
            previous_item_transactions[-1]
            if previous_item_transactions
            else None
        ),
        "next_item_transaction": _summarize_transaction(
            later_item_transactions[0]
            if later_item_transactions
            else None
        ),
        "later_repurchase": _summarize_transaction(later_repurchase),
        "transformation_purchase": _summarize_transaction(
            transformation_purchase
        ),
        "later_unobserved_replacement": _summarize_transaction(
            later_replacement
        ),
        "final_riot_inventory": dict(
            match["final_validation"]["riot_final_counter"]
        ),
        "final_reconstructed_inventory": dict(
            match["final_validation"]["reconstructed_final_counter"]
        ),
        "final_effective_inventory": dict(final_counter),
        "viego_possible": is_viego,
    }


def _classify_unexplained_destroyed(match, row):
    return _destroyed_evidence_context(match, row)["classification"]


def _summarize_destroyed_audit(matches):
    confident_interpretations = {
        "COMPONENT_CONSUMED_BY_PURCHASE",
        "REMOVED_FROM_HELD_INVENTORY",
        "TRINKET_USE_EVENT_IGNORED_FOR_INVENTORY",
    }
    total_destroyed = 0
    confidently_explained = 0
    remaining = []
    classification_counts = Counter()
    root_cause_counts = Counter()
    missed_transformation_root_cause_counts = Counter()
    champion_counts = Counter()
    item_counts = Counter()
    held_classification_counts = Counter()
    not_held_classification_counts = Counter()
    viego_classification_counts = Counter()
    non_viego_classification_counts = Counter()
    games = set()
    held_ignored = 0
    not_held_ignored = 0
    final_safe = 0
    clear_permanent_removal_evidence = 0
    missed_transformation_evidence = 0
    retained_after_destroy = 0

    for match in matches:
        for row in match["transactions"]:
            if row.get("event_type") != "ITEM_DESTROYED":
                continue

            total_destroyed += 1
            interpretation = row.get("destroyed_interpretation")

            if interpretation in confident_interpretations:
                confidently_explained += 1
                continue

            context = _destroyed_evidence_context(match, row)
            classification = context["classification"]
            classification_counts[classification] += 1
            root_cause_counts[context["root_cause"]] += 1
            if classification == "MISSED_TRANSFORMATION":
                missed_transformation_root_cause_counts[
                    context["root_cause"]
                ] += 1
            champion_counts[match["champion"]] += 1
            item_counts[(row.get("item_id"), row.get("item_name"))] += 1
            games.add(match["match_id"])

            codes = _warning_codes(row)
            if context["held_before"]:
                held_ignored += 1
                held_classification_counts[classification] += 1
            else:
                not_held_ignored += 1
                not_held_classification_counts[classification] += 1

            if context["viego_possible"]:
                viego_classification_counts[classification] += 1
            else:
                non_viego_classification_counts[classification] += 1

            if match["final_validation"]["status"] in EXACT_FINAL_STATUSES:
                final_safe += 1

            if classification == "LIKELY_REAL_REMOVAL":
                clear_permanent_removal_evidence += 1
            if classification == "MISSED_TRANSFORMATION":
                missed_transformation_evidence += 1
            if context["retained_after"]:
                retained_after_destroy += 1

            remaining.append(context)

    return {
        "total_destroyed": total_destroyed,
        "confidently_explained": confidently_explained,
        "remaining_unexplained": len(remaining),
        "games_affected": len(games),
        "classification_counts": classification_counts,
        "root_cause_counts": root_cause_counts,
        "missed_transformation_root_cause_counts": (
            missed_transformation_root_cause_counts
        ),
        "champion_counts": champion_counts,
        "item_counts": item_counts,
        "held_classification_counts": held_classification_counts,
        "not_held_classification_counts": not_held_classification_counts,
        "viego_classification_counts": viego_classification_counts,
        "non_viego_classification_counts": non_viego_classification_counts,
        "held_ignored": held_ignored,
        "not_held_ignored": not_held_ignored,
        "final_safe": final_safe,
        "clear_permanent_removal_evidence": clear_permanent_removal_evidence,
        "missed_transformation_evidence": missed_transformation_evidence,
        "retained_after_destroy": retained_after_destroy,
        "records": remaining,
        "samples": remaining[:12],
    }


def _summarize_viego_audit(matches):
    viego_matches = [
        match
        for match in matches
        if str(match.get("champion", "")).lower() == "viego"
    ]
    destroyed_count = 0
    ambiguous_count = 0
    item_counts = Counter()
    permanent_build_item_events = 0
    classification_counts = Counter()
    held_ambiguous_count = 0

    for match in viego_matches:
        final_counter = match["final_validation"]["riot_final_counter"]

        for row in match["transactions"]:
            if row.get("event_type") != "ITEM_DESTROYED":
                continue

            destroyed_count += 1
            item_counts[(row.get("item_id"), row.get("item_name"))] += 1

            if row.get("reconstruction_status") == "AMBIGUOUS":
                ambiguous_count += 1
                context = _destroyed_evidence_context(match, row)
                classification_counts[context["classification"]] += 1
                if context["held_before"]:
                    held_ambiguous_count += 1

            if row.get("item_id") in final_counter:
                permanent_build_item_events += 1

    return {
        "games": len(viego_matches),
        "destroyed_count": destroyed_count,
        "ambiguous_count": ambiguous_count,
        "item_counts": item_counts,
        "permanent_build_item_events": permanent_build_item_events,
        "classification_counts": classification_counts,
        "held_ambiguous_count": held_ambiguous_count,
        "limitation": "TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE",
    }


def _summarize_sell_warning_audit(matches):
    current_warnings = []
    restored_component_sells = []

    for match in matches:
        transactions = match["transactions"]

        for index, row in enumerate(transactions):
            codes = _warning_codes(row)
            if "SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD" in codes:
                previous_transactions = _previous_item_transactions(
                    match,
                    row,
                )
                current_warnings.append(
                    {
                        "match_id": match["match_id"],
                        "champion": match["champion"],
                        "time": row["time"],
                        "item_id": row.get("item_id"),
                        "item_name": row.get("item_name"),
                        "inventory_before": row.get(
                            "inventory_before_slot_item_ids",
                            [],
                        ),
                        "previous_item_transaction": (
                            _summarize_transaction(
                                previous_transactions[-1]
                            )
                            if previous_transactions
                            else None
                        ),
                    }
                )

            if row.get("event_type") != "ITEM_UNDO":
                continue

            restored_components = row.get("undo_restored_components") or []
            if not restored_components:
                continue

            for component_id in restored_components:
                later_sell = None
                for later in transactions[index + 1:]:
                    if (
                        later.get("event_type") == "ITEM_SOLD"
                        and later.get("item_id") == component_id
                    ):
                        later_sell = later
                        break

                if later_sell:
                    restored_component_sells.append(
                        {
                            "match_id": match["match_id"],
                            "champion": match["champion"],
                            "undo_time": row["time"],
                            "undo_item_id": row.get("item_id"),
                            "undo_item_name": row.get("item_name"),
                            "restored_component_id": component_id,
                            "restored_component_name": (
                                _catalog_for_match(match).name(
                                    component_id
                                )
                            ),
                            "sell_time": later_sell["time"],
                            "sell_warning_codes": sorted(
                                _warning_codes(later_sell)
                            ),
                        }
                    )

    return {
        "current_warning_count": len(current_warnings),
        "current_warning_samples": current_warnings[:5],
        "restored_component_sell_count": len(restored_component_sells),
        "restored_component_sell_samples": restored_component_sells[:5],
    }


def _relevant_prior_ambiguous_component_destroy(
    match,
    purchase_index,
    component_id,
):
    transactions = match["transactions"]
    purchase = transactions[purchase_index]
    purchase_timestamp = purchase.get("timestamp") or 0

    for previous in reversed(transactions[:purchase_index]):
        if (previous.get("timestamp") or 0) >= purchase_timestamp:
            continue

        if _is_acquisition_transaction(previous, component_id):
            return None

        if (
            previous.get("event_type") in {"ITEM_SOLD", "ITEM_UNDO"}
            and _transaction_mentions_item(previous, component_id)
        ):
            return None

        if (
            previous.get("event_type") == "ITEM_DESTROYED"
            and previous.get("item_id") == component_id
            and previous.get("reconstruction_status") == "AMBIGUOUS"
        ):
            context = _destroyed_evidence_context(match, previous)
            if context["retained_after"]:
                return previous, context
            return None

    return None


def _summarize_intermediate_contradictions(matches):
    counts = Counter()
    affected_matches = defaultdict(set)
    samples = defaultdict(list)

    for match in matches:
        transactions = match["transactions"]

        for row in transactions:
            codes = _warning_codes(row)

            if "INVENTORY_CAPACITY_EXCEEDED" in codes:
                counts["slot_capacity_exceeded"] += 1
                affected_matches["slot_capacity_exceeded"].add(
                    match["match_id"]
                )

            if "SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD" in codes:
                counts["sell_item_not_held"] += 1
                affected_matches["sell_item_not_held"].add(
                    match["match_id"]
                )

            if any(code.startswith("UNDO_") for code in codes):
                counts["contradictory_undo"] += 1
                affected_matches["contradictory_undo"].add(
                    match["match_id"]
                )

            major_counts = Counter(row.get("major_item_ids") or [])
            impossible_major_duplicates = [
                item_id
                for item_id, count in major_counts.items()
                if count > 1
                and not _catalog_for_match(match).is_stackable_for_slots(
                    item_id
                )
            ]
            if impossible_major_duplicates:
                counts["duplicate_completed_major_state"] += 1
                affected_matches["duplicate_completed_major_state"].add(
                    match["match_id"]
                )

        for index, row in enumerate(transactions):
            if row.get("event_type") != "ITEM_PURCHASED":
                continue

            for component_id in row.get("components_consumed") or []:
                previous_ambiguous = (
                    _relevant_prior_ambiguous_component_destroy(
                        match,
                        index,
                        component_id,
                    )
                )
                if previous_ambiguous:
                    destroyed, context = previous_ambiguous
                    counts[
                        "component_consumed_after_ignored_destroy"
                    ] += 1
                    affected_matches[
                        "component_consumed_after_ignored_destroy"
                    ].add(match["match_id"])
                    if len(
                        samples["component_consumed_after_ignored_destroy"]
                    ) < 12:
                        samples[
                            "component_consumed_after_ignored_destroy"
                        ].append(
                            {
                                "match_id": match["match_id"],
                                "champion": match["champion"],
                                "destroy_time": destroyed["time"],
                                "purchase_time": row["time"],
                                "component_id": component_id,
                                "component_name": _catalog_for_match(
                                    match
                                ).name(component_id),
                                "purchase_item_id": row.get("item_id"),
                                "purchase_item_name": row.get(
                                    "item_name"
                                ),
                                "destroy_classification": context[
                                    "classification"
                                ],
                                "root_cause": context["root_cause"],
                                "gap_seconds": round(
                                    (
                                        (row.get("timestamp") or 0)
                                        - (
                                            destroyed.get("timestamp")
                                            or 0
                                        )
                                    )
                                    / 1000,
                                    1,
                                ),
                            }
                        )

        for row in transactions:
            if (
                row.get("event_type") != "ITEM_DESTROYED"
                or row.get("reconstruction_status") != "AMBIGUOUS"
            ):
                continue

            context = _destroyed_evidence_context(match, row)
            if (
                context["classification"] == "MISSED_TRANSFORMATION"
                and context["retained_after"]
            ):
                counts["retained_after_missed_transformation"] += 1
                affected_matches[
                    "retained_after_missed_transformation"
                ].add(match["match_id"])
                if len(
                    samples["retained_after_missed_transformation"]
                ) < 12:
                    samples[
                        "retained_after_missed_transformation"
                    ].append(
                        {
                            "match_id": match["match_id"],
                            "champion": match["champion"],
                            "time": row["time"],
                            "item_id": row.get("item_id"),
                            "item_name": row.get("item_name"),
                            "root_cause": context["root_cause"],
                            "later_unobserved_replacement": context[
                                "later_unobserved_replacement"
                            ],
                        }
                    )
            if (
                context["classification"] == "LIKELY_REAL_REMOVAL"
                and context["retained_after"]
            ):
                counts["retained_after_likely_real_removal"] += 1
                affected_matches[
                    "retained_after_likely_real_removal"
                ].add(match["match_id"])

    return {
        "counts": counts,
        "affected_matches": {
            key: sorted(values)
            for key, values in affected_matches.items()
        },
        "samples": dict(samples),
    }


def _inventory_reliability_rank(status):
    ranks = {
        INVENTORY_RELIABLE: 0,
        INVENTORY_AMBIGUOUS_TEMPORARY_STATE: 1,
        INVENTORY_UNRESOLVED_TRANSFORMATION: 2,
    }
    return ranks.get(status, 0)


def _interval_end_timestamp_for_destroy(match, row, context):
    item_id = row.get("item_id")
    start = row.get("timestamp") or 0
    candidates = []

    replacement = context.get("later_unobserved_replacement")
    if replacement:
        candidates.append(replacement.get("timestamp") or 0)

    for transaction in match["transactions"]:
        timestamp = transaction.get("timestamp") or 0
        if timestamp <= start:
            continue

        if _transaction_mentions_item(transaction, item_id):
            candidates.append(timestamp)

        if (
            transaction.get("event_type") == "ITEM_PURCHASED"
            and item_id in (transaction.get("components_consumed") or [])
        ):
            candidates.append(timestamp)

    valid_candidates = [
        timestamp
        for timestamp in candidates
        if timestamp > start
    ]
    if valid_candidates:
        return min(valid_candidates)

    duration_ms = int((match.get("game_duration") or 0) * 1000)
    if duration_ms > start:
        return duration_ms

    return None


def _add_reliability_interval(
    intervals,
    *,
    match,
    status,
    reason,
    root_cause,
    item_id,
    item_name,
    start_timestamp,
    end_timestamp,
    source_event_time,
    resolution_time,
):
    if end_timestamp is not None and end_timestamp <= start_timestamp:
        return

    interval = {
        "match_id": match["match_id"],
        "champion": match["champion"],
        "status": status,
        "reason": reason,
        "root_cause": root_cause,
        "item_id": item_id,
        "item_name": item_name,
        "start_timestamp": start_timestamp,
        "start_time": _format_time(start_timestamp),
        "end_timestamp": end_timestamp,
        "end_time": (
            _format_time(end_timestamp)
            if end_timestamp is not None
            else "END_OF_GAME_OR_UNKNOWN"
        ),
        "source_event_time": source_event_time,
        "resolution_time": resolution_time,
    }
    intervals.append(interval)


def _build_inventory_reliability_intervals(match):
    intervals = []

    for row in match["transactions"]:
        if (
            row.get("event_type") != "ITEM_DESTROYED"
            or row.get("reconstruction_status") != "AMBIGUOUS"
        ):
            continue

        context = _destroyed_evidence_context(match, row)
        root_cause = context["root_cause"]

        if (
            context["classification"] == "MISSED_TRANSFORMATION"
            and root_cause == "TEMPORARY_MECHANIC"
            and row.get("item_id") == SLIGHTLY_MAGICAL_BOOTS_ITEM_ID
            and _has_perk(match, MAGICAL_FOOTWEAR_PERK_ID)
        ):
            timing = _derive_magical_footwear_timestamp(
                match.get("takedown_timestamps")
            )
            start_timestamp = timing.get("derived_timestamp")
            end_timestamp = row.get("timestamp") or 0
            if start_timestamp is not None and start_timestamp < end_timestamp:
                _add_reliability_interval(
                    intervals,
                    match=match,
                    status=INVENTORY_UNRESOLVED_TRANSFORMATION,
                    reason=(
                        "DERIVED_RUNE_GRANT_NOT_MATERIALIZED_AS_RIOT_EVENT"
                    ),
                    root_cause=root_cause,
                    item_id=row.get("item_id"),
                    item_name=row.get("item_name"),
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    source_event_time=row["time"],
                    resolution_time=row["time"],
                )

        if (
            context["classification"] == "MISSED_TRANSFORMATION"
            and context["retained_after"]
        ):
            status = INVENTORY_UNRESOLVED_TRANSFORMATION
            if root_cause == "VIEGO_TEMPORARY_POSSIBLE":
                status = INVENTORY_AMBIGUOUS_TEMPORARY_STATE

            end_timestamp = _interval_end_timestamp_for_destroy(
                match,
                row,
                context,
            )
            _add_reliability_interval(
                intervals,
                match=match,
                status=status,
                reason="RETAINED_AFTER_MISSED_TRANSFORMATION",
                root_cause=root_cause,
                item_id=row.get("item_id"),
                item_name=row.get("item_name"),
                start_timestamp=row.get("timestamp") or 0,
                end_timestamp=end_timestamp,
                source_event_time=row["time"],
                resolution_time=(
                    _format_time(end_timestamp)
                    if end_timestamp is not None
                    else "END_OF_GAME_OR_UNKNOWN"
                ),
            )

        elif (
            context["classification"] == "UNRESOLVED_TEMPORARY_POSSIBLE"
            and context["retained_after"]
        ):
            end_timestamp = _interval_end_timestamp_for_destroy(
                match,
                row,
                context,
            )
            _add_reliability_interval(
                intervals,
                match=match,
                status=INVENTORY_AMBIGUOUS_TEMPORARY_STATE,
                reason="RETAINED_TEMPORARY_STATE_POSSIBLE",
                root_cause=root_cause,
                item_id=row.get("item_id"),
                item_name=row.get("item_name"),
                start_timestamp=row.get("timestamp") or 0,
                end_timestamp=end_timestamp,
                source_event_time=row["time"],
                resolution_time=(
                    _format_time(end_timestamp)
                    if end_timestamp is not None
                    else "END_OF_GAME_OR_UNKNOWN"
                ),
            )

    for index, row in enumerate(match["transactions"]):
        if row.get("event_type") != "ITEM_PURCHASED":
            continue

        for component_id in row.get("components_consumed") or []:
            previous = _relevant_prior_ambiguous_component_destroy(
                match,
                index,
                component_id,
            )
            if not previous:
                continue

            destroyed, context = previous
            status = INVENTORY_UNRESOLVED_TRANSFORMATION
            if context["root_cause"] == "VIEGO_TEMPORARY_POSSIBLE":
                status = INVENTORY_AMBIGUOUS_TEMPORARY_STATE

            _add_reliability_interval(
                intervals,
                match=match,
                status=status,
                reason="COMPONENT_CONSUMED_AFTER_IGNORED_DESTROY",
                root_cause=context["root_cause"],
                item_id=component_id,
                item_name=_catalog_for_match(match).name(component_id),
                start_timestamp=destroyed.get("timestamp") or 0,
                end_timestamp=row.get("timestamp") or 0,
                source_event_time=destroyed["time"],
                resolution_time=row["time"],
            )

    deduped_by_key = {}
    for interval in intervals:
        key = (
            interval["status"],
            interval["root_cause"],
            interval["item_id"],
            interval["start_timestamp"],
            interval["end_timestamp"],
        )
        if key in deduped_by_key:
            existing = deduped_by_key[key]
            reasons = set(existing.get("reasons") or [existing["reason"]])
            reasons.add(interval["reason"])
            existing["reasons"] = sorted(reasons)
            existing["reason"] = " + ".join(existing["reasons"])
            continue

        interval["reasons"] = [interval["reason"]]
        deduped_by_key[key] = interval

    deduped = list(deduped_by_key.values())

    deduped.sort(
        key=lambda interval: (
            interval["start_timestamp"],
            interval["end_timestamp"] or 0,
            interval["item_id"] or 0,
        )
    )
    return deduped


def _annotate_inventory_reliability(match):
    intervals = _build_inventory_reliability_intervals(match)

    for row in match["transactions"]:
        timestamp = row.get("timestamp") or 0
        active = [
            interval
            for interval in intervals
            if interval["start_timestamp"] <= timestamp
            and (
                interval["end_timestamp"] is None
                or timestamp < interval["end_timestamp"]
            )
        ]
        status = INVENTORY_RELIABLE
        if active:
            status = max(
                (interval["status"] for interval in active),
                key=_inventory_reliability_rank,
            )

        row["inventory_reliability_after"] = status
        row["inventory_reliability_reasons"] = sorted(
            {
                reason
                for interval in active
                for reason in (
                    interval.get("reasons") or [interval["reason"]]
                )
                if interval["status"] == status
            }
        )

    match["inventory_reliability"] = {
        "intervals": intervals,
        "interval_counts": Counter(
            interval["status"]
            for interval in intervals
        ),
        "reason_counts": Counter(
            reason
            for interval in intervals
            for reason in (interval.get("reasons") or [interval["reason"]])
        ),
        "root_cause_counts": Counter(
            interval["root_cause"]
            for interval in intervals
        ),
        "affected_transaction_counts": Counter(
            row.get("inventory_reliability_after", INVENTORY_RELIABLE)
            for row in match["transactions"]
        ),
    }


def _summarize_inventory_reliability(matches):
    interval_counts = Counter()
    reason_counts = Counter()
    root_cause_counts = Counter()
    affected_transaction_counts = Counter()
    affected_matches = defaultdict(set)
    samples = []

    for match in matches:
        reliability = match.get("inventory_reliability") or {}
        interval_counts.update(reliability.get("interval_counts") or {})
        reason_counts.update(reliability.get("reason_counts") or {})
        root_cause_counts.update(reliability.get("root_cause_counts") or {})
        affected_transaction_counts.update(
            reliability.get("affected_transaction_counts") or {}
        )

        for interval in reliability.get("intervals") or []:
            affected_matches[interval["status"]].add(match["match_id"])
            if len(samples) < 12:
                samples.append(interval)

    return {
        "interval_counts": interval_counts,
        "reason_counts": reason_counts,
        "root_cause_counts": root_cause_counts,
        "affected_transaction_counts": affected_transaction_counts,
        "affected_matches": {
            key: sorted(values)
            for key, values in affected_matches.items()
        },
        "samples": samples,
    }


def _summarize_warning_buckets(warning_counts):
    bucket_by_code = {
        "VIEGO_TEMPORARY_ITEM_OR_POSSESSION_POSSIBLE": (
            "unresolved_temporary_possible"
        ),
        "DESTROYED_NORMAL_NOT_HELD_IGNORED_AS_AMBIGUOUS": (
            "requires_evidence_audit"
        ),
        "DESTROYED_NORMAL_HELD_IGNORED_AS_AMBIGUOUS": (
            "requires_evidence_audit"
        ),
        "JUNGLE_ITEM_DESTROYED_NOT_HELD": (
            "harmless_riot_representation_limitation"
        ),
        "CONSUMABLE_DESTROYED_NOT_HELD": (
            "harmless_riot_representation_limitation"
        ),
        "SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD": "unresolved",
        "INVENTORY_CAPACITY_EXCEEDED": "genuine_reconstruction_bug",
        "UNKNOWN_ITEM_METADATA": "unresolved",
        "UNDO_BEFORE_ITEM_NOT_RECONSTRUCTED_AS_HELD": "unresolved",
        "UNDO_WITHOUT_BEFORE_OR_AFTER_ITEM": "unresolved",
    }
    buckets = Counter()

    for code, count in warning_counts.items():
        bucket = bucket_by_code.get(code, "unresolved")
        buckets[bucket] += count

    return buckets


def _summarize_major_milestones(matches):
    excluded_categories = {
        "CONSUMABLE",
        "TRINKET",
        "JUNGLE_ITEM",
        "BOOTS",
        "BOOTS_UPGRADE",
        "SPECIAL",
        "UNKNOWN",
    }
    total = 0
    unusual = []

    for match in matches:
        catalog = _catalog_for_match(match)
        for milestone in match["milestones"]["completed_major_items"]:
            total += 1
            category = catalog.category(milestone["item_id"])
            if category in excluded_categories:
                unusual.append(
                    {
                        "match_id": match["match_id"],
                        "champion": match["champion"],
                        "item_id": milestone["item_id"],
                        "item_name": milestone["item_name"],
                        "category": category,
                        "time": milestone["time"],
                    }
                )

    return {
        "completed_major_milestones": total,
        "unusual_count": len(unusual),
        "unusual_samples": unusual[:10],
    }


def _format_counts(counter):
    if not counter:
        return "none"

    return ", ".join(
        f"{key}: {value}"
        for key, value in sorted(
            counter.items(),
            key=lambda item: (-item[1], str(item[0])),
        )
    )


def _format_item_counts(counter, limit=8):
    if not counter:
        return "none"

    parts = []
    for (item_id, item_name), count in sorted(
        counter.items(),
        key=lambda item: (-item[1], str(item[0])),
    )[:limit]:
        parts.append(f"{item_name} ({item_id}): {count}")

    return ", ".join(parts)


def _catalog_for_match(match):
    if match.get("catalog"):
        return match["catalog"]

    raw_items = {}
    for transaction in match["transactions"]:
        item_id = transaction.get("item_id")
        if item_id in (None, 0):
            continue

        raw_items[str(item_id)] = {
            "name": transaction.get("item_name"),
            "gold": {
                "total": transaction.get("item_cost"),
                "base": transaction.get("item_base_cost"),
                "purchasable": transaction.get("item_purchasable"),
            },
            "tags": transaction.get("item_tags") or [],
            "from": transaction.get("item_from") or [],
            "into": transaction.get("item_into") or [],
        }

    for item_id in match["final_validation"]["riot_final_counter"]:
        raw_items.setdefault(str(item_id), {"name": f"ITEM_{item_id}"})
    for item_id in match["final_validation"]["reconstructed_final_counter"]:
        raw_items.setdefault(str(item_id), {"name": f"ITEM_{item_id}"})

    return ItemCatalog.from_raw_items(
        raw_items,
        version=match.get("ddragon_version"),
    )


def render_itemization_audit(history, mismatch_limit=12):
    summary = history["summary"]
    lines = [
        "BUILD / ITEMIZATION ANALYZER V22 - PHASE 1D AUDIT",
        "",
        "Scope: factual Riot item-event reconstruction only. No build",
        "recommendation, item-quality label, or Win/Loss item judgment is",
        "computed here.",
        "",
        "Validation definitions:",
        "- EXACT: observed item transactions reconstruct Riot final inventory.",
        "- EXACT_WITH_EXPLAINED_GRANT: final difference is explained by a confirmed non-purchase grant.",
        "- PARTIAL: normal inventory matches or there is still meaningful overlap.",
        "- MISMATCH: material disagreement remains.",
        "- UNKNOWN: final reference cannot be exploited.",
        "",
        f"Games processed: {summary['games_processed']}",
        f"Item events processed: {summary['item_events_processed']}",
        f"Event counts: {_format_counts(summary['event_type_counts'])}",
        f"Final validation counts: {_format_counts(summary['status_counts'])}",
    ]

    exact_rate = summary["exact_match_rate"]
    if exact_rate is None:
        lines.append("Observed exact final inventory rate: N/A")
    else:
        lines.append(f"Observed exact final inventory rate: {exact_rate:.1%}")

    exact_or_explained_rate = summary["exact_or_explained_rate"]
    if exact_or_explained_rate is None:
        lines.append("Observed or explained final inventory rate: N/A")
    else:
        lines.append(
            "Observed or explained final inventory rate: "
            f"{exact_or_explained_rate:.1%}"
        )

    lines.extend(
        [
            f"Invariant / reconstruction warnings: {_format_counts(summary['warning_counts'])}",
            f"Warning buckets: {_format_counts(summary['warning_buckets'])}",
            f"Mismatch causes: {_format_counts(summary['cause_counts'])}",
            f"Special item cases: {_format_counts(summary['special_case_counts'])}",
            f"Non-purchase grant matches: {summary['grant_match_count']}",
            f"Grant sources: {_format_counts(summary['grant_source_counts'])}",
            f"Grant types: {_format_counts(summary['grant_type_counts'])}",
            f"Grant derived timestamp states: {_format_counts(summary['grant_derived_status_counts'])}",
            "",
            "ITEM_DESTROYED audit:",
            f"- total ITEM_DESTROYED: {summary['destroyed_audit']['total_destroyed']}",
            f"- confidently explained: {summary['destroyed_audit']['confidently_explained']}",
            f"- remaining audit-only ambiguous/unexplained: {summary['destroyed_audit']['remaining_unexplained']}",
            f"- games affected by remaining destroyed audit: {summary['destroyed_audit']['games_affected']}",
            f"- audit-only classifications: {_format_counts(summary['destroyed_audit']['classification_counts'])}",
            f"- audit root causes: {_format_counts(summary['destroyed_audit']['root_cause_counts'])}",
            f"- MISSED_TRANSFORMATION root causes: {_format_counts(summary['destroyed_audit']['missed_transformation_root_cause_counts'])}",
            f"- held before destroy: {summary['destroyed_audit']['held_ignored']} | not held before destroy: {summary['destroyed_audit']['not_held_ignored']}",
            f"- held classifications: {_format_counts(summary['destroyed_audit']['held_classification_counts'])}",
            f"- not-held classifications: {_format_counts(summary['destroyed_audit']['not_held_classification_counts'])}",
            f"- Viego classifications: {_format_counts(summary['destroyed_audit']['viego_classification_counts'])}",
            f"- non-Viego classifications: {_format_counts(summary['destroyed_audit']['non_viego_classification_counts'])}",
            f"- clear permanent-removal evidence: {summary['destroyed_audit']['clear_permanent_removal_evidence']}",
            f"- missed transformation evidence: {summary['destroyed_audit']['missed_transformation_evidence']}",
            f"- retained after ambiguous destroy: {summary['destroyed_audit']['retained_after_destroy']}",
            f"- top remaining destroyed items: {_format_item_counts(summary['destroyed_audit']['item_counts'])}",
            "",
            "Viego ITEM_DESTROYED audit:",
            f"- Viego games: {summary['viego_audit']['games']}",
            f"- Viego ITEM_DESTROYED events: {summary['viego_audit']['destroyed_count']}",
            f"- Viego ambiguous destroyed events: {summary['viego_audit']['ambiguous_count']}",
            f"- Viego held ambiguous destroyed events: {summary['viego_audit']['held_ambiguous_count']}",
            f"- Viego evidence classifications: {_format_counts(summary['viego_audit']['classification_counts'])}",
            f"- Viego permanent-build item destroyed events ignored as ambiguous: {summary['viego_audit']['permanent_build_item_events']}",
            f"- limitation: {summary['viego_audit']['limitation']}",
            f"- top Viego destroyed items: {_format_item_counts(summary['viego_audit']['item_counts'])}",
            "",
            "SELL warning audit:",
            f"- current SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD warnings: {summary['sell_warning_audit']['current_warning_count']}",
            f"- restored-component later sells: {summary['sell_warning_audit']['restored_component_sell_count']}",
            "",
            "Intermediate contradiction audit:",
            f"- counts: {_format_counts(summary['intermediate_contradictions']['counts'])}",
            "",
            "Inventory reliability audit:",
            f"- interval counts: {_format_counts(summary['inventory_reliability_audit']['interval_counts'])}",
            f"- reason counts: {_format_counts(summary['inventory_reliability_audit']['reason_counts'])}",
            f"- root-cause counts: {_format_counts(summary['inventory_reliability_audit']['root_cause_counts'])}",
            f"- affected transaction states: {_format_counts(summary['inventory_reliability_audit']['affected_transaction_counts'])}",
            "",
            "Major item milestone audit:",
            f"- completed-major milestones: {summary['major_milestone_audit']['completed_major_milestones']}",
            f"- unusual excluded-category milestones: {summary['major_milestone_audit']['unusual_count']}",
            "",
        ]
    )

    if summary["sell_warning_audit"]["restored_component_sell_samples"]:
        lines.append("- restored-component sell samples:")
        for sample in summary["sell_warning_audit"][
            "restored_component_sell_samples"
        ]:
            lines.append(
                (
                    f"  {sample['match_id']} | {sample['champion']} | "
                    f"undo {sample['undo_item_name']} at "
                    f"{sample['undo_time']} restored "
                    f"{sample['restored_component_name']} sold at "
                    f"{sample['sell_time']} | sell warnings: "
                    f"{sample['sell_warning_codes'] or 'none'}"
                )
            )

    contradiction_samples = summary["intermediate_contradictions"].get(
        "samples",
        {},
    )
    if contradiction_samples:
        lines.extend(
            [
                "",
                "Focused intermediate samples:",
            ]
        )
        for kind in (
            "retained_after_missed_transformation",
            "component_consumed_after_ignored_destroy",
        ):
            for sample in contradiction_samples.get(kind, [])[:6]:
                lines.append(f"- {kind}: {sample}")

    focused_records = [
        record
        for record in summary["destroyed_audit"]["records"]
        if record["classification"]
        in {
            "MISSED_TRANSFORMATION",
            "UNRESOLVED",
            "CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION",
        }
        or record["root_cause"]
        in {
            "REAL_MISSED_TRANSFORMATION",
            "EVENT_ORDER_DUPLICATE",
            "ALREADY_HANDLED_BY_PURCHASE_COMPONENT_CONSUMPTION",
            "VIEGO_TEMPORARY_POSSIBLE",
        }
    ]
    if focused_records:
        lines.extend(
            [
                "",
                "Focused destroyed evidence samples:",
            ]
        )
        for sample in focused_records[:12]:
            evidence = "; ".join(
                sample.get("classification_evidence") or []
            )
            lines.append(
                (
                    f"- {sample['match_id']} | {sample['champion']} | "
                    f"{sample['time']} | {sample['item_name']} "
                    f"({sample['item_id']}) | "
                    f"{sample['classification']} | root_cause="
                    f"{sample['root_cause']} | held_before="
                    f"{sample['held_before']} | retained_after="
                    f"{sample['retained_after']} | "
                    f"before={sample['inventory_before']} | "
                    f"after={sample['inventory_after']} | "
                    f"evidence={evidence}"
                )
            )

    if summary["inventory_reliability_audit"]["samples"]:
        lines.extend(
            [
                "",
                "Inventory reliability interval samples:",
            ]
        )
        for interval in summary["inventory_reliability_audit"]["samples"]:
            lines.append(
                (
                    f"- {interval['match_id']} | {interval['champion']} | "
                    f"{interval['item_name']} ({interval['item_id']}) | "
                    f"{interval['status']} | {interval['reason']} | "
                    f"root_cause={interval['root_cause']} | "
                    f"{interval['start_time']}->{interval['end_time']}"
                )
            )

    lines.extend(
        [
            "",
            "Champion breakdown:",
        ]
    )

    for champion, counts in sorted(
        summary["champion_status"].items(),
        key=lambda item: (item[0] or ""),
    ):
        lines.append(f"- {champion}: {_format_counts(counts)}")

    non_exact = [
        match
        for match in history["matches"]
        if match["final_validation"]["status"] not in EXACT_FINAL_STATUSES
    ]

    lines.extend(
        [
            "",
            f"Non-exact-or-explained games inspected: {len(non_exact)}",
        ]
    )

    for match in non_exact[:mismatch_limit]:
        catalog = _catalog_for_match(match)
        validation = match["final_validation"]
        lines.extend(
            [
                (
                    f"- {match['match_id']} | {match['champion']} | "
                    f"{validation['status']} | causes: "
                    f"{', '.join(validation['causes']) or 'none'}"
                ),
                (
                    "  reconstructed: "
                    + _format_counter(
                        validation["reconstructed_final_counter"],
                        catalog,
                    )
                    + " | trinket "
                    + catalog.name(validation["reconstructed_trinket"])
                ),
                (
                    "  Riot final: "
                    + _format_counter(
                        validation["riot_final_counter"],
                        catalog,
                    )
                    + " | trinket "
                    + catalog.name(validation["riot_trinket"])
                ),
            ]
        )

        warning_codes = Counter(
            warning["code"]
            for warning in match["invariant_warnings"]
        )
        if warning_codes:
            lines.append(
                "  warning codes: "
                + _format_counts(warning_codes)
            )

    grant_matches = [
        match
        for match in history["matches"]
        if (
            match["final_validation"].get("explained_grants")
            or match["final_validation"].get("unexplained_grants")
        )
    ]

    lines.extend(
        [
            "",
            f"Non-purchase final grants inspected: {len(grant_matches)}",
        ]
    )

    for match in grant_matches[:mismatch_limit]:
        validation = match["final_validation"]
        for grant in (
            validation.get("explained_grants", [])
            + validation.get("unexplained_grants", [])
        ):
            lines.append(
                (
                    f"- {match['match_id']} | {match['champion']} | "
                    f"{grant['item_name']} ({grant['item_id']}) | "
                    f"source={grant['source']} | "
                    f"grant_type={grant['grant_type']} | "
                    f"observed={grant['observed_time']} | "
                    f"derived={grant['derived_time']} "
                    f"({grant['derived_status']})"
                )
            )

    if len(non_exact) > mismatch_limit:
        lines.append(
            f"- {len(non_exact) - mismatch_limit} additional non-EXACT games omitted from this console summary."
        )

    if history["load_warnings"]:
        lines.extend(
            [
                "",
                "Data Dragon load warnings:",
            ]
        )
        for warning in history["load_warnings"][:10]:
            lines.append(
                f"- {warning['match_id']}: {warning['warning']}"
            )

    return "\n".join(lines)


def _format_milestone(milestone):
    if not milestone:
        return "none"

    return (
        f"{milestone['time']} - "
        f"{milestone['item_name']} ({milestone['item_id']})"
    )


def _format_perk_ids(match):
    selections = match.get("perk_selections") or []
    if not selections:
        return "UNKNOWN"

    return ", ".join(
        str(selection.get("perk"))
        for selection in selections
    )


def render_match_itemization_report(history, match_id=TARGET_MATCH_ID):
    match = None

    for candidate in history["matches"]:
        if candidate["match_id"] == match_id:
            match = candidate
            break

    if not match:
        return f"No itemization reconstruction found for {match_id}."

    catalog = _catalog_for_match(match)
    validation = match["final_validation"]
    milestones = match["milestones"]
    lines = [
        f"ITEMIZATION TARGET MATCH AUDIT - {match_id}",
        (
            f"Champion: {match['champion']} | opponent: "
            f"{match.get('opponent_champion') or 'UNKNOWN'} | "
            f"result: {'WIN' if match['win'] else 'LOSS'}"
        ),
        f"Game version: {match['game_version']} | Data Dragon: {match['ddragon_version']}",
        f"Selected rune/perk IDs: {_format_perk_ids(match)}",
        f"Final validation: {validation['status']}",
        (
            "Riot final: "
            + _format_counter(validation["riot_final_counter"], catalog)
            + " | trinket "
            + catalog.name(validation["riot_trinket"])
        ),
        (
            "Reconstructed final: "
            + _format_counter(
                validation["reconstructed_final_counter"],
                catalog,
            )
            + " | trinket "
            + catalog.name(validation["reconstructed_trinket"])
        ),
        (
            "Effective reconstructed final including explained grants: "
            + _format_counter(
                validation["effective_reconstructed_final_counter"],
                catalog,
            )
            + " | trinket "
            + catalog.name(validation["reconstructed_trinket"])
        ),
        (
            "Inventory reliability intervals: "
            + _format_counts(
                match.get("inventory_reliability", {}).get(
                    "interval_counts",
                    Counter(),
                )
            )
        ),
    ]

    grants = (
        validation.get("explained_grants", [])
        + validation.get("unexplained_grants", [])
    )

    if grants:
        lines.extend(
            [
                "",
                "Non-purchase grant audit:",
            ]
        )

        for grant in grants:
            evidence = "; ".join(grant.get("evidence") or [])
            lines.append(
                (
                    f"- {grant['item_name']} ({grant['item_id']}) | "
                    f"source={grant['source']} | "
                    f"grant_type={grant['grant_type']} | "
                    f"purchase_event={grant['purchase_event']} | "
                    f"observed_timestamp={grant['observed_time']} | "
                    f"derived_timestamp={grant['derived_time']} "
                    f"({grant['derived_status']}) | "
                    f"confidence={grant['confidence']} | "
                    f"takedowns_used={grant['takedowns_used']} | "
                    f"evidence={evidence}"
                )
            )

            if grant.get("perk_selection"):
                lines.append(
                    f"  perk_selection={grant['perk_selection']}"
                )

    lines.extend(
        [
        "",
        "Milestones:",
        (
            "- first meaningful purchase: "
            + _format_milestone(
                milestones["first_meaningful_purchase"]
            )
        ),
        "- boots purchase: " + _format_milestone(milestones["boots_purchase"]),
        "- boots upgrade: " + _format_milestone(milestones["boots_upgrade"]),
        "- completed major items:",
        ]
    )

    if milestones["completed_major_items"]:
        for index, milestone in enumerate(
            milestones["completed_major_items"],
            start=1,
        ):
            lines.append(f"  {index}. {_format_milestone(milestone)}")
    else:
        lines.append("  none")

    lines.extend(
        [
            "",
            "Chronological transaction audit:",
        ]
    )

    for transaction in match["transactions"]:
        warnings = transaction["reconstruction_warnings"]
        warning_text = ""
        if warnings:
            warning_text = " | warnings: " + ", ".join(
                warning["code"]
                for warning in warnings
            )

        visit = transaction.get("shop_visit_id")
        visit_text = f"visit {visit}" if visit else "visit N/A"

        detail = ""
        if transaction["event_type"] == "ITEM_UNDO":
            detail = (
                f" before={transaction.get('undo_before_id')} "
                f"after={transaction.get('undo_after_id')}"
            )
        elif transaction.get("destroyed_interpretation"):
            detail = f" {transaction['destroyed_interpretation']}"

        lines.append(
            (
                f"- {transaction['time']} | {visit_text} | "
                f"frame {transaction.get('frame_index')} / event "
                f"{transaction.get('event_index')} | "
                f"{transaction['event_type']} | "
                f"{transaction['item_name']} ({transaction['item_id']}) | "
                f"{transaction['item_category']}{detail} | "
                f"inventory: {transaction['slot_items']} | "
                f"trinket: {transaction['trinket']} | "
                f"status: {transaction['reconstruction_status']}"
                f" | reliability: "
                f"{transaction.get('inventory_reliability_after', INVENTORY_RELIABLE)}"
                f"{warning_text}"
            )
        )

    return "\n".join(lines)


def main():
    account = get_local_account_by_riot_id(
        "ZiRcoN1977",
        "EUW",
        420,
    )

    if not account:
        print("No local account found for ZiRcoN1977#EUW.")
        return

    history = build_itemization_history(
        puuid=account["puuid"],
        position="JUNGLE",
        queue_id=420,
    )
    print(render_itemization_audit(history))
    for match_id in TARGET_MATCH_IDS:
        print()
        print(render_match_itemization_report(history, match_id))


if __name__ == "__main__":
    main()
