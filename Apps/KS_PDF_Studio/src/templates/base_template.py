"""
KS PDF Studio - PDF Templates
Professional templates and styling for PDF generation.

Author: Kalponic Studio
Version: 2.0.0
"""

import json
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, A3
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm


class KSPDFTemplate:
    """
    PDF template system for KS PDF Studio.

    Features:
    - Predefined professional templates
    - Custom branding and styling
    - Responsive layout options
    - Template inheritance and customization
    """

    # Available page sizes
    PAGE_SIZES = {
        'a4': A4,
        'letter': letter,
        'a3': A3,
    }

    # Default color schemes
    COLOR_SCHEMES = {
        'professional': {
            'primary': colors.darkblue,
            'secondary': colors.lightblue,
            'accent': colors.darkgreen,
            'text': colors.black,
            'background': colors.white,
        },
        'modern': {
            'primary': colors.darkslategray,
            'secondary': colors.lightgrey,
            'accent': colors.coral,
            'text': colors.black,
            'background': colors.whitesmoke,
        },
        'tutorial': {
            'primary': colors.darkgreen,
            'secondary': colors.lightgreen,
            'accent': colors.orange,
            'text': colors.black,
            'background': colors.white,
        },
        'technical': {
            'primary': colors.darkred,
            'secondary': colors.lightgrey,
            'accent': colors.blue,
            'text': colors.black,
            'background': colors.white,
        }
    }

    def __init__(
        self,
        template_name: str = 'professional',
        page_size: str = 'a4',
        color_scheme: str = 'professional'
    ):
        """
        Initialize a PDF template.

        Args:
            template_name: Name of the template
            page_size: Page size ('a4', 'letter', 'a3')
            color_scheme: Color scheme name
        """
        self.template_name = template_name
        self.page_size = self.PAGE_SIZES.get(page_size.lower(), A4)
        self.color_scheme = self.COLOR_SCHEMES.get(color_scheme.lower(), self.COLOR_SCHEMES['professional'])

        # Initialize styles
        self.styles = self._create_styles()

        # Template metadata
        self.metadata = {
            'name': template_name,
            'page_size': page_size,
            'color_scheme': color_scheme,
            'version': '2.0.0',
            'author': 'Kalponic Studio'
        }

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create paragraph styles for the template."""
        styles = getSampleStyleSheet()

        # Title styles
        styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=styles['Title'],
            fontSize=28,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=self.color_scheme['primary'],
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            textColor=self.color_scheme['primary'],
            borderColor=self.color_scheme['secondary'],
            borderWidth=0,
            borderPadding=0
        ))

        styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=self.color_scheme['secondary'],
        ))

        # Content styles
        styles.add(ParagraphStyle(
            name='TutorialBody',
            parent=styles['Normal'],
            fontSize=11,
            lineHeight=1.4,
            spaceAfter=12,
            textColor=self.color_scheme['text']
        ))

        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Code'],
            fontSize=9,
            fontName='Courier',
            backColor=colors.lightgrey,
            borderColor=colors.grey,
            borderWidth=1,
            borderPadding=8,
            spaceAfter=15,
            leftIndent=15,
            rightIndent=15
        ))

        # Special content styles
        styles.add(ParagraphStyle(
            name='QuoteBlock',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=30,
            rightIndent=30,
            spaceAfter=15,
            textColor=self.color_scheme['secondary'],
            borderColor=self.color_scheme['accent'],
            borderWidth=1,
            borderPadding=10
        ))

        styles.add(ParagraphStyle(
            name='HighlightBox',
            parent=styles['Normal'],
            fontSize=11,
            backColor=self.color_scheme['secondary'],
            borderColor=self.color_scheme['accent'],
            borderWidth=2,
            borderPadding=10,
            spaceAfter=15,
            leftIndent=10,
            rightIndent=10
        ))

        return styles

    def get_page_setup(self) -> Dict[str, Any]:
        """Get page setup configuration."""
        return {
            'pagesize': self.page_size,
            'margins': {
                'left': 1 * inch,
                'right': 1 * inch,
                'top': 1 * inch,
                'bottom': 1 * inch
            },
            'show_boundary': False,
            'background_color': self.color_scheme['background']
        }

    def get_style(self, style_name: str) -> Optional[ParagraphStyle]:
        """Get a specific style by name."""
        return self.styles.get(style_name)

    def customize_colors(self, color_updates: Dict[str, colors.Color]) -> None:
        """
        Customize the color scheme.

        Args:
            color_updates: Dictionary of color updates
        """
        self.color_scheme.update(color_updates)
        # Recreate styles with new colors
        self.styles = self._create_styles()

    def save_template(self, file_path: Union[str, Path]) -> None:
        """Save the template configuration to a JSON file."""
        config = {
            'metadata': self.metadata,
            'color_scheme': {
                k: v.hexval() if hasattr(v, 'hexval') else str(v)
                for k, v in self.color_scheme.items()
            },
            'page_size': [k for k, v in self.PAGE_SIZES.items() if v == self.page_size][0],
            'styles': {
                name: {
                    'fontSize': style.fontSize,
                    'fontName': style.fontName,
                    'textColor': style.textColor.hexval() if hasattr(style.textColor, 'hexval') else str(style.textColor),
                    'spaceAfter': style.spaceAfter,
                    'leftIndent': style.leftIndent,
                    'rightIndent': style.rightIndent,
                }
                for name, style in self.styles.items()
            }
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load_template(cls, file_path: Union[str, Path]) -> 'KSPDFTemplate':
        """Load a template from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Create template instance
        template = cls(
            template_name=config['metadata']['name'],
            page_size=config.get('page_size', 'a4'),
            color_scheme=config['metadata'].get('color_scheme', 'professional')
        )

        # Apply custom colors if specified
        if 'color_scheme' in config:
            color_updates = {}
            for key, value in config['color_scheme'].items():
                if isinstance(value, str) and value.startswith('#'):
                    color_updates[key] = colors.HexColor(value)
                elif isinstance(value, str):
                    # Try to parse color name
                    try:
                        color_updates[key] = getattr(colors, value.lower())
                    except:
                        pass
            template.customize_colors(color_updates)

        return template


