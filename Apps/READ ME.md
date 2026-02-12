# 🧰 Toolbox

This folder collects all our previous scripts, mini-apps, and utility tools.  
The goal: make it easy to reference, reuse, and eventually integrate any of these into our main app pipeline.

---

## 📦 Apps & Descriptions

Below are the **apps and scripts** in this folder with a short description and the primary interface (GUI / CLI / script).

- `Area_Screenshot_Tool.py` — Interactive area screenshot tool with GUI overlay, multi-monitor support, and sequential naming. (GUI)
- `Batch BG Remover/` — Batch background removal with GUI and CLI, retry/manifest support and modular processors. (GUI + CLI; Working)
- `Batch-cleanup tool/` — Fringe removal and alpha edge refinement for AI cutouts (CustomTkinter GUI). (GUI; Working)
- `FastPBR_MapMaker/` — Single-file PBR map helper script for quick map generation. (Script / Prototype)
- `ImageResize/` — Batch image resizer with GUI and CLI, presets, and configuration. (GUI + CLI; Working)
- `KS AutoModel/` — Automatic model discovery & recommendation system (design doc & core layout present; UI not implemented). (Design / WIP)
- `KS MetaMaker/` — AI-powered tagging/organizing/renaming tool for asset datasets (GUI + CLI). (Working)
- `KS SnapStudio/` — Capture, mask, watermark and export circular previews for materials (GUI + CLI). (Working)
- `KS Sprite Splitter/` — AI-assisted sprite segmentation, part splitting, and matting (GUI + CLI; needs functional verification). (WIP / Needs tests)
- `KSTexturePresentation/` — Icon/sprite sheet generator and sprite sheet maker/splitter (GUI + CLI). (Working)
- `KS_PDF_Extractor_Archived/` — Archived PDF extraction utilities (archived). (Archived)
- `KS_PDF_Studio/` — Production-ready PDF tooling (API server, batch processing, web UI). (Working)
- `KS_Seamless_Checker/` — Seamless / tileability checker with previews, batch mode and export. (GUI; Working)
- `Local AI Model Laucher/` — Helper scripts for analyzing codebases & model readiness (no UI; CLI scripts). (WIP)
- `Model Launcher/` — Model picker / launcher UI (CustomTkinter) for GGUF / Whisper models. (GUI; Working)
- `Pathline/` — Path planning / visualization (folder currently empty — needs implementation). (WIP)
- `PromptSender2ChatGP/` — Small CLI to send prompts and images to a local ChatGPT-style server. (CLI; Working)
- `sprite_sheet_splitter/` — Almost-empty folder (placeholder for splitter tools). (Empty / WIP)
- `TranscriptMaker/` — Batch transcription using Faster-Whisper; CLI-only (no GUI). (CLI; Working but no UI)
- `Universal Model Launcher/` — Full-featured model manager and GUI (Versioned; V4 present). (GUI; Working)
- `zip_image_extractor/` — UI + script to extract images from ZIP files. (GUI; Working)
- Utility scripts: `RemoveSuffix.py` — filename suffix remover (CLI utility)

---

## ✅ Status: What works & what is WIP

### ✅ Working / Stable
- `Area_Screenshot_Tool.py` — GUI screenshot tool (works; interactive overlay). ✅
- `Batch BG Remover/` — GUI + CLI batch background removal (tested entrypoints & README). ✅
- `Batch-cleanup tool/` — Fringe removal and alpha refinement (GUI present and documented). ✅
- `ImageResize/` — Batch resizer with GUI & CLI, presets and tests. ✅
- `KS MetaMaker/` — AI-driven tagging & dataset exporter (readme, tests present). ✅
- `KS SnapStudio/` — Material preview capture & export (GUI + CLI documented). ✅
- `KSTexturePresentation/` — Icon/sprite utilities (GUI + CLI). ✅
- `KS_PDF_Studio/` — PDF processing suite with API & web interface. ✅
- `KS_Seamless_Checker/` — Seam/tile checker with GUI and tests. ✅
- `Model Launcher/` — Model picker UI for local models. ✅
- `Universal Model Launcher/` — V4 GUI + loader present (feature-rich). ✅
- `PromptSender2ChatGP/` — Prompt & image sender to local ChatGP-style servers. ✅
- `zip_image_extractor/` — ZIP image extractor with UI. ✅
- `RemoveSuffix.py` — CLI filename utility (works). ✅
- `TranscriptMaker/` — Batch transcription using faster-whisper (CLI works). ✅

### ⚠️ WIP / Needs verification or UI
- `KS AutoModel/` — **WIP**: design document and core modules present; **no polished UI** yet. Action: implement minimal UI + plugin API. ⚠️
- `Local AI Model Laucher/` — **WIP**: helper scripts and prompts exist; **no launcher UI**. Action: consolidate with `Model Launcher` or Universal launcher. ⚠️
- `KS Sprite Splitter/` — **Needs verification**: has README & GUI launcher but **needs integration tests and runtime validation** on sample sprites. ⚠️
- `Pathline/` — **Empty / Placeholder**: no code. Action: decide scope or remove placeholder. ⚠️
- `sprite_sheet_splitter/` — **Empty**: placeholder only. Action: either remove or implement splitting logic. ⚠️
- `FastPBR_MapMaker/` — **Prototype script**: useful but minimal UX; consider adding tests or CLI args. ⚠️

### Priority next steps
1. Create short issues/tickets for each WIP item (UI, tests, integration). ✅
2. Triage and assign owners; prefer small PRs focused on tests or small UI shims. ✅
3. Decide whether to consolidate `Local AI Model Laucher` into `Model Launcher` / `Universal Model Launcher` (saves duplication). ✅
4. Add a short validation test (smoke test) for `KS Sprite Splitter` and `KS AutoModel` workflows to confirm basic behavior. ✅

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