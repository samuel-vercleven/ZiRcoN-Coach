APP_STYLESHEET = r"""
* { font-family: "Segoe UI"; font-size: 14px; }
QWidget { background: #0a1018; color: #e8edf5; }
QLabel, QWidget#MetricCell { background: transparent; }
QMainWindow { background: #0b0f15; }
QFrame#Sidebar { background: #0d1520; border-right: 1px solid #263447; }
QFrame#Topbar { background: #101925; border-bottom: 1px solid #263447; }
QLabel#Brand { font-size: 23px; font-weight: 800; color: #ffffff; }
QLabel#BrandAccent { font-size: 11px; font-weight: 700; color: #55d6be; letter-spacing: 2px; }
QLabel#PageTitle { font-size: 27px; font-weight: 750; color: #ffffff; }
QLabel#HeroName { font-size: 28px; font-weight: 800; }
QLabel#HeroRank { font-size: 17px; font-weight: 650; color: #55d6be; }
QLabel#SectionTitle { font-size: 19px; font-weight: 750; color: #f5f8fc; }
QLabel#Muted, QLabel#MicroLabel { color: #8491a3; }
QLabel#MicroLabel { font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#MatchChampion, QLabel#MatchMetric { font-size: 15px; font-weight: 700; }
QLabel#Evidence { background: #101721; color: #aeb9c8; border-radius: 7px; padding: 9px; }
QFrame#Card, QFrame#InsightCard, QFrame#AnalyzerHeader { background: #131d29; border: 1px solid #29384a; border-radius: 14px; }
QFrame#EventCard { background: #111b27; border: 1px solid #2a3b50; border-radius: 12px; }
QFrame#CoachCard { background: #10202a; border: 1px solid #2b6671; border-radius: 14px; }
QFrame#HeroCard { background: #132130; border: 1px solid #30465e; border-radius: 16px; }
QFrame#MatchSummaryHero { background: #111d2a; border: 1px solid #31526b; border-radius: 16px; }
QFrame#TeamPanel { background: #101a26; border: 1px solid #263a50; border-radius: 14px; }
QFrame#TeamPanel[side="ally"] { border-top: 3px solid #45c39d; }
QFrame#TeamPanel[side="enemy"] { border-top: 3px solid #e06b79; }
QFrame#RosterRow { background: #162332; border: 1px solid #24384c; border-radius: 10px; }
QFrame#RosterRow[isPlayer="true"] { background: #17343a; border-color: #48c5ae; }
QFrame#OptimizerHero { background: #112832; border: 1px solid #3b8490; border-radius: 16px; }
QFrame#MatchCard { background: #141b25; border: 1px solid #222d3b; border-left: 4px solid #637083; border-radius: 10px; }
QFrame#MatchCard[result="win"] { border-left-color: #48c78e; }
QFrame#MatchCard[result="loss"] { border-left-color: #ef6b73; }
QLabel[result="win"] { color: #48c78e; font-weight: 700; }
QLabel[result="loss"] { color: #ef6b73; font-weight: 700; }
QLabel#CardTitle { color: #94a5b9; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#CardValue { color: #ffffff; font-size: 25px; font-weight: 800; }
QLabel#AssetIcon { background: #202d3e; border: 1px solid #40536b; border-radius: 8px; }
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
QLabel#RosterName { font-size: 15px; font-weight: 750; color: #f5f8fc; }
QLabel#RosterStats { color: #b8c7d8; font-size: 12px; }
QLabel#TeamHeading[side="ally"] { color: #65dbb5; font-size: 17px; font-weight: 800; }
QLabel#TeamHeading[side="enemy"] { color: #f08c97; font-size: 17px; font-weight: 800; }
QLabel#MetricValue { color: #dfe7f1; font-weight: 600; }
QLabel#ContextLine { color: #cbd7e5; background: #182838; border-radius: 7px; padding: 6px 9px; }
QLabel#TechnicalDetails { color: #8f9daf; background: #0d131b; border-radius: 7px; padding: 9px; font-family: Consolas, monospace; font-size: 11px; }
QToolButton { color: #75c9d5; background: transparent; border: none; padding: 4px 0; font-weight: 650; }
QPushButton { background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 12px 14px; color: #b9c3d1; text-align: left; }
QPushButton:hover { background: #19293a; color: #ffffff; }
QPushButton:checked { background: #1a3540; border-color: #3a7280; color: #74e0c9; font-weight: 700; }
QPushButton#PrimaryButton { background: #42bfa7; color: #07120f; font-weight: 800; text-align: center; padding: 10px 18px; }
QPushButton#PrimaryButton:hover { background: #57d2ba; }
QPushButton#CompactButton { background: #202c3b; border-color: #304054; text-align: center; padding: 7px 11px; }
QLineEdit, QComboBox { background: #101721; border: 1px solid #2b394c; border-radius: 8px; padding: 9px 11px; color: #edf2f8; }
QLineEdit:focus, QComboBox:focus { border-color: #55d6be; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #0e141d; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #344154; border-radius: 5px; min-height: 30px; }
QProgressBar { background: #18202c; border: none; border-radius: 4px; height: 7px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #55d6be; border-radius: 4px; }
QStatusBar { background: #0e141d; color: #8491a3; border-top: 1px solid #202937; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: #111c29; color: #93a3b6; padding: 11px 17px; border-radius: 8px; margin-right: 6px; }
QTabBar::tab:hover { background: #172a3b; color: #dbe6f1; }
QTabBar::tab:selected { background: #1a3b46; color: #71e0c7; font-weight: 750; }
"""
