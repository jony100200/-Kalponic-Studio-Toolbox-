# KS AutoModel — Design Document (v1)

> An independent, drop-in “model finder” that analyzes any app, detects what ML tasks it needs, profiles the host machine, searches trusted hubs, then recommends and (optionally) downloads the **best + most optimized** models for that hardware.
> Principles: **KISS**, **SOLID**, **reuse-first**, **low file size bias**, **dark, calm UI** consistent with KS tools.  

## 1) Objectives & Non-Goals

**Objectives**

* Auto-discover an application’s **intent** (tasks) from code/metadata.
* Profile **CPU/GPU/VRAM/RAM** and classify into performance **tiers**.
* Search Hugging Face, GitHub, and ModelScope for **compatible** models (fast, small, license-friendly, ONNX/FP16/INT8 where possible).
* Produce a **ranked, multi-model pipeline** with reasoned tradeoffs; ask for user consent; download to `models/`.
* Be **independent** of target apps (runs “outside” them), with a clear **plugin interface**.

**Non-Goals**

* Not an AutoML trainer. No dataset labeling or training.
* No closed, gated, or questionable licensing unless user opts in.
* No forced integration—always **opt-in**, reversible.

---

## 2) Architectural Overview

### 2.1 High-Level Blocks

* **App Profiler** — inspects code/manifest/readme to infer ML **tasks**.
* **Task Mapper** — maps tasks ↔ model families; supports **multi-model pipelines**.
* **Hardware Profiler** — detects **CPU/GPU/VRAM/RAM/OS**; outputs **tier**.
* **Model Finder** — queries hubs with filters (task, size, format, license).
* **Scoring Engine** — ranks candidates (accuracy/popularity/size/freshness/hardware fit).
* **Pipeline Composer** — assembles compatible models; estimates memory & disk.
* **Downloader & Verifier** — downloads to `models/`, verifies checksum; resumes safely.
* **UI / CLI** — dark, minimal, heuristic-driven UX; consistent with KS design language. 
* **Integrations** — plugin API for target apps to request recommendations.

### 2.2 Design Principles

* **KISS**: simple data contracts, few moving parts.
* **SOLID**: clear interfaces per block; dependency inversion (Model Finder depends on an abstract “IndexProvider”).
* **Reuse-first** + phased release ethic from KS strategy (research → design → proto → UX → package) to keep process disciplined. 
* **Small-first bias**: prefer low-file-size checkpoints if quality is close.

---

## 3) Folder Structure (Monorepo or Standalone Package)

```
ks-automodel/
├─ apps/                         # example adapters for popular app types
│  ├─ unity/                     # sample adapter that inspects Unity project files
│  └─ python/                    # adapter for Python projects (requirements, entrypoints)
├─ core/
│  ├─ app_profiler/              # reads manifests, code patterns, READMEs
│  ├─ task_mapper/               # task ontology + rules
│  ├─ hw_profiler/               # CPU/GPU/RAM/OS detection
│  ├─ model_finder/              # providers (hf, github, modelscope)
│  ├─ scoring/                   # ranking & constraints
│  ├─ pipeline/                  # compose multi-model pipelines; resource estimator
│  ├─ downloader/                # snapshot/download, checksum, resume
│  ├─ config/                    # schema + defaults
│  └─ utils/                     # logging, io, runtime helpers
├─ providers/
│  ├─ huggingface_provider.py
│  ├─ github_provider.py
│  └─ modelscope_provider.py
├─ ui/
│  ├─ desktop/                   # Qt/PySide dark UI (or Tauri/HTML)
│  ├─ cli/                       # Typer/Click commands
│  └─ assets/                    # icons, illustrations, dark palettes
├─ data/
│  ├─ registries/                # curated model registry JSON (optional cache)
│  └─ schemas/                   # jsonschema for config & pipelines
├─ tests/
│  ├─ unit/
│  └─ integration/
├─ docs/
│  ├─ design/                    # this doc + UX spec
│  └─ api/                       # plugin & config reference
├─ scripts/
│  ├─ export_onnx.py
│  └─ build_ui_assets.py
└─ models/                       # default download path (user-editable)
```

---

## 4) Data Contracts

### 4.1 Detected Hardware (JSON)

```json
{
  "cpu": {"name": "Intel i7-12700", "cores": 12},
  "ram_gb": 16,
  "gpu": {"vendor": "NVIDIA", "name": "RTX 3050", "vram_gb": 4},
  "os": "Windows-11",
  "tier": "edge_4g"
}
```

### 4.2 App Profile (JSON)

```json
{
  "summary": "Finds objects in images and captions them",
  "tasks": ["object_detection", "captioning"],
  "hints": {"inputs": ["image"], "outputs": ["bboxes", "text"], "batching": "small"}
}
```

