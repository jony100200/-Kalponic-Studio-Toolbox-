import importlib, traceback

try:
    importlib.import_module('src.core.sequencer')
    importlib.import_module('src.gui.main_window')
    print('Import OK')
except Exception:
    traceback.print_exc()
    raise
