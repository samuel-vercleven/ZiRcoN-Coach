from __future__ import annotations

from collections.abc import Callable, Iterable

from analysis.death_cost_analyzer import OBJECTIVE_WINDOW_SECONDS, build_death_cost_dataset, get_match_death_costs
from analysis.itemization_analyzer import build_itemization_history
from analysis.jungle_tempo_analyzer import build_tempo_intervals, summarize_match_phases
from analysis.objective_analyzer import build_objective_dataset, get_match_objectives
from analysis.reset_analyzer import build_reset_dataset, get_match_resets
from database.tempo_reader import load_tempo_bundles
from services.analysis_contracts import ANALYZER_CACHE_VERSIONS, ANALYZER_VERSIONS
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from viewmodels import CoachingReport, InsightViewModel


_FR_ENUMS = {
    "ALLY": "allié", "ENEMY": "adverse", "NEAR": "proche", "MID": "à distance moyenne",
    "FAR": "éloigné", "BEHIND": "en retard", "AHEAD": "en avance", "EVEN": "équilibre",
    "LOW": "faible", "MEDIUM": "moyenne", "HIGH": "élevée", "NONE": "aucune",
    "SECURED": "sécurisé", "LOST": "perdu", "LOST_WITH_COMPENSATION": "perdu avec compensation",
    "VOLUNTARY_RESET_PROXY": "proxy de reset volontaire", "DEATH_RESET": "retour après mort",
    "VOLUNTARY_NEUTRAL": "reset volontaire — contexte neutre", "WARMUP": "historique insuffisant",
    "GOOD": "au-dessus de la référence", "EXCELLENT": "très au-dessus de la référence",
    "BELOW_BASELINE": "sous la référence", "UNKNOWN": "inconnu",
}


def _enum(value: object) -> str:
    raw = str(value if value is not None else "UNKNOWN")
    return _FR_ENUMS.get(raw, raw.replace("_", " ").lower())


def _time(timestamp: object) -> str:
    value = int(timestamp or 0)
    return f"{value // 60000:02d}:{value // 1000 % 60:02d}"


