from PIL import Image
import customtkinter as ctk
from ui import _to_ctk_image


def test_to_ctk_image_returns_ctk_image():
    img = Image.new('RGBA', (200, 100), color=(255, 0, 0, 255))
    res = _to_ctk_image(img, size=(200, 100))
    # CTkImage may be None on error; prefer that it returns a CTkImage object
    assert res is not None
    assert isinstance(res, ctk.CTkImage)
