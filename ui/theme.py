APP_STYLESHEET = r"""
QWidget {
    background: #0f1218;
    color: #e9edf3;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow {
    background: #0f1218;
}

QFrame#Sidebar {
    background: #111620;
    border-right: 1px solid #222a37;
}

QLabel#Brand {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    padding: 4px 0 18px 0;
}

QLabel#PageTitle {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#Muted {
    color: #8f9aac;
}

QFrame#Card {
    background: #171d27;
    border: 1px solid #242d3b;
    border-radius: 10px;
}

QLabel#CardTitle {
    color: #9da9bb;
    font-size: 12px;
    font-weight: 600;
}

QLabel#CardValue {
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
}

QPushButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 9px 12px;
    text-align: left;
    color: #c8d0dc;
}

QPushButton:hover {
    background: #1a2230;
    color: #ffffff;
}

QPushButton:checked {
    background: #202b3b;
    border-color: #334157;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#PrimaryButton {
    background: #273a55;
    border: 1px solid #355070;
    color: #ffffff;
    text-align: center;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background: #30496b;
}

QComboBox {
    background: #171d27;
    border: 1px solid #2b3545;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 110px;
}

QTableWidget {
    background: #141922;
    alternate-background-color: #171d27;
    border: 1px solid #242d3b;
    border-radius: 8px;
    gridline-color: #242d3b;
    selection-background-color: #24344b;
    selection-color: #ffffff;
}

QHeaderView::section {
    background: #171d27;
    color: #aab4c3;
    border: none;
    border-bottom: 1px solid #2b3545;
    padding: 7px;
    font-weight: 600;
}

QStatusBar {
    background: #111620;
    color: #8f9aac;
    border-top: 1px solid #222a37;
}
"""
