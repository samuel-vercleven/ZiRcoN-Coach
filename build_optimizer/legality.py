"""Conservative purchase legality contract layered over frozen Item Knowledge."""
from dataclasses import asdict, dataclass

from build_optimizer.profiles import item_profile


@dataclass(frozen=True)
class LegalityDecision:
    status: str
    reasons: tuple[str, ...]
    source_version: str
    patch: str
    evidence: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


def decide(item, context, planner):
    """Final candidates are a reviewed major-item whitelist; all else fails closed."""
    profile = item_profile(item, context.patch)
    reasons, evidence = [], []
    if profile is None:
        return LegalityDecision('LEGALITY_UNKNOWN', ('SEMANTIC_PROFILE_OR_PATCH_UNSUPPORTED',),
                               context.patch + '.1', context.patch, ('No reviewed exact-patch profile.',))
    if item.structural_blockers:
        return LegalityDecision('ILLEGAL', tuple(item.structural_blockers), context.patch + '.1', context.patch,
                               ('Frozen Item Knowledge structural applicability.',))
    if item.item_id in context.inventory:
        return LegalityDecision('ILLEGAL', ('TARGET_ALREADY_OWNED_DUPLICATE_RESTRICTED',),
                               context.patch + '.1', context.patch, ('Product v1 duplicate policy for reviewed majors.',))
    if context.inventory_status != 'OBSERVED_PREFIX':
        return LegalityDecision('LEGALITY_UNKNOWN', ('INVENTORY_UNRELIABLE',), context.patch + '.1', context.patch,
                               ('Prefix inventory is not reliable.',))
    if context.gold is None:
        return LegalityDecision('LEGALITY_UNKNOWN', ('CURRENT_GOLD_UNRESOLVED',), context.patch + '.1', context.patch,
                               ('Exact sampled gold is required.',))
    plan = planner.plan(item.item_id, context.inventory, context.gold)
    if plan.status == 'BLOCKED' or 'SEARCH_LIMIT_REACHED' in plan.warnings:
        return LegalityDecision('LEGALITY_UNKNOWN', ('RECIPE_PLAN_UNRESOLVED',), context.patch + '.1', context.patch,
                               tuple(plan.warnings))
    reasons.append('LEGAL_SUPPORTED_MAJOR_SR_ITEM')
    evidence.extend((profile.source, profile.evidence, 'Frozen Item Knowledge purchasable/in_store/SR/recipe checks.',
                     'v1 excludes boots, consumables, trinkets, starters, quests, champion-specific and special items.'))
    return LegalityDecision('LEGAL_SUPPORTED', tuple(reasons), context.patch + '.1', context.patch, tuple(evidence))
