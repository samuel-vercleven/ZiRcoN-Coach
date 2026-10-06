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
    situation_id: str = "review_general"
    review_question: str = ""
    conditional_alternative: str = ""
    experiment_check: str = ""


_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
_TIME_RE = re.compile(r"(?<!\d)([0-9]{1,2}:[0-5][0-9])(?!\d)")


def _event_for_finding(insight: InsightViewModel, finding: dict) -> dict | None:
    """Link a supported finding to its event without guessing across phases."""
    text = f"{finding.get('title', '')} {finding.get('detail', '')}"
    time_match = _TIME_RE.search(text)
    if time_match:
        time = time_match.group(1)
        linked = [event for event in insight.events if any(match.group(1) == time for match in _TIME_RE.finditer(str(event.get("title", ""))))]
        return linked[0] if len(linked) == 1 else None

    phase_match = re.search(r"phase\s+(.+)$", str(finding.get("title", "")), re.IGNORECASE)
    if phase_match:
        phase = phase_match.group(1).strip().casefold().replace("_", " ")
        for event in insight.events:
            technical = " ".join(str(value) for value in (event.get("technical") or ()))
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
        str(metric.get("label", "")): str(metric.get("value") if metric.get("value") is not None else "—")
        for metric in (event.get("metrics") or ())
        if isinstance(metric, dict) and metric.get("label")
    }


