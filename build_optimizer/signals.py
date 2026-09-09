"""Prefix-only historical reference and percentile signals for product heuristics."""
from dataclasses import asdict, dataclass
import math


def phase(timestamp):
    if timestamp < 600000:
        return 'EARLY'
    if timestamp < 900000:
        return 'EARLY_MID'
    if timestamp < 1200000:
        return 'MID'
    return 'LATE'


def _mean(values):
    return sum(values) / len(values) if values else None


def metrics(context):
    enemies = context.enemies
    values = {
        'enemy_hp': _mean([u.observed_stats.get('healthMax') for u in enemies if u.observed_stats.get('healthMax') is not None]),
        'enemy_armor': _mean([u.observed_stats.get('armor') for u in enemies if u.observed_stats.get('armor') is not None]),
        'enemy_mr': _mean([u.observed_stats.get('magicResist') for u in enemies if u.observed_stats.get('magicResist') is not None]),
        'enemy_ad': _mean([u.observed_stats.get('attackDamage') for u in enemies if u.observed_stats.get('attackDamage') is not None]),
        'enemy_ap': _mean([u.observed_stats.get('abilityPower') for u in enemies if u.observed_stats.get('abilityPower') is not None]),
    }
    own_gold = context.game_state.get('own_total_gold')
    enemy_gold = context.game_state.get('enemy_total_gold')
    values['team_gold_delta'] = own_gold - enemy_gold if type(own_gold) in (int, float) and type(enemy_gold) in (int, float) else None
    return values


@dataclass(frozen=True)
class HistoricalBaseline:
    patch: str
    phase: str
    sample_count: int
    distributions: dict
    status: str

    def to_dict(self):
        return asdict(self)


def build_baseline(prior_contexts, context):
    """Caller must provide prior completed matches only; no same-game samples admitted."""
    rows = [metrics(c) for c in prior_contexts if c.patch == context.patch and phase(c.timestamp) == phase(context.timestamp)
            and c.match_id != context.match_id]
    distributions = {key: sorted(v[key] for v in rows if v.get(key) is not None)
                     for key in ('enemy_hp', 'enemy_armor', 'enemy_mr', 'enemy_ad', 'enemy_ap', 'team_gold_delta')}
    # A minimum of three independent prior matches is deliberately explicit.
    status = 'SUPPORTED' if len(rows) >= 3 and all(distributions[k] for k in distributions) else 'BASELINE_UNAVAILABLE'
    return HistoricalBaseline(context.patch, phase(context.timestamp), len(rows), distributions, status)


def _level(value, values):
    if value is None or not values:
        return 'UNKNOWN', None
    percentile = sum(v <= value for v in values) / len(values)
    if percentile >= .9:
        return 'VERY_HIGH', percentile
    if percentile >= .75:
        return 'HIGH', percentile
    if percentile <= .25:
        return 'LOW', percentile
    return 'NORMAL', percentile


def game_signals(context, baseline):
    if baseline is None or baseline.status != 'SUPPORTED':
        return {'status': 'BASELINE_UNAVAILABLE', 'signals': {}, 'facts': {'sample_count': 0 if baseline is None else baseline.sample_count}}
    current = metrics(context)
    mapping = {'frontline_pressure': 'enemy_hp', 'armor_pressure': 'enemy_armor',
               'magic_resist_pressure': 'enemy_mr', 'physical_threat': 'enemy_ad',
               'magic_threat': 'enemy_ap', 'team_state': 'team_gold_delta'}
    signals, facts = {}, {'sample_count': baseline.sample_count, 'phase': baseline.phase}
    for name, key in mapping.items():
        level, percentile = _level(current[key], baseline.distributions[key])
        signals[name] = level
        facts[name] = {'observed': current[key], 'percentile': percentile, 'source': 'FRAME_OBSERVED_VS_PRIOR_MATCHES'}
    return {'status': 'SUPPORTED', 'signals': signals, 'facts': facts}
