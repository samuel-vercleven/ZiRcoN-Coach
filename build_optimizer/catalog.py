"""Read-only consumer of frozen Item Knowledge, not another knowledge parser."""
from copy import deepcopy
from dataclasses import dataclass

from knowledge.item_knowledge import ITEM_KNOWLEDGE_VERSION


def natural(value, positive=False):
    return type(value) is int and value >= (1 if positive else 0)


def patch_of(version):
    parts = str(version).split('.')
    return '.'.join(parts[:2]) if len(parts) >= 2 and all(p.isdigit() for p in parts[:2]) else None


@dataclass(frozen=True)
class ItemView:
    item_id: int
    name: str
    total_cost: int | None
    purchase_cost: int | None
    components: tuple[int, ...]
    builds_into: tuple[int, ...]
    stats: tuple[dict, ...]
    tags: tuple[str, ...]
    structural_blockers: tuple[str, ...]
    restrictions_status: str = 'UNMODELED'
    effects_status: str = 'UNMODELED'


class CatalogView:
    EXCLUDED_CLASSES = frozenset({
        'MODE_SPECIFIC_OR_NOT_SR', 'CHAMPION_SPECIFIC', 'NON_PURCHASABLE',
        'SPECIAL_OR_GENERATED', 'SPECIAL_RECIPE', 'CONSUMABLE', 'TRINKET',
        'JUNGLE_STARTER', 'BOOTS',
    })

    def __init__(self, catalog, game_patch):
        self.version = catalog.get('resolved_ddragon_version')
        self.patch = patch_of(game_patch)
        self.blockers = []
        if (not self.patch or patch_of(self.version) != self.patch
                or catalog.get('version_fallback_used') is not False
                or catalog.get('version_resolution_status') not in ('EXACT_VERSION', 'EXACT_PATCH')):
            self.blockers.append('CATALOG_PATCH_UNRESOLVED')
        if catalog.get('item_knowledge_version') != ITEM_KNOWLEDGE_VERSION:
            self.blockers.append('ITEM_KNOWLEDGE_VERSION_UNSUPPORTED')
        self.records = deepcopy(catalog.get('records') or {})
        self.items = {}
        for item_id, record in self.records.items():
            reasons = list(self.blockers)
            applicability = record.get('applicability') or {}
            classes = set(applicability.get('classes') or [])
            if record.get('purchasable') is not True or applicability.get('purchasable_on_summoners_rift') is not True:
                reasons.append('NOT_SR_PURCHASABLE')
            reasons.extend(sorted(classes & self.EXCLUDED_CLASSES))
            if applicability.get('in_store') is not True:
                reasons.append('NOT_IN_STORE')
            if record.get('ddragon_version') != self.version or record.get('version_fallback_used') is not False:
                reasons.append('ITEM_PATCH_UNRESOLVED')
            gold = record.get('gold') or {}
            if not natural(gold.get('total'), True) or not natural(gold.get('base')):
                reasons.append('PRICE_UNRESOLVED')
            if record.get('metadata_warnings') or (record.get('item_graph') or {}).get('issues'):
                reasons.append('ITEM_METADATA_OR_GRAPH_INCOMPLETE')
            self.items[item_id] = ItemView(item_id, record['name'], gold.get('total'), gold.get('base'),
                tuple(record.get('from_item_ids') or ()), tuple(record.get('into_item_ids') or ()),
                tuple(deepcopy(record.get('normalized_stats') or ())), tuple(record.get('tags') or ()),
                tuple(sorted(set(reasons))))

    def reconstruction_catalog(self):
        from analysis.itemization_analyzer import ItemCatalog
        return ItemCatalog(self.version, {str(k): v['raw_data'] for k, v in self.records.items()})