### 4.3 Model Candidate (JSON)

```json
{
  "hub": "huggingface",
  "repo": "ultralytics/yolov12n-seg",
  "task": "object_detection",
  "filesize_mb": 25,
  "formats": ["onnx", "pt"],
  "precision": ["fp16"],
  "license": "AGPL-3.0",
  "updated": "2025-05-04",
  "popularity": {"downloads_90d": 120000, "stars": 3200},
  "estimated_vram_gb": 1.2,
  "score": 0.86
}
```

### 4.4 Pipeline (JSON)

```json
{
  "app": "generic",
  "pipeline": [
    {"task": "object_detection", "repo": "ultralytics/yolov12n", "format": "onnx"},
    {"task": "captioning", "repo": "Salesforce/blip-image-captioning-base", "format": "onnx"}
  ],
  "disk_mb": 300,
  "vram_peak_gb": 2.7,
  "notes": ["Small-first choices; FP16 preferred; batch_size=1–2"]
}
```

---

## 5) Core Modules — Responsibilities & Interfaces

### 5.1 App Profiler

* **Inputs**: path(s) to target app.
* **Strategy**:

  * Parse manifests (`package.json`, `pyproject.toml`, Unity meta), search for keywords (e.g., “segmentation”, “caption”, “UPDATERemBG”).
  * Lightweight LLM prompt on README/changelogs to infer **tasks**; never auto-execute code.
* **Outputs**: `App Profile` JSON.

### 5.2 Task Mapper

* **Ontology** (extensible): `image_tagging`, `object_detection`, `instance_segmentation`, `background_matting`, `captioning`, `ocr`, `upscaling`, `denoise`, `tts`, `asr`, `translation`, etc.
* **Rules**: each task maps to a curated model **family** and minimum/ideal formats.

### 5.3 Hardware Profiler

* **Collects** CPU cores, RAM, GPU make/model, VRAM, OS.
* **Tiering**: `cpu_only`, `edge_4g`, `mid_8g`, `pro_12g`, `max`.
* **KISS**: single function `detect_hardware()->HardwareInfo`.

*(UI preference, contrast, dark mode, calm motion are applied in the app’s front-end per KS dark-UI guidance.)* 

### 5.4 Model Finder

* **Providers** implement `search(task, constraints)->[ModelCandidate]`.
* **Constraints** include: `max_filesize_mb`, `requires_formats`, `license_allowlist`, `updated_after`, `popularity_window`.
* **Pluggable**: add/remove providers without changing call sites (SOLID: Open/Closed).

### 5.5 Scoring Engine

Weighted score:

* **Accuracy proxy** (benchmarks or community metrics, when available).
* **Hardware fit** (vram_estimate vs tier).
* **Filesize** (small-first bias).
* **Popularity & freshness**.
* **Format readiness** (ONNX/FP16/INT8).
* **License** bonus/penalty.

### 5.6 Pipeline Composer

* Ensures **I/O compatibility** across tasks (tensor shapes, types).
* Estimates **peak VRAM** (sequential vs pipelined), **disk**, and **latency**.
* Produces ranked **top-N pipelines**.

### 5.7 Downloader & Verifier

* Avoids partial/corrupt downloads (checksum).
* Can **resume**; supports **mirror** URL fallback.
* Writes to `models/` (default, user-configurable) + `pipelines/` manifest.

---

## 6) Configuration & Defaults

### 6.1 User Config (`~/.ks_automodel/config.yml`)

* `models_dir`, `allow_licenses: [apache-2.0, mit, bsd-3-clause]`
* `max_filesize_mb: 500` (per model)
* `prefer_formats: [onnx, fp16]`
* `telemetry_opt_in: false` (default)
* `ui.theme: auto` (dark/light auto; manual override) 

### 6.2 Project Config (`<project>/.ks/automodel.yml`)

* `tasks: []` (optional hints)
* `hardware_overrides: {tier: "edge_4g"}` (for predictable CI)
* `pin_models: {object_detection: "ultralytics/yolov12n@sha256:..."}`
* `deny_licenses: []`

---

## 7) UI / UX Specification (Desktop + CLI)

### 7.1 Visual Language

* **Dark, muted surfaces**, off-white text, high legibility; avoid pure black/white; 60-30-10 color balance; subtle neon accents only for highlights; consistent spacing and calm motion. 
* **Accessibility**: 4.5:1 body text contrast; visible focus; reduced motion mode. 

### 7.2 Screens

1. **Home**

* “Analyze Application” (select folder) → summary card of detected tasks.
* “Detect Hardware” → tier and specs.
* “Preferences” (theme toggle, licenses, size limits).

2. **Results**

* **Task cards** (Tagging / Detection / …) with top 1–3 model picks.
* Each card: **Size**, **Format**, **VRAM est.**, **Pros/Cons**, **Reasoning**.

