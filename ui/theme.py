TOKENS = {
    "background": "#08111B",
    "background_alt": "#0B1521",
    "sidebar": "#0C1724",
    "surface": "#111D2B",
    "surface_alt": "#152332",
    "surface_hover": "#192A3C",
    "border": "#23374B",
    "border_soft": "#1A2B3D",
    "text": "#F3F6FA",
    "text_secondary": "#91A5BB",
    "text_muted": "#657B91",
    "accent": "#31C9B0",
    "accent_hover": "#52DDC5",
    "success": "#43D39E",
    "danger": "#F06F7C",
    "warning": "#E9B85F",
}


def apply_zircon_theme(app) -> None:
    """Apply the native ZiRcoN design system without a theme engine."""
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)


APP_STYLESHEET = r"""
* { font-family: "Segoe UI"; font-size: 13px; }
QWidget { background: #08111B; color: #F3F6FA; }
QWidget QWidget { background: transparent; }
QLabel, QWidget#MetricCell { background: transparent; }
QMainWindow { background: #08111B; }
QFrame#Sidebar { background: #0C1724; border-right: 1px solid #1A2B3D; }
QFrame#Topbar { background: #0B1521; border-bottom: 1px solid #1A2B3D; }
QLabel#Brand { font-size: 20px; font-weight: 700; color: #F3F6FA; }
QLabel#BrandAccent { font-size: 10px; font-weight: 600; color: #657B91; letter-spacing: 1px; }
QLabel#PageTitle { font-size: 26px; font-weight: 600; color: #F3F6FA; }
QLabel#HeroName { font-size: 24px; font-weight: 700; }
QLabel#HeroRank { font-size: 15px; font-weight: 600; color: #31C9B0; }
QLabel#SectionTitle { font-size: 18px; font-weight: 600; color: #F3F6FA; }
QLabel#Muted, QLabel#MicroLabel { color: #91A5BB; }
QLabel#MicroLabel { font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#MatchChampion, QLabel#MatchMetric { font-size: 15px; font-weight: 700; }
QLabel#Evidence { background: #0B1521; color: #91A5BB; border-radius: 7px; padding: 9px; }
QFrame#Card, QFrame#InsightCard, QFrame#AnalyzerHeader { background: #111D2B; border: 1px solid #1A2B3D; border-radius: 10px; }
QFrame#EventCard { background: #111D2B; border: 1px solid #23374B; border-radius: 10px; }
QFrame#CoachCard { background: #10262C; border: 1px solid #245A5B; border-radius: 10px; }
QFrame#HeroCard { background: #111D2B; border: 1px solid #23374B; border-radius: 12px; }
QFrame#MatchSummaryHero { background: #111D2B; border: 1px solid #23374B; border-radius: 12px; }
QFrame#MatchupBoard { background: #0f1b28; border: 1px solid #2a435b; border-radius: 15px; }
QFrame#TeamPanel { background: #101a26; border: 1px solid #263a50; border-radius: 14px; }
QFrame#TeamPanel[side="ally"] { border-top: 3px solid #45c39d; }
QFrame#TeamPanel[side="enemy"] { border-top: 3px solid #e06b79; }
QFrame#RosterRow { background: #162332; border: 1px solid #24384c; border-radius: 10px; }
QFrame#RosterRow[isPlayer="true"] { background: #17343a; border-color: #48c5ae; }
QFrame#OptimizerHero { background: #112832; border: 1px solid #3b8490; border-radius: 16px; }
QFrame#DashboardCard { background: #111D2B; border: 1px solid #1A2B3D; border-radius: 10px; }
QFrame#OptimizerPreview { background: #0f2b31; border: 1px solid #348579; border-radius: 14px; }
QFrame#TimelineCard { background: #101f2d; border: 1px solid #284a5f; border-radius: 14px; }
QFrame#RecapCard { background: #10222b; border: 1px solid #285467; border-radius: 14px; }
QFrame#MetricTile { background: #18293a; border: 1px solid #29445a; border-radius: 9px; }
QFrame#MatchCard { background: #111D2B; border: 1px solid #1A2B3D; border-left: 3px solid #657B91; border-radius: 9px; }
QFrame#Scoreboard { background: #354252; border: 1px solid #455467; border-radius: 8px; }
QFrame#ScoreboardRow { background: transparent; border-bottom: 1px solid #455467; }
QFrame#ScoreboardRow[isPlayer="true"] { background: #3c5260; border-radius: 6px; }
QLabel#ScoreboardName { color: #f3f6fa; font-weight: 600; font-size: 13px; }
QLabel#ScoreboardMeta { color: #acbfd2; font-size: 11px; }
QFrame#MatchCard:hover { background: #152332; border-color: #23374B; }
QFrame#MatchCard[result="win"] { border-left-color: #43D39E; }
QFrame#MatchCard[result="loss"] { border-left-color: #F06F7C; }
QFrame#MatchupStrip { background: transparent; border: none; }
QLabel#MatchupLine { font-size: 12px; font-weight: 600; }
QLabel#MatchupLine[side="ally"] { color: #77d8b8; }
QLabel#MatchupLine[side="enemy"] { color: #ef9aa2; }
QLabel[result="win"] { color: #48c78e; font-weight: 700; }
QLabel[result="loss"] { color: #ef6b73; font-weight: 700; }
QLabel#CardTitle { color: #91A5BB; font-size: 10px; font-weight: 600; letter-spacing: 1px; }
QLabel#CardValue { color: #F3F6FA; font-size: 23px; font-weight: 700; }
QLabel#AssetIcon { background: #152332; border: 1px solid #23374B; border-radius: 7px; }
QLabel#AssetIcon[player="true"] { border: 2px solid #31C9B0; }
QLabel#StatusBadge { border-radius: 8px; padding: 3px 8px; font-size: 10px; font-weight: 700; }
QLabel#StatusBadge[tone="green"] { color: #62dba6; background: #173229; }
QLabel#StatusBadge[tone="support"] { color: #67c9d8; background: #173039; border: 1px solid #28505b; }
QLabel#StatusBadge[tone="amber"] { color: #f1c76d; background: #342b18; }
QLabel#StatusBadge[tone="red"] { color: #ff858b; background: #351c22; }
QLabel#StatusBadge[tone="slate"] { color: #a7b2c2; background: #232c39; }
QLabel#SeverityBadge { border-radius: 8px; padding: 3px 8px; font-size: 10px; font-weight: 750; }
QLabel#SeverityBadge[tone="high"] { color: #ff9298; background: #3a1f26; }
QLabel#SeverityBadge[tone="medium"] { color: #f1c76d; background: #342b18; }
QLabel#SeverityBadge[tone="low"] { color: #b8c3d2; background: #26303d; }
QLabel#EventTitle { font-size: 16px; font-weight: 750; color: #f5f8fc; }
QLabel#InsightMarker { background: #1a4350; color: #72e0c7; border-radius: 15px; font-size: 16px; font-weight: 800; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; qproperty-alignment: AlignCenter; }
QLabel#EventMarker { color: #64d7c0; font-size: 20px; }
QLabel#InsightFact { color: #9fb0c3; background: #1a2b3c; border-radius: 7px; padding: 4px 7px; font-size: 11px; font-weight: 650; }
QLabel#RosterName { font-size: 15px; font-weight: 750; color: #f5f8fc; }
QLabel#RosterStats { color: #b8c7d8; font-size: 12px; }
QLabel#TeamHeading[side="ally"] { color: #65dbb5; font-size: 17px; font-weight: 800; }
QLabel#TeamHeading[side="enemy"] { color: #f08c97; font-size: 17px; font-weight: 800; }
QLabel#TeamChampion { color: #b7c5d6; font-size: 10px; font-weight: 650; }
QLabel#Versus { color: #8294a9; font-size: 17px; font-weight: 800; letter-spacing: 2px; }
QLabel#PerformanceScore { color: #69dfc2; font-size: 30px; font-weight: 800; }
QLabel#OptimizerScore { color: #75e1ca; font-size: 12px; font-weight: 750; }
QLabel#MetricValue { color: #dfe7f1; font-weight: 600; }
QLabel#ContextLine { color: #cbd7e5; background: #182838; border-radius: 7px; padding: 6px 9px; }
QLabel#TechnicalDetails { color: #8f9daf; background: #0d131b; border-radius: 7px; padding: 9px; font-family: Consolas, monospace; font-size: 11px; }
QToolButton { color: #75c9d5; background: transparent; border: none; padding: 4px 0; font-weight: 650; }
QPushButton { min-height: 20px; background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 9px 12px; color: #91A5BB; text-align: left; }
QPushButton:hover { background: #192A3C; color: #F3F6FA; }
QPushButton:checked { background: #12313A; color: #52DDC5; font-weight: 600; }
QPushButton#NavButton { min-height: 26px; padding: 9px 14px; }
QPushButton#PrimaryButton { background: #31C9B0; color: #061613; font-weight: 700; text-align: center; padding: 9px 16px; }
QPushButton#PrimaryButton:hover { background: #52DDC5; }
QPushButton#SecondaryButton, QPushButton#CompactButton { background: #152332; border-color: #23374B; color: #D9E3ED; text-align: center; padding: 7px 11px; }
QPushButton#GhostButton, QPushButton#BackButton { background: transparent; color: #91A5BB; text-align: center; padding: 7px 10px; }
QPushButton#DangerButton { background: #321B24; border-color: #63303D; color: #F59AA3; text-align: center; }
QLineEdit, QComboBox, QPlainTextEdit { background: #0B1521; border: 1px solid #23374B; border-radius: 8px; padding: 9px 11px; color: #F3F6FA; selection-background-color: #246B68; }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus { border-color: #31C9B0; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #2A4054; border-radius: 4px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #3A566C; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background: #18202c; border: none; border-radius: 4px; height: 7px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #55d6be; border-radius: 4px; }
QStatusBar { background: #0B1521; color: #657B91; border-top: 1px solid #1A2B3D; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: #111c29; color: #93a3b6; padding: 11px 17px; border-radius: 8px; margin-right: 6px; }
QTabBar::tab:hover { background: #172a3b; color: #dbe6f1; }
QTabBar::tab:selected { background: #1a3b46; color: #71e0c7; font-weight: 750; }
"""
