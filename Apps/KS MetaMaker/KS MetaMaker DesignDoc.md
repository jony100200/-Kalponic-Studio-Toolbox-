> 🧠 **KS MetaMaker** — “Tag. Name. Organize. Simplify.”

It will follow the same structure as your KS suite documents (Sprite Splitter, SnapStudio) and adhere to **KISS** and **SOLID** principles throughout.

---

# KS MetaMaker — Design Document (v1)

> **Purpose:**
> Automate the understanding, tagging, renaming, and organizing of visual assets (images, textures, props, backgrounds, renders) into structured, dataset-ready folders — all offline and customizable.

---

## 1️⃣ Overview

**KS MetaMaker** is an **AI-assisted local utility** that:

* Reads images from user folders
* Detects **what they contain** (props, backgrounds, characters)
* Generates **meaningful tags**
* Renames files intelligently (prefix, style, tag-based)
* Organizes outputs into category folders
* Creates **paired `.txt` files** for dataset or LoRA training
* Optionally packages everything for export (zip, CSV, JSON)

---

## 2️⃣ Guiding Principles

| Principle                         | Application                                                                                                               |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **KISS** (Keep It Simple & Smart) | Single-click automation: Drop → Tag → Organize. Clean UI, minimal steps.                                                  |
| **SOLID**                         | Modular design for independent features (tagging, renaming, organizing). Each class or script handles one responsibility. |
| **Automation First**              | Every repeated task (rename, tag, move, caption) happens automatically.                                                   |
| **Offline & Private**             | Runs entirely local — no uploads, no dependencies on cloud APIs.                                                          |
| **Template Driven**               | Predictable output: user-defined schema ensures dataset consistency.                                                      |
| **Interoperable**                 | Follows KS suite standards (context JSON, folder layout, logging).                                                        |

---

## 3️⃣ Core Objectives

1. Save creators, dataset builders, and artists **time** on asset cleanup.
2. Produce **machine- and human-friendly** naming and tagging formats.
3. Work **offline** with fast ONNX models.
4. Be **configurable** through presets and YAML templates.
5. Output **LoRA / dataset-ready** folders with no extra manual work.

---

## 4️⃣ Pipeline

1. **Ingest**

   * Read images (any format: PNG, JPG, WEBP, etc.)
   * Hash and index files for duplicate detection
   * Extract basic info (size, orientation, color palette)

2. **Classification & Tagging (AI)**

   * Run model registry (`OpenCLIP`, `YOLOv11`, `BLIP2`)
   * Identify **type** → prop / background / character
   * Extract up to N tags (category-specific count rules)
   * Optional style tagging (cinematic, 4k, stylized)

3. **Renaming & Organization**

   * Apply name template: `{category}_{top_tags}_{date}_{index}`
   * Move into target folders by class: `/Props/`, `/Backgrounds/`, `/Characters/`
   * Remove redundant words and invalid symbols.

4. **Export**

   * Generate paired `.txt` (same filename) for LoRA training
   * Write `metadata.json` and `tags_summary.csv`
   * Optional dataset `.zip` for direct sharing.

5. **Review / History**

   * UI view of runs (tags, folder locations, rename log)
   * Undo or reapply last rename.

---

## 5️⃣ AI Models

| Task                 | Model                                           | Why                                            |
| -------------------- | ----------------------------------------------- | ---------------------------------------------- |
| Tag & classification | **OpenCLIP (ViT-H/14)**                         | Strong semantic understanding, ONNX compatible |
| Object detection     | **YOLOv11-seg (Ultralytics)**                   | Fast, precise, detects multiple visible props  |
| Captioning           | **BLIP2**                                       | Human-like descriptions when tags are sparse   |
| Blur/quality filter  | **Variance of Laplacian + Aesthetic Predictor** | Detect unusable or poor-quality images         |
| Duplicate detection  | **Perceptual hash (phash)**                     | Finds near-identical copies quickly            |

All models run locally via **ONNX Runtime / CUDA / CPU fallback**.

---

## 6️⃣ Category-Specific Tag Rules

| Type                           | Tag Range | Priority Tags               | Example                                   |
| ------------------------------ | --------- | --------------------------- | ----------------------------------------- |
| **Props / Objects**            | 10–20     | Material, shape, function   | `metal barrel, rusty, industrial, 4k`     |
| **Backgrounds / Environments** | 10–25     | Scene, mood, lighting, time | `city skyline, night, neon, rainy`        |
| **Characters (optional)**      | 15–30     | Pose, clothing, style       | `female knight, armor, fantasy, detailed` |

---

## 7️⃣ Core Features (Top 5 In-Boundary)

### 1. **Smart Auto-Tagging & Captioning**

* Template-based prefix (`kalponic studio background`) + style descriptor (`cinematic lighting`) + auto tags.
* Category-based tag limits (10–30).
* Outputs paired `.txt` files matching filenames.

### 2. **Intelligent Renaming**

* Replace meaningless names (`IMG_1234`) with structured patterns.
* Templates: `{category}_{top_tags}_{YYYYMMDD}_{counter}`.
* Batch rename logs for undo.

### 3. **Auto-Organization**

* Move files by detected type:

  ```
  /Props/
  /Backgrounds/
  /Characters/
  ```
* Option to create date folders:

  ```
  /Output/2025-10-14/Backgrounds/
  ```

### 4. **Duplicate & Quality Filter**

* Remove or flag duplicates (hash comparison).
* Detect blur or low-res files (Laplacian variance).
* Keep only the best-quality variant per group.

### 5. **Smart Pack (Dataset Exporter)**

* Bundle processed images + tags + metadata into ready-to-train LoRA set.
* Optional `.zip`, `.csv`, or `.json` summary for quick upload.

---

## 8️⃣ Optional Add-ons (Future)

* **Color palette extractor** (top 3–5 colors as tags).
* **Aspect ratio sorter** (landscape, square, portrait).
* **Simple tag search/filter panel**.
* **Multilingual tag translation (optional local model)**.

---

## 9️⃣ Folder Structure

```
ks-metamaker/
├─ app/
│  ├─ main.py
│  ├─ ui/
│  ├─ widgets/
│  ├─ qss/
│  └─ icons/
├─ ks_metamaker/
│  ├─ __init__.py
│  ├─ ingest.py
│  ├─ classify.py
│  ├─ tagger.py
│  ├─ rename.py
│  ├─ organize.py
│  ├─ export.py
│  ├─ quality.py
│  ├─ utils/
│  │   ├─ hash_tools.py
│  │   ├─ image_ops.py
│  │   ├─ textclean.py
│  │   ├─ logging.py
│  │   └─ config.py
│  └─ registry/
│      ├─ model_loader.py
│      └─ tag_templates.yml
├─ models/
│  ├─ openclip_vith14.onnx
│  ├─ yolov11.onnx
│  └─ blip2.onnx
├─ configs/
│  ├─ config.yml
│  └─ presets/
│      ├─ props.yml
│      ├─ backgrounds.yml
│      └─ characters.yml
├─ output/
│  └─ Run_YYYYMMDD_HHMM/
│      ├─ Props/
│      ├─ Backgrounds/
│      ├─ Characters/
│      ├─ metadata.json
│      ├─ tags_summary.csv
│      └─ logs/
├─ tests/
│  ├─ test_tagger.py
│  ├─ test_rename.py
│  ├─ test_quality.py
│  └─ data/
├─ scripts/
│  ├─ download_models.py
│  ├─ demo_run.sh
│  └─ bench.py
├─ samples/
├─ README.md
└─ pyproject.toml
```

---

## 🔧 Example Config (`configs/config.yml`)

