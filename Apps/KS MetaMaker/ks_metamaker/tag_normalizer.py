"""
Tag Normalization and Taxonomy System for KS MetaMaker
Handles synonym mapping, category organization, NSFW filtering, and tag validation
"""

import re
from typing import Dict, List, Set, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from .profile_manager import TagCategory, TagTaxonomy
else:
    try:
        from .profile_manager import TagCategory, TagTaxonomy
    except ImportError:
        # For testing or when run as script
        class TagCategory(Enum):
            GENERAL = "general"
            STYLE = "style"
            SUBJECT = "subject"
            COMPOSITION = "composition"
            QUALITY = "quality"
            TECHNICAL = "technical"

        @dataclass
        class TagTaxonomy:
            synonyms: Dict[str, List[str]] = None
            categories: Dict[str, TagCategory] = None
            nsfw_filters: List[str] = None
            priority_tags: List[str] = None
            banned_tags: List[str] = None

            def __post_init__(self):
                if self.synonyms is None:
                    self.synonyms = {}
                if self.categories is None:
                    self.categories = {}
                if self.nsfw_filters is None:
                    self.nsfw_filters = []
                if self.priority_tags is None:
                    self.priority_tags = []
                if self.banned_tags is None:
                    self.banned_tags = []


@dataclass
class NormalizedTag:
    """Represents a normalized tag with metadata"""
    original: str
    normalized: str
    category: TagCategory
    confidence: float = 1.0
    is_synonym: bool = False
    source_synonym: Optional[str] = None


class TagNormalizer:
    """Handles tag normalization, taxonomy mapping, and filtering"""

    def __init__(self, taxonomy: TagTaxonomy):
        self.taxonomy = taxonomy
        self._synonym_map = self._build_synonym_map()
        self._category_map = taxonomy.categories
        self._nsfw_patterns = self._build_nsfw_patterns()
        self._banned_tags = set(taxonomy.banned_tags or [])

        # Default values for normalization settings (can be overridden)
        self.min_confidence = 0.1
        self.remove_duplicates = True
        self.sort_by_confidence = True
        self.case_sensitive = False

    def _build_synonym_map(self) -> Dict[str, str]:
        """Build a mapping from synonyms to canonical tags"""
        synonym_map = {}

        for canonical, synonyms in self.taxonomy.synonyms.items():
            for synonym in synonyms:
                synonym_map[synonym.lower()] = canonical

        return synonym_map

    def _build_nsfw_patterns(self) -> List[re.Pattern]:
        """Build regex patterns for NSFW content detection"""
        patterns = []

        for filter_word in self.taxonomy.nsfw_filters:
            # Create case-insensitive pattern with word boundaries
            pattern = re.compile(r'\b' + re.escape(filter_word) + r'\b', re.IGNORECASE)
            patterns.append(pattern)

        return patterns

    def normalize_tags(self, tags: List[str], confidences: Optional[List[float]] = None) -> List[NormalizedTag]:
        """
        Normalize a list of tags according to the taxonomy

        Args:
            tags: List of raw tags from the model
            confidences: Optional confidence scores for each tag

        Returns:
            List of normalized tags with metadata
        """
        if confidences is None:
            confidences = [1.0] * len(tags)

        normalized_tags = []

        for tag, confidence in zip(tags, confidences):
            # Skip if confidence is too low
            if confidence < self.min_confidence:
                continue

            # Check for banned tags
            if tag.lower() in self._banned_tags:
                continue

            # Check for NSFW content
            if self._is_nsfw(tag):
                continue

            # Normalize the tag
            normalized = self._normalize_single_tag(tag)

            if normalized:
                normalized_tags.append(normalized)

        # Apply taxonomy-based filtering and prioritization
        normalized_tags = self._apply_taxonomy_rules(normalized_tags)

        return normalized_tags

    def _normalize_single_tag(self, tag: str) -> Optional[NormalizedTag]:
        """Normalize a single tag"""
        original_tag = tag
        tag_lower = tag.lower()

        # Check if it's a synonym
        if tag_lower in self._synonym_map:
            canonical = self._synonym_map[tag_lower]
            category = self._get_category(canonical)

            return NormalizedTag(
                original=original_tag,
                normalized=canonical,
                category=category,
                is_synonym=True,
                source_synonym=original_tag
            )

        # Direct category mapping
        category = self._get_category(tag)
        if category != TagCategory.GENERAL:
            return NormalizedTag(
                original=original_tag,
                normalized=tag,
                category=category
            )

        # Default normalization (clean up the tag)
        normalized_tag = self._clean_tag(tag)

        return NormalizedTag(
            original=original_tag,
            normalized=normalized_tag,
            category=TagCategory.GENERAL
        )

    def _get_category(self, tag: str) -> TagCategory:
        """Get the category for a tag"""
        tag_lower = tag.lower()
        return self._category_map.get(tag_lower, TagCategory.GENERAL)

    def _is_nsfw(self, tag: str) -> bool:
        """Check if a tag contains NSFW content"""
        tag_lower = tag.lower()

        for pattern in self._nsfw_patterns:
            if pattern.search(tag_lower):
                return True

        return False

    def _clean_tag(self, tag: str) -> str:
        """Clean up a tag (remove special characters, normalize spacing, etc.)"""
        # Remove extra whitespace
        tag = re.sub(r'\s+', ' ', tag.strip())

        # Remove or replace special characters
        tag = re.sub(r'[^\w\s-]', '', tag)

        # Convert to lowercase if not case sensitive
        if not self.case_sensitive:
            tag = tag.lower()

        return tag

    def _apply_taxonomy_rules(self, tags: List[NormalizedTag]) -> List[NormalizedTag]:
        """Apply taxonomy-based filtering and prioritization"""
        # Remove duplicates (keep highest confidence)
        seen_normalized = {}
        for tag in tags:
            normalized_key = tag.normalized.lower()
            if normalized_key not in seen_normalized or tag.confidence > seen_normalized[normalized_key].confidence:
                seen_normalized[normalized_key] = tag

        tags = list(seen_normalized.values())

        # Sort by priority and confidence
        priority_order = {tag: i for i, tag in enumerate(self.taxonomy.priority_tags or [])}

        def sort_key(tag: NormalizedTag) -> Tuple[int, float, str]:
            # Priority tags first, then by confidence, then alphabetically
            priority = priority_order.get(tag.normalized, len(priority_order))
            return (priority, -tag.confidence, tag.normalized.lower())

        tags.sort(key=sort_key)

        return tags

    def get_category_counts(self, tags: List[NormalizedTag]) -> Dict[TagCategory, int]:
        """Get count of tags per category"""
        counts = {}
        for tag in tags:
            counts[tag.category] = counts.get(tag.category, 0) + 1
        return counts

    def filter_by_category_budget(self, tags: List[NormalizedTag],
                                budget_config: 'BudgetConfig') -> List[NormalizedTag]:
        """Filter tags according to category budget limits"""
        filtered_tags = []

        # Group by category
        by_category = {}
        for tag in tags:
            if tag.category not in by_category:
                by_category[tag.category] = []
            by_category[tag.category].append(tag)

        # Apply budget limits
        for category, category_tags in by_category.items():
            max_tags = budget_config.max_tags_per_category.get(category, float('inf'))

            # Sort by confidence and take top N
            category_tags.sort(key=lambda t: (-t.confidence, t.normalized))
            filtered_tags.extend(category_tags[:max_tags])

        return filtered_tags

    def apply_diversity_filter(self, tags: List[NormalizedTag],
                             diversity_weight: float = 0.3) -> List[NormalizedTag]:
        """Apply diversity filtering to avoid too many similar tags"""
        if not tags or diversity_weight <= 0:
            return tags

        # Simple diversity: penalize tags that are too similar to already selected ones
        selected = []

        for tag in tags:
            # Calculate similarity penalty
            similarity_penalty = 0
            for selected_tag in selected:
                if self._tags_similar(tag.normalized, selected_tag.normalized):
                    similarity_penalty += diversity_weight

            # Adjust confidence by penalty
            adjusted_confidence = tag.confidence * (1 - similarity_penalty)

            if adjusted_confidence >= self.min_confidence:
                tag.confidence = adjusted_confidence
                selected.append(tag)

        return selected

    def _tags_similar(self, tag1: str, tag2: str) -> bool:
        """Check if two tags are similar (simple implementation)"""
        # Convert to sets of words
        words1 = set(tag1.lower().split())
        words2 = set(tag2.lower().split())

        # Check for significant overlap
        intersection = words1 & words2
        union = words1 | words2

        if not union:
            return False

        # Consider similar if >50% word overlap
        return len(intersection) / len(union) > 0.5


