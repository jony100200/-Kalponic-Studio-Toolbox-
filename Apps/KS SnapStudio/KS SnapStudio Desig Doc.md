# KS SnapStudio — Design Document (v1)

> **Purpose:**
> A desktop application that captures, masks, watermarks, and exports professional circular previews for Substance Sampler, Blender, AI-generated, or scanned materials—automatically and safely.

---

## 1) Product Overview

* **Name:** KS SnapStudio
* **Platform:** Desktop (Windows / macOS / Linux)
* **Stack:** Python 3.11+, PySide6 (Qt), OpenCV, Pillow, NumPy, mss (for capture), PyTorch/ONNX (optional AI modules)
* **Goal:** Make material and texture presentation **instant** — one hotkey or drag-drop generates protected, circular, branded previews.
* **Users:** 3D artists, texture creators, indie studios, AI art creators.

---

## 2) Key Outcomes

* **One-click capture** from active viewport (or area select)
* **Automatic circle crop**, soft feather, and brand ring overlay
* **Watermarking & random background composition**
* **Batch folder processing + daily organization**
* **Clipboard and quick share** (Discord / ArtStation / Reddit)
* **AI-powered assistance** (auto-detect circle, auto-crop, background removal)
* **Safe previews** capped to ≤ 2 K px, metadata removed
* **Watch Mode** → live-capture from apps like Substance Sampler
* **Presets** for different platforms (e.g. ArtStation Dark 2048, Discord 1024 Light)

---

## 3) Scope & Use Cases

| Scenario            | Workflow                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| Material Preview    | Press hotkey → Capture Sampler viewport → Auto circle mask → Add ring/watermark → Save + copy to clipboard |
| Batch Folder        | Drop folder of images → Apply preset (crop + ring + BG) → Export                                           |
| Turntable Preview   | Capture 12 frames → Generate looping GIF/MP4                                                               |
| Safe Demo Upload    | Auto add micro-watermark pattern + reduce res → prevent re-use                                             |
| Presentation Boards | Combine multi-maps (Color / Normal / Roughness) in grid layout                                             |

---

## 4) Pipeline (High Level)

1. **Capture Module** → Active window / area / folder input
2. **Circle Mask Module** → AI-detect object or manual mask → feathered crop
3. **Compose Module** → Add ring, shadow, watermark, BG composition
4. **Export Module** → Resize, save, copy to clipboard, metadata strip
5. **Preset Engine** → Load settings (size, ring, text, watermark, BG)
6. **Batch/Watch Manager** → Apply pipeline to many files
7. **History + Logs** → track captures and outputs

---

## 5) AI Modules (Enhancements)

| Feature                         | Suggested Model                                                  | Purpose                                               |
| ------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| Auto circle detection / crop    | OpenCV Hough Transform + tiny CNN refiner                        | Find sphere region in Sampler viewport automatically. |
| Background removal              | MODNet or U²-Net (ONNX int8)                                     | Clean edges when non-uniform background detected.     |
| Smart composition / relight     | Lightweight image-to-material diffusion filter                   | Enhance contrast and shadow for presentation.         |
| Watermark placement assist      | OCR + layout estimation model (optional)                         | Avoid overlapping bright areas.                       |
| Background generator (optional) | Stable Diffusion SDXL / ControlNet – “texture background” prompt | AI-generate soft studio BGs.                          |

---

## 6) Outputs & File Layout

```
/Output/
  /Runs/Run_YYYYMMDD_HHMM/
    /CirclePreviews/
      <img_name>_circle.png
      <img_name>_ringed.png
      <img_name>_composed.png
    /BackgroundsUsed/
    /Logs/context.json
  /Presets/
  /History.db
```

**context.json**

```json
{
  "source": "SamplerViewport.png",
  "preset": "ArtStation_Dark_2048",
  "mask": "circle",
  "background": "bg_003.jpg",
  "watermark": "KS Studio",
  "size": 2048,
  "timestamp": "2025-10-14T22:15:33",
  "status": "ok"
}
```

---

## 7) UI & UX (PySide6)

* **Dark theme / flat design** (KS style)
* **Left Nav Bar:** Capture | Batch | Presets | History | Settings
* **Top Toolbar:** Hotkey indicator • Preview size dropdown • Start/Stop button
* **Preview Area:** Before / After circle overlay, ring, watermark preview
* **Right Panel:** Preset details (size, ring color, text, BG folder)

Keyboard shortcuts:

