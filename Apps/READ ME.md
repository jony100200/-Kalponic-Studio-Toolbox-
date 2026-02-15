# 🧰 Toolbox

This folder collects all our previous scripts, mini-apps, and utility tools.  
The goal: make it easy to reference, reuse, and eventually integrate any of these into our main app pipeline.

---

## 📦 Apps & Descriptions

Below are the **apps and scripts** in this folder with a short description and the primary interface (GUI / CLI / script).

- `KS SnapClip/` — Clipboard-first screenshot tool (area/fullscreen capture, history, copy to clipboard). (GUI; MVP)
- `KS_CodeOps/` — VS Code multi-worker orchestration runtime (GUI + CLI; active development).
- `PromptSender2VSCode/` — Prompt sender workflow for VS Code chat targets (GUI + CLI utilities).
- `Batch BG Remover/` — Batch background removal with GUI + CLI, retry/manifest support and modular processors. (GUI + CLI)
- `Batch-cleanup tool/` — Fringe removal and alpha edge refinement for AI cutouts. (GUI)
- `FastPBR_MapMaker/` — Single-file PBR map helper script for quick map generation. (Script / Prototype)
- `ImageResize/` — Batch image resizer with GUI + CLI, presets and tests. (GUI + CLI)
- `KS AutoModel/` — Model discovery/recommendation project with design and core modules; still maturing. (WIP)
- `KS MetaMaker/` — AI-powered tagging/organizing/renaming tool for asset datasets. (GUI + CLI)
- `KS SnapStudio/` — Capture/mask/watermark/export workflow for material previews. (GUI + CLI)
- `KS Sprite Splitter/` — AI-assisted sprite segmentation and part splitting. (GUI + CLI)
- `KSTexturePresentation/` — Icon/sprite sheet generator and splitter tools. (GUI + CLI)
- `KS_PDF_Extractor_Archived/` — Archived PDF extraction utilities. (Archived)
- `KS_PDF_Studio/` — PDF tooling suite (API/server + processing components). (WIP)
- `KS_Seamless_Checker/` — Seam/tileability checker with preview and batch/export workflow. (GUI)
- `Local AI Model Laucher/` — Helper scripts for model/codebase analysis. (CLI scripts / WIP)
- `Model Launcher/` — Local model picker/launcher UI (GGUF/Whisper focused). (GUI)
- `PromptSender2ChatGP/` — CLI sender for prompts/images to local ChatGPT-style endpoint. (CLI)
- `TranscriptMaker/` — Batch transcription using Faster-Whisper. (CLI)
- `Universal Model Launcher/` — Full-featured model manager/launcher. (GUI)
- `zip_image_extractor/` — Extract images from ZIP archives. (GUI + script)
- Utility script: `RemoveSuffix.py` — filename suffix remover. (CLI utility)
- Packaging artifact: `PromptSender2ChatGP.zip`

---

## ✅ Status: What works & what is WIP

### ✅ Verified working / stable (current confidence)
- `ImageResize/`
- `PromptSender2ChatGP/`
- `KS SnapClip/` (MVP with minor hardening still useful)

### ⚠️ Working but needs hardening / broader verification
- `Batch BG Remover/`
- `Batch-cleanup tool/`
- `KSTexturePresentation/`
- `Model Launcher/`
- `Universal Model Launcher/`
- `zip_image_extractor/`
- `TranscriptMaker/`
- `KS MetaMaker/`
- `KS_Seamless_Checker/`
- `KS Sprite Splitter/`
- `KS_CodeOps/`
- `PromptSender2VSCode/`

### 🚧 Blocked / currently failing critical paths
- `KS SnapStudio/`
- `KS_PDF_Studio/`

### 🗃️ Archived / prototype / early stage
- `KS_PDF_Extractor_Archived/` (archived)
- `FastPBR_MapMaker/` (prototype)
- `KS AutoModel/` (early stage)
- `Local AI Model Laucher/` (early scripts)

### Priority next steps (updated)
1. Fix blockers first: `KS SnapStudio` and `KS_PDF_Studio` with reproducible smoke tests.
2. Keep one-line `STATUS.md` in each app to avoid root README drift.
3. Consolidate overlapping launcher tools (`Local AI Model Laucher` vs `Model Launcher` / `Universal Model Launcher`).
4. Add/maintain smoke tests for `KS_CodeOps`, `PromptSender2VSCode`, `KS Sprite Splitter`, and `KS MetaMaker`.

---


## 💡 How to Use

- Each script/app here can be run independently.
- When upgrading the main pipeline, check here for modules or logic to reuse.
- If you update/fix a tool, please document it here.

---

## 🗂️ Integration Notes

- Scripts here are candidates for full module integration in the central pipeline.
- When integrating, refactor and add tests as needed.
- Mark “integrated” or “deprecated” as the pipeline evolves.

---

## 📝 Contribution

- Add new scripts in this folder as you create them.
- Update this README with a short description and notes.