"""Reviewed, patch-pinned product contracts; never infer traits from item text."""
from dataclasses import dataclass

MODEL_KIND = 'DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1'
SHYVANA_AP_PROFILE_VERSION = 'shyvana_ap_build_profile_v1'
VIEGO_PROFILE_VERSION = 'viego_build_profile_v1'
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
_SHYVANA_ITEMS = {
    3118: (('AP', 'ABILITY_HASTE', 'SUSTAINED_DAMAGE', 'UTILITY'), 2700, (3802, 1026)),
    2503: (('AP', 'ABILITY_HASTE', 'SUSTAINED_DAMAGE', 'RAW_DAMAGE'), 2800, (3802, 2508)),
    4645: (('AP', 'FLAT_MAGIC_PEN', 'BURST', 'RAW_DAMAGE'), 3200, (3145, 1058)),
    3135: (('AP', 'PERCENT_MAGIC_PEN', 'RAW_DAMAGE'), 3000, (4630, 1026)),
    3089: (('AP', 'RAW_DAMAGE'), 3500, (1058, 1058)),
    3157: (('AP', 'DEFENSE_ARMOR', 'STASIS', 'SURVIVABILITY'), 3250, (1058, 2420)),
    3102: (('AP', 'DEFENSE_MR', 'SPELL_SHIELD', 'SURVIVABILITY'), 3000, (1058, 4632)),
    3100: (('AP', 'ABILITY_HASTE', 'BURST', 'MOVE_SPEED', 'RAW_DAMAGE'), 2900, (3057, 3113, 1026)),
}

# These contracts describe only the reviewed item directions used by this
# product heuristic.  They do not execute an item's tooltip, on-hit formula,
# passive reset, or Viego possession mechanics.
_VIEGO_ITEMS = {
    3153: (('AD', 'ATTACK_SPEED', 'ON_HIT', 'SUSTAINED_DAMAGE', 'ANTI_HP', 'LIFESTEAL'), 3200, (1053, 1043, 1037)),
    6672: (('AD', 'ATTACK_SPEED', 'ON_HIT', 'SUSTAINED_DAMAGE'), 3000, (6690, 3051, 1043)),
    3302: (('ATTACK_SPEED', 'ON_HIT', 'SUSTAINED_DAMAGE', 'PERCENT_ARMOR_PEN', 'ARMOR', 'MR', 'SURVIVABILITY'), 3000, (3051, 1043)),
    3071: (('AD', 'HEALTH', 'SUSTAINED_DAMAGE', 'PERCENT_ARMOR_PEN'), 3000, (3044, 3067, 1037)),
    3036: (('AD', 'CRIT', 'PERCENT_ARMOR_PEN'), 3300, (3035, 6670)),
    6333: (('AD', 'ARMOR', 'DEFENSE_ARMOR', 'SURVIVABILITY'), 3300, (2019, 1037, 3133)),
    3156: (('AD', 'MR', 'DEFENSE_MR', 'SURVIVABILITY'), 3100, (3155, 3133)),
    6610: (('AD', 'HEALTH', 'SUSTAINED_DAMAGE', 'SURVIVABILITY'), 3100, (2021, 3133)),
    3078: (('AD', 'ATTACK_SPEED', 'HEALTH', 'SUSTAINED_DAMAGE'), 3333, (3057, 3044, 3051)),
    3091: (('ATTACK_SPEED', 'ON_HIT', 'MR', 'DEFENSE_MR', 'SUSTAINED_DAMAGE'), 2800, (1043, 1057, 1043)),
    6673: (('AD', 'CRIT', 'LIFESTEAL', 'SURVIVABILITY'), 3000, (1037, 6670)),
    6676: (('AD', 'CRIT', 'BURST', 'FLAT_ARMOR_PEN'), 3000, (1037, 3134, 1018)),
}

_ITEMS_BY_CHAMPION = {'Shyvana': _SHYVANA_ITEMS, 'Viego': _VIEGO_ITEMS}


def item_profile(item, patch, champion=None):
    """Return a profile only when its exact patch facts still match review."""
    contracts = _ITEMS_BY_CHAMPION.get(champion) if champion else _SHYVANA_ITEMS
    if patch not in SUPPORTED_PATCHES or not contracts or item.item_id not in contracts:
        return None
    traits, total, components = contracts[item.item_id]
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
    central_trait_weights: dict[str, int]


SHYVANA_AP = ChampionBuildProfile(
    'Shyvana', 'AP', SHYVANA_AP_PROFILE_VERSION,
    frozenset({'AP', 'ABILITY_HASTE', 'RAW_DAMAGE', 'BURST', 'SUSTAINED_DAMAGE',
               'ANTI_HP', 'FLAT_MAGIC_PEN', 'PERCENT_MAGIC_PEN', 'MOVE_SPEED'}),
    frozenset({'DEFENSE_ARMOR', 'DEFENSE_MR', 'STASIS', 'SPELL_SHIELD', 'SURVIVABILITY'}),
    {'AP': 30},
)

VIEGO = ChampionBuildProfile(
    'Viego', 'AD_ON_HIT', VIEGO_PROFILE_VERSION,
    frozenset({'AD', 'ATTACK_SPEED', 'ON_HIT', 'CRIT', 'SUSTAINED_DAMAGE', 'BURST',
               'ANTI_HP', 'PERCENT_ARMOR_PEN', 'FLAT_ARMOR_PEN', 'HEALTH', 'ARMOR',
               'MR', 'LIFESTEAL', 'SURVIVABILITY'}),
    frozenset({'ARMOR', 'MR', 'DEFENSE_ARMOR', 'DEFENSE_MR', 'SURVIVABILITY', 'HEALTH'}),
    {'AD': 9, 'ATTACK_SPEED': 7, 'ON_HIT': 7, 'SUSTAINED_DAMAGE': 4,
     'LIFESTEAL': 2, 'CRIT': 1},
)


def champion_profile(champion, patch):
    if patch not in SUPPORTED_PATCHES:
        return None
    return {'Shyvana': SHYVANA_AP, 'Viego': VIEGO}.get(champion)
