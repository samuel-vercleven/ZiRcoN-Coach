"""Temporal projection of the existing GameContext. Never imports UI or network."""
from copy import deepcopy
from dataclasses import asdict, dataclass
import math

from analysis.itemization_analyzer import (
    ITEM_EVENT_TYPES, MAGICAL_FOOTWEAR_PERK_ID, reconstruct_item_timeline,
)
from services.game_context import GameContext
from build_optimizer.catalog import CatalogView, natural, patch_of

# Same input-cadence tolerance as services.game_context.GameContext; not a
# scoring threshold. Riot's nominal minute frames have millisecond drift.
MAX_PREFIX_FRAME_GAP_MS = 90000


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


@dataclass(frozen=True)
class UnitState:
    participant_id: int
    champion: str
    team_id: int
    level: int | None
    inventory: tuple[int, ...]
    inventory_status: str
    warnings: tuple[str, ...]
    observed_stats: dict


@dataclass(frozen=True)
class BuildContext:
    match_id: str
    champion: str
    role: str
    timestamp: int
    sample_timestamp: int | None
    patch: str
    level: int | None
    gold: int | float | None
    inventory: tuple[int, ...]
    inventory_status: str
    allies: tuple[UnitState, ...]
    enemies: tuple[UnitState, ...]
    game_state: dict
    warnings: tuple[str, ...]
    status: str

    def to_dict(self):
        return asdict(self)


def _inventory(game, subject, events, timestamp, catalog):
    warnings = []
    pid = subject['participantId']
    selected = []
    for index, event in enumerate(events):
        if event.get('type') not in ITEM_EVENT_TYPES or event.get('participantId') != pid:
            continue
        if (not natural(event.get('itemId'), True) and event['type'] != 'ITEM_UNDO'):
            warnings.append('ITEM_EVENT_ID_UNRESOLVED')
            continue
        selected.append({'timestamp': event['timestamp'], 'event_type': event['type'],
                         'participant_id': pid, 'item_id': event.get('itemId'),
                         'frame_index': 0, 'event_index': index, 'raw': deepcopy(event)})
    # Only pre-game perk identities, never end-of-game var1/var2/var3 counters.
    perk_ids = [selection.get('perk') for style in (subject.get('perks') or {}).get('styles', [])
                for selection in style.get('selections', [])]
    if MAGICAL_FOOTWEAR_PERK_ID in perk_ids:
        warnings.append('UNOBSERVED_RUNE_GRANT_UNMODELED')
    if subject.get('championName') == 'Viego':
        warnings.append('TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE')
    # Required v22 final-reference fields are explicitly absent/unknown. Its
    # final_validation and retrospective reliability are NOT consumed below.
    meta = {'match_id': game.game_state['match_id'], 'game_creation': None,
            'game_duration': timestamp / 1000, 'game_version': game.game_state.get('patch'),
            'champion': subject.get('championName'), 'win': None,
            'final_items': None, 'final_trinket': None, 'perk_selections': []}
    result = reconstruct_item_timeline(meta, selected, catalog.reconstruction_catalog())
    for row in result['transactions']:
        if row['reconstruction_status'] != 'OK' or row['reconstruction_warnings']:
            warnings.append('PREFIX_TRANSACTION_UNRELIABLE')
    state = result['final_state']['slot_items']
    inventory = tuple(sorted(item_id for item_id, count in state.items() for _ in range(count)))
    if any(item_id not in catalog.items for item_id in inventory):
        warnings.append('UNKNOWN_INVENTORY_ITEM')
    if len(inventory) > 6:
        warnings.append('INVENTORY_CAPACITY_UNRESOLVED')
    # Prefix-only reconstruction is observational, not a proof that every
    # game mechanic emits an event. Completeness remains a separate contract.
    status = 'PARTIAL' if warnings else 'OBSERVED_PREFIX'
    return inventory, status, tuple(sorted(set(warnings)))


