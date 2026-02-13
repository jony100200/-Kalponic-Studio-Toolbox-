from utils import validate_hotkeys


def test_validate_hotkeys_detects_empty():
    ok, msg = validate_hotkeys({'area': '', 'window': '<ctrl>+<shift>+2'})
    assert ok is False
    assert 'empty' in msg


def test_validate_hotkeys_detects_conflict():
    ok, msg = validate_hotkeys({'area': '<ctrl>+<shift>+1', 'window': '<ctrl>+<shift>+1'})
    assert ok is False
    assert 'conflict' in msg.lower()


def test_validate_hotkeys_accepts_valid():
    ok, msg = validate_hotkeys({'area': '<ctrl>+<shift>+1', 'window': '<ctrl>+<shift>+2', 'monitor': '<ctrl>+<shift>+3'})
    assert ok is True
    assert msg == ''
