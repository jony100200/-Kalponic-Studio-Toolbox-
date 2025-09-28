import tempfile
from pathlib import Path
from BatchBGRemover import ImageProcessor


class DummyRemover:
    def __call__(self, data: bytes) -> bytes:
        # pretend to remove bg by returning the same bytes (valid PNG header ok for test)
        return data


def test_process_folder_creates_outputs(tmp_path):
    # create fake images
    inp = tmp_path / "in"
    out = tmp_path / "out"
    inp.mkdir()
    out.mkdir()

    # create two small "png" files
    (inp / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00")
    (inp / "b.jpg").write_bytes(b"\xff\xd8\xff\xdb\x00")

    processor = ImageProcessor(remover=DummyRemover())
    processed = processor.process_folder(inp, out)

    assert processed == 2
    assert (out / "a_cleaned.png").exists()
    assert (out / "b_cleaned.png").exists()
