"""Design tokens for KS AutoModel PySide UI."""

KS_TOKENS = {
    "motion.fast": 120,
    "motion.medium": 250,
    "motion.slow": 400,
    "radius.panel": 8,
    "radius.button": 6,
    "spacing.unit": 8,
}

_DARK_COLORS = {
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
}

_LIGHT_COLORS = {
    "color.bg.base": "#F5F7FA",
    "color.bg.panel": "#FFFFFF",
    "color.bg.raised": "#EEF1F6",
    "color.text.primary": "#1F2A35",
    "color.text.secondary": "#4A5A6A",
    "color.accent.primary": "#007ACC",
    "color.accent.success": "#2E8540",
    "color.accent.error": "#B83232",
    "color.border.subtle": "#CED6E0",
    "color.border.strong": "#A3B1C2",
}


def get_color_tokens(mode: str = "dark") -> dict:
    mode = mode.lower()
    if mode == "light":
        return _LIGHT_COLORS
    return _DARK_COLORS


def build_qss(mode: str = "dark") -> str:
    """Generate a QSS stylesheet derived from design tokens."""
    spacing = KS_TOKENS["spacing.unit"]
    colors = get_color_tokens(mode)
    return f"""
    QWidget {{
        background-color: {colors['color.bg.base']};
        color: {colors['color.text.primary']};
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 12px;
    }}
    QFrame#Panel {{
        background-color: {colors['color.bg.panel']};
        border: 1px solid {colors['color.border.subtle']};
        border-radius: {KS_TOKENS['radius.panel']}px;
        padding: {spacing * 2}px;
    }}
    QPushButton {{
        background-color: {colors['color.bg.panel']};
        border: 1px solid {colors['color.border.subtle']};
        border-radius: {KS_TOKENS['radius.button']}px;
        padding: {spacing + 2}px {spacing * 2}px;
        color: {colors['color.text.primary']};
    }}
    QPushButton:hover {{
        background-color: {colors['color.accent.primary']}33;
        border-color: {colors['color.accent.primary']};
    }}
    QPushButton:pressed {{
        background-color: {colors['color.accent.primary']}55;
    }}
    QLabel#Heading {{
        font-size: 18px;
        font-weight: 700;
        color: {colors['color.text.primary']};
    }}
    QLabel#SubHeading {{
        font-size: 14px;
        font-weight: 600;
        color: {colors['color.text.secondary']};
    }}
    QListWidget, QTextEdit {{
        background-color: {colors['color.bg.raised']};
        border: 1px solid {colors['color.border.subtle']};
        border-radius: {KS_TOKENS['radius.button']}px;
    }}
    QProgressBar {{
        border: 1px solid {colors['color.border.subtle']};
        border-radius: {KS_TOKENS['radius.button']}px;
        background: {colors['color.bg.panel']};
        text-align: center;
        color: {colors['color.text.primary']};
    }}
    QProgressBar::chunk {{
        background-color: {colors['color.accent.primary']};
        border-radius: {KS_TOKENS['radius.button']}px;
    }}
    QTabWidget::pane {{
        border: 1px solid {colors['color.border.subtle']};
        border-radius: {KS_TOKENS['radius.panel']}px;
        background: {colors['color.bg.panel']};
    }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        padding: {spacing}px {spacing * 2}px;
        color: {colors['color.text.secondary']};
    }}
    QTabBar::tab:selected {{
        color: {colors['color.accent.primary']};
        font-weight: 600;
    }}
    """
