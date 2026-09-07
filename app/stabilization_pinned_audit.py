"""Frozen Phase 2D regression, explicitly separate from the latest-patch audit."""
from pathlib import Path
from knowledge.champion_knowledge import build_champion_knowledge_catalog
from knowledge.champion_level_stats import build_level_stats_catalog_audit, render_level_stats_catalog_audit


def main():
    catalog = build_champion_knowledge_catalog('16.16.1', versions=['16.16.1'])
    audit = build_level_stats_catalog_audit(champion_catalog=catalog)
    rendered = render_level_stats_catalog_audit(audit)
    folder = Path(__file__).resolve().parents[1] / 'logs/stabilization/real-audits'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'phase2d_pinned_16_16.txt').write_text(rendered, encoding='utf-8')
    print(rendered)
    return int(bool(audit['blocking'] or audit['review']))


if __name__ == '__main__':
    raise SystemExit(main())
