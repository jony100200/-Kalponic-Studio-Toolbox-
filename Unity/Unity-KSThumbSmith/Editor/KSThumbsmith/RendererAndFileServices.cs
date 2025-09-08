// Assets/KalponicGames/Editor/Thumbnailer/RendererAndFileServices.cs
// Implements IRendererService (transparent capture) and IFileService (PNG save).
// Supports both URP and Built-in Render Pipeline for transparent PNG output.

using System;
using System.IO;
using UnityEditor;
using UnityEngine;

#if UNITY_RENDER_PIPELINE_UNIVERSAL
using UnityEngine.Rendering.Universal;
#endif

namespace KalponicGames
{
    public sealed class RendererService : IRendererService
    {
        private readonly ISceneStager stager;

        public RendererService(ISceneStager stager)
        {
            this.stager = stager;
        }

        public Texture2D RenderToTexture(ThumbnailRunConfig rc, GameObject instance, int width, int height)
        {
            var cam = stager.GetCamera();
            if (cam == null) 
                throw new InvalidOperationException("No camera available in SceneStager.");

            // Validate render pipeline compatibility
            ValidateRenderPipelineSetup(cam);

            // Validate input parameters
            ValidateInputParameters(instance, width, height);

            // Create RenderTexture with alpha support for transparent output
            var rt = CreateAlphaSupportedRenderTexture(width, height);

            var prevActive = RenderTexture.active;
            var prevTarget = cam.targetTexture;

            try
            {
                cam.targetTexture = rt;
                RenderTexture.active = rt;
                
                // FIX: Force camera aspect to match RT to prevent projection math lies
                // This ensures the captured image matches the requested dimensions exactly
                var prevAspect = cam.aspect;
                cam.aspect = (float)width / height;
                
                // Validate camera can render
                ValidateCameraState(cam);

                // Render the scene
                cam.Render();

                // Restore original aspect
                cam.aspect = prevAspect;

                // Read back into CPU texture with alpha preservation
                var tex = ReadRenderTextureWithAlpha(rt, width, height);

                return tex;
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to render texture: {ex.Message}", ex);
            }
            finally
            {
                // Always clean up resources
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                rt.Release();
                UnityEngine.Object.DestroyImmediate(rt);
            }
        }

        /// <summary>
        /// Creates a RenderTexture configured for transparent PNG output in both URP and Built-in.
        /// Uses ARGB32 format with proper sRGB settings for color-accurate results.
        /// </summary>
        private RenderTexture CreateAlphaSupportedRenderTexture(int width, int height)
        {
            // Use ARGB32 for full alpha channel support in both pipelines
            var descriptor = new RenderTextureDescriptor(width, height, RenderTextureFormat.ARGB32, 24)
            {
                msaaSamples = 1, // No MSAA for crisp thumbnail edges
                useMipMap = false, // Not needed for static thumbnails
                autoGenerateMips = false, // Explicit control
                sRGB = QualitySettings.activeColorSpace == ColorSpace.Linear // Match project color space
            };

            var rt = new RenderTexture(descriptor)
            {
                name = "KG_Thumb_RT_Alpha"
            };

            if (!rt.Create())
                throw new InvalidOperationException($"Failed to create RenderTexture with resolution {width}x{height}. Check available VRAM.");

            return rt;
        }

        /// <summary>
        /// Reads RenderTexture data with proper alpha channel preservation.
        /// Ensures transparent pixels remain transparent in the final PNG.
        /// </summary>
        private Texture2D ReadRenderTextureWithAlpha(RenderTexture rt, int width, int height)
        {
            // Use RGBA32 format to preserve alpha channel during readback
            var tex = new Texture2D(width, height, TextureFormat.RGBA32, false, /*linear*/ false);
            var rect = new Rect(0, 0, width, height);
            
            // ReadPixels preserves alpha channel when using RGBA32 format
            tex.ReadPixels(rect, 0, 0, false);
            tex.Apply(false, false);

            return tex;
        }

        /// <summary>
        /// Validates camera state to ensure it can render properly.
        /// Checks for common issues that prevent rendering.
        /// </summary>
        private void ValidateCameraState(Camera cam)
        {
            if (!cam.enabled || !cam.gameObject.activeInHierarchy)
                throw new InvalidOperationException("Camera is disabled or its GameObject is inactive.");
        }

        /// <summary>
        /// Validates input parameters for rendering.
        /// Ensures safe values that won't cause memory issues.
        /// </summary>
        private void ValidateInputParameters(GameObject instance, int width, int height)
        {
            if (instance == null)
                throw new ArgumentNullException(nameof(instance), "Instance GameObject cannot be null.");
            
            if (width <= 0 || height <= 0)
                throw new ArgumentException($"Invalid resolution: {width}x{height}. Must be positive values.");

            if (width > 8192 || height > 8192)
                throw new ArgumentException($"Resolution {width}x{height} exceeds maximum supported size (8192x8192).");
        }

        /// <summary>
        /// Validates render pipeline setup for transparent capture.
        /// Provides helpful warnings for both URP and Built-in pipelines.
        /// </summary>
        private void ValidateRenderPipelineSetup(Camera cam)
        {
            var currentPipeline = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline;
            
            if (currentPipeline == null)
            {
                // Built-in Render Pipeline
                Debug.Log("[KSThumbSmith] Using Built-in Render Pipeline for transparent capture.");
                ValidateBuiltInPipelineSettings(cam);
            }
            else
            {
                // URP or other pipeline
                if (currentPipeline.GetType().Name.Contains("Universal"))
                {
                    Debug.Log("[KSThumbSmith] Using Universal Render Pipeline for transparent capture.");
                    ValidateUrpSettings(cam);
                }
                else
                {
                    Debug.LogWarning($"[KSThumbSmith] Unknown render pipeline: {currentPipeline.GetType().Name}. Transparent capture may not work correctly.");
                }
            }
        }

