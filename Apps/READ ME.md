# 🧰 Toolbox

This folder collects all our previous scripts, mini-apps, and utility tools.  
The goal: make it easy to reference, reuse, and eventually integrate any of these into our main app pipeline.

---

## 📦 Contents

Example Names not actual names. See the script name themeselves to what they are named and their folders

| Script / App Name          | Description                                    | Status      | Notes / Pipeline Integration Plans         |
|----------------------------|------------------------------------------------|-------------|--------------------------------------------|
| `audio_to_text.py`         | Converts audio/video files to text using Whisper| Working     | To be pipelined into new voice automation  |
| `batch_renamer.py`         | Renames files in bulk based on rules           | Working     | Useful for asset organization modules      |
| `json_to_markdown.py`      | Converts JSON output to Markdown summaries     | Working     | Can be chained after LLM summarization     |
| `youtube_downloader.py`    | Downloads videos for offline transcription     | Prototype   | Integrate as input source for pipelines    |
| `data_cleaner.py`          | Cleans text or code files before processing    | Working     | Use before analysis or summarization nodes |
| ...                        | ...                                            | ...         | ...                                        |

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