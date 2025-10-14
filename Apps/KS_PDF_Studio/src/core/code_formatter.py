"""
KS PDF Studio - Code Formatter
Syntax highlighting and code formatting for PDF generation.

Author: Kalponic Studio
Version: 2.0.0
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer, guess_lexer
from pygments.formatters import TerminalFormatter, HtmlFormatter, LatexFormatter
from pygments.styles import get_style_by_name

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Preformatted


class KSCodeFormatter:
    """
    Professional code formatting for KS PDF Studio.

    Features:
    - Syntax highlighting for 100+ languages
    - Multiple output formats (PDF, HTML, LaTeX)
    - Custom styling and themes
    - Line numbers and highlighting
    - Code block processing
    """

    # Default style settings
    DEFAULT_STYLE = 'monokai'  # Dark theme suitable for code
    DEFAULT_FONT_SIZE = 9
    DEFAULT_LINE_HEIGHT = 1.2

    # Supported languages mapping
    LANGUAGE_ALIASES = {
        'js': 'javascript',
        'py': 'python',
        'cpp': 'cpp',
        'c++': 'cpp',
        'cs': 'csharp',
        'c#': 'csharp',
        'html': 'html',
        'xml': 'xml',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'sh': 'bash',
        'shell': 'bash',
        'ps1': 'powershell',
        'sql': 'sql',
        'css': 'css',
        'scss': 'scss',
        'sass': 'sass',
        'less': 'less',
        'java': 'java',
        'kt': 'kotlin',
        'swift': 'swift',
        'go': 'go',
        'rs': 'rust',
        'php': 'php',
        'rb': 'ruby',
        'pl': 'perl',
        'lua': 'lua',
        'r': 'r',
        'matlab': 'matlab',
        'scala': 'scala',
        'hs': 'haskell',
        'ml': 'ocaml',
        'fs': 'fsharp',
        'vb': 'vbnet',
        'asm': 'nasm',
        'dockerfile': 'docker',
        'makefile': 'make',
        'nginx': 'nginx',
        'apache': 'apache',
        'toml': 'toml',
        'ini': 'ini',
        'cfg': 'ini',
        'conf': 'ini',
    }

    def __init__(
        self,
        style: str = DEFAULT_STYLE,
        font_size: int = DEFAULT_FONT_SIZE,
        line_height: float = DEFAULT_LINE_HEIGHT
    ):
        """
        Initialize the code formatter.

        Args:
            style: Pygments style name
            font_size: Font size for code
            line_height: Line height multiplier
        """
        self.style = style
        self.font_size = font_size
        self.line_height = line_height

        # Initialize formatters
        self.html_formatter = HtmlFormatter(style=get_style_by_name(style))
        self.latex_formatter = LatexFormatter(style=get_style_by_name(style))

        # PDF styles for code
        self.code_style = ParagraphStyle(
            name='CodeFormatted',
            fontName='Courier',
            fontSize=font_size,
            leading=font_size * line_height,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=15,
            backColor=colors.lightgrey,
            borderColor=colors.grey,
            borderWidth=1,
            borderPadding=10
        )

    def format_code_block(
        self,
        code: str,
        language: str = 'text',
        show_line_numbers: bool = False,
        highlight_lines: Optional[List[int]] = None
    ) -> Dict[str, Union[str, Preformatted]]:
        """
        Format a code block with syntax highlighting.

        Args:
            code: Raw code text
            language: Programming language
            show_line_numbers: Whether to show line numbers
            highlight_lines: List of line numbers to highlight

        Returns:
            Dict with 'html', 'latex', and 'pdf' formatted versions
        """
        # Normalize language
        language = self._normalize_language(language)

        try:
            # Get appropriate lexer
            lexer = self._get_lexer(code, language)

            # Configure formatter options
            formatter_options = {
                'style': self.style,
                'linenos': show_line_numbers,
                'linenostart': 1,
            }

            if highlight_lines:
                formatter_options['hl_lines'] = highlight_lines

            # Create formatters with options
            html_formatter = HtmlFormatter(**formatter_options)
            latex_formatter = LatexFormatter(**formatter_options)

            # Generate formatted code
            html_code = highlight(code, lexer, html_formatter)
            latex_code = highlight(code, lexer, latex_formatter)

            # Create PDF version (simplified for ReportLab)
            pdf_code = self._create_pdf_code_element(code, language)

            return {
                'html': html_code,
                'latex': latex_code,
                'pdf': pdf_code,
                'language': language,
                'lexer': lexer.name,
                'lines': len(code.splitlines())
            }

        except Exception as e:
            # Fallback to plain text
            return self._fallback_formatting(code, language)

    def _normalize_language(self, language: str) -> str:
        """Normalize language name to Pygments format."""
        language = language.lower().strip()

        # Check aliases
        if language in self.LANGUAGE_ALIASES:
            return self.LANGUAGE_ALIASES[language]

        return language

    def _get_lexer(self, code: str, language: str):
        """Get the appropriate Pygments lexer."""
        try:
            if language and language != 'text':
                return get_lexer_by_name(language)
            else:
                # Try to guess the language
                return guess_lexer(code)
        except:
            # Fallback to plain text
            return TextLexer()

    def _create_pdf_code_element(self, code: str, language: str) -> Preformatted:
        """Create a ReportLab Preformatted element for PDF."""
        # Add language header
        header = f"[{language.upper()}]" if language != 'text' else "[CODE]"
        formatted_code = f"{header}\n{code}"

        return Preformatted(formatted_code, self.code_style)

    def _fallback_formatting(self, code: str, language: str) -> Dict[str, Union[str, Preformatted]]:
        """Fallback formatting when syntax highlighting fails."""
        return {
            'html': f'<pre><code class="language-{language}">{code}</code></pre>',
            'latex': f'\\begin{{verbatim}}{code}\\end{{verbatim}}',
            'pdf': self._create_pdf_code_element(code, language),
            'language': language,
            'lexer': 'text',
            'lines': len(code.splitlines()),
            'error': 'Syntax highlighting failed, using plain text'
        }

    def extract_code_blocks(self, markdown_content: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown content.

        Args:
            markdown_content: Raw markdown string

        Returns:
            List of code block dictionaries
        """
        code_blocks = []

        # Regex to find fenced code blocks
        fenced_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(fenced_pattern, markdown_content, re.DOTALL)

        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip(),
                'lines': len(code.strip().split('\n'))
            })

        return code_blocks

    def batch_format_code_blocks(
        self,
        code_blocks: List[Dict[str, str]],
        **kwargs
    ) -> List[Dict[str, Union[str, Preformatted]]]:
        """
        Format multiple code blocks.

        Args:
            code_blocks: List of code block dictionaries
            **kwargs: Formatting options

        Returns:
            List of formatted code block dictionaries
        """
        formatted_blocks = []

        for block in code_blocks:
            formatted = self.format_code_block(
                block['code'],
                block['language'],
                **kwargs
            )
            formatted_blocks.append(formatted)

        return formatted_blocks

    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        from pygments.lexers import get_all_lexers

        languages = []
        for lexer_info in get_all_lexers():
            languages.extend(lexer_info[1])  # Add aliases

        return sorted(set(languages))

    def get_available_styles(self) -> List[str]:
        """Get list of available Pygments styles."""
        from pygments.styles import get_all_styles
        return list(get_all_styles())

    def create_custom_style(
        self,
        name: str,
        base_style: str = 'default',
        custom_colors: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a custom Pygments style.

        Args:
            name: Name for the custom style
            base_style: Base style to extend
            custom_colors: Dictionary of token types to colors

        Returns:
            Style name (can be used with set_style)
        """
        # This is a simplified implementation
        # In a full implementation, you'd create a custom Style class
        if custom_colors:
            # For now, just return the base style
            # A complete implementation would create a new Style class
            pass

        return base_style

    def set_style(self, style_name: str) -> bool:
        """
        Set the current style for formatting.

        Args:
            style_name: Name of the Pygments style

        Returns:
            bool: True if style was set successfully
        """
        try:
            # Validate style exists
            get_style_by_name(style_name)

            # Update formatters
            self.style = style_name
            self.html_formatter = HtmlFormatter(style=get_style_by_name(style_name))
            self.latex_formatter = LatexFormatter(style=get_style_by_name(style_name))

            return True

        except:
            return False

    def validate_code_block(self, code: str, language: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate a code block.

        Args:
            code: Code content
            language: Language name

        Returns:
            Dict with validation results
        """
        result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }

        # Check if language is supported
        if language and language != 'text':
            try:
                get_lexer_by_name(language)
            except:
                result['warnings'].append(f'Language "{language}" not recognized, will use plain text')

        # Check for common issues
        if not code.strip():
            result['errors'].append('Code block is empty')
            result['valid'] = False

        # Check for very long lines
        lines = code.split('\n')
        long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 120]
        if long_lines:
            result['warnings'].append(f'Long lines detected at: {long_lines[:5]}...')

        # Check for mixed tabs/spaces (common Python issue)
        if language.lower() in ['python', 'py']:
            has_tabs = '\t' in code
            has_spaces = '    ' in code
            if has_tabs and has_spaces:
                result['warnings'].append('Mixed tabs and spaces detected')

        return result


