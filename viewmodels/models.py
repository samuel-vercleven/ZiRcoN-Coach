from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PlayerViewModel:
    puuid: str = ""
    riot_id: str = "Local player"
    queue: str = "Ranked Solo/Duo"
    rank: str = "UNAVAILABLE"
    lp: Optional[int] = None
    profile_icon_id: Optional[int] = None
    summoner_level: Optional[int] = None
    ranked_wins: Optional[int] = None
    ranked_losses: Optional[int] = None
    profile_status: str = "LOCAL"


@dataclass(frozen=True)
class MatchSummaryViewModel:
    match_id: str
    champion: str
    result: str
    kills: int
    deaths: int
    assists: int
    cs: int
    duration_seconds: int
    played_at: str
    queue: str
    position: str = "UNKNOWN"
    items: tuple[int, ...] = ()
    game_version: str = ""
    analysis_status: str = "UNAVAILABLE"

    @property
    def kda_text(self) -> str:
        return f"{self.kills}/{self.deaths}/{self.assists}"

    @property
    def cs_per_min(self) -> Optional[float]:
        return self.cs / (self.duration_seconds / 60) if self.duration_seconds else None


@dataclass(frozen=True)
class InsightViewModel:
    category: str
    title: str
    summary: str
    severity: str = "INFO"
    status: str = "UNAVAILABLE"
    evidence: tuple[str, ...] = ()
    source_module: str = ""
    timestamp: Optional[int] = None
    source_version: str = ""


@dataclass(frozen=True)
class CoachingReport:
    match_id: str
    insights: tuple[InsightViewModel, ...] = ()
    status: str = "UNAVAILABLE"


@dataclass(frozen=True)
class MatchDetailViewModel:
    match: MatchSummaryViewModel
    items: tuple[int, ...] = ()
    coaching: CoachingReport = field(default_factory=lambda: CoachingReport(""))


@dataclass(frozen=True)
class ProgressViewModel:
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: Optional[float] = None
    kda: Optional[float] = None
    cs_per_min: Optional[float] = None
    deaths_per_match: Optional[float] = None
    average_duration_minutes: Optional[float] = None
    recent_comparison: str = "Insufficient local history for a comparison."
    champion_rows: tuple[dict, ...] = ()


@dataclass(frozen=True)
class StatusViewModel:
    db_path: str
    db_available: bool
    match_count: int
    latest_match_date: str = "UNAVAILABLE"
    api_configured: bool = False
    sync_status: str = "Offline / not synced this session"
    api_status: str = "NOT_CONFIGURED"
    timeline_count: int = 0
    analyzed_match_count: int = 0
    last_sync_at: str = "UNAVAILABLE"
