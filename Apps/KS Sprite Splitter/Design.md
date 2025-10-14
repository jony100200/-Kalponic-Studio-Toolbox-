# KS Sprite Splitter — Engineering Specification (Pro)

## 0) Purpose & Scope

A Python desktop/CLI tool that **auto-separates 2D sprites into semantic parts** (e.g., Tree: Leaves/Branches/Trunk; Flag: Cloth/Pole), produces **soft mattes**, and exports **engine-ready, channel-packed maps** with logs and previews. Batch + watch workflows are first-class. This aligns with your v1 outcomes, pipeline, and outputs.

---

## 1) Repository Layout (Production-Ready)

```
Apps\KS Sprite Splitter/
├─ app/                         # (Phase 2) PySide6 UI
│  ├─ main.py
│  ├─ ui/                       # screens, layouts
│  ├─ widgets/
│  ├─ qss/                      # themed via configs/tokens.yml
│  └─ icons/                    # 24px SVG
├─ ks_splitter/                 # CORE LIB (importable)
│  ├─ __init__.py
│  ├─ ingest.py                 # IO, color, proxies, hashing
│  ├─ segment.py                # Protocols + backends registry
│  ├─ parts.py                  # Templates + heuristics + TinyPartNet bridge
│  ├─ matte.py                  # Trimap + matting backends + CPU fallback
│  ├─ pack.py                   # Channel packing (parts/wind/emissive)
│  ├─ export.py                 # Writers, naming, previews, run tree
│  ├─ context.py                # Run/per-image JSON schemas
│  ├─ workers.py                # (Phase 2) pools, backpressure
│  └─ utils/                    # logging, timing, imops (OpenCV/NP)
├─ models/                      # ONNX weights or downloader
│  ├─ README.md
│  ├─ sam2.onnx
│  ├─ mask2former_*.onnx        # optional alt
│  ├─ yolo_seg_*.onnx           # optional alt
│  ├─ modnet.onnx
│  └─ fba_matting.onnx          # optional HQ
├─ templates/                   # Category rules
│  ├─ tree.yml
│  ├─ flag.yml
│  ├─ char.yml
│  ├─ arch.yml
│  └─ vfx.yml
├─ configs/
│  ├─ config.yml                # global defaults (paths, backends)
│  └─ tokens.yml                # (UI) theme tokens
├─ cli/
│  └─ ks_splitter.py            # console_script entrypoint
├─ scripts/
│  ├─ download_models.py
│  ├─ bench.py
│  └─ demo_run.sh
├─ tests/
│  ├─ test_segment.py
│  ├─ test_parts.py
│  ├─ test_matte.py
│  ├─ test_pack_export.py
│  └─ data/                     # tiny samples
├─ samples/
├─ .env.example
├─ pyproject.toml
├─ README.md
└─ LICENSE
```

**Why this structure:** mirrors the v1 pipeline stages and output tree for reproducibility and portability.

---

## 2) Core Contracts (SOLID, pluggable)

```python
# ks_splitter/segment.py
from typing import Protocol, List, Dict, Any
import numpy as np

class Segmenter(Protocol):
    def infer(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Return instances: [{id, class, mask (H×W bool), bbox}]"""

# ks_splitter/matte.py
class Matter(Protocol):
    def refine(self, image: np.ndarray, mask: np.ndarray, band_px: int) -> np.ndarray:
        """Return soft alpha (H×W float32 0..1)"""

# ks_splitter/parts.py
class PartSplitter(Protocol):
    def split(self, image: np.ndarray, inst: Dict[str, Any], template: Dict) -> Dict[str, np.ndarray]:
        """Return dict of named part masks: {'Leaves': mask, 'Trunk': mask, ...}"""
```

**Registries** (Open/Closed):

