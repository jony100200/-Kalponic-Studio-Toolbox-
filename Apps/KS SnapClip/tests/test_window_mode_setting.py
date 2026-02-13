from settings import Settings, save_settings, load_settings, get_settings_path
import os


def test_window_mode_persist(tmp_path):
    s = Settings()
    s.window_capture_mode = 'click'
    save_settings(s, portable=True)
    loaded = load_settings(portable=True)
    assert loaded.window_capture_mode == 'click'
    try:
        os.remove(get_settings_path(portable=True))
    except Exception:
        pass
