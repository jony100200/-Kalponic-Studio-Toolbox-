"""
Centralized theme tokens for KS PDF Studio.
Keep this file minimal — other modules should import COLORS from here instead of using literal hex strings.
"""

COLORS = {
    'bg_primary': '#1e1e1e',      # Main background
    'bg_secondary': '#2d2d2d',    # Secondary backgrounds
    'bg_tertiary': '#3a3a3a',     # Tertiary backgrounds
    'fg_primary': '#e0e0e0',      # Primary text
    'fg_secondary': '#b0b0b0',    # Secondary text
    'fg_accent': '#4a9eff',       # Accent color (muted blue)
    'border': '#404040',          # Borders
    'highlight': '#505050',       # Highlights
    'success': '#4a9e4a',         # Success color
    'warning': '#9e9e4a',         # Warning color
    'error': '#9e4a4a',           # Error color
    'button_bg': '#404040',       # Button background
    'button_fg': '#e0e0e0',       # Button text
    'entry_bg': '#2d2d2d',        # Entry background
    'entry_fg': '#e0e0e0',        # Entry text
    'text_bg': '#1a1a1a',         # Text widget background
    'text_fg': '#e0e0e0',         # Text widget text
    'scrollbar_bg': '#404040',    # Scrollbar background
    'scrollbar_fg': '#606060',    # Scrollbar foreground
    # Selection and subtle UI accents
    'select_bg': '#2f5a8a',       # muted blue selection background for text/list selections
    'select_fg': '#ffffff',       # selection foreground
    'scroll_thumb': '#5a5a5a',    # scrollbar thumb color
    'scroll_track': '#2d2d2d',    # scrollbar track color
    'menu_active_bg': '#33383e',  # menu hover background
    'menu_active_fg': '#e8eef8',  # menu hover foreground
    'focus_ring': '#2b3a4a',      # subtle focus ring color
    'button_active_bg': '#3b4756',
    'button_active_fg': '#ffffff',
    'entry_select_bg': '#2f5a8a',
    'entry_select_fg': '#ffffff',
    'tree_selected_bg': '#2f5a8a',
    'tree_selected_fg': '#ffffff',
}
