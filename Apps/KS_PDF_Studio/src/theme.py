"""
Centralised design tokens for KS PDF Studio.

The values here are the concrete implementation of the
"KS Universal UI System Blueprint (v2.0 - 2025 Standard)".
Other modules should import TOKENS / COLORS instead of
hardcoding hex strings or spacing values.
"""

# Base unit used throughout the layout (8 px grid in the blueprint)
BASE_SPACING_UNIT = 8

TOKENS = {
    # Colour tokens stay close to the blueprint naming scheme so they can
    # be serialised for other platforms later (PySide, Unity, web, etc.).
    "color": {
        "bg": {
            "base": "#1C1F2A",
            "panel": "#262E38",
            "raised": "#303B4C",  # Slightly lighter for tertiary surfaces
        },
        "text": {
            "primary": "#D9D8D8",
            "secondary": "#A0A0A0",
            "muted": "#7A8793",
        },
        "accent": {
            "primary": "#00C2FF",
            "success": "#32CD32",
            "warning": "#DFAA29",
            "error": "#E45757",
            "glow": "#00C2FF59",  # rgba(0,194,255,0.35) expressed as ARGB hex
        },
        "border": {
            "subtle": "#293346",
            "strong": "#37445A",
        },
        "shadow": {
            "base": "#00000040",
            "elevated": "#00000059",
        },
    },
    "typography": {
        "title": {"family": "Inter", "weight": 700, "size": 18},
        "subtitle": {"family": "Inter", "weight": 600, "size": 15},
        "body": {"family": "Inter", "weight": 400, "size": 13},
        "mono": {"family": "JetBrains Mono", "weight": 500, "size": 12},
    },
    "spacing": {
        "unit": BASE_SPACING_UNIT,
        "gutter": BASE_SPACING_UNIT * 2,
        "section": BASE_SPACING_UNIT * 3,
        "panel_padding": BASE_SPACING_UNIT * 2,
        "element_padding": BASE_SPACING_UNIT,
    },
    "radius": {
        "panel": 8,
        "button": 6,
        "chip": 12,
    },
    "motion": {
        "fast": {"duration_ms": 120, "curve": (0.25, 1, 0.5, 1)},
        "medium": {"duration_ms": 250, "curve": "ease-in-out"},
        "slow": {"duration_ms": 400, "curve": "ease"},
        "spring": {"stiffness": 200, "damping": 20},
    },
}

# Backwards-compatible colour aliases used by the Tk GUI layer.
COLORS = {
    'bg_primary': TOKENS["color"]["bg"]["base"],
    'bg_secondary': TOKENS["color"]["bg"]["panel"],
    'bg_tertiary': TOKENS["color"]["bg"]["raised"],
    'fg_primary': TOKENS["color"]["text"]["primary"],
    'fg_secondary': TOKENS["color"]["text"]["secondary"],
    'fg_muted': TOKENS["color"]["text"]["muted"],
    'fg_accent': TOKENS["color"]["accent"]["primary"],
    'border': TOKENS["color"]["border"]["subtle"],
    'border_strong': TOKENS["color"]["border"]["strong"],
    'highlight': '#1F2F3D',  # muted hover fill derived from panel tone
    'glow': TOKENS["color"]["accent"]["glow"],
    'success': TOKENS["color"]["accent"]["success"],
    'warning': TOKENS["color"]["accent"]["warning"],
    'error': TOKENS["color"]["accent"]["error"],
    'button_bg': TOKENS["color"]["bg"]["panel"],
    'button_fg': TOKENS["color"]["text"]["primary"],
    'button_active_bg': '#133C4E',  # accent-darkened for pressed state
    'button_active_fg': TOKENS["color"]["text"]["primary"],
    'entry_bg': TOKENS["color"]["bg"]["panel"],
    'entry_fg': TOKENS["color"]["text"]["primary"],
    'entry_select_bg': '#1F4E62',
    'entry_select_fg': TOKENS["color"]["text"]["primary"],
    'text_bg': '#161923',
    'text_fg': TOKENS["color"]["text"]["primary"],
    'select_bg': '#1F4E62',
    'select_fg': TOKENS["color"]["text"]["primary"],
    'scrollbar_bg': TOKENS["color"]["bg"]["panel"],
    'scrollbar_fg': '#3F5264',
    'scroll_thumb': '#3F5264',
    'scroll_track': TOKENS["color"]["bg"]["panel"],
    'menu_active_bg': '#1F2F3D',
    'menu_active_fg': TOKENS["color"]["text"]["primary"],
    'focus_ring': TOKENS["color"]["accent"]["primary"],
    'tree_selected_bg': '#1F4E62',
    'tree_selected_fg': TOKENS["color"]["text"]["primary"],
}


def get_token(path: str, default=None):
    """
    Retrieve a token using dot notation (e.g. "color.bg.base").
    Returns default when the path does not exist.
    """
    parts = path.split(".")
    value = TOKENS
    try:
        for part in parts:
            value = value[part]
        return value
    except (KeyError, TypeError):
        return default
