import os
import queue
from types import SimpleNamespace

from src.core.sequencer import PromptSequencer


def _make_config(tmp_path, dry_run=True):
    return SimpleNamespace(
        target_window="",
        dry_run=dry_run,
        text_auto_enter=True,
        text_paste_enter_grace=10,
        text_generation_wait=0,
        text_jitter_percent=0,
        image_intra_delay=0,
        image_repeat_prompt=False,
        image_auto_enter=False,
        image_paste_enter_grace=0,
        image_generation_wait=0,
        image_jitter_percent=0,
        focus_retries=1,
        paste_max_retries=1,
        paste_retry_delay=0.1,
        enable_error_screenshots=False,
        error_screenshot_dir=str(tmp_path / "screens"),
        queue_snapshot_enabled=True,
        queue_snapshot_file=str(tmp_path / "queue_snapshot.json"),
        image_queue_items=[],
        skip_duplicates=False,
        prompt_variables_enabled=True,
        auto_resume_queue_from_snapshot=False,
        image_queue_cancel_requests=set(),
        image_queue_skip_requests=set(),
    )


def test_prompt_variable_rendering(tmp_path):
    cfg = _make_config(tmp_path)
    seq = PromptSequencer(cfg)

    source = tmp_path / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    rendered = seq._apply_prompt_variables(
        "File={{filename}} Index={{index}}",
        seq._build_prompt_context(mode="text", source_file=str(source), index=7, title="Test"),
    )

    assert "sample.txt" in rendered
    assert "7" in rendered
    assert "{{" not in rendered


def test_dry_run_does_not_move_file(tmp_path):
    cfg = _make_config(tmp_path, dry_run=True)
    seq = PromptSequencer(cfg)

    src_file = tmp_path / "prompt.txt"
    src_file.write_text("hello", encoding="utf-8")

    seq._move_file_to_sent(str(src_file), is_image=False, failed=False)
    assert src_file.exists()


def test_preflight_text_mode_counts_prompts(tmp_path):
    cfg = _make_config(tmp_path, dry_run=True)
    seq = PromptSequencer(cfg)

    folder = tmp_path / "texts"
    folder.mkdir()
    (folder / "a.txt").write_text("first\n---\nsecond", encoding="utf-8")

    result = seq.run_preflight(mode="text", input_folder=str(folder))
    assert result["ok"] is True
    assert result["estimated_items"] == 2


def test_queue_snapshot_roundtrip(tmp_path):
    cfg = _make_config(tmp_path, dry_run=True)
    seq = PromptSequencer(cfg)

    q = queue.Queue()
    q.put({"id": "x1", "image_folder": "C:/tmp", "prompt_file": "", "name": "tmp"})

    seq._save_queue_snapshot("running", q, processed_images=1)
    snapshot = seq.load_queue_snapshot()

    assert snapshot is not None
    assert snapshot["status"] == "running"
    rebuilt = seq.build_queue_from_snapshot(snapshot)
    assert rebuilt.qsize() == 1
