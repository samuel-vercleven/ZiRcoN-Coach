"""Economic diagnostics only. Unsupported gameplay factors are not numeric zeros."""
from dataclasses import asdict, dataclass

from build_optimizer.profiles import MODEL_KIND

BUILD_SCORE_WEIGHTS = {
    'ChampionSynergy': None,
    'EnemyCounter': None,
    'CurrentBuildSynergy': None,
    'GameNeed': None,
    'PowerSpikeValue': None,
    'EconomyValue': 1,
    'PurchaseFeasibility': None,
    'RedundancyPenalty': None,
    'IncompatibilityPenalty': None,
}

BUILD_SCORE_WEIGHTS_V1 = {
    'ChampionFit': 30, 'EnemyResponse': 25, 'CurrentBuildSynergy': 15,
    'GameStateNeed': 10, 'PowerSpikeValue': 10, 'EconomyValue': 5,
    'PurchaseFeasibility': 5,
}
# 1 preserves the unit of the diagnostic fraction: recipe cost covered / total
# price. It is NOT a calibrated gameplay weight or a cross-item utility scale.


@dataclass(frozen=True)
class Contribution:
    factor: str
    status: str
    value: float | None
    weight: int | None
    contribution: float | None
    reasons: tuple[str, ...]
    supporting_facts: dict


def score_recipe(plan, catalog):
    item = catalog.items[plan.target_item]
    factors = []
    for name, weight in BUILD_SCORE_WEIGHTS.items():
        if name == 'EconomyValue' and plan.remaining_cost_after is not None:
            covered = item.total_cost - plan.remaining_cost_after
            value = covered / item.total_cost
            factors.append(Contribution(name, 'EXPERIMENTAL', value, weight, value * weight,
                (f'{covered}/{item.total_cost} PO de recette couvertes après le plan diagnostique.',) if value else (),
                {'target_total_cost': item.total_cost, 'remaining_cost': plan.remaining_cost_after,
                 'plan_spend': plan.total_spend, 'source': 'ITEM_KNOWLEDGE_RECIPE'}))
        else:
            factors.append(Contribution(name, 'UNMODELED', None, weight, None, (), {}))
    return {'target_item': plan.target_item, 'score': None, 'status': 'PARTIAL',
            'diagnostic_subtotal': sum(f.contribution for f in factors if f.contribution is not None),
            'score_breakdown': [asdict(f) for f in factors],
            'positive_reasons': [reason for f in factors if f.contribution is not None and f.contribution > 0 for reason in f.reasons],
            'negative_reasons': [reason for f in factors if f.contribution is not None and f.contribution < 0 for reason in f.reasons],
            'warnings': ['NO_CONTEXTUAL_UTILITY_CONTRACT', 'ECONOMIC_SUBTOTAL_IS_NOT_FINAL_SCORE']}


def _contribution(name, value, reasons, facts):
    maximum = BUILD_SCORE_WEIGHTS_V1[name]
    value = max(0, min(maximum, value))
    return Contribution(name, 'EXPERIMENTAL_PRODUCT_HEURISTIC', value, maximum, value,
                        tuple(reasons), facts)


