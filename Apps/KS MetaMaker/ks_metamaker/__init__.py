"""
KS MetaMaker - AI-assisted local utility for tagging, renaming, and organizing visual assets
"""

__version__ = "0.1.0"
__author__ = "Kalponic Studio"

from .ingest import ImageIngester
from .tagger import ImageTagger
from .rename import FileRenamer
from .organize import FileOrganizer
from .export import DatasetExporter
from .hardware_detector import HardwareDetector
from .model_recommender import ModelRecommender
from .model_downloader import ModelDownloader
from .hardware_setup_dialog import HardwareSetupDialog

__all__ = [
    "ImageIngester",
    "ImageTagger",
    "FileRenamer",
    "FileOrganizer",
    "DatasetExporter",
    "HardwareDetector",
    "ModelRecommender",
    "ModelDownloader",
    "HardwareSetupDialog"
]