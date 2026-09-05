"""Validated raw-data boundary, not a combat model or a replacement frozen reader."""
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from contextlib import closing


class ContextUnavailable(ValueError):
    """Safe machine code only; never includes raw API bodies or credentials."""


@dataclass(frozen=True)
class GameContext:
    player: dict
    allies: tuple[dict, ...]
    enemies: tuple[dict, ...]
    timeline: tuple[dict, ...]
    events: tuple[dict, ...]
    items: tuple[int | None, ...]
    gold: tuple[dict, ...]
    objectives: tuple[dict, ...]
    game_state: dict
    issues: tuple[str, ...]

    @property
    def death_timestamps(self):
        return tuple(e['timestamp'] for e in self.events
                     if e.get('type') == 'CHAMPION_KILL' and e.get('victimId') == self.player['participantId'])

    @classmethod
    def from_raw(cls, match, timeline, puuid):
        if not isinstance(match, dict) or not isinstance(match.get('info'), dict):
            raise ContextUnavailable('MATCH_INVALID')
        info = match['info']
        players = info.get('participants')
        if not isinstance(players, list) or not all(isinstance(p, dict) for p in players):
            raise ContextUnavailable('PARTICIPANTS_INVALID')
        selected = [p for p in players if p.get('puuid') == puuid]
        if len(selected) != 1 or not selected[0].get('participantId') or not selected[0].get('teamId'):
            raise ContextUnavailable('PARTICIPANT_UNRESOLVED')
        match_id = (match.get('metadata') or {}).get('matchId')
        if not match_id:
            raise ContextUnavailable('MATCH_ID_MISSING')
        if not isinstance(timeline, dict) or not isinstance(timeline.get('info'), dict):
            raise ContextUnavailable('TIMELINE_UNAVAILABLE')
        if (timeline.get('metadata') or {}).get('matchId') != match_id:
            raise ContextUnavailable('TIMELINE_MATCH_MISMATCH')
        duration = info.get('gameDuration')
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise ContextUnavailable('DURATION_UNAVAILABLE')
        frames = timeline['info'].get('frames')
        if not isinstance(frames, list) or len(frames) < 2:
            raise ContextUnavailable('FRAMES_UNAVAILABLE')
        issues, events, gold = [], [], []
        player = selected[0]
        role = player.get('teamPosition') or player.get('individualPosition')
        if role not in ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'):
            issues.append('ROLE_UNRESOLVED')
        opponents = [p for p in players if p.get('teamId') != player['teamId']
                     and (p.get('teamPosition') or p.get('individualPosition')) == role]
        if len(opponents) != 1:
            issues.append('OPPONENT_ROLE_UNRESOLVED')
        previous = -1
        for frame in frames:
            if not isinstance(frame, dict):
                raise ContextUnavailable('FRAME_INVALID')
            timestamp = frame.get('timestamp')
            if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool) or timestamp <= previous or timestamp < 0 or timestamp > duration * 1000 + 999:
                raise ContextUnavailable('FRAME_TIMESTAMP_INVALID')
            if previous >= 0 and timestamp - previous > 90000:
                issues.append('FRAME_GAP')
            previous = timestamp
            participants = frame.get('participantFrames')
            if not isinstance(participants, dict):
                raise ContextUnavailable('PARTICIPANT_FRAMES_INVALID')
            for subject in (player, *opponents):
                pf = participants.get(str(subject['participantId']))
                if not isinstance(pf, dict):
                    issues.append('PARTICIPANT_FRAME_MISSING')
                    continue
                if any(not isinstance(pf.get(k), (int, float)) for k in ('totalGold', 'currentGold', 'xp', 'level', 'minionsKilled', 'jungleMinionsKilled')):
                    issues.append('FRAME_RESOURCE_MISSING')
            own = participants.get(str(player['participantId'])) or {}
            gold.append({'timestamp': timestamp, 'total': own.get('totalGold'), 'current': own.get('currentGold')})
            frame_events = frame.get('events')
            if not isinstance(frame_events, list):
                raise ContextUnavailable('EVENTS_UNAVAILABLE')
            for event in frame_events:
                if not isinstance(event, dict):
                    raise ContextUnavailable('EVENT_INVALID')
                ts = event.get('timestamp')
                if not isinstance(ts, (int, float)) or isinstance(ts, bool) or ts < 0 or ts > duration * 1000 + 999:
                    raise ContextUnavailable('EVENT_TIMESTAMP_INVALID')
                events.append(event)
        if frames[0]['timestamp'] != 0 or duration * 1000 - frames[-1]['timestamp'] > 60000:
            issues.append('TIMELINE_INCOMPLETE')
        events.sort(key=lambda e: e['timestamp'])
        if any(player.get(k) is None for k in ('kills', 'deaths', 'assists', 'win', 'totalMinionsKilled', 'neutralMinionsKilled', 'championName')):
            issues.append('PLAYER_METRIC_MISSING')
        death_count = sum(e.get('type') == 'CHAMPION_KILL' and e.get('victimId') == player['participantId'] for e in events)
        if player.get('deaths') != death_count:
            issues.append('DEATH_EVENT_COUNT_MISMATCH')
        return cls(deepcopy(player), tuple(deepcopy(p) for p in players if p != player and p.get('teamId') == player['teamId']),
                   tuple(deepcopy(p) for p in players if p.get('teamId') != player['teamId']), tuple(deepcopy(frames)),
                   tuple(deepcopy(events)), tuple(player.get(f'item{i}') for i in range(7)), tuple(gold),
                   tuple(deepcopy(e) for e in events if e.get('type') in ('ELITE_MONSTER_KILL', 'BUILDING_KILL')),
                   {'match_id': match_id, 'queue_id': info.get('queueId'), 'patch': info.get('gameVersion'),
                    'duration_seconds': duration, 'role': role, 'source': 'RIOT_RAW_LOCAL', 'time_precision': 'FRAME_SAMPLED'},
                   tuple(sorted(set(issues))))


def load_game_context(db_path: Path, match_id: str, puuid: str) -> GameContext:
    try:
        with closing(sqlite3.connect(f'{Path(db_path).resolve().as_uri()}?mode=ro', uri=True)) as connection:
            match = connection.execute('SELECT raw_json FROM matches WHERE match_id=?', (match_id,)).fetchone()
            timeline = connection.execute('SELECT raw_json FROM timelines WHERE match_id=?', (match_id,)).fetchone()
        if not match:
            raise ContextUnavailable('MATCH_UNAVAILABLE')
        if not timeline:
            raise ContextUnavailable('TIMELINE_UNAVAILABLE')
        return GameContext.from_raw(json.loads(match[0]), json.loads(timeline[0]), puuid)
    except (sqlite3.Error, json.JSONDecodeError, TypeError) as error:
        raise ContextUnavailable('LOCAL_DATA_INVALID') from error
