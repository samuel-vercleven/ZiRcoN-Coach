import re
from collections import Counter, defaultdict

from knowledge.rune_knowledge import (
    DEFAULT_LOCALE,
    RUNE_FORMULA_INCOMPLETE,
    SEMANTIC_PARSER_SUPPORTED,
    build_observed_rune_audit,
    build_rune_knowledge_catalog,
)


BASELINE_RUNE_COUNT = 62
BASELINE_DDRAGON_VERSION = "16.16.1"

LEGACY_EFFECT_TYPES = {
    "HEALTH",
    "ARMOR",
    "MAGIC_RESISTANCE",
    "MOVE_SPEED",
    "ATTACK_SPEED",
    "ABILITY_HASTE",
    "ADAPTIVE_FORCE",
    "MANA",
    "ENERGY",
    "TENACITY",
}

KNOWN_UNPARSED_KINDS = {
    "UNPARSED_RUNE_TEXT",
    "PARTIALLY_STRUCTURED_RUNE_TEXT",
}


def _normalize(value):
    import unicodedata

    normalized = unicodedata.normalize("NFKD", str(value or ""))
    normalized = "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    )
    return normalized.lower()


def _contains_health_reference(normalized):
    return (
        re.search(r"(^|[^a-z])pv([^a-z]|$)", normalized) is not None
        or "points de vie" in normalized
    )


def _contains_self_gain_language(normalized):
    has_self_subject = any(
        token in normalized
        for token in (
            "vous ",
            "vous gagne",
            "vous obten",
            "vous rece",
            "vous augment",
            "votre ",
            "vos ",
        )
    )

    has_gain_action = any(
        token in normalized
        for token in (
            "gagne",
            "gagnez",
            "obten",
            "recev",
            "augmente",
            "augmentent",
            "confere",
            "octroie",
            "accorde",
        )
    )

    return has_self_subject and has_gain_action


def _contains_target_language(normalized):
    return any(
        token in normalized
        for token in (
            "cible",
            "ennemi",
            "ennemis",
            "champion adverse",
            "champions adverses",
        )
    )


def _contains_reduction_language(normalized):
    return any(
        token in normalized
        for token in (
            "reduit",
            "reduisez",
            "reduire",
            "diminue",
            "diminuez",
            "retire",
            "retirez",
            "perd ",
            "perdent ",
        )
    )


def _contains_scaling_language(normalized):
    return (
        "%" in normalized
        or "en fonction de" in normalized
        or "selon " in normalized
        or "base sur" in normalized
        or "equivalent" in normalized
    )


def _short(record):
    return f"{record['rune_id']} - {record['name']}"


def _new_report(catalog):
    return {
        "catalog": catalog,
        "blocking": [],
        "review": [],
        "info": [],
        "audited_rune_ids": set(),
        "effect_counts": Counter(),
        "review_by_rune": defaultdict(list),
    }


def _blocking(report, record, message, evidence=None):
    row = {
        "rune_id": record.get("rune_id") if record else None,
        "rune_name": record.get("name") if record else None,
        "message": message,
        "evidence": evidence,
    }
    report["blocking"].append(row)


def _review(report, record, message, evidence=None):
    row = {
        "rune_id": record.get("rune_id") if record else None,
        "rune_name": record.get("name") if record else None,
        "message": message,
        "evidence": evidence,
    }
    report["review"].append(row)
    if record:
        report["review_by_rune"][record["rune_id"]].append(row)