```yaml
main_prefix: "kalponic studio background"
style_preset: "cinematic lighting, 4k render"
max_tags:
  props: 20
  backgrounds: 25
  characters: 30
rename_pattern: "{category}_{main_tag}_{YYYYMMDD}_{index}"
models:
  tagger: "openclip_vith14.onnx"
  detector: "yolov11.onnx"
  captioner: "blip2.onnx"
performance:
  threads: 4
  batch_size: 4
export:
  paired_txt: true
  rename_images: true
  package_zip: true
  write_metadata: true
```

---

## 🧠 Data Output Example

### **Before**

```
IMG_5242.jpg
```

### **After**

```
background_skyline_neon_20251014_001.jpg
background_skyline_neon_20251014_001.txt
```

**.txt content:**

```
kalponic studio background, cinematic lighting, night city skyline, neon lights, wet streets, reflections, futuristic, urban, 4k render
```

---

## 🔍 CLI Example

```
ks-metamaker \
  --input ./Unsorted \
  --out ./Output \
  --preset backgrounds \
  --rename true \
  --organize true \
  --export dataset \
  --threads 6
```

---

## 📦 Example Run Output

```
/Output/Run_2025-10-14/
├─ Backgrounds/
│  ├─ kalponic_studio_background_001.png
│  ├─ kalponic_studio_background_001.txt
│  ├─ kalponic_studio_background_002.png
│  └─ kalponic_studio_background_002.txt
├─ Props/
│  ├─ kalponic_studio_prop_001.png
│  ├─ kalponic_studio_prop_001.txt
└─ metadata.json
```

---

## ⚙️ Core Interfaces (SOLID)

```python
class Tagger(Protocol):
    def tag(self, image: np.ndarray) -> List[str]:
        """Return a ranked list of tags"""

class Renamer(Protocol):
    def rename(self, file_path: Path, tags: List[str], template: str) -> Path:
        """Return new file path"""

class Organizer(Protocol):
    def move(self, file_path: Path, category: str) -> Path:
        """Move file to destination folder"""

class Exporter(Protocol):
    def save(self, img_path: Path, tags: List[str], caption: str) -> None:
        """Write paired text + metadata"""
```

---

## 📈 Quality Metrics

| Metric                   | Target                           |
| ------------------------ | -------------------------------- |
| Tagging accuracy         | ≥85 % top-10 match               |
| Duplicate recall         | ≥95 % identical images detected  |
| Naming consistency       | 100 % unique names per run       |
| Blur detection precision | ≥90 %                            |
| Runtime                  | ≤1 s per image (GPU), ≤3 s (CPU) |

---

## ⚡ Performance

* Batch inference via ONNX Runtime CUDA.
* Parallel renaming/organizing via `ThreadPoolExecutor`.
* Asynchronous export logging.

---

## 🔒 Privacy & Offline

* No network calls.
* No telemetry by default.
* Local cache for models and configs only.

---

## 💼 Commercial & Practical Use Cases

| User                | Benefit                                   |
| ------------------- | ----------------------------------------- |
| Game / VFX studio   | Organize props and textures into datasets |
| AI model trainers   | Create LoRA-ready paired datasets         |
| Designers / Artists | Clean up downloaded reference folders     |
| Researchers         | Build labeled datasets for CV experiments |

---

## 🚀 Roadmap

| Version | Features                                     |
| ------- | -------------------------------------------- |
| v1.0    | Auto-tagging, renaming, organizing, export   |
| v1.1    | Color palette, tag search/filter, duplicates |
| v1.2    | Template manager GUI (PySide6)               |
| v1.3    | Multilingual tag translation                 |
| v2.0    | Integration with KS Suite SuperApp           |

---

## ✅ Summary

**KS MetaMaker** becomes the intelligent backbone of your KS ecosystem:

* Organizes messy folders
* Creates dataset-ready metadata
* Works offline
* Respects KISS and SOLID
* Scales easily with your future tools

It directly **saves hours** for creators, dataset builders, and small studios while fitting perfectly into your “KS Automation” brand.

---