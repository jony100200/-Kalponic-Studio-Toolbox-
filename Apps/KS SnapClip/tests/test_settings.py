from settings import Settings, save_settings, load_settings, get_settings_path
import os
import json

def test_settings_save_and_load(tmp_path):
    s = Settings()
    s.output_folder = str(tmp_path / "out")
    s.auto_save = True
    path = get_settings_path(portable=True)
    # ensure we use portable path
    save_settings(s, portable=True)
    loaded = load_settings(portable=True)
    assert loaded.output_folder == s.output_folder
    assert loaded.auto_save == True
    # new defaults present
    assert hasattr(loaded, 'instant_paste')
    assert loaded.instant_paste == False
    assert hasattr(loaded, 'ai_optimization_enabled')
    assert loaded.ai_optimization_enabled == False
    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass
