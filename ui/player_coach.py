"""Player-facing coaching assembled only from explicitly supported findings."""

from __future__ import annotations

import re
from dataclasses import dataclass

from viewmodels import CoachingReport, InsightViewModel


@dataclass(frozen=True)
class CoachingFocus:
    title: str
    observation: str
    why_review: str
    next_game_experiment: str
    evidence: tuple[str, ...]
    limitation: str
    source: str
    source_tab_title: str
    severity: str


_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
_TIME_RE = re.compile(r"\b([0-9]{1,2}:[0-9]{2})\b")


def _event_for_finding(insight: InsightViewModel, finding: dict) -> dict | None:
    """Link a supported finding to its event without guessing across phases."""
    text = f"{finding.get('title', '')} {finding.get('detail', '')}"
    time_match = _TIME_RE.search(text)
    if time_match:
        time = time_match.group(1)
        return next((event for event in insight.events if time in str(event.get("title", ""))), None)

    phase_match = re.search(r"phase\s+(.+)$", str(finding.get("title", "")), re.IGNORECASE)
    if phase_match:
        phase = phase_match.group(1).strip().casefold().replace("_", " ")
        for event in insight.events:
            technical = " ".join(str(value) for value in event.get("technical", ()))
            event_phase = re.search(r"(?:^|\s)phase=([^\s]+)", technical, re.IGNORECASE)
            if event_phase and event_phase.group(1).casefold().replace("_", " ") == phase:
                return event
            if str(event.get("title", "")).casefold() == phase:
                return event
    return None


def _metric_values(event: dict | None) -> dict[str, str]:
    if not event:
        return {}
    return {
        str(metric.get("label", "")): str(metric.get("value", "—"))
        for metric in event.get("metrics", ())
        if isinstance(metric, dict) and metric.get("label")
    }


