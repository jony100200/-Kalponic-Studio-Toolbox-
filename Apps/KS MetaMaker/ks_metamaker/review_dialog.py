"""
Review UI for KS MetaMaker
Allows manual review and editing of generated tags
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QGroupBox, QCheckBox, QProgressBar, QMessageBox,
    QScrollArea, QWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QFont

from ..utils.config import Config


class TagItemWidget(QFrame):
    """Widget for displaying and editing a single tag"""

    def __init__(self, tag: str, confidence: float = 1.0, category: str = "general"):
        super().__init__()
        self.tag = tag
        self.confidence = confidence
        self.category = category

        self.init_ui()

    def init_ui(self):
        """Initialize the tag item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Tag label
        self.tag_label = QLabel(self.tag)
        self.tag_label.setStyleSheet("font-weight: bold;")

        # Confidence indicator
        self.confidence_label = QLabel(f"{self.confidence:.2f}")
        self.confidence_label.setStyleSheet(self._get_confidence_style())

        # Category label
        self.category_label = QLabel(f"[{self.category}]")
        self.category_label.setStyleSheet("color: #666; font-size: 10px;")

        # Remove button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setMaximumWidth(20)
        self.remove_btn.setMaximumHeight(20)
        self.remove_btn.clicked.connect(self.remove_requested)

        layout.addWidget(self.tag_label)
        layout.addWidget(self.confidence_label)
        layout.addWidget(self.category_label)
        layout.addStretch()
        layout.addWidget(self.remove_btn)

        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 3px; }")

    def _get_confidence_style(self) -> str:
        """Get color style based on confidence"""
        if self.confidence >= 0.8:
            return "color: green; font-weight: bold;"
        elif self.confidence >= 0.6:
            return "color: orange; font-weight: bold;"
        else:
            return "color: red; font-weight: bold;"

    def remove_requested(self):
        """Emit signal when remove is requested"""
        self.hide()  # Hide the widget


