"""Reviewed, patch-pinned product contracts; never infer traits from item text."""
from dataclasses import dataclass

MODEL_KIND = 'DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1'
SHYVANA_AP_PROFILE_VERSION = 'shyvana_ap_build_profile_v1'
VIEGO_PROFILE_VERSION = 'viego_build_profile_v1'
GENERIC_CLASS_PROFILE_VERSION = 'generic_class_build_profile_v1'
SUPPORTED_PATCHES = frozenset({
    '16.8', '16.9', '16.11', '16.12', '16.14', '16.15', '16.16', '16.17', '16.18', '16.19',
})


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
_GENERIC_ITEMS = {**_SHYVANA_ITEMS, **_VIEGO_ITEMS}

# Patch 26.19 / Data Dragon 16.19.1 reviewed 2026-10-05 against 16.18.1.
# All 20 complete item records are unchanged. Pin these records, not just prices,
# so a tooltip/stat/applicability drift cannot silently reuse their traits.
_PATCH_RECORD_FINGERPRINTS = {'16.19': {
    2503: '9f9a957d66869c43eaa58ab9d689940caf8a24126927a7dd4d6882bc20f89abc',
    3036: '25d8ddfe69e735d0784331a133aa8acb6f1f1a85ef7c8321fc2685cf3fd521b3',
    3071: '33f4ec02c52601c5998173649c6b9fccc655bda612292559a7aec37f101d0d5c',
    3078: '386594dadf481b59ec7f3998ffce28141602010dd60d5bad61109bc62c3254b1',
    3089: '699acc922f1698d5ec5952128861c93ce7f5b1fa8c5220bcc7199bbcb3f5063b',
    3091: '64a9d5bb2955e0b7c2e1c57363a0af98d6641384200667897589a85f72e963aa',
    3100: '900c44cad4feb1a2bff50a42d433eac31a283d596798f40653365acfa5bc63ca',
    3102: 'ed46d14963c4b541ca45df4b15d6cf7c046b53832834bba7d24f4b96ea5b1fe6',
    3118: 'fa802bfd5227edf216ee1a3b11e47ff14545f4db25c97334d1835d56e0162329',
    3135: '6210e5b1e81729564aaba2fc7fdccfb3e7723589cc7c7730d3a4d307e0fe549c',
    3153: '1582a7bc1120af0362aa2aa5cd8375949e885b8a01d8c47d01c4ded096f8375a',
    3156: 'b8d0fd08413fc5b4b4e77e3d585a25332853880c49be0eb988a2ddb60d5e1559',
    3157: '9cda6bd2fc5190df40644525dc90d8b4d6c1976317e71e7f469e0944bb7b968b',
    3302: 'f88832d0da315114982a66852a053b0cf03160d530fdd9d1638377ed93ef3ac4',
    4645: 'c8bdb73bc6b86840c97267aabcdbf04397e0703ea76ce79622e95c9678f902ad',
    6333: '3591167f4375f6f54ce5088cb0229131dc74c9a349649694930b9b10281781ca',
    6610: '858f2caf7fb385b40fc12683d8d76f0d1036e97e3539ddb0d6f8ecf2ee496919',
    6672: 'cfc9c018fc9846b6469cc941ba676e89c2ad194e77b6874cc86bb3d9187c864d',
    6673: '97b7ff37acfe9c00306b3d03ee46c2f98db52218d5822a76bd9a26d7c4e55d27',
    6676: '5d5c7483e2b4623a75d54b8a7467532f8c562b9fd315ac87edddf2d66a2844a1',
}}


def item_profile(item, patch, champion=None):
    """Return a profile only when its exact patch facts still match review."""
    contracts = _ITEMS_BY_CHAMPION.get(champion, _GENERIC_ITEMS) if champion else _GENERIC_ITEMS
    if patch not in SUPPORTED_PATCHES or not contracts or item.item_id not in contracts:
        return None
    traits, total, components = contracts[item.item_id]
    if item.total_cost != total or item.components != components:
        return None
    fingerprints = _PATCH_RECORD_FINGERPRINTS.get(patch)
    if fingerprints and item.semantic_fingerprint != fingerprints.get(item.item_id):
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


_CLASS_TRAIT_WEIGHTS = {
    'Mage': {'AP': 10, 'ABILITY_HASTE': 5, 'RAW_DAMAGE': 5, 'BURST': 3, 'PERCENT_MAGIC_PEN': 3},
    'Assassin': {'BURST': 8, 'RAW_DAMAGE': 5, 'AD': 4, 'AP': 4,
                 'FLAT_ARMOR_PEN': 2, 'FLAT_MAGIC_PEN': 2},
    'Fighter': {'AD': 8, 'ATTACK_SPEED': 4, 'SUSTAINED_DAMAGE': 5, 'HEALTH': 4, 'ON_HIT': 3},
    'Tank': {'HEALTH': 8, 'ARMOR': 5, 'MR': 5, 'SURVIVABILITY': 5,
             'DEFENSE_ARMOR': 3, 'DEFENSE_MR': 3},
    'Marksman': {'AD': 8, 'ATTACK_SPEED': 7, 'CRIT': 6, 'SUSTAINED_DAMAGE': 5, 'ON_HIT': 3},
    'Support': {'ABILITY_HASTE': 7, 'UTILITY': 7, 'SURVIVABILITY': 6, 'HEALTH': 4, 'AP': 4},
}


def champion_profile(champion, patch, champion_tags=()):
    """Use a reviewed champion contract or a deliberately broad class fallback.

    The generic fallback consumes only exact-patch Data Dragon class tags. It
    does not claim a champion-specific build, role or ability damage model.
    """
    if patch not in SUPPORTED_PATCHES:
        return None
    reviewed = {'Shyvana': SHYVANA_AP, 'Viego': VIEGO}.get(champion)
    if reviewed is not None:
        return reviewed
    classes = sorted(set(champion_tags or ()) & _CLASS_TRAIT_WEIGHTS.keys())
    if not classes:
        return None
    weights = {}
    for class_name in classes:
        for trait, weight in _CLASS_TRAIT_WEIGHTS[class_name].items():
            weights[trait] = max(weights.get(trait, 0), weight)
    defensive = frozenset(trait for trait in weights if trait in {
        'HEALTH', 'ARMOR', 'MR', 'SURVIVABILITY', 'DEFENSE_ARMOR', 'DEFENSE_MR',
        'STASIS', 'SPELL_SHIELD',
    })
    return ChampionBuildProfile(
        champion, '+'.join(classes), GENERIC_CLASS_PROFILE_VERSION,
        frozenset(weights), defensive, weights,
    )
