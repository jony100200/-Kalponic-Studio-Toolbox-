// Assets/KalponicGames/Editor/Thumbnailer/ThumbnailController.cs
// Batch orchestrator for Prefab Thumbnailer (KISS + SOLID).
// Finds prefabs, iterates work, reports progress, and delegates to services.
// Services are interfaces to be implemented in later scripts.

using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KalponicGames
{
    /// <summary>
    /// Thin, testable config snapshot used by the controller (immutable during run).
    /// </summary>
    public readonly struct ThumbnailRunConfig
    {
        public readonly ThumbnailConfig Config;
        public readonly string InputPathAbs;
        public readonly string OutputPathAbs;
        public readonly int Resolution;

        public ThumbnailRunConfig(ThumbnailConfig cfg, string inputAbs, string outputAbs)
        {
            Config = cfg;
            InputPathAbs = inputAbs;
            OutputPathAbs = outputAbs;
            Resolution = Mathf.Clamp(cfg.outputResolution, 64, 4096);
        }
    }

    /// <summary>
    /// Progress data for UI updates.
    /// </summary>
    public readonly struct ThumbnailProgress
    {
        public readonly int Index;
        public readonly int Total;
        public readonly string CurrentAssetPath;
        public readonly string Message;
        public readonly float Normalized; // 0..1

        public ThumbnailProgress(int index, int total, string path, string message)
        {
            Index = index;
            Total = total;
            CurrentAssetPath = path;
            Normalized = total > 0 ? Mathf.Clamp01((float)index / total) : 0f;
            Message = message;
        }
    }

    /// <summary>
    /// Controller orchestrates the batch and talks to services.
    /// </summary>
    public sealed class ThumbnailController
    {
        // Dependencies (SOLID: injected)
        private readonly ISceneStager sceneStager;
        private readonly IPrefabFramer prefabFramer;
        private readonly IRendererService rendererService;
        private readonly IFileService fileService;

        // Run state
        private bool isRunning;
        private bool cancelRequested;
        private IEnumerator<YieldToken> runner;

        // Performance settings
        private const int DEFAULT_BATCH_SIZE_LIMIT = 1000;
        private const int OPERATIONS_PER_FRAME = 2; // Increased for better performance

        // Events / callbacks for UI
        public event Action<ThumbnailProgress> OnProgress;
        public event Action<string> OnLog;
        public event Action<string> OnError;
        public event Action OnCompleted;
        public bool IsRunning => isRunning;

        public ThumbnailController(
            ISceneStager sceneStager,
            IPrefabFramer prefabFramer,
            IRendererService rendererService,
            IFileService fileService)
        {
            this.sceneStager = sceneStager;
            this.prefabFramer = prefabFramer;
            this.rendererService = rendererService;
            this.fileService = fileService;
        }

        /// <summary>
        /// Start batch run. Returns false if already running or invalid paths.
        /// </summary>
        public bool Start(ThumbnailConfig uiConfig)
        {
            if (isRunning) return false;

            // Validate & normalize
            uiConfig.Validate();
            var inputAbs = ResolveAbsolutePath(uiConfig.inputFolder);
            var outputAbs = ResolveAbsolutePath(uiConfig.outputFolder);

            if (string.IsNullOrWhiteSpace(inputAbs) || !Directory.Exists(inputAbs))
            {
                OnError?.Invoke("Invalid Input Folder.");
                return false;
            }
            if (string.IsNullOrWhiteSpace(outputAbs))
            {
                OnError?.Invoke("Invalid Output Folder.");
                return false;
            }
            Directory.CreateDirectory(outputAbs);

            var rc = new ThumbnailRunConfig(uiConfig, inputAbs, outputAbs);

            // Build worklist
            var prefabAssetPaths = FindPrefabsUnder(inputAbs);
            if (prefabAssetPaths.Count == 0)
            {
                OnLog?.Invoke("No prefabs found under input folder.");
                return false;
            }

            // Create staging scene/resources
            try
            {
                sceneStager.Open(rc);
            }
            catch (Exception e)
            {
                OnError?.Invoke("Failed to open staging scene: " + e.Message);
                return false;
            }

            cancelRequested = false;
            isRunning = true;

            // Create runner coroutine
            runner = RunBatch(rc, prefabAssetPaths).GetEnumerator();

            // Hook editor update loop
            EditorApplication.update += TickRunner;

            OnLog?.Invoke($"Batch started. {prefabAssetPaths.Count} prefabs.");
            return true;
        }

        public void Cancel()
        {
            if (!isRunning) return;
            cancelRequested = true;
            OnLog?.Invoke("Cancel requested…");
        }

        private void TickRunner()
        {
            if (!isRunning) return;

            try
            {
                if (runner != null)
                {
                    // Advance a few steps per tick to keep UI smooth
                    int steps = 1;
                    while (steps-- > 0 && runner.MoveNext())
                    {
                        // noop: YieldToken is just a pacing marker
                    }
                }
                else
                {
                    // Safety: end if runner missing
                    Finish();
                }
            }
            catch (Exception e)
            {
                OnError?.Invoke("Unhandled error in batch: " + e.Message);
                Finish();
            }
        }

        private void Finish()
        {
            try
            {
                sceneStager.Close();
            }
            catch (Exception e)
            {
                OnLog?.Invoke("Stager close error: " + e.Message);
            }

            EditorApplication.update -= TickRunner;
            isRunning = false;
            runner = null;
            OnCompleted?.Invoke();
        }

        // ------------------------------------------------------------
        // Enhanced Validation Methods
        // ------------------------------------------------------------

        private void ValidateConfiguration(ThumbnailConfig config)
        {
            if (config == null)
                throw new ArgumentNullException(nameof(config), "Configuration cannot be null.");

            if (config.outputResolution < 64 || config.outputResolution > 4096)
                throw new ArgumentException($"Invalid output resolution: {config.outputResolution}. Must be between 64 and 4096.");

            if (string.IsNullOrWhiteSpace(config.filenameSuffix))
                throw new ArgumentException("Filename suffix cannot be empty.");

            if (config.margin < 0f || config.margin > 1f)
                throw new ArgumentException($"Invalid margin: {config.margin}. Must be between 0 and 1.");
        }

        private bool ValidateInputPath(string inputAbs)
        {
            if (string.IsNullOrWhiteSpace(inputAbs))
            {
                OnError?.Invoke("Input folder path is empty.");
                return false;
            }

            if (!Directory.Exists(inputAbs))
            {
                OnError?.Invoke($"Input folder does not exist: {inputAbs}");
                return false;
            }

            // Check if input folder is inside Unity project for proper prefab scanning
            string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            string fullPath = Path.GetFullPath(inputAbs);
            
            if (!fullPath.StartsWith(projectRoot))
            {
                OnLog?.Invoke($"Warning: Input folder is outside the Unity project. Prefab scanning may not work properly. Path: {inputAbs}");
                // Don't fail, just warn - let user proceed
            }

            try
            {
                // Test read access
                Directory.GetDirectories(inputAbs);
            }
            catch (UnauthorizedAccessException)
            {
                OnError?.Invoke($"No read permission for input folder: {inputAbs}");
                return false;
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"Cannot access input folder: {inputAbs}. Error: {ex.Message}");
                return false;
            }

            return true;
        }

        private bool ValidateOutputPath(string outputAbs)
        {
            if (string.IsNullOrWhiteSpace(outputAbs))
            {
                OnError?.Invoke("Output folder path is empty.");
                return false;
            }

            try
            {
                // Create output directory if it doesn't exist
                Directory.CreateDirectory(outputAbs);
                
                // Test write access
                var testFile = Path.Combine(outputAbs, $"thumbnailer_test_{Guid.NewGuid():N}.tmp");
                File.WriteAllText(testFile, "test");
                File.Delete(testFile);
            }
            catch (UnauthorizedAccessException)
            {
                OnError?.Invoke($"No write permission for output folder: {outputAbs}");
                return false;
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"Cannot create or access output folder: {outputAbs}. Error: {ex.Message}");
                return false;
            }

            return true;
        }

        private int ValidatePrefabAssets(List<string> prefabPaths)
        {
            int invalidCount = 0;
            
            // Sample validation - check first few prefabs for common issues
            int samplesToCheck = Math.Min(10, prefabPaths.Count);
            
            for (int i = 0; i < samplesToCheck; i++)
            {
                try
                {
                    var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPaths[i]);
                    if (prefab == null)
                    {
                        invalidCount++;
                        continue;
                    }

                    // Check for common issues
                    var renderers = prefab.GetComponentsInChildren<Renderer>();
                    if (renderers.Length == 0)
                    {
                        OnLog?.Invoke($"Warning: Prefab '{prefabPaths[i]}' has no renderers - may result in empty thumbnail.");
                    }
                }
                catch (Exception ex)
                {
                    OnLog?.Invoke($"Warning: Could not validate prefab '{prefabPaths[i]}': {ex.Message}");
                    invalidCount++;
                }
            }

            return invalidCount;
        }

        // ------------------------------------------------------------
        // Batch coroutine
        // ------------------------------------------------------------

        private IEnumerable<YieldToken> RunBatch(ThumbnailRunConfig rc, List<string> prefabAssetPaths)
        {
            // Get selected capture angles
            var captureAngles = rc.Config.GetSelectedAngles();
            
            // Calculate total work: prefabs × angles
            int totalWork = prefabAssetPaths.Count * captureAngles.Length;
            int workIndex = 0;

            foreach (var assetPath in prefabAssetPaths)
            {
                if (cancelRequested)
                {
                    OnLog?.Invoke("Batch canceled.");
                    break;
                }

                // Load prefab once for all angles
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
                if (prefab == null)
                {
                    OnError?.Invoke($"Failed to load prefab: {assetPath}");
                    // Skip all angles for this prefab
                    workIndex += captureAngles.Length;
                    continue;
                }

                // Process each selected angle for this prefab
                foreach (var angle in captureAngles)
                {
                    if (cancelRequested) break;

                    workIndex++;
                    string progressMsg = captureAngles.Length > 1 
                        ? $"Capturing {angle.Name} view" 
                        : "Capturing";
                    
                    OnProgress?.Invoke(new ThumbnailProgress(workIndex - 1, totalWork, assetPath, progressMsg));

                    try
                    {
                        // Compute output path with angle subfolder
                        string outputAbsForThis = ComputeOutputPathWithAngle(rc, assetPath, angle);

                        // Skip if output exists and configured to skip
                        if (rc.Config.skipIfExists && File.Exists(outputAbsForThis))
                        {
                            OnProgress?.Invoke(new ThumbnailProgress(workIndex, totalWork, assetPath, $"{angle.Name} (skipped)"));
                            continue;
                        }

                        // Process this angle
                        bool success = ProcessAngleCapture(rc, assetPath, prefab, angle, outputAbsForThis);
                        
                        string savedMsg = success 
                            ? (captureAngles.Length > 1 ? $"{angle.Name} saved" : "Saved")
                            : (captureAngles.Length > 1 ? $"{angle.Name} failed" : "Failed");
                        OnProgress?.Invoke(new ThumbnailProgress(workIndex, totalWork, assetPath, savedMsg));
                    }
                    catch (Exception e)
                    {
                        OnError?.Invoke($"Error processing {assetPath} ({angle.Name}): {e.Message}");
                    }

                    // Yield to keep Editor responsive
                    yield return YieldToken.Next;
                }

                if (cancelRequested) break;
            }

            // Done
            Finish();
        }

        /// <summary>
        /// Applies the specified angle rotation to the prefab instance.
        /// Rotates the prefab, not the camera, for consistent framing.
        /// </summary>
        private void ApplyAngleRotation(GameObject instance, CaptureAngle angle)
        {
            // Apply Y-axis rotation to show different sides of the prefab
            var currentRotation = instance.transform.rotation;
            var angleRotation = Quaternion.Euler(0f, angle.YawDegrees, 0f);
            instance.transform.rotation = angleRotation * currentRotation;
        }

        /// <summary>
        /// Computes the output file path including angle subfolder for multi-angle capture.
        /// Format: OutputRoot/AngleFolder/MirroredInputPath/PrefabName_thumb_Resolution.png
        /// </summary>
        private string ComputeOutputPathWithAngle(ThumbnailRunConfig rc, string assetPath, CaptureAngle angle)
        {
            // Get the base output path without angle
            string baseOutputPath = ComputeOutputPath(rc, assetPath);
            
            // Get directory and filename parts
            string baseDir = Path.GetDirectoryName(baseOutputPath);
            string fileName = Path.GetFileName(baseOutputPath);
            
            // Insert angle folder into the path
            string angleDir = Path.Combine(baseDir, angle.FolderName);
            string finalPath = Path.Combine(angleDir, fileName);
            
            return finalPath;
        }

        /// <summary>
        /// Processes a single angle capture for a prefab.
        /// Returns true if successful, false otherwise.
        /// </summary>
        private bool ProcessAngleCapture(ThumbnailRunConfig rc, string assetPath, GameObject prefab, CaptureAngle angle, string outputPath)
        {
            try
            {
                // Stage instance
                var instance = sceneStager.Spawn(prefab);

                // Apply angle-specific rotation to the prefab instance (not camera)
                ApplyAngleRotation(instance, angle);

                // Frame camera for subject (camera stays fixed, subject rotates)
                prefabFramer.FrameSubject(rc, instance);

                // Render to texture (transparent)
                var tex = rendererService.RenderToTexture(rc, instance, rc.Resolution, rc.Resolution);

                // Ensure output directory exists
                Directory.CreateDirectory(Path.GetDirectoryName(outputPath) ?? rc.OutputPathAbs);

                // Save file (PNG by default)
                fileService.SaveTexture(tex, outputPath, rc.Config.forcePng);

                // Cleanup spawned instance
                sceneStager.Despawn(instance);

                return true;
            }
            catch (Exception e)
            {
                OnError?.Invoke($"Failed to process angle {angle.Name} for {assetPath}: {e.Message}");
                return false;
            }
        }

        private enum ProcessStatus { Success, Skipped, Error }
        
        private struct ProcessResult 
        { 
            public ProcessStatus Status; 
            public string ProgressMessage; 
        }

        private ProcessResult ProcessPrefabSafely(ThumbnailRunConfig rc, string assetPath, int index, int total)
        {
            try
            {
                // Check if output already exists and skip if configured
                string outputAbsForThis = ComputeOutputPath(rc, assetPath);
                if (rc.Config.skipIfExists && File.Exists(outputAbsForThis))
                {
                    return new ProcessResult { Status = ProcessStatus.Skipped, ProgressMessage = "Skipped (exists)" };
                }

                // Load prefab with validation
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
                if (prefab == null)
                {
                    OnError?.Invoke($"Failed to load prefab: {assetPath}");
                    return new ProcessResult { Status = ProcessStatus.Error, ProgressMessage = "Error (load failed)" };
                }

                // Validate prefab has renderable content
                if (!ValidatePrefabForRendering(prefab, assetPath))
                {
                    return new ProcessResult { Status = ProcessStatus.Skipped, ProgressMessage = "Skipped (no renderers)" };
                }

                // Process the prefab
                bool success = ProcessSinglePrefab(rc, assetPath, prefab, outputAbsForThis);
                if (success)
                {
                    return new ProcessResult { Status = ProcessStatus.Success, ProgressMessage = "Saved" };
                }
                else
                {
                    return new ProcessResult { Status = ProcessStatus.Error, ProgressMessage = "Error (process failed)" };
                }
            }
            catch (Exception e)
            {
                OnError?.Invoke($"Error processing {assetPath}: {e.Message}");
                return new ProcessResult { Status = ProcessStatus.Error, ProgressMessage = "Error (exception)" };
            }
        }

        private bool ValidatePrefabForRendering(GameObject prefab, string assetPath)
        {
            var renderers = prefab.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0)
            {
                OnLog?.Invoke($"Skipping '{assetPath}' - no renderers found.");
                return false;
            }

            // Check if any renderers are enabled
            bool hasEnabledRenderer = false;
            foreach (var renderer in renderers)
            {
                if (renderer.enabled && renderer.gameObject.activeInHierarchy)
                {
                    hasEnabledRenderer = true;
                    break;
                }
            }

            if (!hasEnabledRenderer)
            {
                OnLog?.Invoke($"Skipping '{assetPath}' - no enabled renderers found.");
                return false;
            }

            return true;
        }

        private bool ProcessSinglePrefab(ThumbnailRunConfig rc, string assetPath, GameObject prefab, string outputPath)
        {
            GameObject instance = null;
            try
            {
                // Stage instance
                instance = sceneStager.Spawn(prefab);
                if (instance == null)
                {
                    OnError?.Invoke($"Failed to spawn instance for: {assetPath}");
                    return false;
                }

                // Apply LOD settings
                if (rc.Config.forceHighestLod)
                {
                    ApplyHighestLOD(instance);
                }

                // Handle particle systems
                if (!rc.Config.includeParticles)
                {
                    DisableParticleSystems(instance);
                }

                // Frame camera for subject
                prefabFramer.FrameSubject(rc, instance);

                // Render to texture (transparent)
                var tex = rendererService.RenderToTexture(rc, instance, rc.Resolution, rc.Resolution);
                if (tex == null)
                {
                    OnError?.Invoke($"Failed to render texture for: {assetPath}");
                    return false;
                }

                try
                {
                    // Ensure output directory exists
                    var outputDir = Path.GetDirectoryName(outputPath);
                    if (!string.IsNullOrEmpty(outputDir))
                    {
                        Directory.CreateDirectory(outputDir);
                    }

                    // Save file (PNG by default)
                    fileService.SaveTexture(tex, outputPath, rc.Config.forcePng);
                    return true;
                }
                finally
                {
                    // Always cleanup texture
                    UnityEngine.Object.DestroyImmediate(tex);
                }
            }
            finally
            {
                // Always cleanup spawned instance
                if (instance != null)
                {
                    sceneStager.Despawn(instance);
                }
            }
        }

        private void ApplyHighestLOD(GameObject instance)
        {
            var lodGroups = instance.GetComponentsInChildren<LODGroup>();
            foreach (var lodGroup in lodGroups)
            {
                lodGroup.ForceLOD(0); // Force highest quality LOD
            }
        }

        private void DisableParticleSystems(GameObject instance)
        {
            var particleSystems = instance.GetComponentsInChildren<ParticleSystem>();
            foreach (var ps in particleSystems)
            {
                ps.gameObject.SetActive(false);
            }
        }

        // ------------------------------------------------------------
        // Helpers
        // ------------------------------------------------------------

        private static string ResolveAbsolutePath(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) return string.Empty;

            // If already absolute, normalize
            if (Path.IsPathRooted(path))
            {
                return Path.GetFullPath(path);
            }
            // Treat as project-relative (e.g., "Assets/...")
            string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            string combined = Path.GetFullPath(Path.Combine(projectRoot, path));
            return combined;
        }

        private static string AbsoluteToProjectPath(string absPath)
        {
            string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            absPath = Path.GetFullPath(absPath);
            if (!absPath.StartsWith(projectRoot)) return string.Empty;

            string rel = absPath.Substring(projectRoot.Length + 1).Replace('\\', '/');
            return rel;
        }

        private static List<string> FindPrefabsUnder(string inputAbs)
        {
            var results = new List<string>();

            string projectPath = AbsoluteToProjectPath(inputAbs);
            if (string.IsNullOrEmpty(projectPath))
            {
                // Allow non-project folder: use file system, then map to AssetDatabase if possible
                // But for Editor processing we prefer Assets/… so we warn.
                Debug.LogWarning("[Thumbnailer] Input folder is outside project; prefabs must be under Assets/ to load via AssetDatabase.");
                return results;
            }

            // Collect GUIDs for prefabs under folder (recursive)
            string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { projectPath });
            foreach (var guid in guids)
            {
                string assetPath = AssetDatabase.GUIDToAssetPath(guid);
                if (assetPath.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase))
                    results.Add(assetPath);
            }

            return results;
        }

        private string ComputeOutputPath(ThumbnailRunConfig rc, string prefabAssetPath)
        {
            string fileName = Path.GetFileNameWithoutExtension(prefabAssetPath);
            string suffix = rc.Config.filenameSuffix ?? "_thumb";

            string relativeSubdir = "";
            if (rc.Config.mirrorFolders)
            {
                // Mirror structure under the chosen output root
                // e.g., Assets/MyPrefabs/Props/Chair.prefab -> Thumbnails/MyPrefabs/Props/Chair_thumb_512.png
                var dir = Path.GetDirectoryName(prefabAssetPath)?.Replace('\\', '/');
                // Strip leading "Assets/" if present to keep it clean
                if (!string.IsNullOrEmpty(dir))
                {
                    relativeSubdir = dir.StartsWith("Assets/") ? dir.Substring("Assets/".Length) : dir;
                }
            }

            string outDirAbs = string.IsNullOrEmpty(relativeSubdir)
                ? rc.OutputPathAbs
                : Path.Combine(rc.OutputPathAbs, relativeSubdir);

            string ext = rc.Config.forcePng ? ".png" : ".png"; // PNG default for alpha-safe MVP
            string resTag = $"_{rc.Resolution}";
            string outName = $"{fileName}{suffix}{resTag}{ext}";

            return Path.Combine(outDirAbs, outName);
        }
    }

    // ============================================================
    // Lightweight yield token to pace the Editor update loop.
    // ============================================================
    public struct YieldToken
    {
        public static readonly YieldToken Next = new YieldToken();
    }

    // ============================================================
    // Service interfaces — to be implemented in upcoming scripts.
    // Keep them minimal and SRP-compliant.
    // ============================================================

    public interface ISceneStager
    {
        void Open(ThumbnailRunConfig rc);
        GameObject Spawn(GameObject prefab); // returns instance in staging scene
        void Despawn(GameObject instance);
        void Close();

        // Added for PrefabFramer
        Camera GetCamera();
    }

    public interface IPrefabFramer
    {
        void FrameSubject(ThumbnailRunConfig rc, GameObject instance);
    }

    public interface IRendererService
    {
        Texture2D RenderToTexture(ThumbnailRunConfig rc, GameObject instance, int width, int height);
    }

    public interface IFileService
    {
        void SaveTexture(Texture2D tex, string absolutePath, bool forcePng);
    }
}
