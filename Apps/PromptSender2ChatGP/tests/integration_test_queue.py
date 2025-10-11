"""Integration test for queue processing.

This test seeds a queue.Queue with a couple of dummy folders (created in a temp dir),
enqueues additional items while the sequencer is running, and verifies that the
sequencer invokes the completion callback for each item.

This does not start the GUI; it runs the sequencer in a separate thread with a
mocked PasteController and WindowDetector behaviour.
"""

import tempfile
import os
import threading
import time
import queue

from src.core.sequencer import PromptSequencer, SequencerState


class DummyConfig:
    def __init__(self):
        self.target_window = None
        self.image_intra_delay = 0
        self.image_repeat_prompt = False
        self.image_auto_enter = False
        self.image_paste_enter_grace = 0
        self.image_generation_wait = 0.1
        self.image_jitter_percent = 0


def run_test():
    cfg = DummyConfig()
    seq = PromptSequencer(cfg)

    # Replace heavy controllers with no-op mocks
    class DummyPaste:
        def paste_image(self, path, target_window=None):
            return True
        def paste_text(self, text, auto_enter=False, grace_delay=0, target_window=None):
            return True

    seq.paste_controller = DummyPaste()
    # Mock window detector to always succeed
    class DummyWindowDetector:
        def focus_window(self, name):
            return True
        def focus_input_box(self, retries=1):
            return True

    seq.window_detector = DummyWindowDetector()

    completed = []
    logs = []
    def done_cb(item_id):
        completed.append(item_id)

    def log_cb(msg, level='info'):
        logs.append(msg)

    seq.on_log_message = log_cb

    seq.queue_item_done_callback = done_cb

    # Create temp folders with dummy images
    tmp = tempfile.TemporaryDirectory()
    folder1 = os.path.join(tmp.name, 'a')
    folder2 = os.path.join(tmp.name, 'b')
    os.makedirs(folder1)
    os.makedirs(folder2)
    # create dummy image files
    open(os.path.join(folder1, '1.png'), 'wb').close()
    open(os.path.join(folder2, '2.png'), 'wb').close()

    # Seed queue
    q = queue.Queue()
    q.put({'id': 'seed1', 'image_folder': folder1, 'prompt_file': '', 'name': 'a'})
    q.put({'id': 'seed2', 'image_folder': folder2, 'prompt_file': '', 'name': 'b'})

    # Run sequencer in thread
    t = threading.Thread(target=seq.start_image_queue_mode, args=(q,), daemon=True)
    t.start()

    # Enqueue another item while running
    time.sleep(0.2)
    folder3 = os.path.join(tmp.name, 'c')
    os.makedirs(folder3)
    open(os.path.join(folder3, '3.png'), 'wb').close()
    q.put({'id': 'seed3', 'image_folder': folder3, 'prompt_file': '', 'name': 'c'})

    # Wait for processing
    t.join(timeout=10)

    print('Completed callbacks:', completed)
    assert 'seed1' in completed and 'seed2' in completed and 'seed3' in completed


if __name__ == '__main__':
    run_test()