class TagValidator:
    """Validates tags against various criteria"""

    def __init__(self, taxonomy: TagTaxonomy):
        self.taxonomy = taxonomy

    def validate_tag_list(self, tags: List[str]) -> Dict[str, List[str]]:
        """Validate a list of tags and return issues found"""
        issues = {
            'nsfw_detected': [],
            'banned_tags': [],
            'invalid_format': [],
            'duplicates': []
        }

        seen_tags = set()

        for tag in tags:
            tag_lower = tag.lower()

            # Check for duplicates
            if tag_lower in seen_tags:
                issues['duplicates'].append(tag)
                continue
            seen_tags.add(tag_lower)

            # Check NSFW
            if self._is_nsfw(tag):
                issues['nsfw_detected'].append(tag)

            # Check banned
            if tag_lower in (self.taxonomy.banned_tags or []):
                issues['banned_tags'].append(tag)

            # Check format
            if not self._is_valid_format(tag):
                issues['invalid_format'].append(tag)

        return issues

    def _is_nsfw(self, tag: str) -> bool:
        """Check if tag contains NSFW content"""
        tag_lower = tag.lower()
        for nsfw_word in (self.taxonomy.nsfw_filters or []):
            if nsfw_word.lower() in tag_lower:
                return True
        return False

    def _is_valid_format(self, tag: str) -> bool:
        """Check if tag has valid format"""
        # Basic validation: not empty, reasonable length, no weird characters
        if not tag or not tag.strip():
            return False

        if len(tag) > 100:  # Too long
            return False

        # Allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[\w\s\-]+$', tag):
            return False

        return True