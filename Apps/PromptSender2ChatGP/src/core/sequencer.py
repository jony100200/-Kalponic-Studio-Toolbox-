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
import json
import csv
import hashlib
import copy
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

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

    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        if hasattr(self.config, 'sanitize'):
            self.config.sanitize()
        
        # Components
        self.window_detector = WindowDetector()
        self.clipboard_manager = ClipboardManager()
        self.paste_controller = PasteController()
        self._apply_runtime_settings()
        
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

        # Run summary
        self.run_summary: Dict[str, Any] = {}
        self.run_results: List[Dict[str, Any]] = []
        self.last_run_summary_file = ""

        # Duplicate tracking
        self.processed_history_file = os.path.join("logs", "processed_history.json")
        self.processed_history = {"text": set(), "image": set()}

        # Cancellation requests for queue items (ids)
        # Stored on config as image_queue_cancel_requests (a set) for cross-component signaling
        self._ensure_set_attr('image_queue_cancel_requests')
        self._ensure_set_attr('image_queue_skip_requests')

        # Track currently processing queue item id for diagnostics
        self.current_queue_item_id = None
        
        # Setup directories
        self._setup_directories()
        self._load_processed_history()
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = [
            "sent_prompts",
            "sent_images",
            "sent_prompts/failed",
            "sent_images/failed",
            "logs",
            getattr(self.config, 'error_screenshot_dir', 'logs/error_screenshots')
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        snapshot_file = getattr(self.config, 'queue_snapshot_file', 'logs/queue_snapshot.json')
        snapshot_dir = os.path.dirname(snapshot_file)
        if snapshot_dir:
            os.makedirs(snapshot_dir, exist_ok=True)

    def _apply_runtime_settings(self):
        """Apply retry/timing runtime settings to automation controller."""
        try:
            self.paste_controller.configure_retries(
                getattr(self.config, 'paste_max_retries', 3),
                getattr(self.config, 'paste_retry_delay', 0.5),
                getattr(self.config, 'focus_retries', 2),
            )
        except Exception:
            pass

    def _ensure_set_attr(self, attr_name: str):
        """Ensure a config attribute exists and is a set."""
        if not hasattr(self.config, attr_name):
            setattr(self.config, attr_name, set())
            return
        try:
            setattr(self.config, attr_name, set(getattr(self.config, attr_name)))
        except Exception:
            setattr(self.config, attr_name, set())
    
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

    def _json_write_atomic(self, file_path: str, payload: Dict[str, Any]):
        """Write JSON atomically to avoid partial writes."""
        temp_file = f"{file_path}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, file_path)

    def _load_processed_history(self):
        """Load persisted duplicate-tracking history."""
        if not os.path.exists(self.processed_history_file):
            return
        try:
            with open(self.processed_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.processed_history["text"] = set(data.get("text", []))
            self.processed_history["image"] = set(data.get("image", []))
        except Exception as e:
            self._log_message(f"Could not load duplicate history: {e}", "warning")

    def _save_processed_history(self):
        """Persist duplicate-tracking history."""
        payload = {
            "text": sorted(self.processed_history.get("text", set())),
            "image": sorted(self.processed_history.get("image", set())),
            "updated_at": datetime.now().isoformat(),
        }
        try:
            self._json_write_atomic(self.processed_history_file, payload)
        except Exception as e:
            self._log_message(f"Could not save duplicate history: {e}", "warning")

    def _hash_text(self, text: str) -> str:
        """Hash normalized text content."""
        normalized = re.sub(r"\s+", " ", (text or "").strip())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _hash_file(self, file_path: str) -> str:
        """Hash file content."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _is_duplicate_text(self, text: str) -> bool:
        return self._hash_text(text) in self.processed_history["text"]

    def _is_duplicate_image(self, image_path: str) -> bool:
        return self._hash_file(image_path) in self.processed_history["image"]

    def _mark_text_processed(self, text: str):
        self.processed_history["text"].add(self._hash_text(text))

    def _mark_image_processed(self, image_path: str):
        self.processed_history["image"].add(self._hash_file(image_path))

    def _capture_error_screenshot(self, context: str = "error") -> Optional[str]:
        """Capture a screenshot for diagnostics when an action fails."""
        if not getattr(self.config, 'enable_error_screenshots', True):
            return None
        try:
            import pyautogui
            screenshot_dir = getattr(self.config, 'error_screenshot_dir', 'logs/error_screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{context}.png"
            target = os.path.join(screenshot_dir, filename)
            pyautogui.screenshot().save(target)
            self._log_message(f"Captured error screenshot: {target}", "warning")
            return target
        except Exception as e:
            self._log_message(f"Failed to capture screenshot: {e}", "warning")
            return None

    def _start_run_summary(self, mode: str, total_items: int = 0):
        """Initialize run summary tracking."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_results = []
        self.run_summary = {
            "run_id": run_id,
            "mode": mode,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": 0.0,
            "outcome": "running",
            "dry_run": bool(getattr(self.config, 'dry_run', False)),
            "total_items": int(total_items),
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "skipped_duplicates": 0,
            "error_messages": [],
            "summary_file": None,
            "summary_csv": os.path.join("logs", "run_summary_history.csv"),
        }

    def _record_run_result(self, status: str, source: str, details: str = ""):
        """Record an item-level result in the run summary."""
        if not self.run_summary:
            return

        self.run_results.append({
            "time": datetime.now().isoformat(),
            "status": status,
            "source": source,
            "details": details,
        })
        self.run_summary["processed"] += 1

        if status in {"success", "dry_run_success"}:
            self.run_summary["success"] += 1
        elif status == "failed":
            self.run_summary["failed"] += 1
            if details:
                self.run_summary["error_messages"].append(details)
        elif status == "skipped_duplicate":
            self.run_summary["skipped"] += 1
            self.run_summary["skipped_duplicates"] += 1
        elif status == "skipped":
            self.run_summary["skipped"] += 1

    def _finalize_run_summary(self, outcome: str):
        """Finalize and persist run summary as JSON + CSV."""
        if not self.run_summary:
            return

        self.run_summary["end_time"] = datetime.now().isoformat()
        start_time = datetime.fromisoformat(self.run_summary["start_time"])
        self.run_summary["duration_seconds"] = round((datetime.now() - start_time).total_seconds(), 3)
        self.run_summary["outcome"] = outcome

        payload = copy.deepcopy(self.run_summary)
        payload["results"] = self.run_results
        json_path = os.path.join("logs", f"run_summary_{self.run_summary['run_id']}.json")

        try:
            self._json_write_atomic(json_path, payload)
            self.last_run_summary_file = json_path
            self.run_summary["summary_file"] = json_path
            self._log_message(f"Run summary saved: {json_path}")
        except Exception as e:
            self._log_message(f"Failed to save run summary JSON: {e}", "warning")

        csv_path = self.run_summary["summary_csv"]
        csv_exists = os.path.exists(csv_path)
        try:
            with open(csv_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                if not csv_exists:
                    writer.writerow([
                        "run_id", "mode", "start_time", "end_time", "duration_seconds",
                        "outcome", "dry_run", "total_items", "processed", "success",
                        "failed", "skipped", "skipped_duplicates"
                    ])
                writer.writerow([
                    self.run_summary["run_id"],
                    self.run_summary["mode"],
                    self.run_summary["start_time"],
                    self.run_summary["end_time"],
                    self.run_summary["duration_seconds"],
                    self.run_summary["outcome"],
                    self.run_summary["dry_run"],
                    self.run_summary["total_items"],
                    self.run_summary["processed"],
                    self.run_summary["success"],
                    self.run_summary["failed"],
                    self.run_summary["skipped"],
                    self.run_summary["skipped_duplicates"],
                ])
        except Exception as e:
            self._log_message(f"Failed to save run summary CSV: {e}", "warning")

        self._save_processed_history()

    def _wait_if_paused(self) -> bool:
        """Sleep while paused. Returns False if stopping is requested."""
        while self.state == SequencerState.PAUSED:
            time.sleep(0.1)
        return self.state != SequencerState.STOPPING

    def _build_prompt_context(
        self,
        mode: str,
        source_file: str = "",
        index: int = 0,
        title: str = "",
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Build variable map for prompt templates."""
        now = datetime.now()
        source_path = Path(source_file) if source_file else None
        context = {
            "mode": mode,
            "index": str(index),
            "title": title or "",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "filename": source_path.name if source_path else "",
            "file_stem": source_path.stem if source_path else "",
            "file_ext": source_path.suffix if source_path else "",
            "folder": str(source_path.parent) if source_path else "",
        }
        if extra:
            for key, value in extra.items():
                context[str(key).strip().lower()] = "" if value is None else str(value)
        return context

    def _apply_prompt_variables(self, text: str, context: Dict[str, str]) -> str:
        """Resolve {{variables}} in prompt text."""
        if not getattr(self.config, 'prompt_variables_enabled', True):
            return text

        def _replace(match: re.Match) -> str:
            key = match.group(1).strip().lower()
            return context.get(key, match.group(0))

        return self.VARIABLE_PATTERN.sub(_replace, text or "")

    def _queue_to_list(self, queue_obj) -> List[Dict[str, Any]]:
        """Safely snapshot a queue.Queue into a list."""
        try:
            if hasattr(queue_obj, 'mutex'):
                with queue_obj.mutex:
                    return [copy.deepcopy(item) for item in list(queue_obj.queue)]
            return [copy.deepcopy(item) for item in list(queue_obj.queue)]
        except Exception:
            return []

    def _save_queue_snapshot(self, status: str, queue_obj=None, processed_images: int = 0):
        """Persist queue progress for crash-safe resumption."""
        if not getattr(self.config, 'queue_snapshot_enabled', True):
            return
        snapshot_file = getattr(self.config, 'queue_snapshot_file', 'logs/queue_snapshot.json')
        payload = {
            "saved_at": datetime.now().isoformat(),
            "status": status,
            "processed_images": processed_images,
            "current_queue_item_id": self.current_queue_item_id,
            "pending_queue_items": self._queue_to_list(queue_obj) if queue_obj is not None else [],
            "config_queue_items": copy.deepcopy(getattr(self.config, 'image_queue_items', [])),
        }
        try:
            self._json_write_atomic(snapshot_file, payload)
        except Exception as e:
            self._log_message(f"Could not save queue snapshot: {e}", "warning")

    def load_queue_snapshot(self) -> Optional[Dict[str, Any]]:
        """Load queue snapshot from disk."""
        snapshot_file = getattr(self.config, 'queue_snapshot_file', 'logs/queue_snapshot.json')
        if not os.path.exists(snapshot_file):
            return None
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self._log_message(f"Could not read queue snapshot: {e}", "warning")
            return None

    def build_queue_from_snapshot(self, snapshot: Dict[str, Any]):
        """Build queue.Queue object from snapshot payload."""
        import queue as _pyqueue
        q = _pyqueue.Queue()
        for item in (snapshot.get("pending_queue_items") or snapshot.get("config_queue_items") or []):
            q.put(item)
        return q

    def resume_image_queue_from_snapshot(self) -> bool:
        """Resume queue mode from saved snapshot if possible."""
        snapshot = self.load_queue_snapshot()
        if not snapshot:
            self._log_message("No queue snapshot found", "warning")
            return False
        pending_items = snapshot.get("pending_queue_items") or snapshot.get("config_queue_items") or []
        if not pending_items:
            self._log_message("Queue snapshot has no pending items", "warning")
            return False
        q = self.build_queue_from_snapshot(snapshot)
        self.start_image_queue_mode(q)
        return True

    def run_preflight(
        self,
        mode: str,
        input_folder: str = "",
        global_prompt_file: str = "",
        queue_items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Run preflight checks and return diagnostics."""
        result = {
            "mode": mode,
            "ok": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "estimated_items": 0,
            "estimated_duration_sec": 0.0,
        }

        target_window = (getattr(self.config, 'target_window', '') or '').strip()
        dry_run = bool(getattr(self.config, 'dry_run', False))

        if not target_window and not dry_run:
            result["errors"].append("Target window is not configured.")
        elif target_window:
            try:
                matching = self.window_detector.find_windows(target_window)
                if matching:
                    result["info"].append(f"Detected {len(matching)} matching window(s).")
                elif not dry_run:
                    result["warnings"].append(f"No active window currently matches '{target_window}'.")
            except Exception as e:
                result["warnings"].append(f"Could not enumerate windows: {e}")

        if mode == "text":
            if not input_folder or not os.path.isdir(input_folder):
                result["errors"].append("Text input folder does not exist.")
            else:
                text_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.txt')]
                if not text_files:
                    result["warnings"].append("No .txt files found in selected text folder.")
                prompt_count = 0
                for name in text_files:
                    path = os.path.join(input_folder, name)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            prompt_count += len(self._parse_prompts(f.read()))
                    except Exception:
                        result["warnings"].append(f"Could not parse {name} during preflight.")
                result["estimated_items"] = prompt_count
                per_item = (
                    float(getattr(self.config, 'text_generation_wait', 45))
                    + float(getattr(self.config, 'text_paste_enter_grace', 400)) / 1000.0
                )
                result["estimated_duration_sec"] = round(
                    float(getattr(self.config, 'initial_delay', 0)) + prompt_count * per_item, 2
                )
        elif mode == "image":
            if not input_folder or not os.path.isdir(input_folder):
                result["errors"].append("Image input folder does not exist.")
            else:
                image_files = [f for f in os.listdir(input_folder) if Path(f).suffix.lower() in self.IMAGE_EXTENSIONS]
                if not image_files:
                    result["warnings"].append("No image files found in selected folder.")
                result["estimated_items"] = len(image_files)
                per_item = (
                    float(getattr(self.config, 'image_generation_wait', 60))
                    + float(getattr(self.config, 'image_intra_delay', 3000)) / 1000.0
                )
                if getattr(self.config, 'image_repeat_prompt', True):
                    per_item += float(getattr(self.config, 'image_paste_enter_grace', 400)) / 1000.0
                result["estimated_duration_sec"] = round(
                    float(getattr(self.config, 'initial_delay', 0)) + len(image_files) * per_item, 2
                )
            if global_prompt_file and not os.path.exists(global_prompt_file):
                result["warnings"].append("Global prompt file is set but missing.")
        elif mode == "queue":
            items = queue_items or []
            if hasattr(items, 'queue'):
                items = self._queue_to_list(items)
            if not items:
                result["warnings"].append("Queue has no items.")
            total_images = 0
            for item in items:
                folder = item.get('image_folder', '')
                if not folder or not os.path.isdir(folder):
                    result["warnings"].append(f"Queue folder missing: {folder}")
                    continue
                total_images += len([f for f in os.listdir(folder) if Path(f).suffix.lower() in self.IMAGE_EXTENSIONS])
            result["estimated_items"] = total_images
            per_item = (
                float(getattr(self.config, 'image_generation_wait', 60))
                + float(getattr(self.config, 'image_intra_delay', 3000)) / 1000.0
            )
            result["estimated_duration_sec"] = round(
                float(getattr(self.config, 'initial_delay', 0)) + total_images * per_item, 2
            )
        else:
            result["errors"].append(f"Unknown mode: {mode}")

        result["ok"] = len(result["errors"]) == 0
        return result
    
    def _move_file_to_sent(self, file_path: str, is_image: bool = False, failed: bool = False):
        """Move processed file to appropriate directory"""
        if getattr(self.config, 'dry_run', False):
            self._log_message(f"[DRY RUN] Would move file: {file_path}")
            return

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
        if getattr(self.config, 'dry_run', False):
            self._log_message(
                f"[DRY RUN] Would save sent prompt '{prompt_title}' from {os.path.basename(source_file)}"
            )
            return

        try:
            # Create sent directory if it doesn't exist
            sent_dir = "sent_prompts"
            os.makedirs(sent_dir, exist_ok=True)
            
            # Create filename based on prompt title and timestamp
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
        if getattr(self.config, 'dry_run', False):
            return True

        if not self.config.target_window:
            self._log_message("No target window configured", "error")
            return False
        
        # Focus window first
        if not self.window_detector.focus_window(self.config.target_window):
            self._log_message("Failed to focus target window", "error")
            self._capture_error_screenshot("focus_window_failed")
            
            # Request manual intervention
            self._request_manual_intervention("Could not focus target window. Please click on the target application window and then resume.")
            return False
        
        # Then focus input box with keyboard navigation
        focus_retries = int(getattr(self.config, 'focus_retries', 3))
        if not self.window_detector.focus_input_box(retries=focus_retries):
            self._log_message("Auto-focus failed - requesting manual intervention", "warning")
            self._capture_error_screenshot("focus_input_failed")
            
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

        self._apply_runtime_settings()
        outcome = "completed"

        try:
            self._change_state(SequencerState.RUNNING)
            self._log_message(f"Starting text mode from folder: {input_folder}")

            # Get text files
            text_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.txt')]

            # Pre-calculate total prompt count for better progress/summaries
            prompt_count = 0
            for file_name in text_files:
                file_path = os.path.join(input_folder, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_count += len(self._parse_prompts(f.read()))
                except Exception:
                    pass
            self.current_item = 0
            self.total_items = prompt_count
            self._start_run_summary("text", self.total_items)

            if not text_files:
                self._log_message("No text files found in input folder", "warning")
                return
            
            # Process each file
            for file_name in text_files:
                if self.state == SequencerState.STOPPING:
                    outcome = "stopped"
                    break
                
                file_path = os.path.join(input_folder, file_name)
                self.current_file = file_name
                self._process_text_file(file_path)
            
            self._log_message("Text mode processing completed")
            
        except Exception as e:
            outcome = "error"
            self._log_message(f"Error in text mode: {e}", "error")
            self._capture_error_screenshot("text_mode_error")
            self._change_state(SequencerState.ERROR)
        finally:
            if self.state == SequencerState.STOPPING:
                outcome = "stopped"
            self._finalize_run_summary(outcome)
            if self.state != SequencerState.ERROR:
                self._change_state(SequencerState.IDLE)
    
    def _process_text_file(self, file_path: str):
        """Process a single text file with enhanced prompt parsing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content.strip()
            
            if not content:
                self._log_message(f"Empty file: {os.path.basename(file_path)}", "warning")
                self._record_run_result("skipped", file_path, "empty_file")
                return
            
            # Enhanced prompt parsing
            prompts = self._parse_prompts(content)
            
            if not prompts:
                self._log_message(f"No valid prompts found in: {os.path.basename(file_path)}", "warning")
                self._record_run_result("skipped", file_path, "no_valid_prompts")
                return

            file_failed = False
            remaining_content = original_content  # Start with full content
            
            for i, prompt_data in enumerate(prompts):
                if self.state == SequencerState.STOPPING:
                    break
                
                # Handle pause
                if not self._wait_if_paused():
                    break
                
                self.current_item += 1
                self._update_progress()
                
                # Extract prompt text and metadata
                prompt_text = prompt_data['text']
                prompt_title = prompt_data.get('title', f"Prompt {i + 1}")
                original_segment = prompt_data.get('original_segment', prompt_text)

                context = self._build_prompt_context(
                    mode="text",
                    source_file=file_path,
                    index=self.current_item,
                    title=prompt_title
                )
                prompt_text = self._apply_prompt_variables(prompt_text, context)
                
                self._log_message(f"Processing: {prompt_title}")

                if getattr(self.config, 'skip_duplicates', False) and self._is_duplicate_text(prompt_text):
                    self._log_message(f"Skipped duplicate prompt: {prompt_title}", "warning")
                    self._record_run_result("skipped_duplicate", file_path, prompt_title)
                    if not getattr(self.config, 'dry_run', False):
                        remaining_content = remaining_content.replace(original_segment, '', 1)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(remaining_content.strip())
                    continue
                
                success = self._send_text_prompt(prompt_text, self.current_item, prompt_title)
                
                if success:
                    if getattr(self.config, 'dry_run', False):
                        self._record_run_result("dry_run_success", file_path, prompt_title)
                    else:
                        self._record_run_result("success", file_path, prompt_title)
                        self._save_sent_prompt(prompt_text, prompt_title, file_path)
                        self._mark_text_processed(prompt_text)

                        # Remove the original segment from the remaining content
                        remaining_content = remaining_content.replace(original_segment, '', 1)
                        
                        # Update the file with remaining content
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(remaining_content.strip())
                        
                        self._log_message(f"Successfully sent and removed prompt: {prompt_title}")
                else:
                    self._record_run_result("failed", file_path, prompt_title)
                    file_failed = True
                    break
            
            if getattr(self.config, 'dry_run', False):
                self._log_message(f"[DRY RUN] No file changes committed for: {os.path.basename(file_path)}")
                return

            # Handle file disposition
            remaining_content = remaining_content.strip()
            if remaining_content:
                # Move remaining content to appropriate directory
                self._move_file_to_sent(file_path, is_image=False, failed=file_failed)
            else:
                # File is empty, just move it to sent_prompts
                self._move_file_to_sent(file_path, is_image=False, failed=False)
            
        except Exception as e:
            self._record_run_result("failed", file_path, f"text_file_exception: {e}")
            self._log_message(f"Error processing file {file_path}: {e}", "error")
            self._capture_error_screenshot("text_file_error")
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

            if getattr(self.config, 'dry_run', False):
                self._log_message(f"[DRY RUN] Would paste text prompt {prompt_index}")
                return True
            
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
                self._capture_error_screenshot("paste_text_failed")
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
            self._capture_error_screenshot("send_text_exception")
            return False
    
    def start_image_mode(self, image_folder: str, global_prompt_file: str):
        """Start image+text mode sequencing"""
        if self.state != SequencerState.IDLE:
            self._log_message("Sequencer is already running", "warning")
            return

        self._apply_runtime_settings()
        outcome = "completed"

        try:
            self._change_state(SequencerState.RUNNING)
            self._log_message(f"Starting image mode from folder: {image_folder}")
            
            # Load global prompt
            global_prompt = ""
            if global_prompt_file and os.path.exists(global_prompt_file):
                with open(global_prompt_file, 'r', encoding='utf-8') as f:
                    global_prompt = f.read().strip()
            
            # Get image files
            image_files = [f for f in os.listdir(image_folder) 
                          if Path(f).suffix.lower() in self.IMAGE_EXTENSIONS]
            
            if not image_files:
                self._log_message("No image files found in input folder", "warning")
                return
            
            self.current_item = 0
            self.total_items = len(image_files)
            self._start_run_summary("image", self.total_items)
            
            # Process each image
            for i, image_file in enumerate(image_files):
                if self.state == SequencerState.STOPPING:
                    outcome = "stopped"
                    break
                
                # Handle pause
                if not self._wait_if_paused():
                    outcome = "stopped"
                    break
                
                self.current_item += 1
                self.current_file = image_file
                self._update_progress()
                
                image_path = os.path.join(image_folder, image_file)

                if getattr(self.config, 'skip_duplicates', False) and self._is_duplicate_image(image_path):
                    self._log_message(f"Skipped duplicate image: {image_file}", "warning")
                    self._record_run_result("skipped_duplicate", image_path, image_file)
                    if not getattr(self.config, 'dry_run', False):
                        self._move_file_to_sent(image_path, is_image=True, failed=False)
                    continue

                context = self._build_prompt_context(
                    mode="image",
                    source_file=image_path,
                    index=self.current_item,
                    title=image_file
                )
                rendered_prompt = self._apply_prompt_variables(global_prompt, context)
                success = self._send_image_prompt(image_path, rendered_prompt, self.current_item)
                
                if success:
                    if getattr(self.config, 'dry_run', False):
                        self._record_run_result("dry_run_success", image_path, image_file)
                    else:
                        self._record_run_result("success", image_path, image_file)
                        self._mark_image_processed(image_path)
                        self._move_file_to_sent(image_path, is_image=True, failed=False)
                else:
                    self._record_run_result("failed", image_path, image_file)
                    self._move_file_to_sent(image_path, is_image=True, failed=True)
            
            self._log_message("Image mode processing completed")
            
        except Exception as e:
            outcome = "error"
            self._log_message(f"Error in image mode: {e}", "error")
            self._capture_error_screenshot("image_mode_error")
            self._change_state(SequencerState.ERROR)
        finally:
            if self.state == SequencerState.STOPPING:
                outcome = "stopped"
            self._finalize_run_summary(outcome)
            if self.state != SequencerState.ERROR:
                self._change_state(SequencerState.IDLE)
    
    def start_image_queue_mode(self, queue_items):
        """Start image+text mode with queue processing.

        Accepts either a Python list (legacy) or a queue.Queue for dynamic enqueueing.
        If a callback `self.queue_item_done_callback` is set, it will be called with item id
        after each queue item completes so the GUI can remove it.
        """
        if self.state != SequencerState.IDLE:
            self._log_message("Sequencer is already running", "warning")
            return

        self._apply_runtime_settings()

        # Normalize input: allow list or queue.Queue
        import queue as _pyqueue
        q: _pyqueue.Queue
        using_queue = False

        if queue_items is None and getattr(self.config, 'auto_resume_queue_from_snapshot', False):
            snapshot = self.load_queue_snapshot()
            if snapshot:
                queue_items = self.build_queue_from_snapshot(snapshot)

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

        self._change_state(SequencerState.RUNNING)
        outcome = "completed"
        processed_images = 0

        try:
            # For legacy list mode, total items can be calculated in advance.
            try:
                if not using_queue:
                    total_images = 0
                    items_for_count = self._queue_to_list(q)
                    for item in items_for_count:
                        folder = item.get('image_folder', '')
                        if os.path.exists(folder):
                            folder_images = [f for f in os.listdir(folder)
                                             if Path(f).suffix.lower() in self.IMAGE_EXTENSIONS]
                            total_images += len(folder_images)
                    self.total_items = total_images
                else:
                    # Unknown total for dynamic queue; leave as 0 and update as we process
                    self.total_items = 0
            except Exception:
                # If anything goes wrong, continue with unknown total
                self.total_items = 0

            self.current_item = 0
            self._start_run_summary("queue", self.total_items)
            self._save_queue_snapshot("running", q, processed_images)

            # Process items from the queue until stopped. This supports new items being
            # added to the queue when a queue.Queue is passed by the GUI.
            queue_idx = 0
            idle_cycles = 0
            while True:
                if self.state == SequencerState.STOPPING:
                    outcome = "stopped"
                    break

                try:
                    queue_item = q.get(timeout=0.5)
                    idle_cycles = 0
                except _pyqueue.Empty:
                    if not using_queue:
                        break
                    idle_cycles += 1
                    if idle_cycles >= 6:
                        # End dynamic mode once UI queue and runtime queue are empty for ~3 seconds
                        remaining_ui_items = getattr(self.config, 'image_queue_items', [])
                        if not remaining_ui_items and q.empty():
                            break
                    continue

                queue_idx += 1

                item_id = queue_item.get('id')
                folder = queue_item.get('image_folder', '')
                prompt_file = queue_item.get('prompt_file', '')
                folder_name = queue_item.get('name', f"Folder {queue_idx}")
                self.current_queue_item_id = item_id

                # Skip items removed from queue UI while still present in runtime queue.
                skip_set = getattr(self.config, 'image_queue_skip_requests', set())
                if item_id in skip_set:
                    self._log_message(f"Skipping removed queue item id={item_id}", "warning")
                    try:
                        skip_set.discard(item_id)
                    except Exception:
                        pass
                    self._save_queue_snapshot("running", q, processed_images)
                    continue

                # Log dequeue event
                self._log_message(f"Dequeued queue item: {folder_name} id={item_id}")

                if not os.path.exists(folder):
                    self._log_message(f"Folder not found: {folder}", "warning")
                    self._record_run_result("failed", folder, "missing_folder")
                    self._save_queue_snapshot("running", q, processed_images)
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
                                   if Path(f).suffix.lower() in self.IMAGE_EXTENSIONS]

                    if not folder_images:
                        self._log_message(f"No images found in: {folder_name}", "warning")
                        self._record_run_result("skipped", folder, "empty_folder")
                        self._save_queue_snapshot("running", q, processed_images)
                        continue

                    # Process each image in this folder
                    for img_idx, image_file in enumerate(folder_images):
                        if self.state == SequencerState.STOPPING:
                            outcome = "stopped"
                            break

                        # Handle pause
                        if not self._wait_if_paused():
                            outcome = "stopped"
                            break

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

                        if getattr(self.config, 'skip_duplicates', False) and self._is_duplicate_image(image_path):
                            self._log_message(f"Skipped duplicate image: {image_path}", "warning")
                            self._record_run_result("skipped_duplicate", image_path, "duplicate_image")
                            if not getattr(self.config, 'dry_run', False):
                                self._move_file_to_sent(image_path, is_image=True, failed=False)
                            continue

                        context = self._build_prompt_context(
                            mode="queue",
                            source_file=image_path,
                            index=processed_images,
                            title=folder_name,
                            extra={"queue_id": item_id, "queue_name": folder_name}
                        )
                        rendered_prompt = self._apply_prompt_variables(folder_prompt, context)
                        success = self._send_image_prompt(image_path, rendered_prompt, processed_images)

                        if success:
                            if getattr(self.config, 'dry_run', False):
                                self._record_run_result("dry_run_success", image_path, folder_name)
                            else:
                                self._record_run_result("success", image_path, folder_name)
                                self._mark_image_processed(image_path)
                                self._move_file_to_sent(image_path, is_image=True, failed=False)
                        else:
                            self._record_run_result("failed", image_path, folder_name)
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
                    self._save_queue_snapshot("running", q, processed_images)
                except Exception as e:
                    # If processing this folder fails, log and continue with next one
                    self._log_message(f"Error processing folder {folder_name}: {e}", "error")
                    self._record_run_result("failed", folder_name, f"queue_folder_exception: {e}")
                    self._capture_error_screenshot("queue_folder_error")
                    self._save_queue_snapshot("running", q, processed_images)
                    continue

            self._log_message("Image queue mode processing completed")
        except Exception as e:
            outcome = "error"
            self._log_message(f"Error in image queue mode: {e}", "error")
            self._capture_error_screenshot("queue_mode_error")
            self._change_state(SequencerState.ERROR)
        finally:
            if self.state == SequencerState.STOPPING:
                outcome = "stopped"
            self.current_queue_item_id = None
            self._save_queue_snapshot(outcome, q, processed_images)
            self._finalize_run_summary(outcome)
            if self.state != SequencerState.ERROR:
                self._change_state(SequencerState.IDLE)
    
    def _send_image_prompt(self, image_path: str, global_prompt: str, image_index: int) -> bool:
        """Send image + text prompt"""
        try:
            self._log_message(f"Sending image {image_index}: {os.path.basename(image_path)}")

            if getattr(self.config, 'dry_run', False):
                self._log_message(f"[DRY RUN] Would paste image: {image_path}")
                if self.config.image_repeat_prompt and global_prompt:
                    self._log_message(f"[DRY RUN] Would paste text for image {image_index}")
                return True
            
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
                self._capture_error_screenshot("paste_image_failed")
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
                    self._capture_error_screenshot("paste_image_text_failed")
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
            self._capture_error_screenshot("send_image_exception")
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
        if self.state in [SequencerState.RUNNING, SequencerState.PAUSED, SequencerState.WAITING_FOR_USER]:
            self.manual_intervention_pending = False
            self._change_state(SequencerState.STOPPING)
            self._log_message("Stopping sequencer...")
    
    def reset(self):
        """Reset sequencer to idle state"""
        self._change_state(SequencerState.IDLE)
        self.current_item = 0
        self.total_items = 0
        self.current_file = ""
