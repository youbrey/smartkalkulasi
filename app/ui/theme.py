ACCENT = "#4F46E5"
ACCENT_SOFT = "#EEF2FF"
INK = "#111827"
MUTED = "#6B7280"
LINE = "#E5E7EB"
BG = "#F5F6FA"

QSS = f"""
* {{ font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif; font-size: 10pt; color: {INK}; }}
QMainWindow, QDialog {{ background: {BG}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

#Sidebar {{ background: #FFFFFF; border-right: 1px solid {LINE}; }}
#Brand {{ font-size: 15pt; font-weight: 700; color: {INK}; }}
#BrandSub {{ color: {MUTED}; font-size: 8.5pt; }}
QPushButton#Nav {{ text-align: left; padding: 10px 14px; border: none; border-radius: 10px;
                  color: {MUTED}; background: transparent; font-weight: 500; }}
QPushButton#Nav:hover {{ background: #F3F4F6; color: {INK}; }}
QPushButton#Nav:checked {{ background: {ACCENT_SOFT}; color: {ACCENT}; font-weight: 600; }}

#PageTitle {{ font-size: 18pt; font-weight: 700; }}
#PageSub {{ color: {MUTED}; }}

QFrame#Card {{ background: #FFFFFF; border: 1px solid {LINE}; border-radius: 14px; }}
QLabel#CardTitle {{ font-size: 11pt; font-weight: 650; }}
QLabel#CardHint {{ color: {MUTED}; font-size: 8.5pt; }}
QLabel[cls="field"] {{ color: {MUTED}; font-size: 8.5pt; font-weight: 600; }}
QLabel[cls="muted"] {{ color: {MUTED}; }}
QFrame#Leg {{ background: #FAFAFC; border: 1px solid {LINE}; border-radius: 12px; }}
QLabel#Chip {{ background: {ACCENT_SOFT}; color: {ACCENT}; border-radius: 8px; padding: 2px 9px; font-weight: 600; }}
QLabel#Info {{ color: {MUTED}; font-size: 8.5pt; }}
QLabel#Warn {{ background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; border-radius: 10px; padding: 8px 10px; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {{
    background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 8px; padding: 6px 10px;
    selection-background-color: {ACCENT}; selection-color: white; min-height: 20px; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:disabled, QComboBox:disabled {{ background: #F3F4F6; color: {MUTED}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{ border: 1px solid {LINE}; background: white; selection-background-color: {ACCENT_SOFT};
                              selection-color: {ACCENT}; outline: 0; padding: 4px; }}
QDateEdit::drop-down {{ border: none; width: 24px; }}

QPushButton {{ background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 9px; padding: 8px 16px; font-weight: 500; }}
QPushButton:hover {{ background: #F9FAFB; border-color: #9CA3AF; }}
QPushButton:pressed {{ background: #F3F4F6; }}
QPushButton[kind="primary"] {{ background: {ACCENT}; border: 1px solid {ACCENT}; color: white; font-weight: 600; }}
QPushButton[kind="primary"]:hover {{ background: #4338CA; border-color: #4338CA; }}
QPushButton[kind="ghost"] {{ border: none; background: transparent; color: {ACCENT}; font-weight: 600; padding: 6px 8px; }}
QPushButton[kind="ghost"]:hover {{ background: {ACCENT_SOFT}; }}
QPushButton[kind="danger"] {{ border: none; background: transparent; color: #B91C1C; padding: 4px 8px; }}
QPushButton[kind="danger"]:hover {{ background: #FEE2E2; }}
QPushButton:disabled {{ color: #9CA3AF; background: #F3F4F6; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid #9CA3AF; background: white; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QTableWidget {{ background: white; border: 1px solid {LINE}; border-radius: 10px; gridline-color: #F1F2F6;
               alternate-background-color: #FAFAFC; selection-background-color: {ACCENT_SOFT}; selection-color: {INK}; }}
QHeaderView::section {{ background: #F9FAFB; border: none; border-bottom: 1px solid {LINE}; padding: 8px 10px;
                       font-weight: 600; color: {MUTED}; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; padding: 8px 16px; margin-right: 4px; color: {MUTED}; border-radius: 8px; }}
QTabBar::tab:selected {{ background: {ACCENT_SOFT}; color: {ACCENT}; font-weight: 600; }}
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ background: #D1D5DB; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QLabel#Total {{ font-size: 20pt; font-weight: 700; color: {ACCENT}; }}
QToolTip {{ background: {INK}; color: white; border: none; padding: 6px; }}
"""
