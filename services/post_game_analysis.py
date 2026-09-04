from __future__ import annotations

from collections.abc import Callable, Iterable

from analysis.death_cost_analyzer import build_death_cost_dataset, get_match_death_costs
from analysis.itemization_analyzer import build_itemization_history
from analysis.jungle_tempo_analyzer import build_tempo_intervals, summarize_match_phases
from analysis.objective_analyzer import build_objective_dataset, get_match_objectives
from analysis.reset_analyzer import build_reset_dataset, get_match_resets
from database.tempo_reader import load_tempo_bundles
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from viewmodels import CoachingReport, InsightViewModel


ANALYZER_VERSIONS = {
    "death": "death_analyzer_v11", "tempo": "jungle_tempo_pathing_v17",
    "objectives": "objective_analyzer_v20", "resets": "recall_reset_v21",
    "build": "itemization_v22_phase1",
}


class PostGameAnalysisService:
    """Fail-closed UI adapter around the immutable analyzer APIs."""

    def __init__(self, local_data: LocalDataService, cache: CacheRepository):
        self.local_data = local_data
        self.cache = cache

    @staticmethod
    def _value(row: dict, *keys, default=None):
        for key in keys:
            value = row.get(key)
            if value is not None:
                return value
        return default

    def _death_payload(self, rows: list[dict]) -> dict:
        evidence = []
        for row in rows[:8]:
            timestamp = int(row.get("timestamp") or 0)
            score = self._value(row, "personal_cost_score", "death_cost_score")
            state = self._value(row, "death_advantage_state", "advantage_state", default="UNKNOWN")
            text = f"{timestamp // 60000:02d}:{timestamp // 1000 % 60:02d} • context {state}"
            if score is not None:
                text += f" • historical cost score {float(score):.1f}"
            evidence.append(text)
        status = "AVAILABLE" if rows else "AVAILABLE"
        return {"title": "Deaths", "summary": f"{len(rows)} death event(s) analyzed from the frozen v11 contract.",
                "status": status, "severity": "INFO", "evidence": evidence}

    def _tempo_payload(self, summary: dict) -> dict:
        evidence = []
        for phase, values in (summary or {}).items():
            if isinstance(values, dict):
                label = self._value(values, "tempo_label", "pathing_label", "label", default="SUPPORTED CONTEXT")
                evidence.append(f"{phase}: {str(label).replace('_', ' ')}")
        return {"title": "Tempo / Pathing", "summary": "Frozen v17 phase summaries are available." if summary else "No supported tempo phase was available.",
                "status": "AVAILABLE" if summary else "PARTIAL", "severity": "INFO", "evidence": evidence[:8]}

    def _objective_payload(self, rows: list[dict]) -> dict:
        evidence = []
        for row in rows[:10]:
            timestamp = int(row.get("timestamp") or 0)
            kind = self._value(row, "objective_family", "objective_type", "monster_type", default="OBJECTIVE")
            outcome = self._value(row, "objective_outcome", "outcome", "team_result", default="context available")
            evidence.append(f"{timestamp // 60000:02d}:{timestamp // 1000 % 60:02d} • {str(kind).replace('_', ' ')} • {str(outcome).replace('_', ' ')}")
        return {"title": "Objectives", "summary": f"{len(rows)} objective window(s) reconstructed by frozen v20.",
                "status": "AVAILABLE" if rows else "PARTIAL", "severity": "INFO", "evidence": evidence}

    def _reset_payload(self, rows: list[dict]) -> dict:
        evidence = []
        for row in rows[:10]:
            timestamp = int(self._value(row, "timestamp", "cluster_end", "end_timestamp", default=0) or 0)
            classification = self._value(row, "reentry_label", "reset_label", "origin", default="SHOP/RESET proxy")
            evidence.append(f"{timestamp // 60000:02d}:{timestamp // 1000 % 60:02d} • {str(classification).replace('_', ' ')}")
        return {"title": "Recalls / Resets", "summary": f"{len(rows)} SHOP/RESET proxy sequence(s) from frozen v21.",
                "status": "AVAILABLE" if rows else "PARTIAL", "severity": "INFO", "evidence": evidence}

    def _build_payload(self, match: dict | None) -> dict:
        if not match:
            return {"title": "Build / Itemization", "summary": "No frozen itemization report is available for this match.",
                    "status": "UNAVAILABLE", "severity": "INFO", "evidence": []}
        transactions = match.get("transactions") or []
        milestones = match.get("major_milestones") or []
        evidence = []
        for row in transactions[:12]:
            timestamp = int(row.get("timestamp") or 0)
            action = row.get("event_type") or "ITEM EVENT"
            item = row.get("item_name") or row.get("item_id") or "unknown item"
            evidence.append(f"{timestamp // 60000:02d}:{timestamp // 1000 % 60:02d} • {action} • {item}")
        validation = (match.get("final_validation") or {}).get("status", "UNKNOWN")
        return {"title": "Build / Itemization", "summary": f"Factual purchase reconstruction: {validation}. No optimal-build claim is made.",
                "status": "AVAILABLE" if validation.startswith("EXACT") else "PARTIAL", "severity": "INFO",
                "evidence": evidence or [f"{len(milestones)} factual milestone(s) available."]}

    def generate_for_matches(self, match_ids: Iterable[str], progress: Callable[[str], None] | None = None) -> None:
        ids = list(dict.fromkeys(match_ids))
        player = self.local_data.player()
        if not ids or not player.puuid:
            return
        details = {match_id: self.local_data.match_detail(match_id) for match_id in ids}
        position = next((detail.match.position for detail in details.values() if detail), "JUNGLE")
        datasets: dict[str, object] = {}

        def attempt(name: str, function):
            if progress:
                progress(f"Running {name} analyzer")
            try:
                datasets[name] = function()
            except Exception as error:
                datasets[name] = error

        attempt("death", lambda: build_death_cost_dataset(player.puuid, position=position))
        attempt("bundles", lambda: load_tempo_bundles(player.puuid, position=position))
        bundles = datasets.get("bundles") if isinstance(datasets.get("bundles"), list) else []
        deaths = datasets.get("death") if isinstance(datasets.get("death"), list) else []
        attempt("tempo", lambda: build_tempo_intervals(bundles))
        tempo = datasets.get("tempo") if isinstance(datasets.get("tempo"), list) else []
        attempt("objectives", lambda: build_objective_dataset(bundles, deaths, tempo))
        objectives = datasets.get("objectives") if isinstance(datasets.get("objectives"), list) else []
        attempt("resets", lambda: build_reset_dataset(bundles, deaths, tempo, objectives))
        attempt("build", lambda: build_itemization_history(player.puuid, position=position))
        build_history = datasets.get("build") if isinstance(datasets.get("build"), dict) else {}
        build_by_match = {row.get("match_id"): row for row in build_history.get("matches", [])}

        for match_id in ids:
            payloads = {
                "death": self._death_payload(get_match_death_costs(deaths, match_id)),
                "tempo": self._tempo_payload(summarize_match_phases(tempo, match_id)),
                "objectives": self._objective_payload(get_match_objectives(objectives, match_id)),
                "resets": self._reset_payload(get_match_resets(datasets.get("resets") if isinstance(datasets.get("resets"), list) else [], match_id)),
                "build": self._build_payload(build_by_match.get(match_id)),
            }
            for name, payload in payloads.items():
                source_error = datasets.get(name)
                if isinstance(source_error, Exception):
                    payload = {"title": payload["title"], "summary": "Analyzer failed independently; local match remains available.",
                               "status": "ERROR", "severity": "INFO", "evidence": []}
                self.cache.save_report(match_id, name, ANALYZER_VERSIONS[name], payload["status"], payload)

    def get_match_insights(self, match_id: str) -> CoachingReport:
        reports = self.cache.reports(match_id)
        if not reports:
            unavailable = tuple(InsightViewModel(name.title(), name.title(),
                "Analysis has not been cached for this match.", status="UNAVAILABLE",
                source_module=ANALYZER_VERSIONS[name], source_version=ANALYZER_VERSIONS[name]) for name in ANALYZER_VERSIONS)
            return CoachingReport(match_id, unavailable, "UNAVAILABLE")
        insights = []
        for report in reports:
            payload = report["payload"]
            insights.append(InsightViewModel(
                report["analyzer"].upper(), str(payload.get("title") or report["analyzer"]),
                str(payload.get("summary") or "UNAVAILABLE"), str(payload.get("severity") or "INFO"),
                str(report["status"]), tuple(str(value) for value in payload.get("evidence", [])),
                report["analyzer"], source_version=report["version"],
            ))
        order = {name: index for index, name in enumerate(ANALYZER_VERSIONS)}
        insights.sort(key=lambda row: order.get(row.source_module, 99))
        overall = "AVAILABLE" if all(row.status == "AVAILABLE" for row in insights) else "PARTIAL"
        return CoachingReport(match_id, tuple(insights), overall)