3. **Pipeline View**

* Visual chain of chosen models; show **estimated VRAM**, **disk use**, **runtime**.
* Toggle **“Favor smaller models”** or **“Favor quality”**.

4. **Confirm & Download**

* Summary; target `models/` path; checkbox “write project config”.
* Progress bar; **clear status** and remedial guidance on errors. (Visibility of system status, error prevention/recovery.) 

5. **History**

* Past analyses, pinned pipelines, quick re-apply.

**CLI**

* `ks-automodel analyze /path/to/app --download --favor small --tier auto`

---

## 8) Performance & Footprint Budgets

* **Cold start UI** < 1.5s; first analysis < 10s on modest machines.
* **RAM while analyzing** < 300MB.
* **Disk cache cap** default 6GB; LRU eviction.
* **Model size bias**: prefer ≤ 500MB per model unless better accuracy justifies more (transparent rationale shown in UI).

---

## 9) Security, Privacy, Licensing

* **No code execution** from target apps; static inspection only.
* **Network**: read-only queries to hubs; SHA-256 verify downloads.
* **Licensing filters** default to permissive; gated repos require explicit user auth.
* **Telemetry**: off by default; if enabled, anonymized model IDs + timings. (Clear disclosure in UI with calm, readable copy.) 

---

## 10) Testing Strategy

* **Unit**: each provider, scorer, parser.
* **Golden files**: sample apps with known tasks → expected pipelines.
* **Hardware mocks**: simulate `cpu_only`, `edge_4g`, `mid_8g`, etc.
* **Smoke E2E**: analyze → propose → download (dry-run mode).
* **UX Heuristics**: checklists derived from KS process phases; polish rounds. 

---

## 11) Example End-to-End Flow

1. User selects `/apps/background_remover`.
2. App Profiler finds `segmentation`, `refinement`, `upscaling`.
3. Hardware Profiler → **edge_4g**.
4. Finder queries providers with constraints: format `onnx`, size `< 500MB`, licenses `Apache/MIT/BSD`, recent updates.
5. Scoring picks:

   * `U^2-Net (onnx)` for segmentation,
   * `MODNet (onnx)` for matting,
   * `Real-ESRGAN (fp16)` for upscaling.
6. Pipeline Composer estimates **disk 320MB**, **VRAM peak 3.1GB**; shows rationale.
7. UI asks: “Download & configure to `/models/`?” → user accepts.
8. Downloader saves and writes `.ks/automodel.yml` with pinned SHAs.

---

## 12) Plugin API (for Host Apps)

**Discovery**

```ts
// host requests recommendation
POST /v1/recommend
{
  "project_root": "/path/to/app",
  "hints": {"tasks": ["object_detection"], "prefer_small": true}
}
```

**Response**

```json
{
  "hardware": {...},
  "tasks": ["object_detection","captioning"],
  "top_pipeline": {...},
  "alternatives": [ ... ],
  "ask_consent": true
}
```

**Download**

```ts
POST /v1/download
{ "pipeline_id": "abc123", "target_dir": "models/" }
```

(When embedded locally, these are plain function calls; HTTP is optional.)

---

## 13) Roadmap

* **v1.0**: CV tasks (tagging/detection/segmentation/captioning); ONNX & FP16; HF provider; CLI + desktop UI; small-first bias.
* **v1.1**: INT8 paths (CPU-first), GitHub/ModelScope providers, history view, better freshness metrics.
* **v1.2**: Speech (ASR/TTS) + OCR; model “capability matrix”; per-task micro-benchmarks.
* **v2.0**: Cross-platform helper SDK for Unity/Unreal; per-project telemetry opt-in; team policies.

---

## 14) Documentation & Packaging

* Ship with a **short, clear guide** and demo projects; screenshots; tooltips; consistent KS branding. (Teach as you ship; package cleanly.) 
* UI follows **dark-mode best practices** and **accessibility** guidance (contrast, calm motion, theme toggle). 

---

## 15) “Concise Agent Prompt” (baked into the app)

> Analyze the selected application directory to infer its ML tasks and whether it needs multiple models. Detect CPU cores, RAM, GPU model and VRAM; classify hardware into {cpu_only, edge_4g, mid_8g, pro_12g, max}. Search trusted hubs for models matching each task, **favoring smaller file sizes**, ONNX/FP16/INT8 readiness, and permissive licenses. Rank candidates by hardware fit, size, popularity, freshness, and reported quality. Compose a compatible, multi-model pipeline and estimate disk, VRAM, and latency. Present the top pipeline with rationale, then—on consent—download to `models/` and write a project config with pinned SHAs.

---

### Final Notes

* Keep it **simple to operate**, **modular to extend**, and **clear to understand**—aligning with KS creation ethos and UX polish standards.  

