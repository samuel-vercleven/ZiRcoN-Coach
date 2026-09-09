"""Reviewed, patch-pinned product contracts; never infer traits from item text."""
from dataclasses import dataclass

MODEL_KIND = 'DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1'
SHYVANA_AP_PROFILE_VERSION = 'shyvana_ap_build_profile_v1'
SUPPORTED_PATCHES = frozenset({'16.9', '16.16', '16.17', '16.18'})


@dataclass(frozen=True)
class ItemSemanticProfile:
    item_id: int
    traits: frozenset[str]
    status: str
    patch: str
    source: str
    evidence: str
    total_cost: int
    components: tuple[int, ...]


# These are hand-reviewed declarations from the exact French Data Dragon item
# records. They are deliberately a small whitelist, not a parser and not an
# assertion that the item's full live-game mechanics are formally executed.
_ITEMS = {
    3118: (('AP', 'ABILITY_HASTE', 'SUSTAINED_DAMAGE', 'UTILITY'), 2700, (3802, 1026)),
    2503: (('AP', 'ABILITY_HASTE', 'SUSTAINED_DAMAGE', 'RAW_DAMAGE'), 2800, (3802, 2508)),
    4645: (('AP', 'FLAT_MAGIC_PEN', 'BURST', 'RAW_DAMAGE'), 3200, (3145, 1058)),
    3135: (('AP', 'PERCENT_MAGIC_PEN', 'RAW_DAMAGE'), 3000, (4630, 1026)),
    3089: (('AP', 'RAW_DAMAGE'), 3500, (1058, 1058)),
    3157: (('AP', 'DEFENSE_ARMOR', 'STASIS', 'SURVIVABILITY'), 3250, (1058, 2420)),
    3102: (('AP', 'DEFENSE_MR', 'SPELL_SHIELD', 'SURVIVABILITY'), 3000, (1058, 4632)),
    3100: (('AP', 'ABILITY_HASTE', 'BURST', 'MOVE_SPEED', 'RAW_DAMAGE'), 2900, (3057, 3113, 1026)),
}


def item_profile(item, patch):
    """Return a profile only when its exact patch facts still match review."""
    if patch not in SUPPORTED_PATCHES or item.item_id not in _ITEMS:
        return None
    traits, total, components = _ITEMS[item.item_id]
    if item.total_cost != total or item.components != components:
        return None
    return ItemSemanticProfile(
        item.item_id, frozenset(traits), 'SUPPORTED', patch,
        f'DATA_DRAGON_{patch}.1_FR_REVIEWED',
        'Exact item id, total price and direct recipe fingerprint matched the reviewed profile.',
        total, components,
    )


@dataclass(frozen=True)
class ChampionBuildProfile:
    champion: str
    archetype: str
    version: str
    supported_traits: frozenset[str]
    defensive_traits: frozenset[str]


SHYVANA_AP = ChampionBuildProfile(
    'Shyvana', 'AP', SHYVANA_AP_PROFILE_VERSION,
    frozenset({'AP', 'ABILITY_HASTE', 'RAW_DAMAGE', 'BURST', 'SUSTAINED_DAMAGE',
               'ANTI_HP', 'FLAT_MAGIC_PEN', 'PERCENT_MAGIC_PEN', 'MOVE_SPEED'}),
    frozenset({'DEFENSE_ARMOR', 'DEFENSE_MR', 'STASIS', 'SPELL_SHIELD', 'SURVIVABILITY'}),
)


def champion_profile(champion, patch):
    return SHYVANA_AP if champion == 'Shyvana' and patch in SUPPORTED_PATCHES else None