def _readable(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _focus_for(insight: InsightViewModel, finding: dict) -> CoachingFocus:
    title = str(finding.get("title") or "Signal observé")
    detail = str(finding.get("detail") or "Un signal pris en charge apparaît dans cette partie.")
    source = (insight.source_module or insight.category or insight.title).casefold()
    event = _event_for_finding(insight, finding)
    metrics = _metric_values(event)
    time_match = _TIME_RE.search(f"{title} {detail}")
    time = time_match.group(1) if time_match else None
    evidence = []

    if "death" in source or "mort" in source:
        score = metrics.get("Coût historique", "")
        state = metrics.get("État avant la mort", "")
        killer = metrics.get("Tueur", "")
        zone = metrics.get("Zone approximative", "")
        if time and score:
            observation = f"À {time}, l’indice historique de coût relatif de cette mort est de {score}."
        else:
            observation = detail
        why = "Ce repère sert à revoir le contexte autour de la mort, pas à conclure qu’elle explique à elle seule la suite de la partie."
        action = (
            f"Dans le replay autour de {time or 'ce moment'}, arrête-toi juste avant la mort : quelles menaces étaient visibles, "
            "quels alliés pouvaient suivre et quelle sortie restait possible ? À la prochaine situation comparable, teste une courte vérification avant de t’engager."
        )
        if state:
            evidence.append(f"État avant la mort : {_readable(state)}")
        if killer and killer not in ("—", "None"):
            evidence.append(f"Tueur observé : {killer}")
        if zone and zone not in ("—", "None"):
            evidence.append(f"Zone approximative : {_readable(zone)}")
        limitation = "L’indice est expérimental et relatif à une référence historique ; les fenêtres observées ne prouvent pas une causalité et peuvent se chevaucher."
        coach_title = "Revoir le contexte de cette mort"
    elif "pathing" in title.casefold() or "tempo" in title.casefold() or "tempo" in source:
        phase = str(event.get("title")) if event else title.split("phase", 1)[-1].strip()
        observation = "Pendant " + phase + ", " + detail.rstrip(".") + "."
        pathing = metrics.get("Pathing historique", "")
        tempo = metrics.get("Tempo historique", "")
        if pathing and pathing != "—":
            evidence.append(f"Repère de pathing sur la phase : {pathing}")
        if tempo and tempo != "—":
            evidence.append(f"Repère de tempo sur la phase : {tempo}")
        why = "Cette fenêtre vaut un replay pour comprendre ce que tu cherchais à obtenir sur la carte et si ton trajet servait cette priorité. Le signal ne désigne pas une route optimale."
        action = "Sur le replay de cette phase, formule d’abord ton objectif (farm, regroupement ou préparation d’objectif), puis vérifie si ton trajet réel y conduisait compte tenu de ce qui était disponible."
        limitation = "Le résultat est agrégé par phase de jeu ; il ne reconstitue pas à lui seul chaque décision ni la vision disponible seconde par seconde."
        coach_title = "Vérifier le choix de trajet"
    elif "reset" in source or "reset" in title.casefold() or "shop" in title.casefold():
        score = metrics.get("Production après reset vs historique", "")
        observation = f"Après le retour boutique vers {time}, la production observée est sous la référence historique{f' ({score})' if score else ''}." if time else detail
        why = "C’est utile pour examiner comment la reprise s’est enchaînée après la boutique ; ce constat ne dit pas que le retour boutique était mauvais."
        action = "À ton prochain retour, annonce-toi une destination de reprise (camp, lane ou préparation d’objectif) avant de quitter la base ; revois ensuite si ton premier trajet t’en a rapproché."
        if score:
            evidence.append(f"Production après reset vs historique : {score}")
        limitation = "Le retour est reconstruit à partir d’un proxy boutique, et la production postérieure est comparée à l’historique ; aucune causalité du reset n’est établie."
        coach_title = "Mieux relier boutique et reprise"
    else:
        observation = detail
        why = "Ce constat est conservé comme une question de replay ; les données disponibles ne suffisent pas à en faire un diagnostic plus précis."
        action = "Revois le moment indiqué et note ce que tu voulais faire, ce qui t’en a empêché et une seule décision à tester la prochaine fois."
        limitation = "Piste de revue prudente, pas une conclusion de cause à effet."
        coach_title = title

    if event and time is None:
        for label in ("Durée analysée", "XP personnel/min", "CS jungle/min"):
            value = metrics.get(label)
            if value and value != "—":
                evidence.append(f"{label} : {value}")
    if not evidence:
        evidence.append("Événement associé visible dans l’onglet d’analyse détaillée.")

    return CoachingFocus(
        title=coach_title,
        observation=observation,
        why_review=why,
        next_game_experiment=action,
        evidence=tuple(evidence[:3]),
        limitation=limitation,
        source=f"{insight.title} · {insight.source_version or insight.status}",
        source_tab_title=insight.title,
        severity=str(finding.get("severity") or "INFO").upper(),
    )


def coaching_focuses(report: CoachingReport, limit: int = 3) -> tuple[CoachingFocus, ...]:
    """Return concise, varied prompts; detailed same-analyzer events remain in their tabs."""
    if limit <= 0:
        return ()
    candidates = []
    for analyzer_index, insight in enumerate(report.insights):
        if insight.status not in ("AVAILABLE", "PARTIAL"):
            continue
        for finding_index, finding in enumerate(insight.findings):
            if finding.get("supported") is not True:
                continue
            severity = str(finding.get("severity") or "INFO").upper()
            candidates.append((
                _SEVERITY_ORDER.get(severity, 9), analyzer_index, finding_index,
                _focus_for(insight, finding),
            ))
    candidates.sort(key=lambda item: item[:3])
    selected = []
    selected_families = set()
    for _severity, analyzer_index, _finding_index, focus in candidates:
        insight = report.insights[analyzer_index]
        family = (insight.source_module or insight.category or insight.title).casefold()
        if family in selected_families:
            continue
        selected_families.add(family)
        selected.append(focus)
        if len(selected) >= limit:
            break
    return tuple(selected)


def coaching_empty_message(report: CoachingReport) -> str:
    if all(insight.status == "UNAVAILABLE" for insight in report.insights):
        return "Les analyses de cette partie ne sont pas disponibles. Synchronise ou régénère les analyses pour obtenir des pistes personnalisées."
    if any(insight.status != "AVAILABLE" for insight in report.insights):
        return "Les données disponibles ne font pas ressortir de piste assez étayée pour te conseiller. Certaines analyses sont absentes ou partielles ; leurs faits restent consultables dans les onglets dédiés."
    return "Aucune piste de coaching assez étayée n’a été isolée dans cette partie. Les moments et mesures disponibles restent consultables dans les onglets d’analyse."