class ReviewDialog(QDialog):
    """Dialog for reviewing and editing generated tags"""

    # Signals
    tags_approved = pyqtSignal(list)  # list of approved tag lists
    tags_rejected = pyqtSignal(list)  # list of rejected image paths
    tags_modified = pyqtSignal(dict)  # dict of path -> modified tags

    def __init__(self, image_data: List[Dict[str, Any]], config: Config, parent=None):
        """
        Args:
            image_data: List of dicts with 'path', 'tags', 'metadata' keys
            config: Application config
        """
        super().__init__(parent)
        self.image_data = image_data
        self.config = config
        self.current_index = 0
        self.modified_tags = {}  # path -> modified tag list

        self.init_ui()
        self.load_current_image()

    def init_ui(self):
        """Initialize the review UI"""
        self.setWindowTitle("KS MetaMaker - Tag Review")
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.show_previous)
        toolbar_layout.addWidget(self.prev_btn)

        self.image_counter = QLabel("Image 1 of X")
        self.image_counter.setStyleSheet("font-weight: bold; font-size: 14px;")
        toolbar_layout.addWidget(self.image_counter)

        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.show_next)
        toolbar_layout.addWidget(self.next_btn)

        toolbar_layout.addStretch()

        # Batch actions
        self.approve_all_btn = QPushButton("✅ Approve All")
        self.approve_all_btn.clicked.connect(self.approve_all)
        toolbar_layout.addWidget(self.approve_all_btn)

        self.reject_all_btn = QPushButton("❌ Reject All")
        self.reject_all_btn.clicked.connect(self.reject_all)
        toolbar_layout.addWidget(self.reject_all_btn)

        layout.addLayout(toolbar_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Image display
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)

        self.image_label = QLabel("Loading image...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background: #f0f0f0;")
        image_layout.addWidget(self.image_label)

        # Image info
        info_group = QGroupBox("Image Information")
        info_layout = QVBoxLayout(info_group)

        self.filename_label = QLabel("Filename: ")
        self.dimensions_label = QLabel("Dimensions: ")
        self.file_size_label = QLabel("File Size: ")
        self.category_label = QLabel("Category: ")

        info_layout.addWidget(self.filename_label)
        info_layout.addWidget(self.dimensions_label)
        info_layout.addWidget(self.file_size_label)
        info_layout.addWidget(self.category_label)

        image_layout.addWidget(info_group)
        splitter.addWidget(image_panel)

        # Right panel - Tags editing
        tags_panel = QWidget()
        tags_layout = QVBoxLayout(tags_panel)

        # Current tags
        tags_group = QGroupBox("Generated Tags")
        tags_group_layout = QVBoxLayout(tags_group)

        self.tags_scroll = QScrollArea()
        self.tags_widget = QWidget()
        self.tags_layout = QVBoxLayout(self.tags_widget)
        self.tags_scroll.setWidget(self.tags_widget)
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setMinimumHeight(300)

        tags_group_layout.addWidget(self.tags_scroll)

        # Add tag input
        add_tag_layout = QHBoxLayout()
        self.new_tag_input = QTextEdit()
        self.new_tag_input.setMaximumHeight(60)
        self.new_tag_input.setPlaceholderText("Enter new tags (one per line)...")
        self.add_tag_btn = QPushButton("Add Tags")
        self.add_tag_btn.clicked.connect(self.add_new_tags)

        add_tag_layout.addWidget(self.new_tag_input)
        add_tag_layout.addWidget(self.add_tag_btn)

        tags_group_layout.addLayout(add_tag_layout)
        tags_layout.addWidget(tags_group)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.approve_btn = QPushButton("✅ Approve")
        self.approve_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; }")
        self.approve_btn.clicked.connect(self.approve_current)

        self.reject_btn = QPushButton("❌ Reject")
        self.reject_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; }")
        self.reject_btn.clicked.connect(self.reject_current)

        self.skip_btn = QPushButton("⏭️ Skip")
        self.skip_btn.clicked.connect(self.skip_current)

        actions_layout.addWidget(self.reject_btn)
        actions_layout.addWidget(self.skip_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.approve_btn)

        tags_layout.addLayout(actions_layout)

        splitter.addWidget(tags_panel)
        splitter.setSizes([500, 700])

        layout.addWidget(splitter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.image_data))
        self.progress_bar.setValue(1)
        layout.addWidget(self.progress_bar)

        # Update navigation buttons
        self.update_navigation()

    def load_current_image(self):
        """Load the current image and its tags"""
        if not self.image_data:
            return

        data = self.image_data[self.current_index]
        image_path = Path(data['path'])

        # Load and display image
        self.display_image(image_path)

        # Display image info
        self.filename_label.setText(f"Filename: {image_path.name}")
        self.dimensions_label.setText(f"Dimensions: {data.get('dimensions', 'Unknown')}")
        self.file_size_label.setText(f"File Size: {data.get('file_size', 'Unknown')}")
        self.category_label.setText(f"Category: {data.get('category', 'Unknown')}")

        # Display tags
        self.display_tags(data.get('tags', []), data.get('metadata', {}))

        # Update counter
        self.image_counter.setText(f"Image {self.current_index + 1} of {len(self.image_data)}")

    def display_image(self, image_path: Path):
        """Display the image in the label"""
        try:
            pixmap = QPixmap(str(image_path))

            # Scale to fit while maintaining aspect ratio
            label_size = self.image_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.image_label.setPixmap(scaled_pixmap)
        except Exception as e:
            self.image_label.setText(f"Failed to load image:\n{str(e)}")

    def display_tags(self, tags: List[str], metadata: Dict[str, Any]):
        """Display the tags for editing"""
        # Clear existing tags
        for i in reversed(range(self.tags_layout.count())):
            widget = self.tags_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Add tag widgets
        for tag in tags:
            # Get metadata for this tag if available
            tag_meta = metadata.get(tag, {})
            confidence = tag_meta.get('confidence', 1.0)
            category = tag_meta.get('category', 'general')

            tag_widget = TagItemWidget(tag, confidence, category)
            self.tags_layout.addWidget(tag_widget)

        # Add stretch at the end
        self.tags_layout.addStretch()

    def add_new_tags(self):
        """Add new tags from the input field"""
        new_tags_text = self.new_tag_input.toPlainText().strip()
        if not new_tags_text:
            return

        # Split by lines and clean
        new_tags = [tag.strip() for tag in new_tags_text.split('\n') if tag.strip()]

        # Add each new tag
        for tag in new_tags:
            tag_widget = TagItemWidget(tag, 1.0, "manual")  # Manual tags get full confidence
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, tag_widget)  # Insert before stretch

        # Clear input
        self.new_tag_input.clear()

    def get_current_tags(self) -> List[str]:
        """Get the current list of tags from the UI"""
        tags = []
        for i in range(self.tags_layout.count()):
            widget = self.tags_layout.itemAt(i).widget()
            if isinstance(widget, TagItemWidget) and widget.isVisible():
                tags.append(widget.tag)
        return tags

    def approve_current(self):
        """Approve the current image's tags"""
        current_path = self.image_data[self.current_index]['path']
        current_tags = self.get_current_tags()

        self.modified_tags[current_path] = current_tags

        if self.current_index < len(self.image_data) - 1:
            self.show_next()
        else:
            self.finish_review()

    def reject_current(self):
        """Reject the current image"""
        # For now, just skip to next
        if self.current_index < len(self.image_data) - 1:
            self.show_next()
        else:
            self.finish_review()

    def skip_current(self):
        """Skip the current image (keep original tags)"""
        if self.current_index < len(self.image_data) - 1:
            self.show_next()
        else:
            self.finish_review()

    def approve_all(self):
        """Approve all remaining images with their current tags"""
        for i in range(self.current_index, len(self.image_data)):
            data = self.image_data[i]
            path = data['path']
            # For approved images, use the current displayed tags
            if i == self.current_index:
                tags = self.get_current_tags()
            else:
                tags = data.get('tags', [])
            self.modified_tags[path] = tags

        self.finish_review()

    def reject_all(self):
        """Reject all remaining images"""
        # For rejected images, we'll just not include them in modified_tags
        self.finish_review()

    def show_previous(self):
        """Show the previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            self.update_navigation()

    def show_next(self):
        """Show the next image"""
        if self.current_index < len(self.image_data) - 1:
            self.current_index += 1
            self.load_current_image()
            self.update_navigation()

    def update_navigation(self):
        """Update navigation button states"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_data) - 1)
        self.progress_bar.setValue(self.current_index + 1)

    def finish_review(self):
        """Finish the review process and emit results"""
        approved_tags = []
        rejected_paths = []

        for data in self.image_data:
            path = data['path']
            if path in self.modified_tags:
                approved_tags.append({
                    'path': path,
                    'tags': self.modified_tags[path]
                })
            else:
                rejected_paths.append(path)

        self.tags_approved.emit(approved_tags)
        self.tags_rejected.emit(rejected_paths)
        self.tags_modified.emit(self.modified_tags)

        self.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.approve_current()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject_current()
        else:
            super().keyPressEvent(event)