def score_contextual(profile, plan, legality, signals, context, catalog=None):
    """A bounded, directional product heuristic; never combat simulation."""
    traits, values = profile.traits, []
    from build_optimizer.profiles import champion_profile, item_profile
    champion = champion_profile(context.champion, context.patch)
    if champion is None:
        raise ValueError('UNSUPPORTED_CHAMPION_PROFILE')
    fit = sum(weight for trait, weight in champion.central_trait_weights.items() if trait in traits)
    values.append(_contribution('ChampionFit', fit,
        tuple(f'Trait central {trait} compatible avec le profil {champion.version}.'
              for trait in champion.central_trait_weights if trait in traits),
        {'profile': champion.version, 'traits': sorted(traits),
         'central_trait_weights': champion.central_trait_weights}))
    s, f = signals['signals'], signals['facts']
    response, reasons = 0, []
    if s.get('frontline_pressure') in ('HIGH', 'VERY_HIGH') and {'ANTI_HP', 'SUSTAINED_DAMAGE'} & traits:
        response += 10; reasons.append('La pression HP ennemie est élevée dans la référence historique.')
    if champion.champion == 'Shyvana':
        if s.get('magic_resist_pressure') in ('HIGH', 'VERY_HIGH') and 'PERCENT_MAGIC_PEN' in traits:
            response += 12; reasons.append('La résistance magique ennemie est élevée dans la référence historique.')
        if s.get('frontline_pressure') == 'LOW' and s.get('magic_resist_pressure') in ('LOW', 'NORMAL') and {'BURST', 'FLAT_MAGIC_PEN'} & traits:
            response += 9; reasons.append('Le profil ennemi relatif favorise une direction burst/pénétration plate.')
    if champion.champion == 'Viego':
        if s.get('armor_pressure') in ('HIGH', 'VERY_HIGH') and 'PERCENT_ARMOR_PEN' in traits:
            response += 12; reasons.append('L’armure ennemie est élevée dans la référence historique.')
        if s.get('frontline_pressure') == 'LOW' and {'CRIT', 'BURST', 'FLAT_ARMOR_PEN'} & traits:
            response += 9; reasons.append('Le profil ennemi relatif favorise une direction crit/burst.')
    if s.get('physical_threat') == 'VERY_HIGH' and {'DEFENSE_ARMOR', 'STASIS'} & traits:
        response += 15; reasons.append('La menace physique relative est très élevée.')
    if s.get('magic_threat') == 'VERY_HIGH' and {'DEFENSE_MR', 'SPELL_SHIELD'} & traits:
        response += 15; reasons.append('La menace magique relative est très élevée.')
    values.append(_contribution('EnemyResponse', response, reasons, f))
    held_traits = set()
    # Only reviewed major items contribute; no text/tag inference for unknown inventory.
    for item_id in context.inventory:
        view = catalog.items.get(item_id) if catalog is not None else None
        held = item_profile(view, context.patch, context.champion) if view else None
        if held:
            held_traits.update(held.traits)
    overlap = len(held_traits & traits)
    synergy = 8 if not overlap else max(2, 8 - 2 * overlap)
    values.append(_contribution('CurrentBuildSynergy', synergy,
        ('La direction ajoutée ne dépend que des profils d’items déjà revus.',), {'held_reviewed_traits': sorted(held_traits)}))
    game_need, game_reasons = 0, []
    if s.get('team_state') == 'LOW' and {'SURVIVABILITY', 'STASIS', 'SPELL_SHIELD'} & traits:
        game_need = 5; game_reasons.append('Le delta de gold d’équipe est bas dans la référence historique.')
    elif s.get('team_state') in ('HIGH', 'VERY_HIGH') and {'RAW_DAMAGE', 'SUSTAINED_DAMAGE', 'BURST'} & traits:
        game_need = 4; game_reasons.append('Le delta de gold d’équipe est positif dans la référence historique.')
    values.append(_contribution('GameStateNeed', game_need, game_reasons, f))
    spike = 10 if plan.target_completed else (6 if plan.steps else 0)
    values.append(_contribution('PowerSpikeValue', spike,
        ('L’item complet est réalisable dans le modèle de recette.' if plan.target_completed else 'Un progrès de recette réalisable est disponible.',) if spike else (),
        {'target_completed': plan.target_completed, 'steps': len(plan.steps), 'remaining_cost': plan.remaining_cost_after}))
    covered = (profile.total_cost - plan.remaining_cost_after) / profile.total_cost
    values.append(_contribution('EconomyValue', 5 * covered,
        ('La couverture de recette utilise seulement coûts et composants observés.',),
        {'covered_fraction': covered, 'remaining_cost': plan.remaining_cost_after}))
    values.append(_contribution('PurchaseFeasibility', 5 if legality.status == 'LEGAL_SUPPORTED' else 0,
        ('Le contrat de légalité v1 et le plan de recette sont supportés.',), legality.to_dict()))
    total = sum(v.contribution for v in values)
    return {'model_kind': MODEL_KIND, 'target_item': profile.item_id, 'status': 'SUPPORTED', 'score': total,
            'score_breakdown': [asdict(v) for v in values], 'positive_reasons': [r for v in values for r in v.reasons],
            'negative_reasons': [], 'supporting_facts': {'signals': f, 'traits': sorted(traits)},
            'warnings': ['EXPERIMENTAL_PRODUCT_HEURISTIC_NOT_OPTIMAL_SIMULATOR']}
