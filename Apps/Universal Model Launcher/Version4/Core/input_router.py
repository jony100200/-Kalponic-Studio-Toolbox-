"""
🧠 Input Router - Smart Input Type Detection
Role: "Input Detective" - Determine task type from user input
SOLID Principle: Single Responsibility - Input classification only
"""

import os
import re
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """Supported task types for model selection"""
    TEXT = "text"
    IMAGE = "image" 
    AUDIO = "audio"
    CODE = "code"
    PDF = "pdf"
    UNKNOWN = "unknown"


@dataclass
class InputAnalysis:
    """Result of input type analysis"""
    task_type: TaskType
    confidence: float  # 0.0 - 1.0
    details: Dict[str, any]
    reasoning: str


class InputRouter:
    """
    Smart input type detection for automatic model selection.
    
    Analyzes user input (text, file path, or binary data) and determines
    the most appropriate task type for model selection.
    """
    
    def __init__(self):
        self._code_extensions = {
            '.py', '.js', '.ts', '.html', '.css', '.cpp', '.java', 
            '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift',
            '.kt', '.scala', '.sh', '.bat', '.sql', '.json', '.xml',
            '.yaml', '.yml', '.md', '.rst', '.tex'
        }
        
        self._image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.webp', '.svg', '.ico', '.heic', '.avif'
        }
        
        self._audio_extensions = {
            '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma',
            '.opus', '.mp4', '.avi', '.mov', '.mkv'  # Video files for audio extraction
        }
        
        self._code_patterns = [
            r'def\s+\w+\s*\(',  # Python functions
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'class\s+\w+\s*[{:]',  # Class definitions
            r'import\s+[\w.]+',  # Import statements
            r'from\s+\w+\s+import',  # Python imports
            r'#include\s*<[\w.]+>',  # C/C++ includes
            r'package\s+[\w.]+;',  # Java packages
            r'using\s+[\w.]+;'  # C# using statements
        ]
    
    def analyze_input(self, input_data: str, is_file_path: bool = False) -> InputAnalysis:
        """
        Analyze input and determine task type.
        
        Args:
            input_data: Text content or file path
            is_file_path: Whether input_data is a file path
            
        Returns:
            InputAnalysis with task type and confidence
        """
        if is_file_path:
            return self._analyze_file_path(input_data)
        else:
            return self._analyze_text_content(input_data)
    
    def _analyze_file_path(self, file_path: str) -> InputAnalysis:
        """Analyze file path to determine task type"""
        path = Path(file_path)
        
        if not path.exists():
            return InputAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                details={'error': 'File does not exist'},
                reasoning=f"File not found: {file_path}"
            )
        
        extension = path.suffix.lower()
        
        # PDF detection
        if extension == '.pdf':
            return InputAnalysis(
                task_type=TaskType.PDF,
                confidence=1.0,
                details={'extension': extension, 'size_mb': path.stat().st_size / (1024*1024)},
                reasoning="PDF file extension detected"
            )
        
        # Image detection
        if extension in self._image_extensions:
            return InputAnalysis(
                task_type=TaskType.IMAGE,
                confidence=1.0,
                details={'extension': extension, 'size_mb': path.stat().st_size / (1024*1024)},
                reasoning=f"Image file extension: {extension}"
            )
        
        # Audio detection
        if extension in self._audio_extensions:
            return InputAnalysis(
                task_type=TaskType.AUDIO,
                confidence=1.0,
                details={'extension': extension, 'size_mb': path.stat().st_size / (1024*1024)},
                reasoning=f"Audio/video file extension: {extension}"
            )
        
        # Code detection
        if extension in self._code_extensions:
            return InputAnalysis(
                task_type=TaskType.CODE,
                confidence=1.0,
                details={'extension': extension, 'language': self._guess_language(extension)},
                reasoning=f"Code file extension: {extension}"
            )
        
        # Try to analyze content for unknown extensions
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # First 1KB
                return self._analyze_text_content(content, file_extension=extension)
        except Exception:
            # Binary file or unreadable
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type:
                if mime_type.startswith('image/'):
                    return InputAnalysis(
                        task_type=TaskType.IMAGE,
                        confidence=0.8,
                        details={'mime_type': mime_type},
                        reasoning=f"MIME type detection: {mime_type}"
                    )
                elif mime_type.startswith('audio/') or mime_type.startswith('video/'):
                    return InputAnalysis(
                        task_type=TaskType.AUDIO,
                        confidence=0.8,
                        details={'mime_type': mime_type},
                        reasoning=f"MIME type detection: {mime_type}"
                    )
            
            return InputAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                details={'error': 'Binary file, unreadable content'},
                reasoning="Unable to determine file type"
            )
    
    def _analyze_text_content(self, content: str, file_extension: str = None) -> InputAnalysis:
        """Analyze text content to determine if it's code or regular text"""
        if not content.strip():
            return InputAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                details={'error': 'Empty content'},
                reasoning="No content to analyze"
            )
        
        # Check for code patterns
        code_score = 0
        matched_patterns = []
        
        for pattern in self._code_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                code_score += 1
                matched_patterns.append(pattern)
        
        # Additional code indicators
        code_indicators = [
            '{', '}', ';', '()', '[]', '+=', '-=', '*=', '/=',
            'if ', 'else', 'for ', 'while ', 'return ', 'var ', 'let ',
            'const ', 'function', 'class ', 'def ', 'import ', 'include'
        ]
        
        indicator_count = sum(1 for indicator in code_indicators if indicator in content)
        
        # Calculate code probability
        code_probability = min(1.0, (code_score * 0.3 + indicator_count * 0.1))
        
        if code_probability > 0.6:
            return InputAnalysis(
                task_type=TaskType.CODE,
                confidence=code_probability,
                details={
                    'matched_patterns': matched_patterns,
                    'code_indicators': indicator_count,
                    'language': self._guess_language_from_content(content, file_extension)
                },
                reasoning=f"Code patterns detected (confidence: {code_probability:.2f})"
            )
        else:
            return InputAnalysis(
                task_type=TaskType.TEXT,
                confidence=1.0 - code_probability,
                details={'length': len(content), 'word_count': len(content.split())},
                reasoning="Regular text content detected"
            )
    
    def _guess_language(self, extension: str) -> str:
        """Guess programming language from file extension"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.java': 'java',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.bat': 'batch',
            '.sql': 'sql',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        return language_map.get(extension, 'unknown')
    
    def _guess_language_from_content(self, content: str, extension: str = None) -> str:
        """Guess programming language from content analysis"""
        if extension:
            return self._guess_language(extension)
        
        # Simple heuristics for language detection
        if re.search(r'def\s+\w+\s*\(|import\s+\w+|from\s+\w+\s+import', content):
            return 'python'
        elif re.search(r'function\s+\w+\s*\(|var\s+\w+|let\s+\w+|const\s+\w+', content):
            return 'javascript'
        elif re.search(r'class\s+\w+\s*{|public\s+class|private\s+\w+', content):
            return 'java'
        elif re.search(r'#include\s*<|int\s+main\s*\(|void\s+\w+\s*\(', content):
            return 'c'
        elif re.search(r'using\s+System|namespace\s+\w+|public\s+void', content):
            return 'csharp'
        else:
            return 'unknown'
