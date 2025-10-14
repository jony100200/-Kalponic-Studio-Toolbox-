import os
import tempfile
import shutil
from PIL import Image
import numpy as np
import cv2

from src.batch_processor import BatchProcessor
from src.image_checker import ImageChecker


def make_temp_image(path, color=(128, 128, 128), size=(64, 64)):
    img = Image.new('RGB', size, color)
    img.save(path)


def test_process_file_in_memory(tmp_path):
    # prepare
    img_path = tmp_path / 'test.png'
    make_temp_image(str(img_path))
    checker = ImageChecker(threshold=1000000)  # high threshold so seam is True
    processor = BatchProcessor(checker, ['.png'], str(tmp_path))
    processor.preview_mode = 'memory'
    processor.thumbnail_only_in_memory = True
    processor.thumbnail_max_size = 64

    res = processor.process_file(str(img_path))
    assert res is not None
    assert res['file'] == 'test.png'
    assert 'thumb_bytes' in res
    assert res['thumb_bytes'] != b''
    # preview_bytes should be empty due to thumbnail_only_in_memory
    assert res['preview_bytes'] == b''


def test_process_file_disk(tmp_path):
    img_path = tmp_path / 'test2.png'
    make_temp_image(str(img_path), color=(200, 50, 50))
    checker = ImageChecker(threshold=1000000)
    processor = BatchProcessor(checker, ['.png'], str(tmp_path))
    processor.preview_mode = 'disk'
    processor.thumbnail_only_in_memory = False
    processor.thumbnail_max_size = 64

    res = processor.process_file(str(img_path))
    assert res is not None
    assert res['file'] == 'test2.png'
    # preview_bytes should exist in memory (since thumbnail_only_in_memory=False)
    assert res['preview_bytes'] != b''
    # preview_path should point to a file on disk
    assert res['preview_path'] != ''
    assert os.path.exists(res['preview_path'])


if __name__ == '__main__':
    import pytest
    pytest.main([os.path.dirname(__file__)])