def _readable(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _known(value: str) -> bool:
    return value.strip().casefold() not in ('', '—', 'none', 'unknown', 'unavailable', 'inconnu', 'indisponible')


def _objective_situation(value: str) -> str:
    """Interpret only the adapter's explicit categories, never a spawn timer."""
    value = value.strip().casefold()
    if value in ('juste avant un objectif', 'avant un objectif', 'tight_pre_objective', 'pre_objective'):
        return 'before'
    if value in ('après un objectif', 'post_objective'):
        return 'after'
    if value in ('entre deux objectifs', 'between_objectives'):
        return 'between'
    return ''


def _focus_for(insight: InsightViewModel, finding: dict) -> CoachingFocus:
    title = str(finding.get("title") or "Signal observé")
    detail = str(finding.get("detail") or "Un signal pris en charge apparaît dans cette partie.")
    source = (insight.source_module or insight.category or insight.title).casefold()
    event = _event_for_finding(insight, finding)
    metrics = _metric_values(event)
    time_match = _TIME_RE.search(f"{title} {detail}")
    time = time_match.group(1) if time_match else None
    evidence = []
    situation = 'review_general'
    question = 'Quelle décision voulais-tu prendre, et quelles informations avais-tu à ce moment-là ?'
    alternative = 'Compare ton choix à une autre option réaliste dans le replay ; ne suppose pas qu’elle aurait forcément mieux réussi.'
    check = 'À la prochaine revue, note une décision que tu as choisie avant d’agir.'
    contexts = tuple(str(value) for value in ((event.get('context') or ()) if event else ()))

    if "death" in source or "mort" in source:
        score = metrics.get("Coût historique", "")
        state = metrics.get("État avant la mort", "")
        killer = metrics.get("Tueur", "")
        zone = metrics.get("Zone approximative", "")
        if time:
            observation = f"À {time}, une mort est repérée parmi les situations à revoir."
        else:
            observation = 'Une mort ressort dans tes repères de cette partie ; les informations disponibles ne permettent pas de préciser son contexte.'
        if _known(score):
            evidence.append(f"Coût comparé à tes parties précédentes : {score}")
        why = 'Revois le début de l’action : le bon point de comparaison est la décision avec les informations disponibles, pas seulement la mort.'
        action = 'Avant le prochain engagement, choisis une sortie et vérifie quels alliés peuvent te rejoindre.'
        situation = 'death_review'
        question = 'Quand pouvais-tu encore te retirer, et quels alliés pouvaient réellement suivre ?'
        alternative = 'Si les alliés ne pouvaient pas suivre, compare attendre leur arrivée à poursuivre seul. Leur disponibilité reste à vérifier dans le replay.'
        check = 'Dans la prochaine partie, repère une action où tu as prévu ta sortie avant d’engager.'
        normalized_state = state.strip().casefold()
        if normalized_state in ('behind', 'en retard'):
            situation = 'death_resource_deficit'
            observation = (f'À {time}, ' if time else '') + 'le repère de ressources indique un retard avant cette mort.'
            why = 'Le repère avant la mort indique un retard. Revois si tu cherchais un duel ou une action avec tes alliés ; le retard ne suffit pas à juger ce combat.'
            action = 'Quand le repère indique un retard, compare une action groupée à un duel avant de t’engager.'
            question = 'Qu’est-ce qui pouvait compenser ce retard : alliés présents, avantage numérique ou autre information visible ?'
            alternative = 'Si rien ne compensait le retard, compare retarder le combat à le prendre immédiatement. Ne conclus pas qu’un combat était impossible.'
        elif normalized_state in ('ahead', 'en avance'):
            situation = 'death_resource_advantage'
            observation = (f'À {time}, ' if time else '') + 'le repère de ressources indique une avance avant cette mort.'
            why = 'Le repère indique une avance avant cette mort. Revois surtout quand tu pouvais arrêter l’action ; une avance ne garantit pas de gagner le combat.'
            action = 'Même avec une avance, décide quand arrêter l’action avant de prolonger le combat.'
        chain_sizes = [int(match.group(1)) for value in contexts if (match := re.search(r'death chain size\s+(\d+)\b', value.casefold()))]
        if any(size >= 2 for size in chain_sizes):
            situation = 'death_chain_review'
            observation = (f'À {time}, ' if time else '') + 'cette mort appartient à une série de morts rapprochées.'
            why = 'Des morts rapprochées sont signalées. Compare leurs débuts pour voir si une même décision revient, sans supposer qu’elles ont toutes la même cause.'
            action = 'Après une mort, choisis ta reprise avant de repartir vers une nouvelle action.'
            question = 'Ces morts commencent-elles par un choix similaire, ou par des situations différentes ?'
            alternative = 'Si le même déplacement revient, compare une reprise avec les alliés à ce déplacement. Le trajet exact doit être revu, pas deviné.'
        if _known(state):
            evidence.append(f"État avant la mort : {_readable(state)}")
        if _known(killer):
            evidence.append(f"Tueur observé : {killer}")
        if _known(zone):
            evidence.append(f"Zone approximative : {_readable(zone)}")
        limitation = "Ce chiffre est un repère de comparaison, pas la preuve que cette mort a causé la suite de la partie."
        coach_title = {'death_resource_deficit': 'Chercher ce qui compense ton retard', 'death_resource_advantage': 'Avec une avance, savoir arrêter l’action', 'death_chain_review': 'Revoir ce qui revient entre tes morts'}.get(situation, 'Revoir le début de cette mort')
    elif "pathing" in title.casefold() or "tempo" in title.casefold() or "tempo" in source:
        phase = str(event.get("title")) if event else title.split("phase", 1)[-1].strip()
        phase = {'opening': 'ouverture de la partie', 'early': 'début de partie', 'mid': 'milieu de partie', 'late': 'fin de partie'}.get(phase.casefold(), phase)
        if metrics.get("Pathing historique") and metrics.get("Pathing historique") != "—":
            observation = f"Sur la période « {phase} », un repère sur tes déplacements ressort. Il ne décrit pas un trajet précis."
        else:
            observation = f"Sur la période « {phase} », ton rythme mérite une revue ; aucune erreur de trajet précise n’est établie."
        pathing = metrics.get("Pathing historique", "")
        tempo = metrics.get("Tempo historique", "")
        if pathing and pathing != "—":
            evidence.append(f"Repère sur tes déplacements : {pathing}")
        if tempo and tempo != "—":
            evidence.append(f"Repère de tempo sur la phase : {tempo}")
        why = 'Regarde où tes déplacements aboutissent : farm, aide à un allié ou préparation d’un objectif. Le repère ne dit pas quelles occasions étaient réellement accessibles.'
        action = 'Avant le prochain déplacement, choisis ta destination et ce que tu veux y faire.'
        situation = 'tempo_phase_review'
        question = 'Quel était le but du déplacement ? As-tu changé de destination après avoir reçu une nouvelle information ?'
        alternative = 'Si tu ne vois pas de but clair dans le replay, compare une destination choisie à l’avance à ce déplacement. Un détour peut aussi être justifié.'
        check = 'À la prochaine revue, retrouve un déplacement dont tu avais choisi le but avant de partir.'
        limitation = "Ce résumé regarde de grandes périodes ; il ne montre pas chaque décision ni tout ce que tu pouvais voir."
        coach_title = 'Donner un but au prochain déplacement'
    elif "reset" in source or "reset" in title.casefold() or "shop" in title.casefold():
        score = metrics.get("Production après reset vs historique", "")
        observation = f"Après le passage en boutique repéré vers {time}, la reprise est sous tes repères de production habituels." if time and event else 'La reprise après boutique ressort dans tes repères ; le contexte précis reste à vérifier.'
        origin = metrics.get("Origine", "").casefold()
        objective_timing = metrics.get("Timing objectif", "").casefold()
        event_context = tuple(str(value).casefold() for value in (event.get("context", ()) if event else ()))
        is_post_death = "mort" in origin
        death_followed_reset = any("mort observée dans les 120 s" in value for value in event_context)
        objective = _objective_situation(objective_timing)
        situation = 'shop_restart_review'
        question = 'En quittant la base, quelle destination avais-tu choisie et qu’est-ce qui a changé ensuite ?'
        alternative = 'Si tu n’avais pas de destination claire, compare rejoindre tes alliés à reprendre une tâche utile à ton rôle. Le replay doit confirmer ce qui était accessible.'
        check = 'Au prochain retour boutique, choisis ta première destination avant de sortir de la base.'
        if is_post_death:
            situation = 'shop_after_death'
            why = 'Ce passage en boutique suit une mort. On revoit ici la reprise, pas le choix de revenir à la base : ce retour était lié à la mort.'
            action = 'Après ta réapparition, choisis une première destination plutôt que de vouloir rattraper toute la carte.'
            question = 'À ta réapparition, quelle action pouvais-tu encore rejoindre sans arriver trop tard ?'
        elif death_followed_reset:
            observation += ' Une mort est ensuite observée dans les deux minutes.'
            why = "Une mort est survenue dans les deux minutes après ton retour à la base. Revois la séquence, sans en conclure que le retour ou le trajet l’a provoquée."
            situation = 'shop_followed_by_death'
            action = 'Avant de sortir de la base, choisis un trajet et vérifie quelles menaces tu connais déjà.'
            question = 'Quand as-tu eu une information sur le danger, et pouvais-tu encore changer de direction ?'
            alternative = 'Si la zone était sans information, compare une reprise côté alliés à ton trajet. Les données ne prouvent pas que la zone était sans vision.'
        elif objective == 'before':
            situation = 'shop_before_objective'
            why = 'Le temps entre ce passage et un objectif pris ensuite aide à situer le replay ; il ne juge pas à lui seul ton choix. Ce n’est pas un compte à rebours d’apparition.'
            action = 'Avant de repartir, choisis entre rejoindre un objectif préparé par l’équipe et reprendre ton activité.'
            question = 'L’équipe préparait-elle cet objectif au moment de ton départ, et pouvais-tu rejoindre cette action ?'
            alternative = 'Si l’équipe ne préparait pas l’objectif ou si l’accès était risqué, compare une reprise utile ailleurs. Ne suppose pas que tu devais forcément y aller.'
        elif objective == 'after':
            situation = 'shop_after_objective'
            why = 'Le passage en boutique est situé après un objectif enregistré. Revois la décision suivante, sans traiter cet objectif passé comme une urgence à rejoindre.'
            action = 'Après un objectif terminé, choisis la prochaine destination avant de sortir de la base.'
            question = 'Après cet objectif, quelle était la prochaine action utile pour toi et tes alliés ?'
        elif objective == 'between':
            situation = 'shop_between_objectives'
            why = 'Le passage est situé entre deux objectifs enregistrés. Cela situe la reprise, sans prouver qu’un objectif était disponible ou contestable à ce moment-là.'
            action = 'Entre deux actions d’équipe, choisis une reprise utile à ton rôle avant de quitter la base.'
        else:
            why = "Revois comment la reprise s’est déroulée après ton passage à la base ; ce constat ne dit pas que ton retour était mauvais."
            action = 'Avant de quitter la base, choisis ta destination et la première action que tu veux y faire.'
        if _known(score):
            evidence.append(f"Ressources gagnées après la reprise : {score}")
        for context_line in contexts:
            context_line = str(context_line)
            lowered_context = context_line.casefold()
            if "timing objectif" in lowered_context and objective:
                evidence.append('Contexte : retour à la base à proximité d’un objectif enregistré (' + {'before': 'avant', 'after': 'après', 'between': 'entre deux objectifs'}[objective] + ')')
            elif "mort observée" in lowered_context:
                evidence.append("Contexte : une mort est survenue dans les deux minutes après le retour à la base")
            elif "gold non dépensé" in lowered_context:
                evidence.append("Repère : il te restait beaucoup d’or avant le retour à la base")
        limitation = "Les ressources après la reprise sont comparées à tes parties précédentes ; ce repère n’explique pas à lui seul le résultat."
        coach_title = {'shop_after_death': 'Choisir ta reprise après une mort', 'shop_followed_by_death': 'Revoir le départ qui précède cette mort', 'shop_before_objective': 'Relier ton départ à l’action de l’équipe', 'shop_after_objective': 'Choisir la suite après un objectif', 'shop_between_objectives': 'Choisir une reprise entre deux objectifs'}.get(situation, 'Préparer la sortie de boutique')
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
        situation_id=situation,
        review_question=question,
        conditional_alternative=alternative,
        experiment_check=check,
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
