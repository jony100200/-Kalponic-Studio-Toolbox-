import queue, tempfile, os
from src.core.sequencer import PromptSequencer

class DummyConfig:
    def __init__(self):
        self.target_window = None
        self.image_intra_delay = 0
        self.image_repeat_prompt = False
        self.image_auto_enter = False
        self.image_paste_enter_grace = 0
        self.image_generation_wait = 0.1
        self.image_jitter_percent = 0

cfg = DummyConfig()
seq = PromptSequencer(cfg)

class DummyPaste:
    def paste_image(self, path, target_window=None):
        print('paste_image', path)
        return True
    def paste_text(self, text, auto_enter=False, grace_delay=0, target_window=None):
        print('paste_text')
        return True

seq.paste_controller = DummyPaste()
class DummyWindowDetector:
    def focus_window(self, name):
        print('focus_window', name)
        return True
    def focus_input_box(self, retries=1):
        print('focus_input_box')
        return True
seq.window_detector = DummyWindowDetector()

# prepare temp folders
tmp = tempfile.TemporaryDirectory()
folder1 = os.path.join(tmp.name, 'a')
os.makedirs(folder1)
open(os.path.join(folder1, '1.png'), 'wb').close()

q = queue.Queue()
q.put({'id': 'seed1', 'image_folder': folder1, 'prompt_file': '', 'name': 'a'})

seq.queue_item_done_callback = lambda iid: print('callback', iid)

seq.start_image_queue_mode(q)
print('done')
