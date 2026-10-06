"""Read-only real-cache copy/contract audit; prints no player identities or keys."""
from collections import Counter
import json
import sqlite3

from app.paths import DEFAULT_DB_PATH
from services.analysis_contracts import ANALYZER_CACHE_VERSIONS, ANALYZER_VERSIONS
from services.local_data import LocalDataService
from services.runtime_settings import RuntimeSettingsService
from services.coaching_narrative import build_packet, render_or_fallback
from ui.player_coach import coaching_focuses
from viewmodels import CoachingReport, InsightViewModel


def main():
    local = LocalDataService(settings=RuntimeSettingsService())
    player = local._primary_player()
    if player is None:
        print(json.dumps({'status': 'NO_LOCAL_PLAYER', 'audited': 0}))
        return
    with sqlite3.connect(f'{DEFAULT_DB_PATH.resolve().as_uri()}?mode=ro', uri=True) as connection:
        rows = connection.execute('SELECT r.match_id, r.analyzer_name, r.analyzer_version, r.status, r.report_json FROM app_player_analysis_reports r JOIN matches m ON m.match_id=r.match_id WHERE r.puuid=? AND m.queue_id=420 ORDER BY m.game_creation, m.match_id', (player['puuid'],)).fetchall()
    grouped = {}
    for match_id, family, version, status, raw in rows:
        if ANALYZER_CACHE_VERSIONS.get(family) != version:
            continue
        payload = json.loads(raw)
        grouped.setdefault(match_id, []).append(InsightViewModel(family.upper(), payload.get('title', family), payload.get('summary', ''),
            status=status, source_module=family, source_version=ANALYZER_VERSIONS[family],
            findings=tuple(payload.get('findings') or ()), events=tuple(payload.get('events') or ())))
    counts, examples = Counter(), {}
    for index, (match_id, insights) in enumerate(grouped.items()):
        report = CoachingReport(match_id, tuple(insights))
        focuses = coaching_focuses(report)
        packet = build_packet(report, f'audit-{index}')
        assert len(render_or_fallback(packet)['cards']) == len(focuses)
        assert match_id not in json.dumps(packet) and player['puuid'] not in json.dumps(packet)
        for focus in focuses:
            assert all(getattr(focus, key) for key in ('review_question', 'conditional_alternative', 'experiment_check'))
            assert len(focus.observation) < 260 and len(focus.next_game_experiment) < 180
            counts[focus.situation_id] += 1
            examples.setdefault(focus.situation_id, {'observation': focus.observation, 'action': focus.next_game_experiment})
    print(json.dumps({'status': 'PASS', 'audited_matches': len(grouped), 'focuses': sum(counts.values()),
                      'situations': dict(counts), 'examples': examples}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