        /// <summary>
        /// Validates Built-in Render Pipeline settings for transparent capture.
        /// Built-in relies on camera clear flags and background color alpha.
        /// </summary>
        private void ValidateBuiltInPipelineSettings(Camera cam)
        {
            if (cam.clearFlags != CameraClearFlags.SolidColor)
            {
                Debug.LogWarning($"[KSThumbSmith] Camera '{cam.name}' clearFlags should be SolidColor for transparent capture in Built-in pipeline.");
            }
            
            if (cam.backgroundColor.a > 0.01f)
            {
                Debug.LogWarning($"[KSThumbSmith] Camera '{cam.name}' backgroundColor alpha should be 0 for transparent capture (current: {cam.backgroundColor.a:F3}).");
            }
        }

        /// <summary>
        /// Validates URP settings for transparent capture.
        /// URP requires UniversalAdditionalCameraData for optimal results.
        /// </summary>
        private void ValidateUrpSettings(Camera cam)
        {
#if UNITY_RENDER_PIPELINE_UNIVERSAL
            var urpCamData = cam.GetComponent<UniversalAdditionalCameraData>();
            if (urpCamData == null)
            {
                Debug.LogWarning($"[KSThumbSmith] Camera '{cam.name}' is missing UniversalAdditionalCameraData component for optimal URP transparent capture.");
            }
            else
            {
                // Check URP-specific settings
                if (urpCamData.renderPostProcessing)
                {
                    Debug.LogWarning($"[KSThumbSmith] Camera '{cam.name}' has post-processing enabled, which may affect thumbnail quality.");
                }
            }
#else
            Debug.LogWarning("[KSThumbSmith] URP detected but URP package not available in project. Falling back to Built-in pipeline settings.");
#endif
        }
    }

    public sealed class FileService : IFileService
    {
        public void SaveTexture(Texture2D tex, string absolutePath, bool forcePng)
        {
            // Validate inputs
            if (tex == null)
                throw new ArgumentNullException(nameof(tex), "Texture cannot be null.");
            
            if (string.IsNullOrWhiteSpace(absolutePath))
                throw new ArgumentException("Output path cannot be null or empty.", nameof(absolutePath));

            // Validate path accessibility
            ValidateOutputPath(absolutePath);

            try
            {
                // We always write PNG for alpha-safe thumbnails (KISS)
                var dir = Path.GetDirectoryName(absolutePath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }

                // Check write permissions
                ValidateWritePermissions(dir);

                byte[] png = ImageConversion.EncodeToPNG(tex);
                if (png == null || png.Length == 0)
                    throw new InvalidOperationException("Failed to encode texture to PNG. Texture may be corrupted or unreadable.");

                File.WriteAllBytes(absolutePath, png);

                // Verify file was written successfully
                if (!File.Exists(absolutePath))
                    throw new InvalidOperationException($"File was not created successfully at: {absolutePath}");

                var fileInfo = new FileInfo(absolutePath);
                if (fileInfo.Length == 0)
                    throw new InvalidOperationException($"Created file is empty: {absolutePath}");

                // If saving inside the project, refresh so it appears immediately
                string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
                var full = Path.GetFullPath(absolutePath);
                if (full.StartsWith(projectRoot))
                {
                    AssetDatabase.Refresh();
                }
            }
            catch (UnauthorizedAccessException ex)
            {
                throw new InvalidOperationException($"Access denied when writing to: {absolutePath}. Check file permissions.", ex);
            }
            catch (DirectoryNotFoundException ex)
            {
                throw new InvalidOperationException($"Directory not found: {Path.GetDirectoryName(absolutePath)}", ex);
            }
            catch (IOException ex)
            {
                throw new InvalidOperationException($"IO error when writing file: {absolutePath}. {ex.Message}", ex);
            }
        }

        private void ValidateOutputPath(string absolutePath)
        {
            // Check for invalid characters
            var invalidChars = Path.GetInvalidPathChars();
            if (absolutePath.IndexOfAny(invalidChars) >= 0)
                throw new ArgumentException($"Path contains invalid characters: {absolutePath}");

            // Check path length (Windows has 260 char limit)
            if (absolutePath.Length > 250)
                throw new ArgumentException($"Path is too long ({absolutePath.Length} chars). Maximum recommended is 250 characters.");

            // Ensure it's an absolute path
            if (!Path.IsPathRooted(absolutePath))
                throw new ArgumentException($"Path must be absolute: {absolutePath}");
        }

        private void ValidateWritePermissions(string directory)
        {
            if (string.IsNullOrEmpty(directory)) return;

            try
            {
                // Test write access by creating a temporary file
                var testFile = Path.Combine(directory, $"thumbnailer_test_{Guid.NewGuid():N}.tmp");
                File.WriteAllText(testFile, "test");
                File.Delete(testFile);
            }
            catch (Exception ex)
            {
                throw new UnauthorizedAccessException($"No write permission for directory: {directory}", ex);
            }
        }
    }
}
