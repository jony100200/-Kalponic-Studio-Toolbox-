# KSThumbSmith — Unity Prefab Thumbnailer (Editor)

Lightweight Unity Editor tools to batch-generate thumbnails (icons/previews) for prefabs.
This small Editor extension exposes a scrollable window UI and a robust controller that stages
prefabs in a scene, frames them, renders thumbnails and writes image files to disk.

Location in this repo
- `Unity/Unity-KSThumbSmith/Editor/KSThumbsmith/` — Editor code (window, controller, services)
  - `ThumbnailerWindow.cs` — EditorWindow UI (menu entry, queue, presets, run controls)
  - `ThumbnailConfig.cs` — config model and defaults
  - `ThumbnailController.cs` — orchestration and events (OnProgress/OnLog/OnError/OnCompleted)
  - `SceneStager.cs` — scene staging and temporary scene management
  - `PrefabFramer.cs` — prefab instantiation and framing helpers
  - `RendererAndFileServices.cs` — rendering and file writing services

Quick overview
- Purpose: create consistent thumbnail images for prefabs (UI icons, marketing images, catalog
  renders, documentation art) directly from the Unity Editor.
- Open the tool from the menu: `Kalponic -> KSThumbSmith`.
- The window provides a queue-based workflow for batch runs, drag-and-drop folders, presets,
  multi-angle capture, adjustable resolution, and safe output options.

Recent additions
----------------
- Queue header controls: you can now quickly add multiple blank queue entries using the numeric "Add entries:" field (enter a number and press Add). There are also quick actions for "Clear Disabled", "Select All" and "Clear All" (Clear All shows a confirmation dialog).
- Drag-and-drop parent folder -> auto-create entries: drop a parent folder onto the main *Input Folder* drag area and the window will detect subfolders and offer to create one queue entry per subfolder (Create Entries / Use as Input Folder Only / Cancel). Newly-created entries are enabled by default and will use the subfolder name as the entry name. If you have a global Output Folder set, each entry will by default use a sibling output subfolder.
- Safety: the auto-create flow prompts before creating very large numbers of entries and will not touch your project unless you confirm.


Supported workflow highlights
- Queue entries: add input/output pairs to build batch jobs. Each queue entry can be
  individually edited, reordered, and run.
- Drag-and-drop: drop folders into the input/output fields for quick selection.
- Presets: built-in quick presets (UI Icons, Marketing, Documentation, Catalog) to tune
  resolution, framing and naming conventions.
- Output controls: resolution selection (256/512/1024/2048), filename suffix, Force PNG
  (preserve alpha), Mirror input folder structure, Skip if output exists.
- Multi-angle capture: capture front/side/back views and save into angle-named subfolders.

How to install
1. Copy the `Editor/KSThumbsmith` folder into your project under `Assets/Editor/` or
   keep it under `Assets/KalponicGames/Editor/` as provided. The scripts are Editor-only.
2. Open Unity and wait for compilation.
3. Open the window: Unity menu -> `Kalponic -> KSThumbSmith`.

Basic usage (step-by-step)
1. Open KSThumbSmith from the `Kalponic` menu.
2. Add one or more Queue Entries:
   - Click `Add Entry` to add an input/output pair.
   - Set the Input Folder to the folder that contains your prefabs.
   - Set the Output Folder where thumbnails will be saved.
3. Configure output options:
   - Choose `Resolution` (256/512/1024/2048).
   - Toggle `Force PNG Export` to keep alpha transparency.
   - Enable `Mirror Input Folder Structure` to preserve relative paths.
   - Enable `Skip If Output Exists` to avoid re-rendering.
4. (Optional) Choose Camera & Framing options and multi-angle capture.
5. Run an individual entry with `Run` or run the whole queue with `Run Queue`.

Window details & UI notes
- The window uses a scroll view so it adapts to different resolutions and editor layouts.
- Default window minimum size is set to 480×300 and opens at a comfortable default size.
- The Queue shows estimated prefab counts and total captures (based on selected angles).
- Drag-and-drop areas allow quick folder selection — drop a folder onto the `Drop In` or
  `Drop Out` targets in the queue entry.

Automation and extensibility
- The core orchestration is implemented in `ThumbnailController` and exposes events:
  - `OnProgress(float fraction, string message)`
  - `OnLog(string message)`
  - `OnError(string message, Exception e)`
  - `OnCompleted()`

- If you want to script thumbnail generation from editor scripts, you can:
  - Instantiate `ThumbnailConfig` and `ThumbnailController` and call the controller API, or
  - Use the services (`SceneStager`, `PrefabFramer`, `RendererService`, `FileService`) to
    implement custom flows.

Implementation notes for contributors
- The UI window wires the controller to services via simple interfaces (see top of files):
  - `ISceneStager`, `IPrefabFramer`, `IRendererService`, `IFileService`.
- Unit-testable components: `PrefabFramer` and `ThumbnailController` have clear boundaries.
- The code uses safe scene staging: prefabs are instantiated in a temporary staging scene and
  cleaned up after rendering to avoid polluting the main scene.

Troubleshooting & tips
- If thumbnails don't appear or files are missing:
  - Verify the input folder contains prefab files (.prefab) and the output folder is writable.
  - Check the Unity Console for log messages emitted by the tool.
- If captures look too small or cut off:
  - Adjust `Margin`, `Camera Mode` (Orthographic vs Perspective) and `Perspective FOV`.
  - Use the `Force PNG Export` option to retain transparency.
- If the tool is slow on first runs: Unity may need to compile shaders or warm GPU resources.

License
- The Unity editor scripts in this folder follow the repository license. See the top-level
  `LICENSE` file in the repo for full terms (MIT by default for this project).

Contact & contribution
- If you want features (new presets, different framing strategies, or improved file I/O),
  open an issue or create a pull request. Keep changes focused and provide small tests or
  example scenes when adding framing logic.

Enjoy — the tool is intended to speed up generating consistent thumbnails for UI, catalog
images and marketing assets directly from your Unity project.
