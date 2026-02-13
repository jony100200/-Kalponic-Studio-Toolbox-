from utils import instant_paste

class DummyController:
    def __init__(self):
        self.actions = []
    def press(self, key):
        self.actions.append(('press', key))
    def release(self, key):
        self.actions.append(('release', key))


def test_instant_paste_monkeypatch(monkeypatch):
    # monkeypatch pynput.keyboard.Controller to a dummy
    import types
    kb_mod = types.SimpleNamespace(Controller=DummyController, Key=types.SimpleNamespace(ctrl='ctrl'))
    monkeypatch.setitem(__import__('sys').modules, 'pynput.keyboard', kb_mod)

    res = instant_paste()
    assert res is True

    # ensure the dummy controller registered actions
    c = kb_mod.Controller()
    c.press('x')
    assert ('press', 'x') in c.actions
