"""Real offline-replay E2E. Missing local fixtures fail explicitly, never skip to PASS."""
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

from analysis.death_cost_analyzer import build_death_cost_dataset, build_game_death_summary_dataset
from analysis.itemization_analyzer import build_itemization_history
from database import database
from database.death_reader import get_player_death_events, get_frame_before_or_at, get_frame_strictly_after
from services.game_context import GameContext
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from knowledge.item_knowledge import build_item_knowledge_catalog
from knowledge.rune_knowledge import build_rune_knowledge_catalog
from knowledge.champion_knowledge import build_champion_knowledge_catalog

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'logs/stabilization/snapshot'
CATALOGS = ROOT / '.cache/zircon/stabilization-catalogs'


def catalog_json(version, resource):
    """Explicit immutable-version URL; no latest-version semantic substitution."""
    import requests
    path = CATALOGS / version / resource
    if not path.exists():
        response = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/{resource}', timeout=30)
        response.raise_for_status()
        value = response.json()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    expected = json.loads((ROOT / 'tests/fixtures/golden_games/expected.json').read_text(encoding='utf-8'))
    sources, versions, raw_items = {}, {}, {}
    for row in expected:
        folder = SNAPSHOT / row['match_id']
        pair = []
        for kind in ('match', 'timeline'):
            path = folder / (kind + '.json')
            assert path.exists(), f'Real fixture missing: {row["match_id"]}/{kind}'
            data = path.read_bytes()
            assert hashlib.sha256(data).hexdigest() == row[kind + '_sha256'], 'Fixture source drift'
            pair.append(json.loads(data))
        sources[row['match_id']] = pair
        version = '.'.join(row['patch'].split('.')[:2]) + '.1'
        versions[row['patch']] = version
        if version not in raw_items:
            raw_items[version] = catalog_json(version, 'item.json')['data']

    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / 'golden.db'
        with patch.object(database, 'DB_PATH', db):
            database.initialize_database()
            database.initialize_timeline_tables()
            puuid = None
            for row in expected:
                match, timeline = sources[row['match_id']]
                player = next(p for p in match['info']['participants'] if p['participantId'] == row['participant_id'])
                puuid = puuid or player['puuid']
                assert player['puuid'] == puuid
                database.save_match(match)
                database.save_timeline(row['match_id'], timeline)
                context = GameContext.from_raw(match, timeline, puuid)
                assert not context.issues, (row['match_id'], context.issues)
                assert context.player['championName'] == row['champion']
                assert context.game_state['role'] == row['role']
                assert context.game_state['duration_seconds'] == row['duration']
                assert list(context.items) == row['items']
                assert list(context.death_timestamps) == row['death_timestamps']
                assert [[e['timestamp'], e.get('monsterType'), e.get('monsterSubType'), e.get('killerTeamId')]
                        for e in context.objectives if e['type'] == 'ELITE_MONSTER_KILL'] == row['objectives']
                with closing(sqlite3.connect(db)) as connection:
                    result = connection.execute('SELECT champion_name, position, kills, deaths, assists, cs, win, item0,item1,item2,item3,item4,item5,item6 FROM participants WHERE match_id=? AND puuid=?', (row['match_id'], puuid)).fetchone()
                    assert list(result) == [row['champion'], row['role'], *row['kda'], row['cs'], int(row['win']), *row['items']]
                    assert connection.execute('SELECT COUNT(*) FROM timeline_events WHERE match_id=?', (row['match_id'],)).fetchone()[0] == len(context.events)
                deaths = get_player_death_events(row['match_id'], puuid)
                assert [e['timestamp'] for e in deaths] == row['death_timestamps']
                for ts in row['death_timestamps']:
                    before = get_frame_before_or_at(row['match_id'], row['participant_id'], ts)
                    after = get_frame_strictly_after(row['match_id'], row['participant_id'], ts)
                    timestamps = [f['timestamp'] for f in timeline['info']['frames']]
                    assert before['timestamp'] == max(t for t in timestamps if t <= ts)
                    assert after['timestamp'] == min(t for t in timestamps if t > ts)
                version = versions[row['patch']]
                items = build_item_knowledge_catalog(row['patch'], raw_items=raw_items[version], versions=[version])
                assert items['version_fallback_used'] is False
                for item_id in set(row['items']) - {0}:
                    fact = items['records'].get(item_id)
                    assert fact is not None, ('UNKNOWN_ITEM', item_id)
                    raw = raw_items[version][str(item_id)]
                    assert fact['raw_data'] == raw and fact['raw_description'] == raw['description']
                    assert fact['name'] == raw['name'] and fact['gold']['total'] == raw['gold']['total']
                    assert fact['gold']['base'] == raw['gold']['base']
                    assert fact['from_item_ids'] == [int(i) for i in raw.get('from', [])]
                raw_runes = catalog_json(version, 'runesReforged.json')
                runes = build_rune_knowledge_catalog(row['patch'], raw_runes=raw_runes, versions=[version])
                for style in player['perks']['styles']:
                    for selection in style['selections']:
                        record = runes['records'].get(selection['perk'])
                        assert record is not None, 'UNKNOWN_RUNE'
                        assert record['raw_longDesc'] == record['raw_rune_json']['longDesc']
                        assert record['formula']['status'] == 'RUNE_FORMULA_INCOMPLETE'
                champion_raw = catalog_json(version, f"champion/{row['champion']}.json")['data'][row['champion']]
                champions = build_champion_knowledge_catalog(row['patch'], raw_champions={row['champion']: champion_raw},
                    raw_champion_details={row['champion']: champion_raw}, versions=[version])
                assert len(champions['records']) == 1 and champions['version_fallback_used'] is False

            # Network-free replay of frozen itemization with actual patch-matched catalog responses.
            with patch('analysis.itemization_analyzer.get_ddragon_versions', return_value=list(raw_items)), \
                 patch('analysis.itemization_analyzer.get_items', side_effect=lambda version: raw_items[version]):
                cache = CacheRepository(db)
                local = LocalDataService(db, cache)
                service = PostGameAnalysisService(local, cache)
                generation = service.generate_for_matches([r['match_id'] for r in expected])
                assert generation['generated'] == 35
                total_deaths = 0
                for role in {r['role'] for r in expected}:
                    deaths = build_death_cost_dataset(puuid, position=role)
                    games = build_game_death_summary_dataset(deaths, puuid, position=role)
                    assert len(games) == len({r['match_id'] for r in expected if r['role'] == role})
                    assert len({g['match_id'] for g in games}) == len(games), 'Game-level pseudoreplication'
                    builds = {m['match_id']: m for m in build_itemization_history(puuid, position=role)['matches']}
                    for row in (r for r in expected if r['role'] == role):
                        actual = sorted(d['timestamp'] for d in deaths if d['match_id'] == row['match_id'])
                        assert actual == row['death_timestamps'], ('DEATH_COVERAGE', row['match_id'])
                        total_deaths += len(actual)
                        report = service.get_match_insights(row['match_id'])
                        assert len(report.insights[0].events) == len(actual)
                        assert report.insights[0].status == 'AVAILABLE'
                        build = builds[row['match_id']]
                        assert build['final_validation']['riot_final_counter'] == Counter(i for i in row['items'][:6] if i)
                        if row['match_id'] == 'EUW1_7959361127':
                            # Independently audited frozen limitation: observed final support
                            # item 3871 is absent from reconstruction; never invent its grant.
                            assert build['final_validation']['status'] == 'PARTIAL'
                            assert build['final_validation']['missing_counter'] == Counter({3871: 1})
                            assert next(i for i in report.insights if i.source_module == 'build').status == 'PARTIAL'
                        else:
                            assert build['final_validation']['status'].startswith('EXACT'), (row['match_id'], build['final_validation']['status'])
                        if role != 'JUNGLE':
                            assert all(i.status == 'UNAVAILABLE' for i in report.insights if i.source_module in ('tempo','objectives','resets'))
                print(f'Golden raw -> SQL -> GameContext -> frozen analyzers -> knowledge -> cached report: PASS; {len(expected)} games, {total_deaths} deaths, 35 reports')


if __name__ == '__main__':
    main()