def _audit_catalog_structure(report):
    catalog = report["catalog"]
    records = catalog.get("records", {})
    summary = catalog.get("summary", {})

    if summary.get("total_runes") != len(records):
        _blocking(
            report,
            None,
            (
                "summary.total_runes ne correspond pas au nombre réel "
                f"de records ({summary.get('total_runes')} vs {len(records)})."
            ),
        )

    if summary.get("duplicate_rune_ids"):
        _blocking(
            report,
            None,
            f"IDs de rune dupliqués: {summary['duplicate_rune_ids']}",
        )

    if summary.get("invalid_rune_records"):
        _blocking(
            report,
            None,
            (
                "Des records de rune invalides sont présents: "
                f"{len(summary['invalid_rune_records'])}"
            ),
        )

    if len(records) != BASELINE_RUNE_COUNT:
        report["info"].append(
            (
                "Le nombre de runes diffère du baseline 16.16.1 "
                f"({len(records)} au lieu de {BASELINE_RUNE_COUNT}). "
                "Ce n'est pas automatiquement une erreur si Data Dragon "
                "a changé de patch."
            )
        )

    resolved_version = catalog.get("resolved_ddragon_version")
    if resolved_version != BASELINE_DDRAGON_VERSION:
        report["info"].append(
            (
                "Data Dragon utilisé: "
                f"{resolved_version}; baseline gel envisagé: "
                f"{BASELINE_DDRAGON_VERSION}."
            )
        )

    style_rune_ids = set()
    for style in catalog.get("styles", []):
        style_id = style.get("style_id")
        for slot in style.get("slots", []):
            slot_index = slot.get("slot_index")
            for rune_id in slot.get("rune_ids", []):
                if rune_id in style_rune_ids:
                    _blocking(
                        report,
                        records.get(rune_id),
                        "La rune apparaît dans plusieurs slots/styles.",
                    )
                style_rune_ids.add(rune_id)

                record = records.get(rune_id)
                if record is None:
                    _blocking(
                        report,
                        None,
                        (
                            f"Rune {rune_id} référencée dans l'arbre "
                            "mais absente de catalog.records."
                        ),
                    )
                    continue

                if record.get("style_id") != style_id:
                    _blocking(
                        report,
                        record,
                        "style_id du record différent du style parent.",
                    )

                if record.get("slot_index") != slot_index:
                    _blocking(
                        report,
                        record,
                        "slot_index du record différent du slot parent.",
                    )

    missing_from_tree = set(records) - style_rune_ids
    if missing_from_tree:
        _blocking(
            report,
            None,
            f"Runes présentes dans records mais absentes des arbres: {sorted(missing_from_tree)}",
        )


