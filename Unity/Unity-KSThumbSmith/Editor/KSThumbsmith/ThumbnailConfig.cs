// Assets/KalponicGames/Editor/Thumbnailer/ThumbnailConfig.cs
// KISS config model for the Prefab Thumbnailer.
// Namespace + naming follow your conventions.

using System;
using UnityEngine;

namespace KalponicGames
{
    [Serializable]
    public sealed class ThumbnailConfig
    {
        // ===== Enums =====
        public enum Preset
        {
            WhiteMatte,   // default for general assets
            BlackMatte,
            Auto
        }

        public enum CameraMode
        {
            Orthographic, // MVP default
            Perspective
        }

        public enum Orientation
        {
            Front,        // +Z forward
            Top,          // -Y down, top view
            Isometric,    // 30/45 style tilt
            Custom        // use customEuler
        }

        public enum LightingMode
        {
            NoneUnlit,    // fastest catalog look
            Studio3Point, // soft shadows, neutral tone
            SkyboxHDRI    // optional later
        }

        // ===== Basics =====

        [Header("I/O")]
        [Tooltip("Absolute or project-relative path to the input folder containing prefabs.")]
        public string inputFolder = string.Empty;

        [Tooltip("Absolute or project-relative path to the output folder for thumbnails.")]
        public string outputFolder = "Assets/Thumbnails";

        [Header("Output")]
        [Tooltip("Square output resolution in pixels (power of two recommended).")]
        public int outputResolution = 512;

        [Tooltip("Append this to the saved file name before the extension.")]
        public string filenameSuffix = "_thumb";

        [Tooltip("Force PNG export to preserve alpha regardless of source.")]
        public bool forcePng = true;

        // ===== Camera / Framing =====

        [Header("Camera & Framing")]
        public CameraMode cameraMode = CameraMode.Orthographic;

        [Tooltip("Extra space around the bounds (0.0–0.5).")]
        [Range(0f, 0.5f)]
        public float margin = 0.10f;

        [Tooltip("Perspective FOV if CameraMode = Perspective.")]
        [Range(10f, 90f)]
        public float perspectiveFov = 40f;

        [Tooltip("If Orientation = Custom, this Euler (deg) is applied to the subject.")]
        public Vector3 customEuler = Vector3.zero;

        public Orientation orientation = Orientation.Front;

        // ===== Multi-Angle Capture =====

        [Header("Multi-Angle Capture (2D Side-Scroller Workflow)")]
        [Tooltip("Capture front view (yaw 0°) for 2D side-scroller assets.")]
        public bool captureAngleFront = true;

        [Tooltip("Capture side view (yaw +90°) for 2D side-scroller assets.")]
        public bool captureAngleSide = false;

        [Tooltip("Capture back view (yaw 180°) for 2D side-scroller assets.")]
        public bool captureAngleBack = false;

        // ===== Lighting =====

        [Header("Lighting")]
        public LightingMode lightingMode = LightingMode.NoneUnlit;

        [Tooltip("Enable soft shadows in non-unlit modes.")]
        public bool useShadows = false;

        // ===== Alpha / Background =====

        [Header("Background / Alpha")]
        [Tooltip("Clear color for camera background. Alpha must be 0 for transparency.")]
        public Color clearColor = new Color(0f, 0f, 0f, 0f);

        [Tooltip("Export alpha as straight (default) or premultiplied. (MVP: straight only)")]
        public bool exportPremultipliedAlpha = false;

        // ===== Subject Handling =====

        [Header("Subject Handling")]
        [Tooltip("Normalize scale so that largest dimension fits a target size before framing.")]
        public bool normalizeScale = false;

        [Tooltip("Include particle systems during capture (off for clean catalog shots).")]
        public bool includeParticles = false;

        [Tooltip("Always render highest LOD for clarity when LODGroup exists.")]
        public bool forceHighestLod = true;

        // ===== Safety / Batch =====

        [Header("Batch & Safety")]
        [Tooltip("Mirror the input folder structure under the output folder.")]
        public bool mirrorFolders = true;

