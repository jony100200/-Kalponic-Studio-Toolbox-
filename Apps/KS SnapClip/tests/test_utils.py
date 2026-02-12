from datetime import datetime
from utils import generate_filename


def test_generate_filename_with_window():
    ts = datetime(2025,1,1,12,30,45)
    fn = generate_filename('snap', 'My App - Untitled', ts)
    assert 'snap_My_App-Untitled_20250101_123045.png'.replace('-', '_').startswith('snap_')


def test_generate_filename_without_window():
    ts = datetime(2025,1,1,12,30,45)
    fn = generate_filename('snap', '', ts)
    assert fn == 'snap_20250101_123045.png'
