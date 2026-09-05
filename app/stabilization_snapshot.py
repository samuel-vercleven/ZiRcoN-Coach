"""Local recoverable snapshot and candidate golden metadata; never snapshots .env."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ['EUW1_7965168777', 'EUW1_7965120221', 'EUW1_7963255011',
           'EUW1_7959361127', 'EUW1_7951911875', 'EUW1_7836627546', 'EUW1_7839112939']


def main():
    folder = ROOT / 'logs' / 'stabilization' / 'snapshot'
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / 'pre-stabilization-v1.zip'
    if not archive.exists():
        subprocess.run(['git', 'archive', '--format=zip', '-o', str(archive), 'pre-stabilization-v1'], cwd=ROOT, check=True)
    db = folder / 'baseline.db'
    if not db.exists():
        source = sqlite3.connect(f'file:{(ROOT / "database/zircon.db").as_posix()}?mode=ro', uri=True)
        dest = sqlite3.connect(db)
        try:
            source.backup(dest)
        finally:
            dest.close()
            source.close()
    connection = sqlite3.connect(f'file:{db.as_posix()}?mode=ro', uri=True)
    try:
        puuid = connection.execute('SELECT puuid FROM participants GROUP BY puuid ORDER BY count(*) DESC LIMIT 1').fetchone()[0]
        expected = []
        for match_id in TARGETS:
            raw_match = connection.execute('SELECT raw_json FROM matches WHERE match_id=?', (match_id,)).fetchone()[0]
            raw_timeline = connection.execute('SELECT raw_json FROM timelines WHERE match_id=?', (match_id,)).fetchone()[0]
            match, timeline = json.loads(raw_match), json.loads(raw_timeline)
            player = next(p for p in match['info']['participants'] if p['puuid'] == puuid)
            events = [e for f in timeline['info']['frames'] for e in f['events']]
            deaths = sorted(e['timestamp'] for e in events if e['type'] == 'CHAMPION_KILL' and e['victimId'] == player['participantId'])
            objective_events = [[e['timestamp'], e.get('monsterType'), e.get('monsterSubType'), e.get('killerTeamId')]
                                for e in events if e['type'] == 'ELITE_MONSTER_KILL']
            fixture = folder / match_id
            fixture.mkdir(exist_ok=True)
            for name, raw in [('match', raw_match), ('timeline', raw_timeline)]:
                path = fixture / (name + '.json')
                if not path.exists():
                    path.write_text(raw, encoding='utf-8')
            expected.append({'match_id': match_id, 'participant_id': player['participantId'],
                             'champion': player['championName'], 'role': player['teamPosition'],
                             'duration': match['info']['gameDuration'], 'win': player['win'],
                             'kda': [player[k] for k in ('kills', 'deaths', 'assists')],
                             'cs': player['totalMinionsKilled'] + player['neutralMinionsKilled'],
                             'items': [player[f'item{i}'] for i in range(7)], 'death_timestamps': deaths,
                             'objectives': objective_events, 'patch': match['info']['gameVersion'],
                             'match_sha256': hashlib.sha256(raw_match.encode()).hexdigest(),
                             'timeline_sha256': hashlib.sha256(raw_timeline.encode()).hexdigest()})
        print(json.dumps(expected, indent=2))
    finally:
        connection.close()


if __name__ == '__main__':
    main()
