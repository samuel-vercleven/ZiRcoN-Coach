from app.bootstrap import build_app_context
from services.post_game_analysis import ANALYZER_VERSIONS


def main() -> None:
    context = build_app_context()
    matches = context.local_data.matches()
    if not matches:
        print("ZiRcoN Coach analyzer adapter: PASS (offline empty state; no local match)")
        return
    context.analysis.generate_for_matches([matches[0].match_id])
    report = context.analysis.get_match_insights(matches[0].match_id)
    sources = {insight.source_module for insight in report.insights}
    assert sources == set(ANALYZER_VERSIONS)
    assert all(insight.status in {"AVAILABLE", "PARTIAL", "UNAVAILABLE", "ERROR"} for insight in report.insights)
    assert all(insight.source_version == ANALYZER_VERSIONS[insight.source_module] for insight in report.insights)
    print(f"ZiRcoN Coach analyzer adapter: PASS ({len(report.insights)}/5 frozen analyzer sections cached)")


if __name__ == "__main__":
    main()
