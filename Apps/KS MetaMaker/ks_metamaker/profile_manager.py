"""
Enhanced Profile System for KS MetaMaker
Supports configurable schemas for different use cases (CivitAI LoRA, HuggingFace, Custom, etc.)
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProfileType(Enum):
    """Types of profiles supported"""
    CIVITAI_LORA = "civitai_lora"
    HUGGINGFACE_DATASET = "huggingface_dataset"
    STABLE_DIFFUSION = "stable_diffusion"
    CUSTOM = "custom"
    GAME_ASSETS = "game_assets"
    RESEARCH_DATASET = "research_dataset"


class TagCategory(Enum):
    """Tag categories for organization"""
    GENERAL = "general"
    STYLE = "style"
    SUBJECT = "subject"
    COMPOSITION = "composition"
    QUALITY = "quality"
    TECHNICAL = "technical"


@dataclass
class TagTaxonomy:
    """Taxonomy configuration for tag normalization"""
    synonyms: Dict[str, List[str]] = field(default_factory=dict)
    categories: Dict[str, TagCategory] = field(default_factory=dict)
    nsfw_filters: List[str] = field(default_factory=list)
    priority_tags: List[str] = field(default_factory=list)
    banned_tags: List[str] = field(default_factory=list)


@dataclass
class BudgetConfig:
    """Budget configuration for tag allocation"""
    max_tags_per_category: Dict[TagCategory, int] = field(default_factory=dict)
    diversity_weight: float = 0.3
    quality_threshold: float = 0.7
    allocation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizationConfig:
    """Tag normalization configuration"""
    taxonomy: TagTaxonomy = field(default_factory=lambda: TagTaxonomy())
    case_sensitive: bool = False
    remove_duplicates: bool = True
    sort_by_confidence: bool = True
    min_confidence: float = 0.1


@dataclass
class ProfileSchema:
    """Complete profile schema configuration"""
    name: str
    description: str
    profile_type: ProfileType

    # Basic settings
    main_prefix: str = ""
    style_preset: str = ""
    rename_pattern: str = "{category}_{top_tags}_{YYYYMMDD}_{index}"

    # Tag configuration
    max_tags: Dict[str, int] = field(default_factory=lambda: {
        "props": 20, "backgrounds": 25, "characters": 30
    })

    # Advanced features
    normalization: NormalizationConfig = field(default_factory=lambda: NormalizationConfig())
    budget: BudgetConfig = field(default_factory=lambda: BudgetConfig())

    # Model configuration
    models: Dict[str, str] = field(default_factory=lambda: {
        "tagger": "openclip_vith14.onnx",
        "detector": "yolov11.onnx",
        "captioner": "blip2.onnx"
    })

    # Performance settings
    performance: Dict[str, Any] = field(default_factory=lambda: {
        "threads": 4,
        "batch_size": 4,
        "memory_profile": "medium"
    })

    # Export settings
    export: Dict[str, bool] = field(default_factory=lambda: {
        "paired_txt": True,
        "rename_images": True,
        "package_zip": True,
        "write_metadata": True,
        "write_context_json": True
    })

    # UI settings
    ui_features: Dict[str, bool] = field(default_factory=lambda: {
        "review_ui": True,
        "watch_mode": False,
        "collaboration": False
    })


class ProfileManager:
    """Manages loading and validation of profiles"""

    def __init__(self, profiles_dir: Optional[Path] = None):
        if profiles_dir is None:
            # Default to configs/profiles relative to this file
            self.profiles_dir = Path(__file__).parent.parent.parent / "configs" / "profiles"
        else:
            self.profiles_dir = profiles_dir

        self.profiles_dir.mkdir(exist_ok=True)
        self._loaded_profiles: Dict[str, ProfileSchema] = {}

    def load_profile(self, profile_name: str) -> ProfileSchema:
        """Load a profile by name"""
        if profile_name in self._loaded_profiles:
            return self._loaded_profiles[profile_name]

        profile_file = self.profiles_dir / f"{profile_name}.yml"

        if not profile_file.exists():
            raise FileNotFoundError(f"Profile '{profile_name}' not found at {profile_file}")

        with open(profile_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        profile = self._parse_profile_data(data)
        self._loaded_profiles[profile_name] = profile
        return profile

    def save_profile(self, profile: ProfileSchema) -> None:
        """Save a profile to disk"""
        profile_file = self.profiles_dir / f"{profile.name}.yml"

        data = self._profile_to_dict(profile)

        with open(profile_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def list_profiles(self) -> List[str]:
        """List all available profiles"""
        return [f.stem for f in self.profiles_dir.glob("*.yml")]

    def create_default_profiles(self) -> None:
        """Create default profiles for common use cases"""

        # CivitAI LoRA Profile
        civitai_profile = ProfileSchema(
            name="civitai_lora",
            description="Optimized for CivitAI LoRA training datasets",
            profile_type=ProfileType.CIVITAI_LORA,
            main_prefix="",
            style_preset="",
            max_tags={"general": 50},
            normalization=NormalizationConfig(
                taxonomy=TagTaxonomy(
                    categories={
                        "character": TagCategory.SUBJECT,
                        "style": TagCategory.STYLE,
                        "quality": TagCategory.QUALITY,
                        "artist": TagCategory.TECHNICAL
                    },
                    priority_tags=["character", "style", "quality"],
                    nsfw_filters=["nsfw", "adult", "explicit"]
                )
            ),
            budget=BudgetConfig(
                max_tags_per_category={
                    TagCategory.SUBJECT: 10,
                    TagCategory.STYLE: 15,
                    TagCategory.QUALITY: 10,
                    TagCategory.TECHNICAL: 15
                },
                diversity_weight=0.4
            )
        )

        # HuggingFace Dataset Profile
        hf_profile = ProfileSchema(
            name="huggingface_dataset",
            description="Standardized for HuggingFace dataset uploads",
            profile_type=ProfileType.HUGGINGFACE_DATASET,
            max_tags={"general": 30},
            normalization=NormalizationConfig(
                taxonomy=TagTaxonomy(
                    categories={
                        "object": TagCategory.SUBJECT,
                        "scene": TagCategory.COMPOSITION,
                        "quality": TagCategory.QUALITY
                    }
                )
            )
        )

        # Custom Profile
        custom_profile = ProfileSchema(
            name="custom",
            description="Fully customizable profile for specific needs",
            profile_type=ProfileType.CUSTOM
        )

        # Save default profiles
        for profile in [civitai_profile, hf_profile, custom_profile]:
            self.save_profile(profile)

    def _parse_profile_data(self, data: Dict[str, Any]) -> ProfileSchema:
        """Parse YAML data into ProfileSchema"""
        # Handle profile type
        profile_type_str = data.get('profile_type', 'custom')
        profile_type = ProfileType(profile_type_str)

        # Handle taxonomy
        taxonomy_data = data.get('normalization', {}).get('taxonomy', {})
        taxonomy = TagTaxonomy(
            synonyms=taxonomy_data.get('synonyms', {}),
            categories={k: TagCategory(v) for k, v in taxonomy_data.get('categories', {}).items()},
            nsfw_filters=taxonomy_data.get('nsfw_filters', []),
            priority_tags=taxonomy_data.get('priority_tags', []),
            banned_tags=taxonomy_data.get('banned_tags', [])
        )

        # Handle normalization
        normalization_data = data.get('normalization', {})
        normalization = NormalizationConfig(
            taxonomy=taxonomy,
            case_sensitive=normalization_data.get('case_sensitive', False),
            remove_duplicates=normalization_data.get('remove_duplicates', True),
            sort_by_confidence=normalization_data.get('sort_by_confidence', True),
            min_confidence=normalization_data.get('min_confidence', 0.1)
        )

        # Handle budget
        budget_data = data.get('budget', {})
        budget = BudgetConfig(
            max_tags_per_category={TagCategory(k): v for k, v in budget_data.get('max_tags_per_category', {}).items()},
            diversity_weight=budget_data.get('diversity_weight', 0.3),
            quality_threshold=budget_data.get('quality_threshold', 0.7),
            allocation_rules=budget_data.get('allocation_rules', {})
        )

        return ProfileSchema(
            name=data['name'],
            description=data.get('description', ''),
            profile_type=profile_type,
            main_prefix=data.get('main_prefix', ''),
            style_preset=data.get('style_preset', ''),
            rename_pattern=data.get('rename_pattern', '{category}_{top_tags}_{YYYYMMDD}_{index}'),
            max_tags=data.get('max_tags', {"props": 20, "backgrounds": 25, "characters": 30}),
            normalization=normalization,
            budget=budget,
            models=data.get('models', {
                "tagger": "openclip_vith14.onnx",
                "detector": "yolov11.onnx",
                "captioner": "blip2.onnx"
            }),
            performance=data.get('performance', {
                "threads": 4,
                "batch_size": 4,
                "memory_profile": "medium"
            }),
            export=data.get('export', {
                "paired_txt": True,
                "rename_images": True,
                "package_zip": True,
                "write_metadata": True,
                "write_context_json": True
            }),
            ui_features=data.get('ui_features', {
                "review_ui": True,
                "watch_mode": False,
                "collaboration": False
            })
        )

    def _profile_to_dict(self, profile: ProfileSchema) -> Dict[str, Any]:
        """Convert ProfileSchema to dictionary for YAML serialization"""
        return {
            'name': profile.name,
            'description': profile.description,
            'profile_type': profile.profile_type.value,
            'main_prefix': profile.main_prefix,
            'style_preset': profile.style_preset,
            'rename_pattern': profile.rename_pattern,
            'max_tags': profile.max_tags,
            'normalization': {
                'taxonomy': {
                    'synonyms': profile.normalization.taxonomy.synonyms,
                    'categories': {k: v.value for k, v in profile.normalization.taxonomy.categories.items()},
                    'nsfw_filters': profile.normalization.taxonomy.nsfw_filters,
                    'priority_tags': profile.normalization.taxonomy.priority_tags,
                    'banned_tags': profile.normalization.taxonomy.banned_tags
                },
                'case_sensitive': profile.normalization.case_sensitive,
                'remove_duplicates': profile.normalization.remove_duplicates,
                'sort_by_confidence': profile.normalization.sort_by_confidence,
                'min_confidence': profile.normalization.min_confidence
            },
            'budget': {
                'max_tags_per_category': {k.value: v for k, v in profile.budget.max_tags_per_category.items()},
                'diversity_weight': profile.budget.diversity_weight,
                'quality_threshold': profile.budget.quality_threshold,
                'allocation_rules': profile.budget.allocation_rules
            },
            'models': profile.models,
            'performance': profile.performance,
            'export': profile.export,
            'ui_features': profile.ui_features
        }


# Convenience function to get profile manager
def get_profile_manager() -> ProfileManager:
    """Get the global profile manager instance"""
    return ProfileManager()