        [Tooltip("Skip if an existing output file is already present.")]
        public bool skipIfExists = true;

        [Tooltip("Stop on first error (otherwise continue and log).")]
        public bool failFast = false;

        [Header("Performance")]
        [Tooltip("Maximum number of prefabs to process in a single batch (0 = no limit).")]
        [Range(0, 5000)]
        public int maxBatchSize = 1000;

        [Tooltip("Memory cleanup frequency (process N prefabs then force garbage collection).")]
        [Range(10, 500)]
        public int memoryCleanupFrequency = 100;

        // ===== Preset (matte) for future color spill handling, parity with your other tool =====
        [Header("Matte Preset (Reserved)")]
        public Preset mattePreset = Preset.WhiteMatte;

        // ===== Methods =====

        public static ThumbnailConfig Default()
        {
            return new ThumbnailConfig
            {
                inputFolder = string.Empty,
                outputFolder = "Assets/Thumbnails",
                outputResolution = 512,
                filenameSuffix = "_thumb",
                forcePng = true,

                cameraMode = CameraMode.Orthographic,
                margin = 0.10f,
                perspectiveFov = 40f,
                orientation = Orientation.Front,
                customEuler = Vector3.zero,

                // Multi-angle capture defaults
                captureAngleFront = true,
                captureAngleSide = false,
                captureAngleBack = false,

                lightingMode = LightingMode.NoneUnlit,
                useShadows = false,

                clearColor = new Color(0f, 0f, 0f, 0f),
                exportPremultipliedAlpha = false,

                normalizeScale = false,
                includeParticles = false,
                forceHighestLod = true,

                mirrorFolders = true,
                skipIfExists = true,
                failFast = false,

                maxBatchSize = 1000,
                memoryCleanupFrequency = 100,

                mattePreset = Preset.WhiteMatte
            };
        }

        /// <summary>
        /// Clamp and sanitize fields to safe ranges. Call before run.
        /// </summary>
        public void Validate()
        {
            outputResolution = Mathf.Clamp(outputResolution, 64, 4096);
            margin = Mathf.Clamp01(margin);
            perspectiveFov = Mathf.Clamp(perspectiveFov, 10f, 90f);
            maxBatchSize = Mathf.Clamp(maxBatchSize, 0, 5000);
            memoryCleanupFrequency = Mathf.Clamp(memoryCleanupFrequency, 10, 500);

            // Ensure transparent clear color by default
            if (clearColor.a != 0f && lightingMode == LightingMode.NoneUnlit)
                clearColor.a = 0f;

            filenameSuffix ??= "_thumb";
            if (string.IsNullOrWhiteSpace(filenameSuffix))
                filenameSuffix = "_thumb";

            // Ensure at least one angle is selected
            if (!captureAngleFront && !captureAngleSide && !captureAngleBack)
            {
                captureAngleFront = true; // Default fallback
            }
        }

        /// <summary>
        /// Gets the list of capture angles that are enabled.
        /// Each angle includes name, folder name, and Y rotation in degrees.
        /// </summary>
        public CaptureAngle[] GetSelectedAngles()
        {
            var angles = new System.Collections.Generic.List<CaptureAngle>();

            if (captureAngleFront)
                angles.Add(new CaptureAngle("Front", "Front", 0f));

            if (captureAngleSide)
                angles.Add(new CaptureAngle("Side", "Side", 90f));

            if (captureAngleBack)
                angles.Add(new CaptureAngle("Back", "Back", 180f));

            return angles.ToArray();
        }
    }

    /// <summary>
    /// Represents a capture angle configuration for multi-angle thumbnail generation.
    /// </summary>
    [System.Serializable]
    public readonly struct CaptureAngle
    {
        public readonly string Name;          // Display name (e.g., "Front")
        public readonly string FolderName;    // Subfolder name for output
        public readonly float YawDegrees;     // Y-axis rotation in degrees

        public CaptureAngle(string name, string folderName, float yawDegrees)
        {
            Name = name;
            FolderName = folderName;
            YawDegrees = yawDegrees;
        }

        public override string ToString() => $"{Name} ({YawDegrees}°)";
    }
}
