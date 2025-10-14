"""
Core sequencer logic for managing prompt automation workflow.
Handles both text and image+text modes with proper error handling and logging.
"""

import os
import time
import random
import logging
import shutil
import re
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from ..automation.automation import WindowDetector, ClipboardManager, PasteController

class SequencerState(Enum):
    """Sequencer execution states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    WAITING_FOR_USER = "waiting_for_user"  # New state for manual intervention

@dataclass
class PromptItem:
    """Represents a single prompt item to be processed"""
    content: str
    source_file: str
    index: int
    item_type: str = "text"  # "text" or "image"

class PromptSequencer:
    """Main sequencer class handling prompt automation"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.window_detector = WindowDetector()
        self.clipboard_manager = ClipboardManager()
        self.paste_controller = PasteController()
        
        # State
        self.state = SequencerState.IDLE
        self.current_item = 0
        self.total_items = 0
        self.current_file = ""
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_progress_update: Optional[Callable] = None
        self.on_log_message: Optional[Callable] = None
        self.on_manual_intervention_needed: Optional[Callable] = None  # New callback
        
        # Manual intervention
        self.manual_intervention_pending = False
        self.manual_intervention_resolved = False
        # Cancellation requests for queue items (ids)
        # Stored on config as image_queue_cancel_requests (a set) for cross-component signaling
        if not hasattr(self.config, 'image_queue_cancel_requests'):
            try:
                self.config.image_queue_cancel_requests = set()
            except Exception:
                # If config is not dict-like, fall back to internal set
                self._local_cancel_requests = set()
        else:
            # Ensure it's a set
            try:
                self.config.image_queue_cancel_requests = set(self.config.image_queue_cancel_requests)
            except Exception:
                self.config.image_queue_cancel_requests = set()

        # Track currently processing queue item id for diagnostics
        self.current_queue_item_id = None
        
        # Setup directories
        self._setup_directories()
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = ["sent_prompts", "sent_images", "sent_prompts/failed", "sent_images/failed", "logs"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def set_callbacks(self, state_callback=None, progress_callback=None, log_callback=None, 
                      manual_intervention_callback=None):
        """Set callback functions for UI updates"""
        if state_callback:
            self.on_state_change = state_callback
        if progress_callback:
            self.on_progress_update = progress_callback
        if log_callback:
            self.on_log_message = log_callback
        if manual_intervention_callback:
            self.on_manual_intervention_needed = manual_intervention_callback
    
    def _change_state(self, new_state: SequencerState):
        """Change sequencer state and notify callbacks"""
        self.state = new_state
        if self.on_state_change:
            self.on_state_change(new_state)
    
    def _log_message(self, message: str, level: str = "info"):
        """Log message and notify UI"""
        getattr(self.logger, level)(message)
        if self.on_log_message:
            self.on_log_message(message, level)
    
    def _update_progress(self):
        """Update progress and notify callbacks"""
        if self.on_progress_update:
            self.on_progress_update(self.current_item, self.total_items, self.current_file)
    
    def _apply_jitter(self, base_delay: float, jitter_percent: int) -> float:
        """Apply random jitter to delay"""
        if jitter_percent <= 0:
            return base_delay
        
        jitter = (jitter_percent / 100.0) * base_delay
        random_factor = random.uniform(-jitter, jitter)
        return max(0.1, base_delay + random_factor)
    
    def _move_file_to_sent(self, file_path: str, is_image: bool = False, failed: bool = False):
        """Move processed file to appropriate directory"""
        try:
            base_dir = "sent_images" if is_image else "sent_prompts"
            target_dir = f"{base_dir}/failed" if failed else base_dir
            
            filename = os.path.basename(file_path)
            target_path = os.path.join(target_dir, filename)
            
            # Handle duplicate names
            counter = 1
            original_target = target_path
            while os.path.exists(target_path):
                name, ext = os.path.splitext(original_target)
                target_path = f"{name}_{counter}{ext}"
                counter += 1
            
            shutil.move(file_path, target_path)
            self._log_message(f"Moved file to: {target_path}")
            
        except Exception as e:
            self._log_message(f"Failed to move file {file_path}: {e}", "error")
    
    def _save_sent_prompt(self, prompt_text: str, prompt_title: str, source_file: str):
        """Save a successfully sent prompt to a file"""
        try:
            # Create sent directory if it doesn't exist
            sent_dir = "sent_prompts"
            os.makedirs(sent_dir, exist_ok=True)
            
            # Create filename based on prompt title and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in prompt_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            
            filename = f"sent_{timestamp}_{safe_title}.txt"
            filepath = os.path.join(sent_dir, filename)
            
            # Write the prompt to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {prompt_title}\n")
                f.write(f"Source: {os.path.basename(source_file)}\n")
                f.write(f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n")
                f.write(prompt_text)
            
            self._log_message(f"Saved sent prompt to: {filepath}")
            
        except Exception as e:
            self._log_message(f"Failed to save sent prompt: {e}", "error")
    
    def _save_sent_prompt(self, prompt_text: str, prompt_title: str, source_file: str):
        """Save a successfully sent prompt to a file"""
        try:
            # Create sent directory if it doesn't exist
            sent_dir = "sent_prompts"
            os.makedirs(sent_dir, exist_ok=True)
            
            # Create filename based on prompt title and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in prompt_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            
            filename = f"sent_{timestamp}_{safe_title}.txt"
            filepath = os.path.join(sent_dir, filename)
            
            # Write the prompt to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {prompt_title}\n")
                f.write(f"Source: {os.path.basename(source_file)}\n")
                f.write(f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n")
                f.write(prompt_text)
            
            self._log_message(f"Saved sent prompt to: {filepath}")
            
        except Exception as e:
            self._log_message(f"Failed to save sent prompt: {e}", "error")
    
    def _focus_target_window(self) -> bool:
        """Focus the target window and input box with manual intervention fallback"""
        if not self.config.target_window:
            self._log_message("No target window configured", "error")
            return False
        
        # Focus window first
        if not self.window_detector.focus_window(self.config.target_window):
            self._log_message("Failed to focus target window", "error")
            
            # Request manual intervention
            self._request_manual_intervention("Could not focus target window. Please click on the target application window and then resume.")
            return False
        
        # Then focus input box with keyboard navigation
        if not self.window_detector.focus_input_box(retries=3):
            self._log_message("Auto-focus failed - requesting manual intervention", "warning")
            
            # Request manual intervention for input box focus
            self._request_manual_intervention("Could not auto-focus input box. Please click inside the input box of the target application and then resume.")
            return False
        
        return True
    
    def _request_manual_intervention(self, message: str):
        """Request manual intervention from user"""
        self.manual_intervention_pending = True
        self.manual_intervention_resolved = False
        self._change_state(SequencerState.WAITING_FOR_USER)
        self._log_message(f"Manual intervention needed: {message}", "warning")
        
        if self.on_manual_intervention_needed:
            self.on_manual_intervention_needed(message)
        
        # Wait for user to resolve the issue
        while self.manual_intervention_pending and self.state == SequencerState.WAITING_FOR_USER:
            time.sleep(0.1)
    
    def resolve_manual_intervention(self):
        """Mark manual intervention as resolved"""
        self.manual_intervention_pending = False
        self.manual_intervention_resolved = True
        if self.state == SequencerState.WAITING_FOR_USER:
            self._change_state(SequencerState.RUNNING)
        self._log_message("Manual intervention resolved - continuing automation", "info")
    
    def start_text_mode(self, input_folder: str):
        """Start text mode sequencing"""
        if self.state != SequencerState.IDLE:
            self._log_message("Sequencer is already running", "warning")
            return
        
        try:
            self._change_state(SequencerState.RUNNING)
            self._log_message(f"Starting text mode from folder: {input_folder}")
            
            # Get text files
            text_files = [f for f in os.listdir(input_folder) 
                         if f.lower().endswith('.txt')]
            
            if not text_files:
                self._log_message("No text files found in input folder", "warning")
                self._change_state(SequencerState.IDLE)
                return
            
            # Process each file
            for file_name in text_files:
                if self.state == SequencerState.STOPPING:
                    break
                
                file_path = os.path.join(input_folder, file_name)
                self.current_file = file_name
                self._process_text_file(file_path)
            
            self._log_message("Text mode processing completed")
            self._change_state(SequencerState.IDLE)
            
        except Exception as e:
            self._log_message(f"Error in text mode: {e}", "error")
            self._change_state(SequencerState.ERROR)
    
    def _process_text_file(self, file_path: str):
        """Process a single text file with enhanced prompt parsing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content.strip()
            
            if not content:
                self._log_message(f"Empty file: {os.path.basename(file_path)}", "warning")
                return
            
            # Enhanced prompt parsing
            prompts = self._parse_prompts(content)
            
            if not prompts:
                self._log_message(f"No valid prompts found in: {os.path.basename(file_path)}", "warning")
                return
            
            self.total_items = len(prompts)
            file_failed = False
            remaining_content = original_content  # Start with full content
            
            for i, prompt_data in enumerate(prompts):
                if self.state == SequencerState.STOPPING:
                    break
                
                # Handle pause
                while self.state == SequencerState.PAUSED:
                    time.sleep(0.1)
                
                self.current_item = i + 1
                self._update_progress()
                
                # Extract prompt text and metadata
                prompt_text = prompt_data['text']
                prompt_title = prompt_data.get('title', f"Prompt {i + 1}")
                original_segment = prompt_data.get('original_segment', prompt_text)
                
                self._log_message(f"Processing: {prompt_title}")
                
                success = self._send_text_prompt(prompt_text, i + 1, prompt_title)
                
                if success:
                    # Save the sent prompt
                    self._save_sent_prompt(prompt_text, prompt_title, file_path)
                    
                    # Remove the original segment from the remaining content
                    remaining_content = remaining_content.replace(original_segment, '', 1)
                    
                    # Update the file with remaining content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(remaining_content.strip())
                    
                    self._log_message(f"Successfully sent and removed prompt: {prompt_title}")
                else:
                    file_failed = True
                    break
            
            # Handle file disposition
            remaining_content = remaining_content.strip()
            if remaining_content:
                # Move remaining content to appropriate directory
                self._move_file_to_sent(file_path, is_image=False, failed=file_failed)
            else:
                # File is empty, just move it to sent_prompts
                self._move_file_to_sent(file_path, is_image=False, failed=False)
            
        except Exception as e:
            self._log_message(f"Error processing file {file_path}: {e}", "error")
            self._move_file_to_sent(file_path, is_image=False, failed=True)
    
    def _parse_prompts(self, content: str) -> List[Dict[str, str]]:
        """Parse prompts from content with support for numbered format"""
        prompts = []
        
        # Method 1: Try numbered format (1. Title, 2. Title, etc.)
        numbered_prompts = self._parse_numbered_prompts(content)
        if numbered_prompts:
            return numbered_prompts
        
        # Method 2: Try separator-based format (---)
        if '---' in content:
            sections = content.split('---')
            for i, section in enumerate(sections):
                section = section.strip()
                if section:
                    prompts.append({
                        'text': section,
                        'title': f"Section {i + 1}",
                        'original_segment': section
                    })
            return prompts
        
        # Method 3: Try double newline separation
        sections = content.split('\n\n')
        if len(sections) > 1:
            for i, section in enumerate(sections):
                section = section.strip()
                if section:
                    prompts.append({
                        'text': section,
                        'title': f"Paragraph {i + 1}",
                        'original_segment': section
                    })
            return prompts
        
        # Method 4: Single prompt
        prompts.append({
            'text': content,
            'title': "Single Prompt",
            'original_segment': content
        })
        
        return prompts
    
    def _parse_numbered_prompts(self, content: str) -> List[Dict[str, str]]:
        """Parse numbered prompts like '1. Title' followed by 'Prompt:' content"""
        import re
        prompts = []
        
        # Pattern to match numbered sections like "1. Title" or "2. Title"
        section_pattern = r'(\d+)\.\s*([^\n]+)'
        
        # Find all numbered sections
        sections = re.split(section_pattern, content)
        
        if len(sections) < 4:  # Need at least number, title, content
            return []
        
        # Process sections in groups of 3: (content_before, number, title, content_after)
        i = 1  # Skip the first element (content before first match)
        while i < len(sections) - 1:
            try:
                number = sections[i]
                title = sections[i + 1].strip()
                
                # Get content until next numbered section or end
                content_part = ""
                original_segment = ""
                if i + 2 < len(sections):
                    content_part = sections[i + 2]
                    # Reconstruct the original segment: "1. Title" + content_part
                    original_segment = f"{number}. {title}{content_part}"
                else:
                    # Last section
                    original_segment = f"{number}. {title}"
                
                # Extract actual prompt from content
                prompt_variations = self._extract_prompt_variations(content_part)
                
                for variation_title, prompt_text in prompt_variations:
                    if prompt_text:
                        # Create descriptive title
                        full_title = f"{number}. {title}"
                        if variation_title:
                            full_title += f" ({variation_title})"
                        
                        prompts.append({
                            'text': prompt_text,
                            'title': full_title,
                            'number': int(number),
                            'original_segment': original_segment
                        })
                
                i += 3  # Move to next section
                
            except (ValueError, IndexError):
                break
        
        return prompts
    
    def _extract_prompt_variations(self, content: str) -> List[tuple]:
        """Extract multiple prompt variations from content (e.g., Closed and Open versions)"""
        variations = []
        
        # Pattern to match "Prompt (variation):" or just "Prompt:"
        prompt_pattern = r'prompt\s*(?:\(([^)]*)\))?\s*:\s*(.+?)(?=\n\s*prompt\s*(?:\([^)]*\))?\s*:|$)'
        
        matches = re.findall(prompt_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if matches:
            for variation_name, prompt_text in matches:
                # Clean up the prompt text
                clean_text = re.sub(r'\s+', ' ', prompt_text.strip().strip('"'))
                if clean_text:
                    variations.append((variation_name.strip() if variation_name else None, clean_text))
        else:
            # Fallback: try the original extraction method
            prompt_text = self._extract_prompt_text(content)
            if prompt_text:
                variations.append((None, prompt_text))
        
        return variations if variations else [(None, "")]
    
    def _extract_prompt_text(self, content: str) -> str:
        """Extract the actual prompt text from a content section"""
        lines = content.split('\n')
        prompt_lines = []
        found_prompt = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for "Prompt:" indicator (including variations like "Prompt (Closed):")
            if re.search(r'prompt\s*(\([^)]*\))?\s*:', line.lower()):
                found_prompt = True
                # Get text after "Prompt:" or "Prompt (variation):"
                match = re.search(r'prompt\s*(?:\([^)]*\))?\s*:\s*(.+)', line.lower())
                if match:
                    prompt_part = line[match.start(1):].strip().strip('"')
                    if prompt_part:
                        prompt_lines.append(prompt_part)
                continue
            
            # If we found a prompt indicator, collect subsequent lines
            if found_prompt:
                # Stop if we hit another numbered section
                if re.match(r'\d+\.\s', line):
                    break
                # Stop if we hit another prompt variation
                if re.search(r'prompt\s*(\([^)]*\))?\s*:', line.lower()):
                    # This is a new prompt variation - for now, take the first one
                    break
                # Clean up quotes and add to prompt
                clean_line = line.strip('"').strip()
                if clean_line:
                    prompt_lines.append(clean_line)
        
        # If no "Prompt:" found, use the whole content
        if not prompt_lines:
            # Clean the content and remove extra whitespace
            cleaned = re.sub(r'\s+', ' ', content.strip())
            return cleaned
        
        return ' '.join(prompt_lines)
    
    def _send_text_prompt(self, prompt: str, prompt_index: int, prompt_title: str = "") -> bool:
        """Send a single text prompt"""
        try:
            title_info = f" ({prompt_title})" if prompt_title else ""
            self._log_message(f"Sending prompt {prompt_index}{title_info}: {prompt[:50]}...")
            
            # Focus window and input box
            if not self._focus_target_window():
                self._log_message("Failed to focus target window", "error")
                return False
            
            # Paste prompt with improved focus handling
            success = self.paste_controller.paste_text(
                prompt,
                auto_enter=self.config.text_auto_enter,
                grace_delay=self.config.text_paste_enter_grace,
                target_window=self.config.target_window
            )
            
            if not success:
                self._log_message(f"Failed to paste prompt {prompt_index}", "error")
                return False
            
            # Wait for generation
            wait_time = self._apply_jitter(
                self.config.text_generation_wait,
                self.config.text_jitter_percent
            )
            
            self._log_message(f"Waiting {wait_time:.1f}s for generation...")
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            self._log_message(f"Error sending prompt {prompt_index}: {e}", "error")
            return False
    
    def start_image_mode(self, image_folder: str, global_prompt_file: str):
        """Start image+text mode sequencing"""
        if self.state != SequencerState.IDLE:
            self._log_message("Sequencer is already running", "warning")
            return
        
        try:
            self._change_state(SequencerState.RUNNING)
            self._log_message(f"Starting image mode from folder: {image_folder}")
            
            # Load global prompt
            global_prompt = ""
            if global_prompt_file and os.path.exists(global_prompt_file):
                with open(global_prompt_file, 'r', encoding='utf-8') as f:
                    global_prompt = f.read().strip()
            
            # Get image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
            image_files = [f for f in os.listdir(image_folder) 
                          if Path(f).suffix.lower() in image_extensions]
            
            if not image_files:
                self._log_message("No image files found in input folder", "warning")
                self._change_state(SequencerState.IDLE)
                return
            
            self.total_items = len(image_files)
            
            # Process each image
            for i, image_file in enumerate(image_files):
                if self.state == SequencerState.STOPPING:
                    break
                
                # Handle pause
                while self.state == SequencerState.PAUSED:
                    time.sleep(0.1)
                
                self.current_item = i + 1
                self.current_file = image_file
                self._update_progress()
                
                image_path = os.path.join(image_folder, image_file)
                success = self._send_image_prompt(image_path, global_prompt, i + 1)
                
                if success:
                    self._move_file_to_sent(image_path, is_image=True, failed=False)
                else:
                    self._move_file_to_sent(image_path, is_image=True, failed=True)
            
            self._log_message("Image mode processing completed")
            self._change_state(SequencerState.IDLE)
            
        except Exception as e:
            self._log_message(f"Error in image mode: {e}", "error")
            self._change_state(SequencerState.ERROR)
    
    def start_image_queue_mode(self, queue_items):
        """Start image+text mode with queue processing.

        Accepts either a Python list (legacy) or a queue.Queue for dynamic enqueueing.
        If a callback `self.queue_item_done_callback` is set, it will be called with the
        finished folder name after each queue item completes so the GUI can remove it.
        """
        if self.state != SequencerState.IDLE:
            self._log_message("Sequencer is already running", "warning")
            return

        # Normalize input: allow list or queue.Queue
        import queue as _pyqueue
        q: _pyqueue.Queue
        using_queue = False
        if isinstance(queue_items, _pyqueue.Queue):
            q = queue_items
            using_queue = True
            self._log_message("Starting image queue mode (dynamic queue)")
        else:
            # Convert list to queue for simpler processing
            q = _pyqueue.Queue()
            for item in (queue_items or []):
                q.put(item)
            if q.empty():
                self._log_message("No items in queue", "warning")
                return
            self._log_message(f"Starting image queue mode with {q.qsize()} folders")

        try:
            # Calculate total items across all folders (best-effort; for dynamic queue we
            # compute this per-item as we go).
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

            # For legacy list-based queue we already loaded items into q; compute total
            try:
                if not using_queue:
                    total_images = 0
                    items_for_count = list(q.queue)
                    for item in items_for_count:
                        folder = item.get('image_folder', '')
                        if os.path.exists(folder):
                            folder_images = [f for f in os.listdir(folder)
                                             if Path(f).suffix.lower() in image_extensions]
                            total_images += len(folder_images)
                    self.total_items = total_images
                else:
                    # Unknown total for dynamic queue; leave as 0 and update as we process
                    self.total_items = 0
            except Exception:
                # If anything goes wrong, continue with unknown total
                self.total_items = 0

            processed_images = 0

            # Process items from the queue until stopped. This supports new items being
            # added to the queue when a queue.Queue is passed by the GUI.
            queue_idx = 0
            while True:
                if self.state == SequencerState.STOPPING:
                    break

                try:
                    queue_item = q.get(timeout=0.5)
                except _pyqueue.Empty:
                    # If the queue is empty and we're running in list-mode, break out.
                    if not using_queue and q.empty():
                        break
                    # Otherwise continue waiting for items (dynamic queue) or retry
                    continue

                queue_idx += 1

                item_id = queue_item.get('id')
                folder = queue_item.get('image_folder', '')
                prompt_file = queue_item.get('prompt_file', '')
                folder_name = queue_item.get('name', f"Folder {queue_idx}")

                # Log dequeue event
                self._log_message(f"Dequeued queue item: {folder_name} id={item_id}")

                if not os.path.exists(folder):
                    self._log_message(f"Folder not found: {folder}", "warning")
                    continue

                try:
                    self._log_message(f"Processing queue item {queue_idx}: {folder_name}")

                    # Load prompt for this folder
                    folder_prompt = ""
                    if prompt_file and os.path.exists(prompt_file):
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            folder_prompt = f.read().strip()

                    # Get images in this folder
                    folder_images = [f for f in os.listdir(folder)
                                   if Path(f).suffix.lower() in image_extensions]

                    if not folder_images:
                        self._log_message(f"No images found in: {folder_name}", "warning")
                        continue

                    # Process each image in this folder
                    for img_idx, image_file in enumerate(folder_images):
                        if self.state == SequencerState.STOPPING:
                            break

                        # Handle pause
                        while self.state == SequencerState.PAUSED:
                            time.sleep(0.1)

                        processed_images += 1
                        self.current_item = processed_images
                        self.current_file = f"{folder_name}/{image_file}"
                        self._update_progress()

                        # Cooperative cancellation check: if the GUI requested cancel for this item id,
                        # stop processing additional images in this folder.
                        cancel_set = getattr(self.config, 'image_queue_cancel_requests', None)
                        if cancel_set is None:
                            cancel_set = getattr(self, '_local_cancel_requests', set())

                        if item_id in cancel_set:
                            self._log_message(f"Cancellation requested for item id={item_id}; stopping folder processing", "warning")
                            # Remove cancel request now that we acknowledged it
                            try:
                                cancel_set.discard(item_id)
                            except Exception:
                                pass
                            break

                        image_path = os.path.join(folder, image_file)
                        success = self._send_image_prompt(image_path, folder_prompt, processed_images)

                        if success:
                            self._move_file_to_sent(image_path, is_image=True, failed=False)
                        else:
                            self._move_file_to_sent(image_path, is_image=True, failed=True)

                    # After finishing this folder, if GUI registered a callback notify it so
                    # the GUI can remove the completed folder from its list.
                    try:
                        # Log completion
                        self._log_message(f"Completed queue item: {folder_name} id={item_id}")
                        if hasattr(self, 'queue_item_done_callback') and callable(self.queue_item_done_callback):
                            # Provide item id so GUI can remove the exact item
                            self.queue_item_done_callback(item_id)
                    except Exception:
                        pass
                except Exception as e:
                    # If processing this folder fails, log and continue with next one
                    self._log_message(f"Error processing folder {folder_name}: {e}", "error")
                    continue

            self._log_message("Image queue mode processing completed")
            self._change_state(SequencerState.IDLE)
        except Exception as e:
            self._log_message(f"Error in image queue mode: {e}", "error")
            self._change_state(SequencerState.ERROR)
    
    def _send_image_prompt(self, image_path: str, global_prompt: str, image_index: int) -> bool:
        """Send image + text prompt"""
        try:
            self._log_message(f"Sending image {image_index}: {os.path.basename(image_path)}")
            
            # Focus window and input box
            if not self._focus_target_window():
                self._log_message("Failed to focus target window", "error")
                return False
            
            # Paste image with improved focus handling
            success = self.paste_controller.paste_image(
                image_path,
                target_window=self.config.target_window
            )
            if not success:
                self._log_message(f"Failed to paste image {image_index}", "error")
                return False
            
            # Intra delay
            time.sleep(self.config.image_intra_delay / 1000.0)
            
            # Paste text if configured
            if self.config.image_repeat_prompt and global_prompt:
                success = self.paste_controller.paste_text(
                    global_prompt,
                    auto_enter=self.config.image_auto_enter,
                    grace_delay=self.config.image_paste_enter_grace,
                    target_window=self.config.target_window
                )
                
                if not success:
                    self._log_message(f"Failed to paste text for image {image_index}", "error")
                    return False
            
            # Wait for generation
            wait_time = self._apply_jitter(
                self.config.image_generation_wait,
                self.config.image_jitter_percent
            )
            
            self._log_message(f"Waiting {wait_time:.1f}s for generation...")
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            self._log_message(f"Error sending image {image_index}: {e}", "error")
            return False
    
    def pause(self):
        """Pause execution"""
        if self.state == SequencerState.RUNNING:
            self._change_state(SequencerState.PAUSED)
            self._log_message("Sequencer paused")
    
    def resume(self):
        """Resume execution"""
        if self.state == SequencerState.PAUSED:
            self._change_state(SequencerState.RUNNING)
            self._log_message("Sequencer resumed")
    
    def stop(self):
        """Stop execution"""
        if self.state in [SequencerState.RUNNING, SequencerState.PAUSED]:
            self._change_state(SequencerState.STOPPING)
            self._log_message("Stopping sequencer...")
    
    def reset(self):
        """Reset sequencer to idle state"""
        self._change_state(SequencerState.IDLE)
        self.current_item = 0
        self.total_items = 0
        self.current_file = ""