class TemplateManager:
    """Manager for PDF templates."""

    def __init__(self, templates_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the template manager.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
        self.templates = {}

        # Load built-in templates
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        builtin_templates = {
            'professional': KSPDFTemplate('professional', 'a4', 'professional'),
            'modern': KSPDFTemplate('modern', 'a4', 'modern'),
            'tutorial': KSPDFTemplate('tutorial', 'a4', 'tutorial'),
            'technical': KSPDFTemplate('technical', 'a4', 'technical'),
        }

        self.templates.update(builtin_templates)

    def get_template(self, name: str) -> Optional[KSPDFTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """List available templates."""
        return list(self.templates.keys())

    def create_custom_template(
        self,
        name: str,
        base_template: str = 'professional',
        customizations: Optional[Dict[str, Any]] = None
    ) -> KSPDFTemplate:
        """
        Create a custom template.

        Args:
            name: Name for the custom template
            base_template: Base template to extend
            customizations: Customization options

        Returns:
            Custom template instance
        """
        # Start with base template
        base = self.get_template(base_template)
        if not base:
            base = KSPDFTemplate()

        # Apply customizations
        if customizations:
            if 'color_scheme' in customizations:
                base.customize_colors(customizations['color_scheme'])

            if 'page_size' in customizations:
                base.page_size = base.PAGE_SIZES.get(customizations['page_size'], A4)

        # Store custom template
        self.templates[name] = base
        base.template_name = name

        return base

    def save_template(self, template: KSPDFTemplate, filename: Optional[str] = None) -> None:
        """Save a template to disk."""
        if not filename:
            filename = f"{template.template_name}.json"

        file_path = self.templates_dir / filename
        template.save_template(file_path)

    def load_template_from_file(self, filename: str) -> Optional[KSPDFTemplate]:
        """Load a template from file."""
        file_path = self.templates_dir / filename
        if file_path.exists():
            template = KSPDFTemplate.load_template(file_path)
            self.templates[template.template_name] = template
            return template
        return None

    def load_all_templates(self) -> None:
        """Load all template files from the templates directory."""
        for json_file in self.templates_dir.glob('*.json'):
            try:
                template = KSPDFTemplate.load_template(json_file)
                self.templates[template.template_name] = template
            except Exception as e:
                print(f"Failed to load template {json_file}: {e}")


class BrandingManager:
    """Manager for document branding elements."""

    def __init__(self):
        """Initialize branding manager."""
        self.brand_elements = {
            'logo': None,
            'header_text': '',
            'footer_text': '',
            'watermark': None,
            'cover_page': False,
            'toc_style': 'default'
        }

    def set_logo(self, logo_path: Union[str, Path]) -> None:
        """Set the document logo."""
        self.brand_elements['logo'] = Path(logo_path)

    def set_header_footer(self, header: str = '', footer: str = '') -> None:
        """Set header and footer text."""
        self.brand_elements['header_text'] = header
        self.brand_elements['footer_text'] = footer

    def set_watermark(self, watermark_path: Union[str, Path]) -> None:
        """Set document watermark."""
        self.brand_elements['watermark'] = Path(watermark_path)

    def enable_cover_page(self, enabled: bool = True) -> None:
        """Enable or disable cover page generation."""
        self.brand_elements['cover_page'] = enabled

    def get_branding_config(self) -> Dict[str, Any]:
        """Get the current branding configuration."""
        return self.brand_elements.copy()


# Convenience functions
def get_template(name: str = 'professional') -> KSPDFTemplate:
    """Get a template by name."""
    manager = TemplateManager()
    return manager.get_template(name) or KSPDFTemplate()


def create_tutorial_template() -> KSPDFTemplate:
    """Create a template optimized for tutorials."""
    return KSPDFTemplate('tutorial', 'a4', 'tutorial')


def create_technical_template() -> KSPDFTemplate:
    """Create a template optimized for technical documentation."""
    return KSPDFTemplate('technical', 'a4', 'technical')


if __name__ == "__main__":
    # Test the template system
    print("Testing PDF Template System...")

    # Create different templates
    professional = KSPDFTemplate('professional', 'a4', 'professional')
    tutorial = KSPDFTemplate('tutorial', 'a4', 'tutorial')
    modern = KSPDFTemplate('modern', 'a4', 'modern')

    print(f"✅ Created {len([professional, tutorial, modern])} templates")

    # Test template manager
    manager = TemplateManager()
    templates = manager.list_templates()
    print(f"✅ Available templates: {templates}")

    # Test custom template
    custom = manager.create_custom_template(
        'custom_tutorial',
        'tutorial',
        {
            'color_scheme': {
                'primary': colors.purple,
                'accent': colors.gold
            }
        }
    )
    print(f"✅ Created custom template: {custom.template_name}")

    # Test branding
    branding = BrandingManager()
    branding.set_header_footer(
        header="KS PDF Studio - Professional Documentation",
        footer="© 2025 Kalponic Studio"
    )
    print("✅ Branding configured")

    print("Template system test complete!")