def _audit_effect_semantics(report, record, effect):
    effect_type = effect.get("effect_type")
    evidence = effect.get("evidence_text") or ""
    normalized = _normalize(evidence)

    report["effect_counts"][effect_type] += 1

    for required_key in (
        "effect_type",
        "source",
        "source_field",
        "confidence",
        "evidence_text",
        "ddragon_version",
    ):
        if effect.get(required_key) in (None, ""):
            _blocking(
                report,
                record,
                f"Effet {effect_type}: provenance incomplète ({required_key}).",
                evidence,
            )

    if effect_type in LEGACY_EFFECT_TYPES:
        _blocking(
            report,
            record,
            f"Ancien tag générique interdit encore présent: {effect_type}.",
            evidence,
        )

    # HEALTH
    if effect_type == "HEALTH_STAT_GAIN":
        if not _contains_health_reference(normalized):
            _blocking(
                report,
                record,
                "HEALTH_STAT_GAIN sans référence explicite aux PV.",
                evidence,
            )
        if not _contains_self_gain_language(normalized):
            _review(
                report,
                record,
                "HEALTH_STAT_GAIN sans langage de gain personnel suffisamment explicite.",
                evidence,
            )

    elif effect_type == "HEALTH_THRESHOLD_REFERENCE":
        if not _contains_health_reference(normalized):
            _blocking(
                report,
                record,
                "HEALTH_THRESHOLD_REFERENCE sans référence aux PV.",
                evidence,
            )
        threshold_markers = (
            "moins de",
            "plus de",
            "en dessous",
            "au-dessus",
            "a ",
            "infliger ",
        )
        if not any(marker in normalized for marker in threshold_markers):
            _review(
                report,
                record,
                "HEALTH_THRESHOLD_REFERENCE sans marqueur de seuil reconnu par l'audit.",
                evidence,
            )

    elif effect_type == "HEALTH_SCALING_REFERENCE":
        if not _contains_health_reference(normalized):
            _blocking(
                report,
                record,
                "HEALTH_SCALING_REFERENCE sans référence aux PV.",
                evidence,
            )
        if not _contains_scaling_language(normalized):
            _review(
                report,
                record,
                "HEALTH_SCALING_REFERENCE sans marqueur de scaling reconnu.",
                evidence,
            )

    elif effect_type == "HEALTH_REFERENCE":
        if not _contains_health_reference(normalized):
            _blocking(
                report,
                record,
                "HEALTH_REFERENCE sans référence aux PV.",
                evidence,
            )

    # ARMOR / MAGIC RESISTANCE
    for prefix, phrase in (
        ("ARMOR", "armure"),
        ("MAGIC_RESISTANCE", "resistance magique"),
    ):
        if not effect_type.startswith(prefix + "_"):
            continue

        if phrase not in normalized:
            _blocking(
                report,
                record,
                f"{effect_type} sans mention de {phrase}.",
                evidence,
            )

        if effect_type == f"{prefix}_STAT_GAIN":
            if not _contains_self_gain_language(normalized):
                _review(
                    report,
                    record,
                    f"{effect_type} sans langage de gain personnel suffisamment explicite.",
                    evidence,
                )

        elif effect_type == f"{prefix}_REDUCTION_TARGET":
            if not _contains_target_language(normalized):
                _review(
                    report,
                    record,
                    f"{effect_type} sans cible/ennemi explicitement identifié.",
                    evidence,
                )
            if not _contains_reduction_language(normalized):
                _review(
                    report,
                    record,
                    f"{effect_type} sans verbe de réduction reconnu.",
                    evidence,
                )

        elif effect_type == f"{prefix}_SCALING_REFERENCE":
            if not _contains_scaling_language(normalized):
                _review(
                    report,
                    record,
                    f"{effect_type} sans marqueur de scaling reconnu.",
                    evidence,
                )

    # MOVE SPEED
    if effect_type.startswith("MOVE_SPEED_"):
        if "vitesse de deplacement" not in normalized:
            _blocking(
                report,
                record,
                f"{effect_type} sans mention de vitesse de déplacement.",
                evidence,
            )
        if effect_type == "MOVE_SPEED_BONUS_AMPLIFICATION":
            if "plus efficace" not in normalized:
                _blocking(
                    report,
                    record,
                    "MOVE_SPEED_BONUS_AMPLIFICATION sans amplification explicite.",
                    evidence,
                )
        elif effect_type == "MOVE_SPEED_STAT_GAIN":
            if not any(
                token in normalized
                for token in (
                    "gagne",
                    "octroie",
                    "confere",
                    "augmente",
                    "augmentee",
                    "bonus",
                )
            ):
                _blocking(
                    report,
                    record,
                    "MOVE_SPEED_STAT_GAIN sans langage de gain reconnu.",
                    evidence,
                )

    # ATTACK SPEED
    if effect_type.startswith("ATTACK_SPEED_"):
        if "vitesse d'attaque" not in normalized:
            _blocking(
                report,
                record,
                f"{effect_type} sans mention de vitesse d'attaque.",
                evidence,
            )
        if effect_type == "ATTACK_SPEED_STAT_GAIN":
            if not any(
                token in normalized
                for token in ("gagne", "octroie", "augmente")
            ):
                _blocking(
                    report,
                    record,
                    "ATTACK_SPEED_STAT_GAIN sans langage de gain reconnu.",
                    evidence,
                )
        elif effect_type == "ATTACK_SPEED_SCALING_REFERENCE":
            if not (
                "degat" in normalized
                or "en fonction de" in normalized
                or "selon" in normalized
            ):
                _blocking(
                    report,
                    record,
                    "ATTACK_SPEED_SCALING_REFERENCE sans relation de scaling explicite.",
                    evidence,
                )

    # ABILITY HASTE
    if effect_type.startswith("ABILITY_HASTE_"):
        if "acceleration de competence" not in normalized:
            _blocking(
                report,
                record,
                f"{effect_type} sans mention d'accélération de compétence.",
                evidence,
            )
        if effect_type == "ABILITY_HASTE_STAT_GAIN":
            if not any(
                token in normalized
                for token in ("gagne", "octroie", "augmente")
            ):
                _blocking(
                    report,
                    record,
                    "ABILITY_HASTE_STAT_GAIN sans langage de gain reconnu.",
                    evidence,
                )

    # ADAPTIVE FORCE
    if effect_type.startswith("ADAPTIVE_FORCE_"):
        if "force adaptative" not in normalized:
            _blocking(
                report,
                record,
                f"{effect_type} sans mention de force adaptative.",
                evidence,
            )
        if effect_type == "ADAPTIVE_FORCE_STAT_GAIN":
            if not any(
                token in normalized
                for token in ("gagne", "gagner", "octroie", "bonus")
            ):
                _blocking(
                    report,
                    record,
                    "ADAPTIVE_FORCE_STAT_GAIN sans langage de gain reconnu.",
                    evidence,
                )

    # MANA
    if effect_type.startswith("MANA_"):
        if re.search(r"\bmana\b", normalized) is None:
            _blocking(
                report,
                record,
                f"{effect_type} sans mention de mana.",
                evidence,
            )
        if effect_type == "MANA_MAX_STAT_GAIN":
            if "mana max" not in normalized:
                _blocking(
                    report,
                    record,
                    "MANA_MAX_STAT_GAIN sans mention de mana max.",
                    evidence,
                )
            if not any(
                token in normalized
                for token in ("gagne", "augmente", "augmentee")
            ):
                _blocking(
                    report,
                    record,
                    "MANA_MAX_STAT_GAIN sans langage de gain reconnu.",
                    evidence,
                )
        elif effect_type == "MANA_RESTORE":
            if not any(
                token in normalized
                for token in ("recupere", "rend", "restaure")
            ):
                _blocking(
                    report,
                    record,
                    "MANA_RESTORE sans langage de restauration reconnu.",
                    evidence,
                )