def _number(value: object, pattern: str = ".1f", suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{float(value):{pattern}}{suffix}"


def _metric(label: str, value: object, raw_key: str) -> dict:
    return {"label": label, "value": "—" if value is None else str(value), "raw_key": raw_key}


class PostGameAnalysisService:
    """Structured, fail-closed UI projection over immutable analyzer APIs."""

    def __init__(self, local_data: LocalDataService | None, cache: CacheRepository | None):
        self.local_data = local_data
        self.cache = cache

    def _death_payload(self, rows: list[dict]) -> dict:
        evidence, events, findings = [], [], []
        mapped_states = 0
        for row in rows:
            timestamp = int(row.get("timestamp") or 0)
            state = row.get("advantage_state_before_death")
            mapped_states += state is not None
            state_text = str(state).replace("_", " ") if state is not None else "UNKNOWN"
            killer = row.get("killer_champion") or "killer unavailable"
            killer_position = row.get("killer_position")
            killer_text = f"killed by {killer}" + (f" ({str(killer_position).replace('_', ' ')})" if killer_position else "")
            zone = row.get("death_zone_approx")
            headline = f"{_time(timestamp)} • pre-death state {state_text} • {killer_text}"
            if zone:
                headline += f" • zone {str(zone).replace('_', ' ')}"

            score, label = row.get("resource_cost_score"), row.get("resource_cost_label")
            if score is not None:
                cost_text = f"historical severity {float(score):.1f}/100" + (f" ({label})" if label else "")
            elif label:
                cost_text = f"historical severity {label} • {int(row.get('score_reference_size') or 0)} prior-death reference(s)"
            else:
                cost_text = "historical severity unavailable"
            costs = []
            for name, key, precision in (("Gold", "gold_cost_60", 0), ("CS", "cs_cost_60", 1), ("XP", "xp_cost_60", 0)):
                if row.get(key) is not None:
                    costs.append(f"{name} {float(row[key]):.{precision}f}")
            impact_text = cost_text
            if row.get("impact_interval_seconds") is not None:
                impact_text += f" • {float(row['impact_interval_seconds']):.0f}s bracket"
            if costs:
                impact_text += " • relative costs " + ", ".join(costs)

            context = []
            if row.get("current_gold_before_death") is not None:
                context.append(f"unspent Gold {float(row['current_gold_before_death']):.0f}")
            if row.get("killed_by_enemy_jungler"):
                context.append("enemy jungler was the killer")
            if row.get("trade"):
                context.append("trade observed (enemy jungler killed)" if row.get("enemy_jungle_trade") else "trade observed")
            enemy_obj, ally_obj, enemy_towers = (int(row.get(key) or 0) for key in ("enemy_objectives_after", "ally_objectives_after", "enemy_towers_after"))
            if enemy_obj or ally_obj or enemy_towers:
                context.append(f"{OBJECTIVE_WINDOW_SECONDS}s context: enemy objectives {enemy_obj}, ally objectives {ally_obj}, allied towers lost {enemy_towers}")
            if row.get("death_chain"):
                context.append(f"death chain size {int(row.get('death_chain_size') or 0)}")
            if row.get("death_spiral"):
                context.append(f"severe death spiral {float(row.get('death_spiral_score') or 0):.1f}/100")
            lines = [headline, impact_text] + (["v11 context: " + " • ".join(context)] if context else [])
            evidence.append("\n  ".join(lines))
            metrics = [
                _metric("État avant la mort", _enum(state), "advantage_state_before_death"),
                _metric("Coût historique", f"{_number(score)}/100" if score is not None else _enum(label), "resource_cost_score/resource_cost_label"),
                _metric("Tueur", f"{killer}" + (f" · {killer_position}" if killer_position else ""), "killer_champion/killer_position"),
                _metric("Zone approximative", _enum(zone), "death_zone_approx"),
            ]
            if costs:
                metrics.append(_metric("Coûts relatifs", ", ".join(costs), "gold_cost_60/cs_cost_60/xp_cost_60"))
            events.append({"title": f"Mort à {_time(timestamp)}", "subtitle": "Évidence Death Analyzer v11",
                           "status": "AVAILABLE", "severity": "INFO", "metrics": metrics,
                           "context": context, "item_ids": [],
                           "technical": [f"advantage_state_before_death={state}", f"resource_cost_label={label}", f"score_reference_size={row.get('score_reference_size')}"]})
            normalized = str(label or "").upper()
            if any(token in normalized for token in ("HIGH", "VERY", "ÉLEV", "ELEV")):
                findings.append({"title": f"Mort à coût historique {label}", "detail": f"À {_time(timestamp)}, coût relatif v11 {(_number(score) + '/100') if score is not None else label}.", "severity": "HIGH", "supported": True})
        return {"title": "Morts", "summary": (f"{len(rows)} mort(s) analysée(s) par v11 ; état avant la mort disponible pour {mapped_states}/{len(rows)}." if rows else "Aucune mort dans la sortie v11 de cette partie."),
                "status": "AVAILABLE", "severity": "INFO", "evidence": evidence, "events": events,
                "findings": findings, "technical_details": [], "source_version": ANALYZER_VERSIONS["death"]}

    def _tempo_payload(self, summary: dict) -> dict:
        events, evidence, findings = [], [], []
        for phase, values in (summary or {}).items():
            if not isinstance(values, dict):
                continue
            metrics = [
                _metric("Durée analysée", _number(values.get("minutes"), ".1f", " min"), "minutes"),
                _metric("Tempo historique", f"{_number(values.get('tempo_score'))}/100" if values.get("tempo_score") is not None else "—", "tempo_score"),
                _metric("Pathing historique", f"{_number(values.get('pathing_score'))}/100" if values.get("pathing_score") is not None else "—", "pathing_score"),
                _metric("XP personnel/min", _number(values.get("player_xp_per_min"), ".0f"), "player_xp_per_min"),
                _metric("CS jungle/min", _number(values.get("player_jungle_cs_per_min"), ".2f"), "player_jungle_cs_per_min"),
                _metric("Gold relatif/min", _number(values.get("relative_gold_per_min"), "+.0f"), "relative_gold_per_min"),
                _metric("XP relatif/min", _number(values.get("relative_xp_per_min"), "+.0f"), "relative_xp_per_min"),
                _metric("CS jungle relatifs/min", _number(values.get("relative_jungle_cs_per_min"), "+.2f"), "relative_jungle_cs_per_min"),
            ]
            holes = int(values.get("sustained_pathing_holes") or 0)
            watches = int(values.get("single_minute_watches") or 0)
            alerts = []
            if holes:
                alerts.append(f"{holes} épisode(s) de pathing durable signalé(s) par v17")
                findings.append({"title": f"Pathing — phase {phase}", "detail": alerts[-1], "severity": "HIGH", "supported": True})
            if watches:
                alerts.append(f"{watches} surveillance(s) ponctuelle(s) v17")
                findings.append({"title": f"Tempo — phase {phase}", "detail": alerts[-1], "severity": "MEDIUM", "supported": True})
            events.append({"title": _enum(phase).title(), "subtitle": "Mesures exactes par phase v17", "status": "AVAILABLE", "severity": "INFO", "metrics": metrics, "context": alerts, "item_ids": [],
                           "technical": [f"phase={phase}", f"farmable_minutes={values.get('farmable_minutes')}", f"mirrored_minutes={values.get('mirrored_minutes')}", f"strict_minutes={values.get('strict_minutes')}", f"farmable_xp_per_min={values.get('farmable_xp_per_min')}", f"farmable_jungle_cs_per_min={values.get('farmable_jungle_cs_per_min')}", f"mirrored_relative_gold_per_min={values.get('mirrored_relative_gold_per_min')}", f"mirrored_relative_xp_per_min={values.get('mirrored_relative_xp_per_min')}", f"mirrored_relative_jungle_cs_per_min={values.get('mirrored_relative_jungle_cs_per_min')}"]})
            evidence.append(f"{phase}: tempo={values.get('tempo_score')}, pathing={values.get('pathing_score')}, sustained_pathing_holes={holes}, single_minute_watches={watches}")
        return {"title": "Tempo / Pathing", "summary": (f"{len(events)} phase(s) exposée(s) par v17." if events else "Aucune phase Tempo v17 disponible pour cette partie."), "status": "AVAILABLE" if events else "PARTIAL", "severity": "INFO", "evidence": evidence, "events": events, "findings": findings, "technical_details": [], "source_version": ANALYZER_VERSIONS["tempo"]}

    def _objective_payload(self, rows: list[dict]) -> dict:
        events, evidence, findings = [], [], []
        for row in rows:
            timestamp = int(row.get("timestamp") or 0)
            kind, sequence = row.get("objective_kind"), row.get("sequence_classification")
            prep_score, conversion_score = row.get("preparation_score"), row.get("conversion_score")
            metrics = [
                _metric("Issue", _enum(row.get("secured_side")), "secured_side"),
                _metric("Séquence", _enum(sequence), "sequence_classification"),
                _metric("Proximité joueur / adverse", f"{_enum(row.get('player_proximity_pre'))} / {_enum(row.get('opponent_proximity_pre'))}", "player_proximity_pre/opponent_proximity_pre"),
                _metric("État d’entrée", _enum(row.get("entry_state")), "entry_state"),
                _metric("Diff. Gold / XP / JCS / niveau", f"{_number(row.get('entry_gold_diff'), '+.0f')} / {_number(row.get('entry_xp_diff'), '+.0f')} / {_number(row.get('entry_jungle_cs_diff'), '+.0f')} / {_number(row.get('entry_level_diff'), '+.0f')}", "entry_*_diff"),
                _metric("Évidence de contest", _enum(row.get("contest_evidence")), "contest_evidence"),
                _metric("Évidence de trade", _enum(row.get("trade_evidence")), "trade_evidence"),
                _metric("Préparation vs historique", f"{_number(prep_score)}/100 · {_enum(row.get('preparation_label'))}" if prep_score is not None else _enum(row.get("preparation_label")), "preparation_score/label"),
                _metric("Conversion vs historique", f"{_number(conversion_score)}/100 · {_enum(row.get('conversion_label'))}" if conversion_score is not None else _enum(row.get("conversion_label")), "conversion_score/label"),
            ]
            context = []
            if row.get("short_pre_objective_death"):
                context.append("mort du joueur dans les 60 s avant l’objectif")
            elif row.get("pre_objective_death"):
                context.append("mort du joueur dans les 120 s avant l’objectif")
            ally_counter, enemy_counter = row.get("ally_counter_objectives") or [], row.get("enemy_counter_objectives") or []
            if ally_counter or enemy_counter:
                context.append(f"contre-objectifs alliés {', '.join(ally_counter) or 'aucun'} · adverses {', '.join(enemy_counter) or 'aucun'}")
            raw_sequence = str(sequence or "")
            if raw_sequence and raw_sequence not in ("SECURED", "UNKNOWN"):
                findings.append({"title": f"{kind or 'Objectif'} à {_time(timestamp)}", "detail": f"Séquence v20 : {_enum(raw_sequence)}" + (f" ; contest {_enum(row.get('contest_evidence'))}." if row.get("contest_evidence") else "."), "severity": "MEDIUM", "supported": True})
            events.append({"title": f"{_enum(kind).title()} · {_time(timestamp)}", "subtitle": f"{_enum(row.get('secured_side')).title()} · {_enum(sequence)}", "status": "AVAILABLE", "severity": "INFO", "metrics": metrics, "context": context, "item_ids": [],
                           "technical": [f"objective_kind={kind}", f"objective_family={row.get('objective_family')}", f"monster_type={row.get('monster_type')}", f"prior_trade_context={row.get('prior_trade_context')}", f"preparation_reference={row.get('preparation_reference_scope')} N={row.get('preparation_reference_size')}", f"conversion_reference={row.get('conversion_reference_scope')} N={row.get('conversion_reference_size')}", f"resource_compensation_gold_change={row.get('resource_compensation_gold_change')}", f"resource_compensation_xp_change={row.get('resource_compensation_xp_change')}", f"resource_compensation_jungle_cs_change={row.get('resource_compensation_jungle_cs_change')}", f"frozen_tempo_score_change={row.get('frozen_tempo_score_change')}"]})
            evidence.append(f"{_time(timestamp)} • {kind} • secured_side={row.get('secured_side')} • sequence_classification={sequence} • preparation={prep_score}/{row.get('preparation_label')} • conversion={conversion_score}/{row.get('conversion_label')}")
        return {"title": "Objectifs", "summary": f"{len(rows)} fenêtre(s) d’objectif reconstruite(s) par v20.", "status": "AVAILABLE" if rows else "PARTIAL", "severity": "INFO", "evidence": evidence, "events": events, "findings": findings, "technical_details": [], "source_version": ANALYZER_VERSIONS["objectives"]}

    def _reset_payload(self, rows: list[dict]) -> dict:
        events, evidence, findings = [], [], []
        for row in rows:
            timestamp = int(row.get("start_timestamp") or 0)
            score, label, ref_size = row.get("reentry_score"), row.get("reentry_label"), int(row.get("reentry_reference_size") or 0)
            production = f"{_number(score)}/100 · {_enum(label)}" if score is not None else _enum(label)
            metrics = [
                _metric("Origine", _enum(row.get("reset_origin")), "reset_origin"),
                _metric("Séquence", _enum(row.get("sequence_classification")), "sequence_classification"),
                _metric("Achats / ventes / annulations", f"{int(row.get('purchase_count') or 0)} / {int(row.get('sale_count') or 0)} / {int(row.get('undo_count') or 0)}", "purchase_count/sale_count/undo_count"),
                _metric("Gold avant / dépensé (proxy)", f"{_number(row.get('current_gold_before_frame'), '.0f')} / {_number(row.get('current_gold_drop_proxy'), '.0f')}", "current_gold_before_frame/current_gold_drop_proxy"),
                _metric("Diff. entrée Gold / XP / JCS", f"{_number(row.get('entry_gold_diff'), '+.0f')} / {_number(row.get('entry_xp_diff'), '+.0f')} / {_number(row.get('entry_jungle_cs_diff'), '+.0f')}", "entry_*_diff"),
                _metric("Diff. ré-entrée Gold / XP / JCS", f"{_number(row.get('reentry_gold_diff'), '+.0f')} / {_number(row.get('reentry_xp_diff'), '+.0f')} / {_number(row.get('reentry_jungle_cs_diff'), '+.0f')}", "reentry_*_diff"),
                _metric("Production après reset vs historique", production, "reentry_score/reentry_label"),
            ]
            context = []
            if row.get("post_reset_death_120"):
                context.append("mort observée dans les 120 s après le proxy de reset")
            if row.get("high_unspent_gold_context"):
                context.append("contexte exploratoire : Gold non dépensé élevé avant le proxy")
            if score is not None and ref_size > 0 and str(label) in ("LOW", "BELOW_BASELINE"):
                findings.append({"title": f"Production après reset à {_time(timestamp)}", "detail": f"Production observée sous la référence historique v21 ({_number(score)}/100, N={ref_size}). Ce signal ne qualifie pas causalement le reset.", "severity": "MEDIUM", "supported": True})
            item_ids = [int(value) for value in row.get("purchased_item_ids") or [] if value]
            events.append({"title": f"Reset / shop à {_time(timestamp)}", "subtitle": f"{_enum(row.get('phase')).title()} · {_enum(row.get('reset_origin'))}", "status": "AVAILABLE", "severity": "INFO", "metrics": metrics, "context": context, "item_ids": item_ids,
                           "technical": [f"reset_origin={row.get('reset_origin')}", f"sequence_classification={row.get('sequence_classification')}", f"reentry_label={label}", f"reentry_reference={row.get('reentry_reference_scope')} N={ref_size}", f"frozen_pre_tempo_score={row.get('frozen_pre_tempo_score')}", f"frozen_post_tempo_score={row.get('frozen_post_tempo_score')}", f"frozen_tempo_score_change={row.get('frozen_tempo_score_change')}", "Le score de ré-entrée mesure une production observée après le proxy ; il ne prouve pas la qualité causale du reset."]})
            evidence.append(f"{_time(timestamp)} • Production après reset vs historique: {production} • reference={row.get('reentry_reference_scope')} N={ref_size}")
        return {"title": "Recalls / Resets", "summary": f"{len(rows)} séquence(s) SHOP/RESET proxy v21. Les scores décrivent la production observée après le proxy, sans causalité.", "status": "AVAILABLE" if rows else "PARTIAL", "severity": "INFO", "evidence": evidence, "events": events, "findings": findings, "technical_details": [], "source_version": ANALYZER_VERSIONS["resets"]}

    def _build_payload(self, match: dict | None) -> dict:
        if not match:
            return {"title": "Build / Itemisation", "summary": "Aucune reconstruction v22 disponible pour cette partie.", "status": "UNAVAILABLE", "severity": "INFO", "evidence": [], "events": [], "findings": [], "technical_details": [], "source_version": ANALYZER_VERSIONS["build"]}
        validation, milestones = match.get("final_validation") or {}, match.get("milestones") or {}
        status = str(validation.get("status") or "UNKNOWN")
        final_counter = validation.get("riot_final_counter") or {}
        final_items = [int(item_id) for item_id, count in final_counter.items() for _ in range(int(count))]
        trinket = validation.get("riot_trinket")
        if trinket:
            final_items.append(int(trinket))
        events = [{"title": "Build final Riot", "subtitle": f"Reconstruction {status}", "status": "AVAILABLE" if status.startswith("EXACT") else "PARTIAL", "severity": "INFO", "metrics": [_metric("Validation", status, "final_validation.status"), _metric("Objets d’inventaire", len(final_items) - (1 if trinket else 0), "final_validation.riot_final_counter"), _metric("Trinket", trinket or "—", "final_validation.riot_trinket")], "context": ["Présentation factuelle ; aucune recommandation de build optimal."], "item_ids": final_items, "technical": [f"reconstructed_final_counter={dict(validation.get('reconstructed_final_counter') or {})}", f"effective_reconstructed_final_counter={dict(validation.get('effective_reconstructed_final_counter') or {})}"]}]
        named = (("Premier achat significatif", milestones.get("first_meaningful_purchase")), ("Achat de bottes", milestones.get("boots_purchase")), ("Amélioration des bottes", milestones.get("boots_upgrade")))
        for title, milestone in named:
            if milestone:
                events.append({"title": title, "subtitle": milestone.get("time") or _time(milestone.get("timestamp")), "status": "AVAILABLE", "severity": "INFO", "metrics": [_metric("Objet", milestone.get("item_name") or milestone.get("item_id"), "milestones")], "context": [], "item_ids": [milestone.get("item_id")], "technical": [f"item_id={milestone.get('item_id')}"]})
        for index, milestone in enumerate(milestones.get("completed_major_items") or [], 1):
            events.append({"title": f"Objet majeur #{index}", "subtitle": milestone.get("time") or _time(milestone.get("timestamp")), "status": "AVAILABLE", "severity": "INFO", "metrics": [_metric("Objet", milestone.get("item_name") or milestone.get("item_id"), "milestones.completed_major_items")], "context": [], "item_ids": [milestone.get("item_id")], "technical": [f"item_id={milestone.get('item_id')}"]})
        technical = [f"{row.get('time') or _time(row.get('timestamp'))} | {row.get('event_type')} | {row.get('item_name') or row.get('item_id')} | visit={row.get('shop_visit_id')} | reconstruction={row.get('reconstruction_status')}" for row in match.get("transactions") or []]
        return {"title": "Build / Itemisation", "summary": f"Build final et {max(0, len(events)-1)} jalon(s) factuel(s) reconstruits par v22 : {status}. Aucune conclusion de build optimal.", "status": "AVAILABLE" if status.startswith("EXACT") else "PARTIAL", "severity": "INFO", "evidence": [f"final_validation.status={status}", f"completed_major_items={len(milestones.get('completed_major_items') or [])}"], "events": events, "findings": [], "technical_details": technical, "source_version": ANALYZER_VERSIONS["build"]}

    @staticmethod
    def _unavailable(title: str, reason: str, source_version: str) -> dict:
        return {"title": title, "summary": reason, "status": "UNAVAILABLE", "severity": "INFO", "evidence": [], "events": [], "findings": [], "technical_details": [], "source_version": source_version}

    def generate_for_matches(self, match_ids: Iterable[str], progress: Callable[[str], None] | None = None) -> dict:
        ids = list(dict.fromkeys(match_ids))
        player = self.local_data.player() if self.local_data else None
        if not ids or not player or not player.puuid:
            return {"target": len(ids), "generated": 0, "current": 0}
        details = {match_id: self.local_data.match_detail(match_id) for match_id in ids}
        groups: dict[str, list[str]] = {}
        for match_id, detail in details.items():
            role = (detail.match.position if detail else "UNKNOWN").upper()
            groups.setdefault(role, []).append(match_id)
        generated = 0

        for role, role_ids in groups.items():
            datasets: dict[str, object] = {}
            def attempt(name: str, function):
                if progress:
                    progress(f"Analyse {name} · {role}")
                try:
                    datasets[name] = function()
                except Exception as error:
                    datasets[name] = error

            attempt("death", lambda: build_death_cost_dataset(player.puuid, position=role))
            attempt("build", lambda: build_itemization_history(player.puuid, position=role))
            if role == "JUNGLE":
                attempt("bundles", lambda: load_tempo_bundles(player.puuid, position=role))
                bundles = datasets.get("bundles") if isinstance(datasets.get("bundles"), list) else []
                deaths = datasets.get("death") if isinstance(datasets.get("death"), list) else []
                attempt("tempo", lambda: build_tempo_intervals(bundles))
                tempo = datasets.get("tempo") if isinstance(datasets.get("tempo"), list) else []
                attempt("objectives", lambda: build_objective_dataset(bundles, deaths, tempo))
                objectives = datasets.get("objectives") if isinstance(datasets.get("objectives"), list) else []
                attempt("resets", lambda: build_reset_dataset(bundles, deaths, tempo, objectives))
            deaths = datasets.get("death") if isinstance(datasets.get("death"), list) else []
            tempo = datasets.get("tempo") if isinstance(datasets.get("tempo"), list) else []
            objectives = datasets.get("objectives") if isinstance(datasets.get("objectives"), list) else []
            resets = datasets.get("resets") if isinstance(datasets.get("resets"), list) else []
            build_history = datasets.get("build") if isinstance(datasets.get("build"), dict) else {}
            build_by_match = {row.get("match_id"): row for row in build_history.get("matches", [])}

            for match_id in role_ids:
                payloads = {"death": self._death_payload(get_match_death_costs(deaths, match_id)), "build": self._build_payload(build_by_match.get(match_id))}
                if role == "JUNGLE":
                    payloads.update({"tempo": self._tempo_payload(summarize_match_phases(tempo, match_id)), "objectives": self._objective_payload(get_match_objectives(objectives, match_id)), "resets": self._reset_payload(get_match_resets(resets, match_id))})
                else:
                    reason = f"Analyzer jungle non appliqué : rôle local {role or 'UNKNOWN'}."
                    payloads.update({"tempo": self._unavailable("Tempo / Pathing", reason, ANALYZER_VERSIONS["tempo"]), "objectives": self._unavailable("Objectifs", reason, ANALYZER_VERSIONS["objectives"]), "resets": self._unavailable("Recalls / Resets", reason, ANALYZER_VERSIONS["resets"])})
                for name, payload in payloads.items():
                    source_error = datasets.get(name)
                    if isinstance(source_error, Exception):
                        payload = self._unavailable(payload["title"], "Échec isolé de l’analyzer ; la partie locale reste consultable.", ANALYZER_VERSIONS[name])
                        payload["status"] = "ERROR"
                    self.cache.save_report(match_id, name, ANALYZER_CACHE_VERSIONS[name], payload["status"], payload)
                    generated += 1
        return {"target": len(ids), "generated": generated, "current": generated // len(ANALYZER_VERSIONS)}

    def get_match_insights(self, match_id: str) -> CoachingReport:
        reports = {report["analyzer"]: report for report in self.cache.reports(match_id) if ANALYZER_CACHE_VERSIONS.get(report["analyzer"]) == report["version"]}
        insights = []
        for name, version in ANALYZER_VERSIONS.items():
            report = reports.get(name)
            if report is None:
                insights.append(InsightViewModel(name.upper(), name.title(), "Aucune analyse compatible avec la version de présentation actuelle n’est en cache.", status="UNAVAILABLE", source_module=name, source_version=version))
                continue
            payload = report["payload"]
            insights.append(InsightViewModel(report["analyzer"].upper(), str(payload.get("title") or report["analyzer"]), str(payload.get("summary") or "UNAVAILABLE"), str(payload.get("severity") or "INFO"), str(report["status"]), tuple(str(value) for value in payload.get("evidence", [])), report["analyzer"], source_version=str(payload.get("source_version") or version), findings=tuple(value for value in payload.get("findings", []) if isinstance(value, dict)), events=tuple(value for value in payload.get("events", []) if isinstance(value, dict)), technical_details=tuple(str(value) for value in payload.get("technical_details", []))))
        if all(row.status == "UNAVAILABLE" for row in insights):
            overall = "UNAVAILABLE"
        else:
            overall = "AVAILABLE" if all(row.status == "AVAILABLE" for row in insights) else "PARTIAL"
        return CoachingReport(match_id, tuple(insights), overall)
