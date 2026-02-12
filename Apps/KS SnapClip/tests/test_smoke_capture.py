import os
from PIL import Image
from store import CaptureStore


def test_store_add_and_recent(tmp_path):
    store = CaptureStore(max_items=3)
    # create small image
    img = Image.new('RGBA', (10, 10), color=(255,0,0,255))
    store.add(img, name='test')
    recent = store.recent()
    assert len(recent) == 1
    # save
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    path = store.save(0, str(out_dir), prefix='smoke')
    assert os.path.exists(path)
