from hotkey import HotkeyManager


def test_update_hotkeys_sets_map():
    hk = HotkeyManager()
    called = {'a': False}
    def cb():
        called['a'] = True
    hk.update_hotkeys({'<ctrl>+a': cb})
    assert '<ctrl>+a' in hk._hotkeys
    # simulate calling the stored callback
    hk._hotkeys['<ctrl>+a']()
    assert called['a'] is True
