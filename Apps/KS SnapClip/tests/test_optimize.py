from PIL import Image
from utils import optimize_image


def test_optimize_resizes_and_converts():
    # create a wide test image
    img = Image.new('RGB', (2000, 500), color=(255,0,0))
    out = optimize_image(img, max_width=1024, convert_to_png=True)
    assert out.width == 1024
    # conversion to RGBA when convert_to_png True
    assert out.mode in ('RGBA', 'RGB', 'P')