* `Ctrl+Shift+S` = Capture area
* `Ctrl+Shift+B` = Batch folder
* `Ctrl+Shift+R` = Repeat last capture
* `Esc` = Cancel overlay

---

## 8) CLI & Automation

```
ks-snapstudio \
  --mode capture|batch \
  --input "C:/textures" \
  --out "./Output/Runs" \
  --preset "ArtStation_Dark_2048" \
  --watermark on \
  --bg random \
  --size 2048
```

Exit codes: 0=ok, 1=partial, 2=error.
JSONL progress stream for integration with KS suite later.

---

## 9) Configuration & Presets

**config.yml**

```yaml
capture:
  backend: "mss"
  hotkey: "ctrl+shift+s"
circle:
  feather_px: 4
  ring_px: 6
  ring_color: "#FFFFFF"
backgrounds_dir: "./backgrounds"
watermark:
  text: "KS Studio • Demo"
  opacity: 0.12
  curved: true
export:
  max_size: 2048
  copy_to_clipboard: true
  strip_metadata: true
performance:
  threads: 4
  cache_preview: true
```

---

## 10) Folder Structure (Production Ready)

```
ks-snapstudio/
├─ app/
│  ├─ main.py
│  ├─ ui/
│  ├─ widgets/
│  ├─ qss/
│  └─ icons/
├─ ks_snap/
│  ├─ __init__.py
│  ├─ capture.py          # mss backend, hotkey listener, overlay
│  ├─ mask.py             # circle crop + feather
│  ├─ compose.py          # ring, shadow, watermark, background
│  ├─ export.py           # resize, metadata strip, save/clipboard
│  ├─ presets.py          # load/save YAML presets
│  ├─ ai/
│  │   ├─ autodetect_circle.py
│  │   ├─ bg_remove_modnet.py
│  │   └─ gen_background.py
│  ├─ watch.py            # optional watch mode
│  └─ utils/
│      ├─ naming.py
│      ├─ logging.py
│      ├─ clipboard.py
│      └─ timing.py
├─ models/
│  ├─ modnet.onnx
│  ├─ u2net.onnx
│  └─ tiny_circle_detect.onnx
├─ backgrounds/
├─ configs/
│  ├─ config.yml
│  └─ presets/
├─ tests/
│  ├─ test_mask.py
│  ├─ test_compose.py
│  └─ data/
├─ scripts/
│  ├─ download_models.py
│  ├─ bench.py
│  └─ demo_run.sh
├─ samples/
├─ pyproject.toml
└─ README.md
```

---

## 11) Performance & Hardware

* **GPU optional:** for MODNet/U²-Net inference; CPU fallback with threshold filters.
* **Capture speed:** ≤ 100 ms for screen grab; ≤ 1 s full pipeline (2 K).
* **Memory:** stream buffers for multi-capture sessions.
* **Threading:** QtConcurrent / ThreadPoolExecutor for non-blocking saves.

---

## 12) Quality & Validation

* **Mask accuracy:** F1 ≥ 0.9 vs manual circle.
* **Edge smoothness:** halo index ≤ 0.1 in alpha band.
* **Color stability:** ΔE < 1 post processing.
* **Output consistency:** identical hash for same preset + image.

---

## 13) Telemetry & Privacy

* Local logs only by default.
* Optional anonymous metrics (fps, preset used) for future QA.
* No uploads / cloud required.
* All EXIF removed on export.

---

## 14) Risks & Mitigations

| Risk                  | Mitigation                            |
| --------------------- | ------------------------------------- |
| Hotkey conflicts      | Allow custom hotkeys in settings      |
| GPU missing           | Fallback to CPU mode                  |
| Background AI fail    | Fallback to random solid color        |
| User data overwrite   | Timestamped folders + duplicate check |
| Circle detection miss | Manual area capture as fallback       |

---

## 15) Acceptance Criteria (v1)

* End-to-end capture → circle mask → ring/watermark → export works on Windows & macOS.
* Avg processing time ≤ 1 s per 2 K image.
* Exports match preset sizes and naming.
* Deterministic results given same config.
* UI non-blocking and hotkeys responsive.

---

## 16) Roadmap

* **v1.0:** Capture, circle mask, ring, watermark, preset system, hotkey.
* **v1.1:** Batch mode + background AI removal.
* **v1.2:** Turntable capture (GIF/MP4).
* **v1.3:** AI auto-circle detect + smart BG generator.
* **v2.0:** Integration with KS suite (super app).

---