def _audit_record(report, record):
    report["audited_rune_ids"].add(record["rune_id"])

    if record.get("rune_id") is None:
        _blocking(report, record, "rune_id manquant.")

    if not record.get("name"):
        _blocking(report, record, "Nom de rune manquant.")

    expected_role = "KEYSTONE" if record.get("slot_index") == 0 else "MINOR"
    if record.get("rune_role") != expected_role:
        _blocking(
            report,
            record,
            (
                f"rune_role incohérent: {record.get('rune_role')} "
                f"au lieu de {expected_role}."
            ),
        )

    provenance = record.get("rune_role_provenance") or {}
    if provenance.get("source") != "DDRAGON_RUNESREFORGED_SLOT_INDEX":
        _blocking(
            report,
            record,
            "Provenance KEYSTONE/MINOR inattendue.",
        )

    formula = record.get("formula") or {}
    if formula.get("status") != RUNE_FORMULA_INCOMPLETE:
        _blocking(
            report,
            record,
            (
                "Une rune n'est pas marquée RUNE_FORMULA_INCOMPLETE. "
                "Aucune formule exécutable n'est validée à ce stade."
            ),
        )

    parser = record.get("semantic_parser") or {}
    if parser.get("status") != SEMANTIC_PARSER_SUPPORTED:
        _blocking(
            report,
            record,
            (
                "Le catalogue fr_FR réel devrait utiliser le parser "
                f"SUPPORTED, reçu: {parser.get('status')}."
            ),
        )

    if record.get("locale") != DEFAULT_LOCALE:
        _blocking(
            report,
            record,
            f"Locale inattendue: {record.get('locale')}.",
        )

    for effect in record.get("effects", []):
        _audit_effect_semantics(report, record, effect)

    for row in record.get("unparsed_rune_text", []):
        kind = row.get("kind")
        if kind not in KNOWN_UNPARSED_KINDS:
            _blocking(
                report,
                record,
                f"Type de texte non parsé inconnu: {kind}.",
            )

        if not row.get("text"):
            _blocking(
                report,
                record,
                f"{kind}: texte source manquant.",
            )

        if not row.get("unparsed_fragments"):
            _blocking(
                report,
                record,
                f"{kind}: fragments non parsés manquants.",
            )

    # Contradictions au même niveau de preuve.
    by_evidence = defaultdict(set)
    for effect in record.get("effects", []):
        key = (
            effect.get("source_field"),
            _normalize(effect.get("evidence_text")),
        )
        by_evidence[key].add(effect.get("effect_type"))

    for (_, evidence), types in by_evidence.items():
        for prefix in ("ARMOR", "MAGIC_RESISTANCE"):
            if (
                f"{prefix}_STAT_GAIN" in types
                and f"{prefix}_REDUCTION_TARGET" in types
            ):
                _blocking(
                    report,
                    record,
                    (
                        f"Contradiction: {prefix} classé à la fois comme "
                        "gain personnel et réduction de cible sur la même preuve."
                    ),
                    evidence,
                )


