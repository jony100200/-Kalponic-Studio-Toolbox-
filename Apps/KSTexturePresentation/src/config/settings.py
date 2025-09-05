"""
Settings Configuration - Single Responsibility Principle
Manages application configuration and default values
"""

class Settings:
    """Application settings configuration"""
    
    def __init__(self):
        """Initialize default settings"""
        self.default_output_format = "PNG"
        self.default_output_name = "merged_sprite"
        self.supported_formats = [".png", ".jpg", ".jpeg", ".webp"]
        self.default_sprite_size = (512, 512)  # Larger default for better quality
        self.default_columns = 8
        self.default_rows = 8
        self.default_cell_size = (64, 64)
        self.max_power_of_two = 2048
        
        # UI Theme settings
        self.ui_theme = "dark"
        self.ui_color_theme = "blue"
        self.window_size = "900x700"  # Larger window for new controls
        self.sci_fi_colors = {
            "primary": "#00D4AA",     # Cyan
            "secondary": "#FF6B35",   # Orange
            "accent": "#7209B7",      # Purple
            "background": "#0A0E27",  # Dark blue
            "surface": "#1A1F3A",     # Lighter dark blue
            "text": "#FFFFFF"         # White
        }
        
        # Batch processing settings
        self.size_presets = [
            ("Tiny", (32, 32)),
            ("Small", (64, 64)),
            ("Medium", (128, 128)),
            ("Large", (256, 256)),
            ("XLarge", (512, 512)),
            ("XXLarge", (1024, 1024))
        ]
        
    def get_supported_formats(self):
        """Get list of supported image formats"""
        return self.supported_formats
        
    def get_default_output_format(self):
        """Get default output format"""
        return self.default_output_format
        
    def get_default_sprite_size(self):
        """Get default sprite size"""
        return self.default_sprite_size
        
    def get_default_columns(self):
        """Get default number of columns for spritesheet"""
        return self.default_columns
    
    def get_default_rows(self):
        """Get default number of rows for spritesheet"""
        return self.default_rows
    
    def get_default_cell_size(self):
        """Get default cell size"""
        return self.default_cell_size
    
    def get_max_power_of_two(self):
        """Get maximum power of two size"""
        return self.max_power_of_two
    
    def get_size_presets(self):
        """Get size presets for UI"""
        return self.size_presets
    
    def get_ui_theme(self):
        """Get UI theme"""
        return self.ui_theme
    
    def get_ui_color_theme(self):
        """Get UI color theme"""
        return self.ui_color_theme
    
    def get_window_size(self):
        """Get default window size"""
        return self.window_size
    
    def get_sci_fi_colors(self):
        """Get sci-fi color palette"""
        return self.sci_fi_colors
