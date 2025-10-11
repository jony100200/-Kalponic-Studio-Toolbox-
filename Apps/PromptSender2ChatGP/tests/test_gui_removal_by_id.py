import os
import tempfile
import queue

from src.gui.main_window import PromptSequencerGUI
from types import SimpleNamespace

# This unit-style test does not instantiate the full GUI loop.
# Instead we create a minimal fake 'image_tab' and 'config' and call the
# removal helper to verify it removes by id and rebuilds the listbox display.


def test_on_queue_item_done_by_id():
    # Create a minimal config with image_queue_items
    cfg = SimpleNamespace()
    cfg.image_queue_items = []
    cfg.image_queue_obj = None

    # Prepare three dummy items
    items = []
    for i in range(3):
        itm = {
            'id': f'id{i}',
            'image_folder': f'/fake/folder/{i}',
            'prompt_file': f'/fake/prompt/{i}.txt',
            'name': f'folder_{i}'
        }
        items.append(itm)
    cfg.image_queue_items = list(items)

    # Fake GUI object with a listbox-like replacement
    class FakeListbox:
        def __init__(self):
            self._items = []
        def insert(self, idx, value):
            # Support tk.END, 'end', None or integer index
            if idx in (None, 'end'):
                self._items.append(value)
            else:
                try:
                    self._items.insert(int(idx), value)
                except Exception:
                    self._items.append(value)
        def delete(self, a, b=None):
            if b is None:
                # single index
                del self._items[a]
            else:
                self._items = []
        def get(self, a, b=None):
            return tuple(self._items)
        def size(self):
            return len(self._items)

    fake_listbox = FakeListbox()
    for itm in cfg.image_queue_items:
        folder_name = itm.get('name', 'Unknown')
        prompt_name = os.path.basename(itm.get('prompt_file', '')) or 'No prompt'
        display_text = f"{folder_name} → {prompt_name}"
        fake_listbox.insert(len(fake_listbox._items), display_text)

    # Stub the GUI container that has image_tab with queue_listbox
    fake_image_tab = SimpleNamespace()
    fake_image_tab.queue_listbox = fake_listbox

    # Create a minimal PromptSequencerGUI but avoid initializing Tk
    gui = SimpleNamespace()
    gui.config = cfg
    gui.image_tab = fake_image_tab

    # Import the function to test
    from src.gui.main_window import PromptSequencerGUI

    # Use the existing helper function implementation by calling the
    # module-level function via an instance of PromptSequencerGUI created without Tk.
    # We'll create a dummy instance by bypassing __init__
    obj = PromptSequencerGUI.__new__(PromptSequencerGUI)
    obj.config = cfg
    obj.image_tab = fake_image_tab

    # Call removal for id 'id1'
    obj._on_queue_item_done_by_id('id1')

    # Verify that the config no longer contains the item with id1
    remaining_ids = [itm.get('id') for itm in cfg.image_queue_items]
    assert 'id1' not in remaining_ids

    # Verify listbox contents were rebuilt to match remaining items
    lb_items = fake_listbox.get(0, None)
    assert len(lb_items) == 2


if __name__ == '__main__':
    test_on_queue_item_done_by_id()
    print('test passed')
