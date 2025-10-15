"""Design tokens for KS AutoModel PySide UI."""

KS_TOKENS = {
    "color.bg.base": "#1C1F2A",
    "color.bg.panel": "#262E38",
    "color.bg.raised": "#303B4C",
    "color.text.primary": "#D9D8D8",
    "color.text.secondary": "#A0A0A0",
    "color.accent.primary": "#00C2FF",
    "color.accent.success": "#32CD32",
    "color.accent.error": "#E45757",
    "color.border.subtle": "#293346",
    "color.border.strong": "#37445A",
    "motion.fast": 120,
    "motion.medium": 250,
    "motion.slow": 400,
    "radius.panel": 8,
    "radius.button": 6,
    "spacing.unit": 8,
}


def build_qss() -> str:
    """Generate a QSS stylesheet derived from design tokens."""
    tokens = KS_TOKENS
    return f"""
    QWidget {{
        background-color: {tokens['color.bg.base']};
        color: {tokens['color.text.primary']};
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 12px;
    }}
    QFrame#Panel {{
        background-color: {tokens['color.bg.panel']};
        border: 1px solid {tokens['color.border.subtle']};
        border-radius: {tokens['radius.panel']}px;
        padding: {tokens['spacing.unit'] * 2}px;
    }}
    QPushButton {{
        background-color: {tokens['color.bg.panel']};
        border: 1px solid {tokens['color.border.subtle']};
        border-radius: {tokens['radius.button']}px;
        padding: {tokens['spacing.unit'] + 2}px {tokens['spacing.unit'] * 2}px;
        color: {tokens['color.text.primary']};
    }}
    QPushButton:hover {{
        background-color: {tokens['color.accent.primary']}33;
        border-color: {tokens['color.accent.primary']};
    }}
    QPushButton:pressed {{
        background-color: {tokens['color.accent.primary']}55;
    }}
    QLabel#Heading {{
        font-size: 18px;
        font-weight: 700;
        color: {tokens['color.text.primary']};
    }}
    QLabel#SubHeading {{
        font-size: 14px;
        font-weight: 600;
        color: {tokens['color.text.secondary']};
    }}
    QListWidget, QTextEdit {{
        background-color: {tokens['color.bg.raised']};
        border: 1px solid {tokens['color.border.subtle']};
        border-radius: {tokens['radius.button']}px;
    }}
    QProgressBar {{
        border: 1px solid {tokens['color.border.subtle']};
        border-radius: {tokens['radius.button']}px;
        background: {tokens['color.bg.panel']};
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {tokens['color.accent.primary']};
        border-radius: {tokens['radius.button']}px;
    }}
    QTabWidget::pane {{
        border: 1px solid {tokens['color.border.subtle']};
        border-radius: {tokens['radius.panel']}px;
        background: {tokens['color.bg.panel']};
    }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        padding: {tokens['spacing.unit']}px {tokens['spacing.unit'] * 2}px;
        color: {tokens['color.text.secondary']};
    }}
    QTabBar::tab:selected {{
        color: {tokens['color.accent.primary']};
        font-weight: 600;
    }}
    """