```python
REG_SEG = {"sam2": Sam2Segmenter(...), "m2f": Mask2FormerSegmenter(...), "yolo": YOLOSegSegmenter(...)}
REG_MAT = {"modnet": ModNetMatter(...), "fba": FBAMatter(...), "guided": GuidedCPUFallback(...)}
REG_PART = {"tree": TreeSplitter(), "flag": FlagSplitter(), "char": CharSplitter(), "arch": ArchSplitter(), "vfx": VFXSplitter()}
```

---

## 3) Models & Backends (researched)

### 3.1 Object/Instance Segmentation

* **Default:** **SAM 2** (promptable, strong masks; robust autopredict) with modern architecture and real-time memory for streams; ICLR 2025 paper confirms capabilities.
* **Class-aware alt:** **Mask2Former**—universal segmentation, strong panoptic/instance results (CVPR 2022, official repo).
* **Lightweight alt:** **YOLOv8/YOLO11-seg**—easy to deploy, fast instance masks, good for CPU/GPU mixed fleets.

### 3.2 Edge Matting (soft alphas)

* **Default:** **MODNet**—real-time portrait matting; fast and robust trimap-free matting (AAAI 2022).
* **HQ fallback:** **FBA Matting**—predicts F, B, Alpha for high-quality composite edges (arXiv; official repo).
* **CPU fallback:** **Guided filter**-based refinement—edge-preserving, linear-time, related to matting Laplacian.

### 3.3 Inference Runtime

* **ONNX Runtime GPU/CPU** with CUDA EP as default on NVIDIA; packaged DLL loading simplified from v1.19+.
  *Windows/AMD*: consider DirectML EP; track its support notes (issue thread shows current caveats).
  *macOS Metal*: fallback to CPU or ship MPS/Torch path as alt runtime (later).

**Why this stack:** matches v1 pluggability (SAM/Mask2Former/YOLO + MODNet/FBA + CPU fallback), keeps deterministic batch outputs and performance targets.

---

## 4) Pipeline (deterministic)

1. **Ingest**: normalize color, optional proxy downscale (≤ 2048 px), hash source; store metadata.
2. **Object Segmentation**: SAM2 autopredict → stable instances; optional class-aware Mask2Former/YOLO if template benefits from labels.
3. **Part Splitting** (template-driven): Tree/Flag/Char/Arch/VFX heuristics + optional TinyPartNet refine.
4. **Alpha Matting**: trimap (erode/dilate) → MODNet or FBA; guided-filter fallback.
5. **Aux maps (optional)**: quick normal/roughness/AO per part (can be off by default).
6. **Export**: channel-packed `parts.tga`, per-part `matte_*.png`, `wind.png`, `emissive.png`, preview overlays, and `context.json`; logs per run.

---

## 5) Templates (examples)

**templates/tree.yml**

```yaml
name: tree
parts: [Leaves, Branches, Trunk]
heuristics:
  kmeans_k: 4
  freq_window: [3, 9]      # identify leaves as high-frequency
  trunk_skeleton: true     # skeletonize to find trunk axis
matting:
  band_px: 6
extras:
  wind_gradient: true
```

**templates/flag.yml**

```yaml
name: flag
parts: [Cloth, Pole]
heuristics:
  cloth_vs_pole: "blob_largest_vs_thin_line"
  pin_line_detection: true
matting:
  band_px: 5
extras:
  wind_phase_uv: true
```

(Templates mirror v1 categories and extras like wind weights and anchors.)

---

## 6) CLI & Watch Mode

**CLI**

```
ks-splitter \
  --in "/Input/Images" \
  --out "/Output/Runs" \
  --category auto|tree|flag|char|arch|vfx \
  --objects sam2 \
  --parts tiny_partnet=off \
  --matte modnet \
  --pack rgba \
  --aux-maps none \
  --preview true \
  --workers 6
```

Matches v1 CLI with deterministic JSONL progress + exit codes.

**Watch Mode** (same binary): debounced file events → run pipeline; writes to timestamped `Run_*` folders.

---

## 7) Outputs & Naming (unchanged)

