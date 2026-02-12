import os
from clipboard_win import default_provider
from PIL import Image


def test_clipboard_fallback_saves_temp_file(tmp_path):
    img = Image.new('RGB', (10, 10), color=(255, 0, 0))
    res = default_provider.copy(img)
    # Either success True (if win32 available) or fallback path present
    if res.get('success'):
        assert 'message' in res
    else:
        path = res.get('path')
        assert path is not None
        assert os.path.exists(path)
        # cleanup
        os.remove(path)