class CodeBlockProcessor:
    """Utility class for processing code blocks in documents."""

    @staticmethod
    def count_code_blocks(markdown_content: str) -> int:
        """Count the number of code blocks in markdown."""
        fenced_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(fenced_pattern, markdown_content, re.DOTALL)
        return len(matches)

    @staticmethod
    def get_code_languages(markdown_content: str) -> List[str]:
        """Get list of programming languages used in code blocks."""
        languages = []
        fenced_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(fenced_pattern, markdown_content, re.DOTALL)

        for language, _ in matches:
            if language:
                languages.append(language)

        return list(set(languages))

    @staticmethod
    def estimate_code_complexity(code: str, language: str) -> Dict[str, Union[int, float]]:
        """Estimate code complexity metrics."""
        lines = code.split('\n')
        total_lines = len(lines)

        # Remove empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        code_lines = len(non_empty_lines)

        # Estimate complexity (simplified)
        complexity_score = 0

        # Keywords that indicate complexity
        complexity_keywords = {
            'python': ['if', 'for', 'while', 'def', 'class', 'try', 'except'],
            'javascript': ['if', 'for', 'while', 'function', 'class', 'try', 'catch'],
            'java': ['if', 'for', 'while', 'method', 'class', 'try', 'catch'],
        }

        keywords = complexity_keywords.get(language.lower(), [])
        for line in non_empty_lines:
            for keyword in keywords:
                complexity_score += line.lower().count(keyword)

        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'complexity_score': complexity_score,
            'avg_line_length': sum(len(line) for line in non_empty_lines) / max(code_lines, 1)
        }