```
/Output/Runs/Run_YYYYMMDD_HHMM/
  /Backup/
  /Separated/<img_name>/
    color.png
    parts.tga                # R/G/B = part A/B/C, A = BG
    wind.png                 # optional
    emissive.png             # optional
    matte_<part>.png         # soft alpha per part
    nrma.png                 # optional packed normal/roughness/AO
  /Preview/<img_name>_small.png
  /Logs/context.json, run.log
```

Exactly as your v1 spec to preserve interoperability.

---

## 8) Configs (minimal)

**configs/config.yml**

```yaml
objects_backend: sam2
matte_backend: modnet
parts:
  default_template: auto
  templates_dir: "./templates"
export:
  pack: "rgba"
  write_previews: true
  write_aux_maps: false
performance:
  workers: 6
  proxy_max_px: 2048
runtimes:
  onnx:
    prefer: "cuda"          # cuda|cpu|directml
    cuda_version_min: "12"
```

---

## 9) Quality, Metrics & Tests

* **Mask quality:** IoU/F1 vs small labeled set; thin-structure F-score @ 1 px tolerance.
* **Edge quality:** SAD on trimap unknown band; “halo index” target per v1.
* **Pack validity:** parts channels mutually exclusive (no overlaps).
* **Determinism:** same input+config+model hashes ⇒ identical outputs.

**Unit tests**

* `test_segment.py`: instance count ≥1 on sample trees/flags.
* `test_parts.py`: named masks present; coverage ≥ X%.
* `test_matte.py`: alpha ∈ [0,1]; border softening improves SAD.
* `test_pack_export.py`: RGBA exclusivity; filenames + folders correct.

---

## 10) Performance Plan

* **GPU goal:** 2–5 images/sec @ 2K on mid-range GPU (v1 target).
* **CPU fallback:** ≥ 0.3–0.5 img/sec with guided-filter matte path.
* **Runtime:** ONNX Runtime CUDA EP (v1.19+ default CUDA 12.x packaging simplifies deps).
* **Threading:** start single-process; add worker pool in `workers.py` Phase 2.

---

## 11) Packaging & Delivery

* **PyInstaller** triplet (Win/macOS/Linux) + **portable models** in `/models` (or a one-click `scripts/download_models.py`).
* **Console script** via `pyproject.toml` → `ks-splitter`.
* **Artifacts:** binaries, README Quickstart, templates, sample images—per v1 deliverables.

---

## 12) Security, Privacy, Licensing

* **Local-only** inference by default (no uploads).
* Model licenses: SAM2 (research terms), Mask2Former (see repo), MODNet (AAAI 2022), FBA (MIT repo—verify weights/usage).
* Provide a `models/README.md` stating license notes and where to fetch weights.

---

## 13) Roadmap (focused)

* **v1.0 (ship):** SAM2 + MODNet, Tree/Flag templates, CLI + Watch, outputs/logs, small test set.
* **v1.1:** Character/Architecture/VFX templates; optional TinyPartNet ONNX; improved emissive/wind; Mask2Former/YOLO as alt backends.
* **v1.2:** PySide6 UI wizard (step flow aligns with your KS UI conventions); workers; profiling.

---

## 14) Why these model picks (summary)

* **SAM 2**: recent SOTA promptable segmentation with strong masks and good interactive/autopredict behavior—ideal as a universal object mask generator for 2D sprites.
* **Mask2Former / YOLO-seg**: class-aware options when templates benefit from labels or when you want a lighter/faster alternative.
* **MODNet → FBA → Guided**: a quality ladder: fast trimap-free → high-quality alpha (F/B/α) → robust CPU fallback tied to matting literature.

---

## 15) “Definition of Done” (v1)

* End-to-end batch & watch produce **parts**, **soft mattes**, **packed maps**, **previews**, and **context.json/logs** for all inputs, deterministic across runs.
* Meets v1 quality/perf thresholds; passes unit tests; binaries available for all OS targets.

---
