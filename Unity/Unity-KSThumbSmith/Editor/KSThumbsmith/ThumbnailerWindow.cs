// Assets/KalponicGames/Editor/Thumbnailer/ThumbnailerWindow.cs
// Prefab Thumbnailer — Editor UI wired to the real controller and services.
// Features scroll view for responsive UI across different screen resolutions.

using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KalponicGames
{
    public sealed class ThumbnailerWindow : EditorWindow
    {
        private const string WINDOW_TITLE = "KSThumbSmith";
        private const int LABEL_WIDTH = 120;

        // Config & state
        private ThumbnailConfig config;
        private bool showAdvanced = false;
        private bool showPresets = false;
    private int newEntryCount = 1; // number of entries to add when requested
        private float progress = 0f;
        private string statusText = "Idle";
        private bool isRunning = false;
        private string lastProcessedAsset = "";
    private bool isQueueRunning = false;
    private int queueIndex = -1;
    private int queueTotal = 0;
        private DateTime batchStartTime;
        private Vector2 scrollPosition = Vector2.zero; // Scroll position for UI

        // Services & controller
        private ISceneStager sceneStager;
        private IPrefabFramer prefabFramer;
        private IRendererService rendererService;
        private IFileService fileService;
        private ThumbnailController controller;

        #region Menu
        [MenuItem("Kalponic/KSThumbSmith")]
        public static void Open()
        {
            var win = GetWindow<ThumbnailerWindow>(utility: false, title: WINDOW_TITLE);
            // Set reasonable minimum size that works with scroll view
            win.minSize = new Vector2(480, 300);
            // Set a good default size for most workflows
            win.position = new Rect(100, 100, 520, 600);
            win.Show();
        }
        #endregion

        private void OnEnable()
        {
            config ??= ThumbnailConfig.Default();
            BuildServicesIfNeeded();
        }

        private void OnDisable()
        {
            UnhookController();
        }

        private void BuildServicesIfNeeded()
        {
            if (sceneStager == null)
            {
                sceneStager = new SceneStager();
            }
            if (prefabFramer == null)
            {
                prefabFramer = new PrefabFramer(sceneStager);
            }
            if (rendererService == null)
            {
                rendererService = new RendererService(sceneStager);
            }
            if (fileService == null)
            {
                fileService = new FileService();
            }
            if (controller == null)
            {
                controller = new ThumbnailController(sceneStager, prefabFramer, rendererService, fileService);
                HookController();
            }
        }

        private void HookController()
        {
            controller.OnProgress += HandleProgress;
            controller.OnLog += HandleLog;
            controller.OnError += HandleError;
            controller.OnCompleted += HandleCompleted;
        }

        private void UnhookController()
        {
            if (controller == null) return;
            controller.OnProgress -= HandleProgress;
            controller.OnLog -= HandleLog;
            controller.OnError -= HandleError;
            controller.OnCompleted -= HandleCompleted;
        }

        private void OnGUI()
        {
            EditorGUIUtility.labelWidth = LABEL_WIDTH;

            // Begin scroll view to handle different window sizes and resolutions
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
            
            try
            {
                // Add some padding for better visual spacing
                EditorGUILayout.Space(4);

                // Queue Editor (moved to top)
                using (new EditorGUILayout.VerticalScope("box"))
                {
                    GUILayout.Label("Queue", EditorStyles.boldLabel);

                    using (new EditorGUILayout.HorizontalScope())
                    {
                        // Numeric input to add multiple entries quickly
                        GUILayout.Label("Add entries:", GUILayout.Width(80));
                        newEntryCount = EditorGUILayout.IntField(newEntryCount, GUILayout.Width(60));
                        newEntryCount = Mathf.Clamp(newEntryCount, 1, 1000);

                        if (GUILayout.Button("Add", GUILayout.Width(64)))
                        {
                            for (int k = 0; k < newEntryCount; k++)
                            {
                                config.inputQueue.Add(new ThumbnailConfig.QueueEntry());
                            }
                        }

                        if (GUILayout.Button("Clear Disabled", GUILayout.Width(120)))
                        {
                            config.inputQueue.RemoveAll(e => !e.enabled);
                        }

                        if (GUILayout.Button("Select All", GUILayout.Width(90)))
                        {
                            for (int si = 0; si < config.inputQueue.Count; si++)
                            {
                                config.inputQueue[si].enabled = true;
                            }
                        }

                        if (GUILayout.Button("Clear All", GUILayout.Width(90)))
                        {
                            if (EditorUtility.DisplayDialog("Clear All Queue Entries", "Remove all queue entries? This cannot be undone.", "Yes", "No"))
                            {
                                config.inputQueue.Clear();
                            }
                        }

                        GUILayout.FlexibleSpace();
                    }

                    // List entries
                    for (int i = 0; i < config.inputQueue.Count; i++)
                    {
                        var e = config.inputQueue[i];
                        using (new EditorGUILayout.HorizontalScope())
                        {
                            e.enabled = EditorGUILayout.ToggleLeft(string.Empty, e.enabled, GUILayout.Width(18));
                            e.name = EditorGUILayout.TextField(e.name, GUILayout.Width(110));

                            // Input folder with pick and drag-drop
                            e.inputFolder = EditorGUILayout.TextField(e.inputFolder);
                            if (GUILayout.Button("Pick...", GUILayout.Width(64)))
                            {
                                var start = string.IsNullOrEmpty(e.inputFolder) ? Application.dataPath : e.inputFolder;
                                var picked = EditorUtility.OpenFolderPanel("Select Input Folder", start, "");
                                if (!string.IsNullOrEmpty(picked)) e.inputFolder = picked;
                            }
                            var dropRectIn = GUILayoutUtility.GetRect(18, 18, GUILayout.Width(80));
                            DrawDragDropArea(dropRectIn, "Drop In", (path) => e.inputFolder = path, true);

                            // Output folder with pick and drag-drop
                            e.outputFolder = EditorGUILayout.TextField(e.outputFolder, GUILayout.Width(220));
                            if (GUILayout.Button("Pick...", GUILayout.Width(64)))
                            {
                                var start = string.IsNullOrEmpty(e.outputFolder) ? Application.dataPath : e.outputFolder;
                                var picked = EditorUtility.OpenFolderPanel("Select Output Folder", start, "");
                                if (!string.IsNullOrEmpty(picked)) e.outputFolder = picked;
                            }
                            var dropRectOut = GUILayoutUtility.GetRect(18, 18, GUILayout.Width(80));
                            DrawDragDropArea(dropRectOut, "Drop Out", (path) => e.outputFolder = path, true);
                            // Show estimated prefab / capture count for this entry (fall back to global input folder)
                            try
                            {
                                string countPath = !string.IsNullOrEmpty(e.inputFolder) ? e.inputFolder : config.inputFolder;
                                if (!string.IsNullOrEmpty(countPath) && Directory.Exists(countPath))
                                {
                                    var prefabCountEntry = GetPrefabCount(countPath);
                                    if (prefabCountEntry > 0)
                                    {
                                        var selectedAngles = config.GetSelectedAngles();
                                        int totalCaptures = prefabCountEntry * Math.Max(1, selectedAngles.Length);
                                        EditorGUILayout.LabelField($"({prefabCountEntry} prefabs, {totalCaptures} captures)", EditorStyles.miniLabel, GUILayout.Width(180));
                                    }
                                    else
                                    {
                                        EditorGUILayout.LabelField("(0 prefabs)", EditorStyles.miniLabel, GUILayout.Width(80));
                                    }
                                }
                                else
                                {
                                    // empty placeholder to keep layout stable
                                    EditorGUILayout.LabelField(string.Empty, GUILayout.Width(180));
                                }
                            }
                            catch
                            {
                                EditorGUILayout.LabelField(string.Empty, GUILayout.Width(180));
                            }

                            // Reorder
                            if (GUILayout.Button("Up", GUILayout.Width(40)) && i > 0)
                            {
                                var tmp = config.inputQueue[i - 1];
                                config.inputQueue[i - 1] = config.inputQueue[i];
                                config.inputQueue[i] = tmp;
                            }
                            if (GUILayout.Button("Down", GUILayout.Width(48)) && i < config.inputQueue.Count - 1)
                            {
                                var tmp = config.inputQueue[i + 1];
                                config.inputQueue[i + 1] = config.inputQueue[i];
                                config.inputQueue[i] = tmp;
                            }

                            // Run single entry
                            GUI.enabled = !isRunning;
                            if (GUILayout.Button("Run", GUILayout.Width(48)))
                            {
                                StartBatch(e);
                            }
                            GUI.enabled = true;

                            if (GUILayout.Button("Remove", GUILayout.Width(64)))
                            {
                                config.inputQueue.RemoveAt(i);
                                i--;
                                continue;
                            }
                        }
                    }

                    EditorGUILayout.Space(4);
                    using (new EditorGUILayout.HorizontalScope())
                    {
                        GUI.enabled = !isRunning && config.inputQueue.Count > 0;
                        if (GUILayout.Button("Run Queue", GUILayout.Height(22)))
                        {
                            StartQueueRun();
                        }
                        GUI.enabled = isRunning;
                        if (GUILayout.Button("Cancel Queue", GUILayout.Height(22)))
                        {
                            CancelBatch();
                        }
                        GUI.enabled = true;
                    }
                }

                // Input folder with drag-and-drop support
            using (new EditorGUILayout.HorizontalScope())
            {
                GUILayout.Label("Input Folder", GUILayout.Width(LABEL_WIDTH));
                using (new EditorGUILayout.VerticalScope())
                {
                    config.inputFolder = EditorGUILayout.TextField(config.inputFolder);
                    
                    // Drag and drop area for input folder
                    var inputRect = GUILayoutUtility.GetRect(0, 20);
                    DrawDragDropArea(inputRect, "Drag folder here or click Pick...", 
                        (path) => config.inputFolder = path, true);
                    
                    using (new EditorGUILayout.HorizontalScope())
                    {
                        if (GUILayout.Button("Pick...", GUILayout.Width(80)))
                        {
                            var startPath = string.IsNullOrEmpty(config.inputFolder) ? Application.dataPath : config.inputFolder;
                            var picked = EditorUtility.OpenFolderPanel("Select Input Folder", startPath, "");
                            if (!string.IsNullOrEmpty(picked))
                            {
                                config.inputFolder = picked;
                            }
                        }
                        
                        // Quick validation feedback
                        if (!string.IsNullOrEmpty(config.inputFolder))
                        {
                            if (Directory.Exists(config.inputFolder))
                            {
                                EditorGUILayout.LabelField("✓", GUILayout.Width(20));
                            }
                            else
                            {
                                EditorGUILayout.LabelField("✗", GUILayout.Width(20));
                            }
                        }
                        
                        GUILayout.FlexibleSpace();
                    }
                }
            }

            // Output folder with drag-and-drop support
            using (new EditorGUILayout.HorizontalScope())
            {
                GUILayout.Label("Output Folder", GUILayout.Width(LABEL_WIDTH));
                using (new EditorGUILayout.VerticalScope())
                {
                    config.outputFolder = EditorGUILayout.TextField(config.outputFolder);
                    
                    // Drag and drop area for output folder
                    var outputRect = GUILayoutUtility.GetRect(0, 20);
                    DrawDragDropArea(outputRect, "Drag folder here or click Pick...", 
                        (path) => config.outputFolder = path, true);
                    
                    using (new EditorGUILayout.HorizontalScope())
                    {
                        if (GUILayout.Button("Pick...", GUILayout.Width(80)))
                        {
                            var picked = EditorUtility.OpenFolderPanel("Select Output Folder", 
                                string.IsNullOrEmpty(config.outputFolder) ? Application.dataPath : config.outputFolder, "");
                            if (!string.IsNullOrEmpty(picked)) config.outputFolder = picked;
                        }
                        
                        // Show estimated count if input is valid
                        if (!string.IsNullOrEmpty(config.inputFolder) && Directory.Exists(config.inputFolder))
                        {
                            var count = GetPrefabCount(config.inputFolder);
                            if (count > 0)
                            {
                                EditorGUILayout.LabelField($"({count} prefabs)", EditorStyles.miniLabel, GUILayout.Width(80));
                            }
                        }
                        
                        GUILayout.FlexibleSpace();
                    }
                }
            }

            EditorGUILayout.Space(6);

            // Preset configurations
            showPresets = EditorGUILayout.Foldout(showPresets, "Quick Presets");
            if (showPresets)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    if (GUILayout.Button("UI Icons", EditorStyles.miniButton))
                        ApplyUIIconPreset();
                    if (GUILayout.Button("Marketing", EditorStyles.miniButton))
                        ApplyMarketingPreset();
                    if (GUILayout.Button("Documentation", EditorStyles.miniButton))
                        ApplyDocumentationPreset();
                    if (GUILayout.Button("Catalog", EditorStyles.miniButton))
                        ApplyCatalogPreset();
                }
            }

            EditorGUILayout.Space(6);

            // Output basics
            using (new EditorGUILayout.VerticalScope("box"))
            {
                GUILayout.Label("Output", EditorStyles.boldLabel);
                config.outputResolution = EditorGUILayout.IntPopup("Resolution",
                    config.outputResolution,
                    new[] { "256", "512", "1024", "2048" },
                    new[] { 256, 512, 1024, 2048 });

                config.filenameSuffix = EditorGUILayout.TextField("Filename Suffix", config.filenameSuffix);
                config.forcePng = EditorGUILayout.ToggleLeft("Force PNG Export (preserve alpha)", config.forcePng);
                config.mirrorFolders = EditorGUILayout.ToggleLeft("Mirror Input Folder Structure", config.mirrorFolders);
                config.skipIfExists = EditorGUILayout.ToggleLeft("Skip If Output Exists", config.skipIfExists);
            }

            EditorGUILayout.Space(6);


            // Camera & framing
            using (new EditorGUILayout.VerticalScope("box"))
            {
                GUILayout.Label("Camera & Framing", EditorStyles.boldLabel);
                config.cameraMode = (ThumbnailConfig.CameraMode)EditorGUILayout.EnumPopup("Camera Mode", config.cameraMode);
                config.orientation = (ThumbnailConfig.Orientation)EditorGUILayout.EnumPopup("Orientation", config.orientation);
                config.margin = EditorGUILayout.Slider("Margin", config.margin, 0f, 0.5f);

                if (config.cameraMode == ThumbnailConfig.CameraMode.Perspective)
                {
                    config.perspectiveFov = EditorGUILayout.Slider("Perspective FOV", config.perspectiveFov, 10f, 90f);
                }

                if (config.orientation == ThumbnailConfig.Orientation.Custom)
                {
                    config.customEuler = EditorGUILayout.Vector3Field("Custom Euler", config.customEuler);
                }
            }

            EditorGUILayout.Space(6);

            // Multi-Angle Capture
            using (new EditorGUILayout.VerticalScope("box"))
            {
                GUILayout.Label("Multi-Angle Capture (2D Side-Scroller)", EditorStyles.boldLabel);
                
                EditorGUILayout.HelpBox("Select multiple angles to capture different views of your prefabs. " +
                    "Each angle will be saved in its own subfolder (Front/Side/Back).", MessageType.Info);
                
                using (new EditorGUILayout.HorizontalScope())
                {
                    config.captureAngleFront = EditorGUILayout.ToggleLeft("Front (0°)", config.captureAngleFront, GUILayout.Width(100));
                    config.captureAngleSide = EditorGUILayout.ToggleLeft("Side (90°)", config.captureAngleSide, GUILayout.Width(100));
                    config.captureAngleBack = EditorGUILayout.ToggleLeft("Back (180°)", config.captureAngleBack, GUILayout.Width(100));
                }
                
                // Show angle count and estimated total
                var selectedAngles = config.GetSelectedAngles();
                string angleInfo = $"{selectedAngles.Length} angle{(selectedAngles.Length != 1 ? "s" : "")} selected";
                if (selectedAngles.Length > 0)
                {
                    var angleNames = string.Join(", ", System.Array.ConvertAll(selectedAngles, a => a.Name));
                    angleInfo += $": {angleNames}";
                }
                EditorGUILayout.LabelField(angleInfo, EditorStyles.miniLabel);
                
                // Show total capture count
                if (!string.IsNullOrEmpty(config.inputFolder) && Directory.Exists(config.inputFolder))
                {
                    var prefabCount = GetPrefabCount(config.inputFolder);
                    if (prefabCount > 0 && selectedAngles.Length > 0)
                    {
                        var totalCaptures = prefabCount * selectedAngles.Length;
                        EditorGUILayout.LabelField($"Total captures: {totalCaptures} ({prefabCount} prefabs × {selectedAngles.Length} angles)", 
                            EditorStyles.miniLabel);
                    }
                }
            }

            EditorGUILayout.Space(6);

            // Advanced
            showAdvanced = EditorGUILayout.Foldout(showAdvanced, "Advanced");
            if (showAdvanced)
            {
                using (new EditorGUILayout.VerticalScope("box"))
                {
                    GUILayout.Label("Background & Lighting", EditorStyles.boldLabel);
                    config.clearColor = EditorGUILayout.ColorField("Clear Color (alpha=0 for transparent)", config.clearColor);
                    config.lightingMode = (ThumbnailConfig.LightingMode)EditorGUILayout.EnumPopup("Lighting", config.lightingMode);
                    config.useShadows = EditorGUILayout.ToggleLeft("Soft Shadows (if lit)", config.useShadows);

                    EditorGUILayout.Space(4);
                    GUILayout.Label("Subject Handling", EditorStyles.boldLabel);
                    config.normalizeScale = EditorGUILayout.ToggleLeft("Normalize Scale (fit largest dimension)", config.normalizeScale);
                    config.includeParticles = EditorGUILayout.ToggleLeft("Include Particle Systems", config.includeParticles);
                    config.forceHighestLod = EditorGUILayout.ToggleLeft("Force Highest LOD", config.forceHighestLod);

                    EditorGUILayout.Space(4);
                    GUILayout.Label("Failure Behavior", EditorStyles.boldLabel);
                    config.failFast = EditorGUILayout.ToggleLeft("Fail Fast (stop on first error)", config.failFast);

                    EditorGUILayout.Space(4);
                    GUILayout.Label("Performance", EditorStyles.boldLabel);
                    config.maxBatchSize = EditorGUILayout.IntField("Max Batch Size (0 = no limit)", config.maxBatchSize);
                    config.memoryCleanupFrequency = EditorGUILayout.IntField("Memory Cleanup Frequency", config.memoryCleanupFrequency);
                }
            }

            EditorGUILayout.Space(8);

            // Run / Cancel
            using (new EditorGUILayout.HorizontalScope())
            {
                GUI.enabled = !isRunning;
                if (GUILayout.Button("Run", GUILayout.Height(28)))
                {
                    StartBatch();
                }
                GUI.enabled = isRunning;
                if (GUILayout.Button("Cancel", GUILayout.Height(28)))
                {
                    CancelBatch();
                }
                GUI.enabled = true;
            }

            // Progress & status
            EditorGUILayout.Space(6);
            
            // Enhanced progress display
            if (isQueueRunning)
            {
                EditorGUILayout.LabelField($"Queue: {Mathf.Clamp(queueIndex + 1, 0, queueTotal)}/{queueTotal}", EditorStyles.miniLabel);
            }
            else if (isRunning && !string.IsNullOrEmpty(lastProcessedAsset))
            {
                EditorGUILayout.LabelField("Currently Processing:", lastProcessedAsset, EditorStyles.miniLabel);
            }
            
            Rect r = GUILayoutUtility.GetRect(18, 18, "TextField");
            EditorGUI.ProgressBar(r, Mathf.Clamp01(progress), statusText);
            EditorGUILayout.Space(2);

            // Debug information
            if (!string.IsNullOrEmpty(lastProcessedAsset))
            {
                EditorGUILayout.LabelField($"Last: {lastProcessedAsset}", EditorStyles.miniLabel);
            }

            using (new EditorGUILayout.HorizontalScope())
            {
                GUILayout.FlexibleSpace();
                if (isRunning)
                {
                    GUILayout.Label("Processing... Press Cancel to stop", EditorStyles.miniLabel);
                }
                else
                {
                    GUILayout.Label("KISS • SOLID • URP • Transparent PNG", EditorStyles.miniLabel);
                }
            }
            
            // Add bottom padding for better scrolling experience
            EditorGUILayout.Space(8);
            }
            finally
            {
                // Always end the scroll view, even if an exception occurs
                EditorGUILayout.EndScrollView();
            }
        }

        // ----------------- Controller hooks -----------------

        private void StartBatch()
        {
            BuildServicesIfNeeded(); // ensure live services

            // Reset UI
            progress = 0f;
            statusText = "Preparing…";
            isRunning = controller.Start(config);

            if (!isRunning)
            {
                statusText = "Failed to start. Check Console.";
                Repaint();
            }
            else
            {
                Repaint();
            }
        }

        private void StartBatch(ThumbnailConfig.QueueEntry entry)
        {
            // Apply entry-specific paths to a temporary config copy
            var backupIn = config.inputFolder;
            var backupOut = config.outputFolder;

            config.inputFolder = string.IsNullOrWhiteSpace(entry.inputFolder) ? backupIn : entry.inputFolder;
            config.outputFolder = string.IsNullOrWhiteSpace(entry.outputFolder) ? backupOut : entry.outputFolder;

            // Start the regular batch
            StartBatch();

            // Restore UI fields will be handled when queue continues/completes
        }

        private void CancelBatch()
        {
            if (!isRunning || controller == null) return;
            // Stop the entire queue when cancelling
            isQueueRunning = false;
            queueIndex = -1;
            queueTotal = 0;
            statusText = "Cancel requested.";
            controller.Cancel();
        }

        private void HandleProgress(ThumbnailProgress p)
        {
            progress = p.Normalized;
            statusText = $"[{p.Index}/{p.Total}] {p.Message}";
            lastProcessedAsset = p.CurrentAssetPath;
            Repaint();
        }

        private void StartQueueRun()
        {
            if (config.inputQueue == null || config.inputQueue.Count == 0) return;

            // Build a list of enabled entries
            var enabled = config.inputQueue.FindAll(e => e.enabled);
            if (enabled.Count == 0)
            {
                statusText = "No enabled queue entries.";
                Repaint();
                return;
            }

            isQueueRunning = true;
            queueIndex = -1;
            queueTotal = enabled.Count;

            // Kick off first item
            StartNextQueueItem();
        }

        private void StartNextQueueItem()
        {
            if (!isQueueRunning)
            {
                queueIndex = -1;
                queueTotal = 0;
                return;
            }

            // Build enabled list each time to reflect any runtime changes
            var enabled = config.inputQueue.FindAll(e => e.enabled);
            queueIndex++;

            if (queueIndex >= enabled.Count)
            {
                // Queue finished
                isQueueRunning = false;
                queueIndex = -1;
                queueTotal = 0;
                statusText = "Queue finished.";
                Repaint();
                return;
            }

            var entry = enabled[queueIndex];
            statusText = $"Queue: {queueIndex + 1}/{enabled.Count} - {entry.name ?? entry.inputFolder}";
            Repaint();

            // Apply entry and start batch
            StartBatch(entry);
        }

        private void HandleLog(string msg)
        {
            Debug.Log("[Thumbnailer] " + msg);
        }

        private void HandleError(string msg)
        {
            Debug.LogError("[Thumbnailer] " + msg);
            statusText = "Error: " + msg;
            Repaint();
        }

        private void HandleCompleted()
        {
            isRunning = false;
            progress = 1f;
            statusText = "Done.";
            Repaint();

            // If we were running a queue, advance to next
            if (isQueueRunning)
            {
                StartNextQueueItem();
            }
        }

        // --------------------- UI Helper Methods ---------------------

        private void DrawDragDropArea(Rect rect, string label, Action<string> onPathDropped, bool acceptFolders)
        {
            var controlID = GUIUtility.GetControlID(FocusType.Passive);
            var eventType = Event.current.type;

            switch (eventType)
            {
                case EventType.DragUpdated:
                case EventType.DragPerform:
                    if (rect.Contains(Event.current.mousePosition))
                    {
                        bool validDrag = false;
                        string draggedPath = null;

                        if (DragAndDrop.paths.Length > 0)
                        {
                            var path = DragAndDrop.paths[0];
                            if (acceptFolders && Directory.Exists(path))
                            {
                                validDrag = true;
                                draggedPath = path;
                            }
                            else if (!acceptFolders && File.Exists(path))
                            {
                                validDrag = true;
                                draggedPath = path;
                            }
                        }

                        if (validDrag)
                        {
                            DragAndDrop.visualMode = DragAndDropVisualMode.Link;
                            if (eventType == EventType.DragPerform)
                            {
                                DragAndDrop.AcceptDrag();
                                onPathDropped?.Invoke(draggedPath);
                                GUI.changed = true;
                            }
                        }
                        else
                        {
                            DragAndDrop.visualMode = DragAndDropVisualMode.Rejected;
                        }
                        Event.current.Use();
                    }
                    break;

                case EventType.Repaint:
                    var style = new GUIStyle(EditorStyles.helpBox)
                    {
                        alignment = TextAnchor.MiddleCenter,
                        fontSize = 10
                    };
                    
                    if (rect.Contains(Event.current.mousePosition) && DragAndDrop.paths.Length > 0)
                    {
                        style.normal.textColor = Color.white;
                        style.normal.background = Texture2D.whiteTexture;
                    }
                    
                    GUI.Box(rect, label, style);
                    break;
            }
        }

        private int GetPrefabCount(string folderPath)
        {
            try
            {
                if (string.IsNullOrEmpty(folderPath) || !Directory.Exists(folderPath))
                    return 0;

                // Convert to project-relative path if possible
                string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
                string fullPath = Path.GetFullPath(folderPath);
                
                if (!fullPath.StartsWith(projectRoot))
                {
                    // Outside project, can't easily count via AssetDatabase
                    return 0;
                }

                string projectPath = fullPath.Substring(projectRoot.Length + 1).Replace('\\', '/');
                
                // Use AssetDatabase to find prefabs
                string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { projectPath });
                return guids.Length;
            }
            catch
            {
                return 0;
            }
        }

        // --------------------- Preset Configurations ---------------------

        private void ApplyUIIconPreset()
        {
            config.outputResolution = 256;
            config.cameraMode = ThumbnailConfig.CameraMode.Orthographic;
            config.orientation = ThumbnailConfig.Orientation.Front;
            config.margin = 0.15f;
            config.lightingMode = ThumbnailConfig.LightingMode.NoneUnlit;
            config.useShadows = false;
            config.normalizeScale = true;
            config.includeParticles = false;
            config.forceHighestLod = true;
            config.clearColor = new Color(0f, 0f, 0f, 0f);
            config.filenameSuffix = "_icon";
            
            // UI icons typically only need front view
            config.captureAngleFront = true;
            config.captureAngleSide = false;
            config.captureAngleBack = false;
            
            Repaint();
        }

        private void ApplyMarketingPreset()
        {
            config.outputResolution = 1024;
            config.cameraMode = ThumbnailConfig.CameraMode.Perspective;
            config.orientation = ThumbnailConfig.Orientation.Isometric;
            config.margin = 0.10f;
            config.lightingMode = ThumbnailConfig.LightingMode.Studio3Point;
            config.useShadows = true;
            config.normalizeScale = false;
            config.includeParticles = true;
            config.forceHighestLod = true;
            config.clearColor = new Color(0f, 0f, 0f, 0f);
            config.filenameSuffix = "_marketing";
            
            // Marketing materials often benefit from multiple angles
            config.captureAngleFront = true;
            config.captureAngleSide = true;
            config.captureAngleBack = false;
            
            Repaint();
        }

        private void ApplyDocumentationPreset()
        {
            config.outputResolution = 512;
            config.cameraMode = ThumbnailConfig.CameraMode.Orthographic;
            config.orientation = ThumbnailConfig.Orientation.Isometric;
            config.margin = 0.20f;
            config.lightingMode = ThumbnailConfig.LightingMode.NoneUnlit;
            config.useShadows = false;
            config.normalizeScale = true;
            config.includeParticles = false;
            config.forceHighestLod = true;
            config.clearColor = new Color(1f, 1f, 1f, 1f); // White background for docs
            config.filenameSuffix = "_doc";
            
            // Documentation typically shows front and side for technical reference
            config.captureAngleFront = true;
            config.captureAngleSide = true;
            config.captureAngleBack = false;
            
            Repaint();
        }

        private void ApplyCatalogPreset()
        {
            config.outputResolution = 512;
            config.cameraMode = ThumbnailConfig.CameraMode.Orthographic;
            config.orientation = ThumbnailConfig.Orientation.Front;
            config.margin = 0.10f;
            config.lightingMode = ThumbnailConfig.LightingMode.NoneUnlit;
            config.useShadows = false;
            config.normalizeScale = true;
            config.includeParticles = false;
            config.forceHighestLod = true;
            config.clearColor = new Color(0f, 0f, 0f, 0f);
            config.filenameSuffix = "_catalog";
            
            // Catalog view typically shows just front view for consistency
            config.captureAngleFront = true;
            config.captureAngleSide = false;
            config.captureAngleBack = false;
            
            Repaint();
        }
    }
}