# Convenience functions
def format_code_block(
    code: str,
    language: str = 'text',
    **kwargs
) -> Dict[str, Union[str, Preformatted]]:
    """Quick function to format a single code block."""
    formatter = KSCodeFormatter(**kwargs)
    return formatter.format_code_block(code, language)


def extract_and_format_code_blocks(
    markdown_content: str,
    **kwargs
) -> List[Dict[str, Union[str, Preformatted]]]:
    """Extract and format all code blocks from markdown."""
    formatter = KSCodeFormatter(**kwargs)
    code_blocks = formatter.extract_code_blocks(markdown_content)
    return formatter.batch_format_code_blocks(code_blocks)


if __name__ == "__main__":
    # Test the code formatter
    formatter = KSCodeFormatter()

    # Test code block
    test_code = '''
def hello_world():
    """A simple hello world function."""
    print("Hello, KS PDF Studio!")
    return True

if __name__ == "__main__":
    hello_world()
'''

    print("Testing code formatting...")
    result = formatter.format_code_block(test_code, 'python')

    print(f"Language: {result['language']}")
    print(f"Lines: {result['lines']}")
    print(f"Lexer: {result['lexer']}")
    print("✅ Code formatting test complete!")

    # Test extraction
    test_markdown = """
# Test Document

Here's some Python code:

```python
print("Hello!")
```

And some JavaScript:

```javascript
console.log("Hello!");
```
"""

    code_blocks = formatter.extract_code_blocks(test_markdown)
    print(f"Found {len(code_blocks)} code blocks")
    for block in code_blocks:
        print(f"- {block['language']}: {block['lines']} lines")