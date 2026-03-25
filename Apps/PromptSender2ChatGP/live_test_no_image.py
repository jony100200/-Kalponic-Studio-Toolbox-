#!/usr/bin/env python3
import os
import time
import sys

# ensure cli helpers available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli import _build_sequencer, setup_logging
from src.core.config import AppConfig

if __name__ == '__main__':
    setup_logging(quiet=False)
    config = AppConfig()
    try:
        config.sanitize()
    except Exception:
        pass

    seq = _build_sequencer(config)

    # Stub out image paste so we don't copy/paste image data
    seq.paste_controller.paste_image = lambda image_path, target_window=None: True

    # Prepare prompt text
    prompt_text = ""
    gp = getattr(config, 'global_prompt_file', '') or ''
    if gp and os.path.exists(gp):
        with open(gp, 'r', encoding='utf-8') as f:
            prompt_text = f.read().strip()
    if not prompt_text:
        prompt_text = "Test prompt: ensure focus and /image are sent before this text."

    rendered = seq._apply_prompt_variables(
        prompt_text,
        seq._build_prompt_context(mode='image', source_file='live_test_dummy.jpg', index=1, title='LiveTest')
    )

    print('Starting live test (no image). Target window:', getattr(config, 'target_window', '(none)'))
    time.sleep(2)

    ok = seq._send_image_prompt('live_test_dummy.jpg', rendered, 1)
    print('Live test result:', ok)
