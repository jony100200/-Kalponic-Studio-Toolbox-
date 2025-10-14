import traceback
try:
    from src.gui import SeamlessCheckerGUI
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    print('IMPORT_FAIL')