def build_context(game: GameContext, timestamp: int, catalog: CatalogView, champions: dict) -> BuildContext:
    if not natural(timestamp):
        raise ValueError('INVALID_TIMESTAMP')
    warnings = list(catalog.blockers)
    if patch_of(game.game_state.get('patch')) != catalog.patch:
        warnings.append('CONTEXT_CATALOG_PATCH_MISMATCH')
    if game.game_state.get('queue_id') != 420:
        warnings.append('UNSUPPORTED_QUEUE')
    # Deliberately ignore game.issues: these contain end-of-game checks and can
    # change after t. Validate only the projected inputs instead.
    frames = [f for f in game.timeline if number(f.get('timestamp')) and 0 <= f['timestamp'] <= timestamp]
    frames.sort(key=lambda f: f['timestamp'])
    if not frames or frames[0]['timestamp'] != 0:
        warnings.append('PREFIX_START_UNAVAILABLE')
    sample = frames[-1] if frames else {}
    sample_ts = sample.get('timestamp')
    if sample_ts != timestamp:
        warnings.append('EXACT_GOLD_SAMPLE_UNAVAILABLE')
    events = [e for e in game.events if number(e.get('timestamp')) and 0 <= e['timestamp'] <= timestamp]
    if any(b['timestamp'] - a['timestamp'] > MAX_PREFIX_FRAME_GAP_MS for a, b in zip(frames, frames[1:])):
        warnings.append('PREFIX_FRAME_GAP')
    subjects = (game.player, *game.allies, *game.enemies)
    if len({p.get('participantId') for p in subjects}) != len(subjects):
        raise ValueError('DUPLICATE_PARTICIPANT_ID')
    states = {}
    for subject in subjects:
        pid = subject.get('participantId')
        if not natural(pid, True) or not natural(subject.get('teamId'), True):
            raise ValueError('INVALID_PARTICIPANT_IDENTITY')
        frame = (sample.get('participantFrames') or {}).get(str(pid)) or {}
        inventory, reliability, notes = _inventory(game, subject, events, timestamp, catalog)
        notes = list(notes)
        champion = subject.get('championName') or 'UNKNOWN'
        record = champions.get(champion)
        if not record or patch_of(record.get('ddragon_version')) != catalog.patch or record.get('version_fallback_used') is not False:
            notes.append('UNKNOWN_OR_PATCH_MISMATCH_CHAMPION')
        level = frame.get('level')
        if not natural(level, True) or level > 18:
            level = None
            notes.append('LEVEL_UNRESOLVED')
        if not frame:
            notes.append('PARTICIPANT_FRAME_UNAVAILABLE')
        # These are sampled observations, never static-kit inferred values.
        raw_stats = frame.get('championStats') or {}
        stats = {k: raw_stats[k] for k in ('healthMax', 'armor', 'magicResist', 'attackDamage', 'abilityPower')
                 if number(raw_stats.get(k))}
        states[pid] = UnitState(pid, champion, subject['teamId'], level, inventory, reliability,
                                tuple(sorted(set(notes))), stats)
    own = states[game.player['participantId']]
    warnings.extend(own.warnings)
    own_frame = (sample.get('participantFrames') or {}).get(str(own.participant_id)) or {}
    gold = own_frame.get('currentGold')
    if not number(gold) or gold < 0 or sample_ts != timestamp:
        gold = None
        warnings.append('CURRENT_GOLD_UNRESOLVED')
    if any(e.get('type') in ITEM_EVENT_TYPES and e.get('participantId') == own.participant_id
           and e['timestamp'] == sample_ts for e in events):
        gold = None
        warnings.append('GOLD_ITEM_SAME_TIMESTAMP_ORDER_UNRESOLVED')
    allies = tuple(states[p['participantId']] for p in game.allies)
    enemies = tuple(states[p['participantId']] for p in game.enemies)
    if any(p.warnings or p.inventory_status != 'OBSERVED_PREFIX' for p in enemies):
        warnings.append('ENEMY_INFORMATION_PARTIAL')
    state = {'queue_id': game.game_state.get('queue_id'), 'source': 'RIOT_RAW_LOCAL_PREFIX',
             'time_precision': 'FRAME_SAMPLED', 'role_status': 'POSTGAME_ROLE_NOT_ADMITTED',
             'shop_access': 'UNMODELED', 'inventory_completeness': 'UNMODELED',
             'enemy_visibility': 'UNMODELED',
             'objective_events': tuple({'timestamp': e['timestamp'], 'type': e['type'],
                                        'monster_type': e.get('monsterType'), 'team_id': e.get('killerTeamId')}
                                       for e in events if e.get('type') in ('ELITE_MONSTER_KILL', 'BUILDING_KILL'))}
    return BuildContext(game.game_state['match_id'], own.champion, 'UNKNOWN',
                        timestamp, sample_ts, catalog.patch or 'UNKNOWN', own.level, gold, own.inventory,
                        own.inventory_status, allies, enemies, state, tuple(sorted(set(warnings))),
                        'PARTIAL' if warnings else 'OBSERVED_PREFIX')
