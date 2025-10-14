"""
KS PDF Studio - AI Enhancement Module
High-level AI integration for content enhancement and automation.

Author: Kalponic Studio
Version: 2.0.0
"""

import re
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import json

from .ai_manager import AIModelManager, ContentGenerator, ImageMatcher


class AIEnhancer:
    """
    AI-powered content enhancement for KS PDF Studio.

    Features:
    - Intelligent content expansion
    - Image suggestions
    - Quality improvement
    - Automated structuring
    """

    def __init__(self, model_manager: Optional[AIModelManager] = None):
        """
        Initialize AI enhancer.

        Args:
            model_manager: Optional pre-configured model manager
        """
        self.model_manager = model_manager or AIModelManager()
        self.content_generator = ContentGenerator(self.model_manager)
        self.image_matcher = ImageMatcher(self.model_manager)

        # Enhancement settings
        self.settings = {
            'auto_expand_sections': True,
            'suggest_images': True,
            'improve_writing': False,
            'add_examples': True,
            'generate_exercises': False,
            'confidence_threshold': 0.3
        }

    def enhance_markdown(
        self,
        markdown_content: str,
        enhancement_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhance markdown content with AI assistance.

        Args:
            markdown_content: Original markdown content
            enhancement_options: Custom enhancement settings

        Returns:
            Dict with enhanced content and suggestions
        """
        options = {**self.settings, **(enhancement_options or {})}

        result = {
            'original_content': markdown_content,
            'enhanced_content': markdown_content,
            'suggestions': [],
            'applied_enhancements': [],
            'warnings': []
        }

        try:
            # Parse existing content
            content_analysis = self._analyze_content(markdown_content)

            # Apply enhancements based on options
            if options['auto_expand_sections']:
                result = self._expand_sections(result, content_analysis, options)

            if options['suggest_images']:
                result = self._suggest_images(result, content_analysis, options)

            if options['add_examples']:
                result = self._add_examples(result, content_analysis, options)

            if options['generate_exercises']:
                result = self._generate_exercises(result, content_analysis, options)

            if options['improve_writing']:
                result = self._improve_writing(result, content_analysis, options)

        except Exception as e:
            result['warnings'].append(f'AI enhancement failed: {e}')
            # Return original content if enhancement fails
            result['enhanced_content'] = markdown_content

        return result

    def _analyze_content(self, markdown_content: str) -> Dict[str, Any]:
        """Analyze markdown content structure and quality."""
        analysis = {
            'sections': [],
            'code_blocks': 0,
            'images': 0,
            'word_count': 0,
            'readability_score': 0,
            'structure_score': 0
        }

        lines = markdown_content.split('\n')

        current_section = None
        section_content = []

        for line in lines:
            line = line.strip()

            # Count sections
            if line.startswith('#'):
                if current_section:
                    analysis['sections'].append({
                        'title': current_section,
                        'content': '\n'.join(section_content),
                        'level': len(line) - len(line.lstrip('#'))
                    })

                current_section = line.lstrip('#').strip()
                section_content = []
            else:
                section_content.append(line)

            # Count code blocks
            if line.startswith('```'):
                analysis['code_blocks'] += 1

            # Count images
            if '![' in line and '](' in line:
                analysis['images'] += 1

        # Add final section
        if current_section:
            analysis['sections'].append({
                'title': current_section,
                'content': '\n'.join(section_content),
                'level': len(current_section) - len(current_section.lstrip('#'))
            })

        # Calculate word count
        analysis['word_count'] = len(markdown_content.split())

        # Simple structure score
        analysis['structure_score'] = min(100, len(analysis['sections']) * 20)

        return analysis

    def _expand_sections(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expand thin sections with AI-generated content."""
        enhanced_lines = result['enhanced_content'].split('\n')
        new_suggestions = []

        for section in analysis['sections']:
            content_words = len(section['content'].split())

            # Expand sections with less than 100 words
            if content_words < 100 and section['level'] <= 2:
                try:
                    # Generate additional content
                    expansion = self.content_generator.generate_content(
                        section['title'],
                        content_type='section_content',
                        max_length=200
                    )

                    if 'content' in expansion and expansion['content']:
                        new_suggestions.append({
                            'type': 'section_expansion',
                            'section': section['title'],
                            'suggested_content': expansion['content'],
                            'reason': f'Section has only {content_words} words'
                        })

                except Exception as e:
                    result['warnings'].append(f'Failed to expand section "{section["title"]}": {e}')

        result['suggestions'].extend(new_suggestions)
        result['applied_enhancements'].append('section_expansion_analysis')

        return result

    def _suggest_images(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest relevant images for content sections."""
        # This would require an image library - for now, just add placeholder suggestions
        new_suggestions = []

        for section in analysis['sections']:
            if len(section['content']) > 100:  # Only for substantial sections
                new_suggestions.append({
                    'type': 'image_suggestion',
                    'section': section['title'],
                    'suggested_image': f'diagram_{section["title"].lower().replace(" ", "_")}.png',
                    'reason': 'Visual aid would enhance understanding',
                    'confidence': 0.7
                })

        result['suggestions'].extend(new_suggestions)
        result['applied_enhancements'].append('image_suggestions')

        return result

    def _add_examples(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest adding practical examples to theoretical sections."""
        new_suggestions = []

        for section in analysis['sections']:
            content_lower = section['content'].lower()

            # Look for theoretical content without examples
            theoretical_keywords = ['concept', 'theory', 'principle', 'understanding']
            example_keywords = ['example', 'for instance', 'such as', 'like this']

            has_theory = any(keyword in content_lower for keyword in theoretical_keywords)
            has_examples = any(keyword in content_lower for keyword in example_keywords)

            if has_theory and not has_examples and len(section['content']) > 50:
                new_suggestions.append({
                    'type': 'add_example',
                    'section': section['title'],
                    'suggested_content': 'Consider adding a practical example or code snippet to illustrate this concept.',
                    'reason': 'Theoretical content would benefit from practical examples'
                })

        result['suggestions'].extend(new_suggestions)
        result['applied_enhancements'].append('example_suggestions')

        return result

    def _generate_exercises(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate exercise suggestions for learning reinforcement."""
        new_suggestions = []

        # Add exercise section at the end if not present
        if not any('exercise' in section['title'].lower() for section in analysis['sections']):
            try:
                # Extract main topic from title or first section
                main_topic = analysis['sections'][0]['title'] if analysis['sections'] else 'the topic'

                exercise = self.content_generator.generate_content(
                    main_topic,
                    content_type='exercise',
                    max_length=150
                )

                if 'content' in exercise and exercise['content']:
                    new_suggestions.append({
                        'type': 'add_exercise_section',
                        'section': 'Exercises',
                        'suggested_content': exercise['content'],
                        'reason': 'Adding exercises for better learning retention'
                    })

            except Exception as e:
                result['warnings'].append(f'Failed to generate exercises: {e}')

        result['suggestions'].extend(new_suggestions)
        result['applied_enhancements'].append('exercise_generation')

        return result

    def _improve_writing(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest writing improvements (placeholder for future implementation)."""
        # This would require a more sophisticated language model
        result['applied_enhancements'].append('writing_analysis')
        return result

    def create_tutorial_from_topic(
        self,
        topic: str,
        difficulty: str = 'beginner',
        include_images: bool = False
    ) -> Dict[str, Any]:
        """
        Create a complete tutorial from just a topic.

        Args:
            topic: Tutorial topic
            difficulty: Difficulty level
            include_images: Whether to suggest images

        Returns:
            Complete tutorial structure
        """
        try:
            # Generate tutorial structure
            tutorial = self.content_generator.create_tutorial_structure(topic, difficulty)

            # Convert to markdown
            markdown_content = self._tutorial_to_markdown(tutorial)

            # Add enhancements
            enhanced = self.enhance_markdown(
                markdown_content,
                {
                    'auto_expand_sections': True,
                    'suggest_images': include_images,
                    'add_examples': True,
                    'generate_exercises': True
                }
            )

            return {
                'tutorial': tutorial,
                'markdown': enhanced['enhanced_content'],
                'suggestions': enhanced['suggestions'],
                'topic': topic,
                'difficulty': difficulty,
                'generated': True
            }

        except Exception as e:
            return {
                'error': str(e),
                'topic': topic,
                'difficulty': difficulty,
                'generated': False
            }

    def _tutorial_to_markdown(self, tutorial: Dict[str, Any]) -> str:
        """Convert tutorial structure to markdown."""
        lines = []

        # Title
        lines.append(f"# {tutorial['title']}")
        lines.append("")

        # Metadata
        lines.append(f"**Difficulty:** {tutorial['difficulty'].title()}")
        lines.append(f"**Generated by:** KS PDF Studio AI")
        lines.append("")

        # Introduction
        if tutorial.get('introduction'):
            lines.append("## Introduction")
            lines.append("")
            lines.append(tutorial['introduction'])
            lines.append("")

        # Sections
        for section in tutorial.get('sections', []):
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section['content'])
            lines.append("")

        # Conclusion
        if tutorial.get('conclusion'):
            lines.append("## Conclusion")
            lines.append("")
            lines.append(tutorial['conclusion'])
            lines.append("")

        # Exercises
        if tutorial.get('exercises'):
            lines.append("## Exercises")
            lines.append("")
            for exercise in tutorial['exercises']:
                lines.append(f"### {exercise['title']}")
                lines.append("")
                lines.append(exercise['content'])
                lines.append("")

        return '\n'.join(lines)

    def get_enhancement_stats(self) -> Dict[str, Any]:
        """Get statistics about AI enhancement usage."""
        return {
            'settings': self.settings.copy(),
            'models_available': {
                'distilbart': self.model_manager.is_model_available('distilbart'),
                'clip': self.model_manager.is_model_available('clip')
            },
            'cache_info': self.model_manager.get_model_info()
        }

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        Update enhancement settings.

        Args:
            new_settings: New settings to apply
        """
        self.settings.update(new_settings)


class AIPipeline:
    """
    Complete AI processing pipeline for KS PDF Studio.
    """

    def __init__(self):
        """Initialize AI pipeline."""
        self.model_manager = AIModelManager()
        self.enhancer = AIEnhancer(self.model_manager)

    def process_content(
        self,
        input_content: Union[str, Dict[str, Any]],
        pipeline_steps: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process content through the AI pipeline.

        Args:
            input_content: Input markdown content or tutorial specification
            pipeline_steps: List of processing steps to apply

        Returns:
            Processed content with metadata
        """
        if pipeline_steps is None:
            pipeline_steps = ['enhance', 'validate', 'optimize']

        result = {
            'input': input_content,
            'output': input_content,
            'steps_applied': [],
            'metadata': {},
            'warnings': []
        }

        try:
            content = input_content

            for step in pipeline_steps:
                if step == 'enhance':
                    if isinstance(content, str):
                        enhanced = self.enhancer.enhance_markdown(content)
                        content = enhanced['enhanced_content']
                        result['enhancement_suggestions'] = enhanced['suggestions']
                    result['steps_applied'].append('enhance')

                elif step == 'validate':
                    # Basic validation
                    validation = self._validate_content(content)
                    result['validation'] = validation
                    result['steps_applied'].append('validate')

                elif step == 'optimize':
                    # Content optimization
                    optimized = self._optimize_content(content)
                    content = optimized['content']
                    result['optimizations'] = optimized['changes']
                    result['steps_applied'].append('optimize')

            result['output'] = content

        except Exception as e:
            result['warnings'].append(f'Pipeline processing failed: {e}')

        return result

    def _validate_content(self, content: str) -> Dict[str, Any]:
        """Validate content quality and structure."""
        validation = {
            'score': 100,
            'issues': [],
            'suggestions': []
        }

        # Check for basic structure
        if not re.search(r'^#\s+', content, re.MULTILINE):
            validation['issues'].append('Missing main title (# heading)')
            validation['score'] -= 20

        # Check for code blocks without language
        code_blocks = re.findall(r'```\n(.*?)\n```', content, re.DOTALL)
        for block in code_blocks:
            if not block.strip():
                validation['issues'].append('Empty code block found')
                validation['score'] -= 5

        # Check section balance
        sections = re.findall(r'^##\s+', content, re.MULTILINE)
        if len(sections) < 2:
            validation['suggestions'].append('Consider adding more sections for better structure')

        return validation

    def _optimize_content(self, content: str) -> Dict[str, Any]:
        """Optimize content for better readability."""
        optimized = content
        changes = []

        # Fix common markdown issues
        # Remove multiple consecutive blank lines
        original_lines = len(optimized.split('\n'))
        optimized = re.sub(r'\n\n\n+', '\n\n', optimized)
        if len(optimized.split('\n')) != original_lines:
            changes.append('Removed excessive blank lines')

        # Ensure consistent header spacing
        optimized = re.sub(r'^(#+)([^\s])', r'\1 \2', optimized, flags=re.MULTILINE)
        changes.append('Fixed header spacing')

        return {
            'content': optimized,
            'changes': changes
        }


# Convenience functions
def enhance_content(markdown_content: str, **options) -> Dict[str, Any]:
    """Quick function to enhance markdown content."""
    enhancer = AIEnhancer()
    return enhancer.enhance_markdown(markdown_content, options)


def create_tutorial(topic: str, **options) -> Dict[str, Any]:
    """Quick function to create a complete tutorial."""
    enhancer = AIEnhancer()
    return enhancer.create_tutorial_from_topic(topic, **options)


def process_with_ai_pipeline(content: str, **options) -> Dict[str, Any]:
    """Quick function to process content through AI pipeline."""
    pipeline = AIPipeline()
    return pipeline.process_content(content, **options)


if __name__ == "__main__":
    # Test the AI enhancement module
    print("🧪 Testing AI Enhancement Module...")

    # Test basic enhancement
    test_content = """
# Test Tutorial

## Introduction

This is a basic tutorial about Python programming.

## Basic Concepts

Python is a programming language. It has variables and functions.

## Code Example

```
print("Hello, World!")
```
"""

    print("Testing content enhancement...")
    enhancer = AIEnhancer()

    # Note: This will work even without models downloaded
    # The enhancement logic doesn't require models for basic suggestions
    result = enhancer.enhance_markdown(test_content)

    print(f"✅ Enhancement completed")
    print(f"Original content length: {len(result['original_content'])}")
    print(f"Enhanced content length: {len(result['enhanced_content'])}")
    print(f"Suggestions generated: {len(result['suggestions'])}")
    print(f"Applied enhancements: {result['applied_enhancements']}")

    if result['suggestions']:
        print("\nSample suggestions:")
        for i, suggestion in enumerate(result['suggestions'][:3]):
            print(f"  {i+1}. {suggestion['type']}: {suggestion.get('reason', 'N/A')}")

    print("\nAI Enhancement module initialized successfully!")