def _audit_historical_linkage(report):
    catalog = report["catalog"]
    audit = build_observed_rune_audit(catalog)

    report["historical_audit"] = audit

    if not audit.get("patch_aware_catalog_resolution"):
        _blocking(
            report,
            None,
            "L'audit historique n'est pas déclaré patch-aware.",
        )

    if audit.get("observed_match_count", 0) == 0:
        _blocking(
            report,
            None,
            "Aucun match historique local disponible pour valider les runes.",
        )
        return

    unexpected_version_statuses = {
        status: count
        for status, count in audit.get("match_version_resolution_counts", {}).items()
        if status not in {"EXACT_PATCH", "EXACT_VERSION"}
    }
    if unexpected_version_statuses:
        _blocking(
            report,
            None,
            (
                "Résolutions de version historiques non exactes: "
                f"{unexpected_version_statuses}"
            ),
        )

    unexpected_catalog_statuses = {
        status: count
        for status, count in audit.get("catalog_status_counts", {}).items()
        if status != "PATCH_CATALOG_AVAILABLE"
    }
    if unexpected_catalog_statuses:
        _blocking(
            report,
            None,
            (
                "Catalogues de patch historiques indisponibles/incorrects: "
                f"{unexpected_catalog_statuses}"
            ),
        )

    unexpected_links = {
        status: count
        for status, count in audit.get("link_status_counts", {}).items()
        if status != "LINKED_RUNE_CATALOG"
    }
    if unexpected_links:
        _blocking(
            report,
            None,
            f"Sélections de runes non reliées au catalogue: {unexpected_links}",
        )

    if audit.get("unknown_perk_id_counts"):
        _blocking(
            report,
            None,
            (
                "Perk IDs historiques inconnus: "
                f"{audit['unknown_perk_id_counts']}"
            ),
        )

    unexpected_style_links = {
        status: count
        for status, count in audit.get("style_link_status_counts", {}).items()
        if status != "LINKED_RUNE_STYLE"
    }
    if unexpected_style_links:
        _blocking(
            report,
            None,
            f"Styles de runes non reliés: {unexpected_style_links}",
        )

    unexpected_consistency = {
        status: count
        for status, count in audit.get("style_consistency_counts", {}).items()
        if status != "MATCHES_OBSERVED_STYLE"
    }
    if unexpected_consistency:
        _blocking(
            report,
            None,
            (
                "Incohérences entre style observé et style statique: "
                f"{unexpected_consistency}"
            ),
        )

    unexpected_pages = {
        status: count
        for status, count in audit.get("page_resolution_counts", {}).items()
        if status != "RESOLVED"
    }
    if unexpected_pages:
        _blocking(
            report,
            None,
            f"Pages de runes non entièrement résolues: {unexpected_pages}",
        )

    if audit.get("unavailable_catalog_examples"):
        _blocking(
            report,
            None,
            (
                "Exemples de catalogues historiques indisponibles: "
                f"{audit['unavailable_catalog_examples'][:3]}"
            ),
        )

    contract = audit.get("magical_footwear_itemization_contract") or {}
    if contract.get("status") != "PASS":
        _blocking(
            report,
            None,
            (
                "Compatibilité Magical Footwear / Itemization v22: "
                f"{contract.get('status')}"
            ),
        )


