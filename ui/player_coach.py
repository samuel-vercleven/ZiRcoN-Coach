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
            observation = f"À {time}, cette mort ressort parmi les moments à revoir dans tes repères habituels."
            evidence.append(f"Coût comparé à tes parties précédentes : {score}")
        else:
            observation = detail
        why = "Ce repère sert à revoir le contexte autour de la mort, pas à conclure qu’elle explique à elle seule la suite de la partie."
        action = "Avant de t’engager, vérifie les menaces visibles, les alliés qui peuvent suivre et une sortie possible."
        if state:
            evidence.append(f"État avant la mort : {_readable(state)}")
        if killer and killer not in ("—", "None"):
            evidence.append(f"Tueur observé : {killer}")
        if zone and zone not in ("—", "None"):
            evidence.append(f"Zone approximative : {_readable(zone)}")
        limitation = "Ce chiffre est un repère de comparaison, pas la preuve que cette mort a causé la suite de la partie."
        coach_title = "Revoir le contexte de cette mort"
    elif "pathing" in title.casefold() or "tempo" in title.casefold() or "tempo" in source:
        phase = str(event.get("title")) if event else title.split("phase", 1)[-1].strip()
        if metrics.get("Pathing historique") and metrics.get("Pathing historique") != "—":
            observation = f"Pendant {phase}, tes déplacements méritent d’être revus par rapport aux occasions disponibles."
        else:
            observation = f"Pendant {phase}, quelques moments méritent d’être revus pour comprendre ton rythme."
        pathing = metrics.get("Pathing historique", "")
        tempo = metrics.get("Tempo historique", "")
        if pathing and pathing != "—":
            evidence.append(f"Repère sur tes déplacements : {pathing}")
        if tempo and tempo != "—":
            evidence.append(f"Repère de tempo sur la phase : {tempo}")
        why = "Revois cette période pour comprendre ce que tu voulais faire sur la carte et si tes déplacements t’en rapprochaient."
        action = "Choisis ta priorité — farm, regroupement ou objectif — avant de partir, puis vérifie si ton trajet t’en rapproche."
        limitation = "Ce résumé regarde de grandes périodes ; il ne montre pas chaque décision ni tout ce que tu pouvais voir."
        coach_title = "Vérifier le choix de trajet"
    elif "reset" in source or "reset" in title.casefold() or "shop" in title.casefold():
        score = metrics.get("Production après reset vs historique", "")
        observation = f"Après ton retour à la base vers {time}, tu gagnes moins de ressources que dans tes repères habituels." if time else detail
        origin = metrics.get("Origine", "").casefold()
        objective_timing = metrics.get("Timing objectif", "").casefold()
        event_context = tuple(str(value).casefold() for value in (event.get("context", ()) if event else ()))
        is_post_death = "mort" in origin
        death_followed_reset = any("mort observée dans les 120 s" in value for value in event_context)
        is_objective_window = any(token in objective_timing for token in ("objectif", "dragon", "héraut", "baron"))
        if is_post_death:
            why = "Après une mort, ce repère regarde les ressources gagnées à ta reprise ; il ne juge ni la mort ni ton retour à la base."
            action = "Après une mort, choisis une destination de reprise que tu peux rejoindre à temps."
        elif death_followed_reset:
            why = "Une mort est survenue dans les deux minutes après ton retour à la base. Revois la séquence, sans en conclure que le retour ou le trajet l’a provoquée."
            action = "En quittant la boutique, vérifie les menaces et tes alliés visibles avant de choisir ton trajet."
        elif is_objective_window:
            why = "Le moment de ton retour par rapport aux objectifs aide à revoir si tu pouvais rejoindre ta prochaine priorité à temps. Ce repère ne juge pas à lui seul ton choix."
            action = "Avant de quitter la base, compare ton temps de trajet au temps restant avant l’objectif."
        else:
            why = "Revois comment la reprise s’est déroulée après ton passage à la base ; ce constat ne dit pas que ton retour était mauvais."
            action = "Avant de quitter la base, choisis ta destination : camp, voie ou prochain objectif."
        if score:
            evidence.append(f"Ressources gagnées après la reprise : {score}")
        for context_line in (event.get("context", ()) if event else ()):
            context_line = str(context_line)
            lowered_context = context_line.casefold()
            if "timing objectif" in lowered_context:
                evidence.append("Contexte : retour à la base à proximité d’un objectif")
            elif "mort observée" in lowered_context:
                evidence.append("Contexte : une mort est survenue dans les deux minutes après le retour à la base")
            elif "gold non dépensé" in lowered_context:
                evidence.append("Repère : il te restait beaucoup d’or avant le retour à la base")
        limitation = "Les ressources après la reprise sont comparées à tes parties précédentes ; ce repère n’explique pas à lui seul le résultat."
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
        return "Les informations nécessaires à l’analyse de cette partie ne sont pas disponibles. Importe-la à nouveau pour obtenir des pistes personnalisées."
    if any(insight.status != "AVAILABLE" for insight in report.insights):
        return "Les informations disponibles ne suffisent pas pour te conseiller avec confiance. Certains moments de cette partie n’ont pas pu être examinés."
    return "Je n’ai pas repéré de piste assez claire pour cette partie. Cela ne prouve pas qu’il n’y avait rien à améliorer."
