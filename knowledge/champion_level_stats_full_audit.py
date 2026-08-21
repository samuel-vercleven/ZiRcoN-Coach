from knowledge.champion_level_stats import (
    build_level_stats_catalog_audit,
    render_level_stats_catalog_audit,
)


def main():
    audit = build_level_stats_catalog_audit()
    print(render_level_stats_catalog_audit(audit))

    if audit["blocking"]:
        return 2
    if audit["review"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