def build_full_catalog_audit():
    catalog = build_rune_knowledge_catalog()
    report = _new_report(catalog)

    _audit_catalog_structure(report)

    for rune_id in sorted(catalog.get("records", {})):
        _audit_record(report, catalog["records"][rune_id])

    if len(report["audited_rune_ids"]) != len(catalog.get("records", {})):
        _blocking(
            report,
            None,
            (
                "Toutes les runes du catalogue n'ont pas été auditées "
                f"({len(report['audited_rune_ids'])}/"
                f"{len(catalog.get('records', {}))})."
            ),
        )

    _audit_historical_linkage(report)

    return report


def _render_issue(row, prefix):
    rune = ""
    if row.get("rune_id") is not None:
        rune = f"{row['rune_id']} - {row.get('rune_name') or 'UNKNOWN'} | "

    line = f"{prefix} {rune}{row['message']}"
    evidence = row.get("evidence")
    if evidence:
        line += f"\n    preuve: {evidence}"
    return line


def render_full_catalog_audit(report):
    catalog = report["catalog"]
    audit = report.get("historical_audit") or {}

    total_runes = len(catalog.get("records", {}))
    audited = len(report["audited_rune_ids"])

    generic_review_count = sum(
        report["effect_counts"][effect_type]
        for effect_type in (
            "MOVE_SPEED",
            "ATTACK_SPEED",
            "ABILITY_HASTE",
            "ADAPTIVE_FORCE",
            "MANA",
            "ENERGY",
            "TENACITY",
        )
    )

    lines = [
        "=" * 72,
        "RUNE KNOWLEDGE - FULL CATALOG AUDIT",
        "=" * 72,
        f"Rune knowledge version : {catalog.get('rune_knowledge_version')}",
        f"Data Dragon           : {catalog.get('resolved_ddragon_version')}",
        f"Locale                : {catalog.get('locale')}",
        "",
        f"Runes audited         : {audited}/{total_runes}",
        f"Blocking issues       : {len(report['blocking'])}",
        f"Review cases          : {len(report['review'])}",
        f"Generic stat reviews  : {generic_review_count}",
        f"Legacy generic tags  : {sum(report['effect_counts'][x] for x in LEGACY_EFFECT_TYPES)}",
        (
            "Historical selections : "
            f"{audit.get('rune_selection_count', 0)}"
        ),
        (
            "Historical matches     : "
            f"{audit.get('observed_match_count', 0)}"
        ),
        "",
    ]

    if report["blocking"]:
        lines.append("BLOCKING ISSUES")
        lines.append("-" * 72)
        for row in report["blocking"]:
            lines.append(_render_issue(row, "[FAIL]"))
        lines.append("")

    if report["review"]:
        lines.append("REVIEW CASES")
        lines.append("-" * 72)
        for row in report["review"]:
            lines.append(_render_issue(row, "[REVIEW]"))
        lines.append("")

    if report["info"]:
        lines.append("INFORMATION")
        lines.append("-" * 72)
        for row in report["info"]:
            lines.append(f"[INFO] {row}")
        lines.append("")

    if report["blocking"]:
        status = "FAIL"
    elif report["review"]:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS"

    lines.append(f"STATUS : {status}")
    return "\n".join(lines)


def main():
    report = build_full_catalog_audit()
    print(render_full_catalog_audit(report))

    if report["blocking"]:
        return 2

    if report["review"]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
