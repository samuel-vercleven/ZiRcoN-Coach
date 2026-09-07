"""Real local history audit. Only report caches/indexes are written; no Riot sync."""
from collections import Counter
import json
from pathlib import Path

from app.bootstrap import build_app_context
from services.game_context import ContextUnavailable, load_game_context
from analysis.death_cost_analyzer import build_death_cost_dataset, build_game_death_summary_dataset


def main():
    context = build_app_context()
    player = context.local_data.player()
    matches = context.local_data.matches()
    assert player.puuid and len(matches) >= 20, 'Real local history is required'
    input_issues = Counter()
    raw_deaths, roles = {}, {}
    for match in matches:
        try:
            game = load_game_context(context.local_data.db_path, match.match_id, player.puuid)
            input_issues.update(game.issues)
            raw_deaths[match.match_id] = game.death_timestamps
            roles.setdefault(match.position, []).append(match.match_id)
        except ContextUnavailable as error:
            input_issues[str(error)] += 1
    print(f'Local input audit: {len(matches)} matches, {sum(map(len, raw_deaths.values()))} raw death events', flush=True)
    analyzed_deaths = 0
    missing_deaths = {}
    for role, ids in roles.items():
        dataset = build_death_cost_dataset(player.puuid, position=role)
        summaries = build_game_death_summary_dataset(dataset, player.puuid, position=role)
        assert len({r['match_id'] for r in summaries}) == len(summaries)
        for match_id in ids:
            rows = [r for r in dataset if r['match_id'] == match_id]
            actual = tuple(sorted(r['timestamp'] for r in rows))
            assert set(actual) <= set(raw_deaths[match_id]), 'Frozen output invented a death'
            analyzed_deaths += len(actual)
            if actual != raw_deaths[match_id]:
                missing_deaths[match_id] = len(raw_deaths[match_id]) - len(actual)
            for row in rows:
                assert row['impact_seconds_before_death'] >= 0
                assert row['impact_seconds_after_death'] > 0
                assert abs(row['impact_interval_seconds'] - row['impact_seconds_before_death'] - row['impact_seconds_after_death']) < 1e-6
    generated = context.analysis.generate_for_matches([m.match_id for m in matches[:20]], lambda text: print(text, flush=True))
    counts = Counter()
    for match in matches[:20]:
        report = context.analysis.get_match_insights(match.match_id)
        for insight in report.insights:
            counts[f'{insight.source_module}:{insight.status}'] += 1
            if insight.source_module == 'death' and insight.status == 'AVAILABLE':
                assert len(insight.events) == len(raw_deaths[match.match_id])
                for event in insight.events:
                    assert any(m.get('raw_key') == 'impact_interval_seconds' for m in event['metrics'])
                    assert any('EXPERIMENTAL' in text for text in event['context'])
            if insight.source_module == 'objectives':
                assert not insight.findings, 'Team context became personal fault'
    result = {'matches': len(matches), 'raw_deaths': sum(map(len, raw_deaths.values())),
              'frozen_deaths': analyzed_deaths, 'input_issues': dict(input_issues),
              'unmeasurable_deaths': missing_deaths, 'latest20': generated, 'report_states': dict(counts)}
    folder = Path(__file__).resolve().parents[1] / 'logs/stabilization'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'local_batch.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    assert not any(key.endswith(':ERROR') for key in counts), 'Real analyzer errors require review'


if __name__ == '__main__':
    main()
