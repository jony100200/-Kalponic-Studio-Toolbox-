// Assets/KalponicGames/Editor/Thumbnailer/SceneStager.cs
// Creates a temporary staging scene with a transparent camera and optional lights.
// Supports both URP and Built-in Render Pipeline for transparent thumbnail capture.

using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

#if UNITY_RENDER_PIPELINE_UNIVERSAL
using UnityEngine.Rendering.Universal;
#endif

namespace KalponicGames
{
    public sealed class SceneStager : ISceneStager
    {
        private const string STAGE_SCENE_NAME = "KG_Thumb_Stage_Temp";
        private const string ROOT_NAME = "__KG_Thumb_StageRoot";
        private const string CAM_NAME = "KG_Thumb_Camera";
        private const string LIGHT_ROOT_NAME = "KG_Thumb_Lights";

        private Scene stageScene;
        private Transform root;
        private Camera camera;
#if UNITY_RENDER_PIPELINE_UNIVERSAL
        private UniversalAdditionalCameraData urpCamData;
#endif
        private Transform lightRoot;

        private ThumbnailRunConfig runConfig;
        private bool isUrpActive = false; // Track current pipeline for proper cleanup

        // ------------- ISceneStager -------------

        public void Open(ThumbnailRunConfig rc)
        {
            runConfig = rc;

            // Create an untitled, additive scene so we don't touch the user's scene.
            stageScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
            SceneManager.SetActiveScene(stageScene);
            stageScene.name = STAGE_SCENE_NAME;

            // Root container for cleanliness.
            root = new GameObject(ROOT_NAME).transform;

            // Camera
            camera = CreateCamera(rc);
            camera.transform.SetParent(root, worldPositionStays: false);
            camera.transform.position = new Vector3(0f, 0f, -5f);
            camera.transform.rotation = Quaternion.identity;

            // Optional lighting
            if (rc.Config.lightingMode != ThumbnailConfig.LightingMode.NoneUnlit)
            {
                lightRoot = new GameObject(LIGHT_ROOT_NAME).transform;
                lightRoot.SetParent(root, false);
                BuildLighting(rc);
            }

            // Keep the stage clean
            EditorSceneManager.MarkSceneDirty(stageScene); // no save; just ensure objects persist in memory
        }

        public GameObject Spawn(GameObject prefab)
        {
            if (!stageScene.IsValid())
                throw new System.InvalidOperationException("Stage scene not valid. Call Open() first.");

            var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, stageScene);
            var t = instance.transform;
            t.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            t.localScale = Vector3.one;

            // Disable particle systems if not requested
            if (!runConfig.Config.includeParticles)
            {
                foreach (var ps in instance.GetComponentsInChildren<ParticleSystem>(true))
                    ps.gameObject.SetActive(false);
            }

            // Force highest LOD (LOD0) when possible
            if (runConfig.Config.forceHighestLod)
            {
                foreach (var lod in instance.GetComponentsInChildren<LODGroup>(true))
                    lod.ForceLOD(0);
            }

            return instance;
        }

        public void Despawn(GameObject instance)
        {
            if (instance != null)
                Object.DestroyImmediate(instance);
        }

        public void Close()
        {
            if (stageScene.IsValid())
            {
                // Clean up the whole scene
                EditorSceneManager.CloseScene(stageScene, removeScene: true);
            }

            // Reset all references
            stageScene = default;
            root = null;
            camera = null;
            lightRoot = null;
            isUrpActive = false;
            
#if UNITY_RENDER_PIPELINE_UNIVERSAL
            urpCamData = null;
#endif
        }

        // ------------- Helpers -------------

        private Camera CreateCamera(ThumbnailRunConfig rc)
        {
            var go = new GameObject(CAM_NAME);
            var cam = go.AddComponent<Camera>();

            // Detect current render pipeline
            isUrpActive = IsUniversalRenderPipelineActive();

            // Configure camera for transparent background in both pipelines
            ConfigureCameraForTransparency(cam, rc);

            // Render settings
            cam.orthographic = (rc.Config.cameraMode == ThumbnailConfig.CameraMode.Orthographic);
            if (cam.orthographic)
            {
                cam.orthographicSize = 1f; // PrefabFramer will adjust placement/size
            }
            else
            {
                cam.fieldOfView = rc.Config.perspectiveFov;
            }

            cam.nearClipPlane = 0.01f;
            cam.farClipPlane = 1000f;
            cam.allowHDR = true;
            cam.allowMSAA = false; // crisp edges for catalog thumbs

            // Apply URP-specific settings if URP is active
            if (isUrpActive)
            {
                ConfigureUrpCamera(cam);
            }

            return cam;
        }

        /// <summary>
        /// Configures camera for transparent background in both URP and Built-in pipelines.
        /// Built-in: Use SolidColor with alpha 0.
        /// URP: Use SolidColor with alpha 0 + URP transparency settings.
        /// </summary>
        private void ConfigureCameraForTransparency(Camera cam, ThumbnailRunConfig rc)
        {
            // Both pipelines: Use SolidColor clear with transparent background
            cam.clearFlags = CameraClearFlags.SolidColor;
            var clr = rc.Config.clearColor;
            // Force alpha to 0 for transparency in both pipelines
            cam.backgroundColor = new Color(clr.r, clr.g, clr.b, 0f);
        }

        /// <summary>
        /// Applies URP-specific camera settings when URP is active.
        /// Disables post-processing and anti-aliasing for clean thumbnail output.
        /// </summary>
        private void ConfigureUrpCamera(Camera cam)
        {
#if UNITY_RENDER_PIPELINE_UNIVERSAL
            urpCamData = cam.GetComponent<UniversalAdditionalCameraData>();
            if (urpCamData == null) 
            {
                urpCamData = cam.gameObject.AddComponent<UniversalAdditionalCameraData>();
            }
            
            // Disable post-processing for clean thumbnail output
            urpCamData.renderPostProcessing = false;
            // Disable anti-aliasing for crisp edges and performance
            urpCamData.antialiasing = AntialiasingMode.None;
            // Ensure depth buffer is cleared for proper transparency
            urpCamData.clearDepth = true;
            // Set volume trigger to camera transform (standard practice)
            urpCamData.volumeTrigger = cam.transform;
            // Use pipeline settings for color/depth requirements
            urpCamData.requiresColorOption = CameraOverrideOption.UsePipelineSettings;
            urpCamData.requiresDepthTexture = false; // Not needed for thumbnails
#endif
        }

        /// <summary>
        /// Detects if Universal Render Pipeline is currently active.
        /// Returns true if URP is the active render pipeline, false for Built-in.
        /// </summary>
        private bool IsUniversalRenderPipelineActive()
        {
#if UNITY_RENDER_PIPELINE_UNIVERSAL
            // Check if URP is actually active by examining the current render pipeline asset
            var currentPipeline = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline;
            return currentPipeline != null && currentPipeline.GetType().Name.Contains("Universal");
#else
            // URP not available in this project
            return false;
#endif
        }

        private void BuildLighting(ThumbnailRunConfig rc)
        {
            switch (rc.Config.lightingMode)
            {
                case ThumbnailConfig.LightingMode.Studio3Point:
                    CreateStudioLights(rc.Config.useShadows);
                    break;
                case ThumbnailConfig.LightingMode.SkyboxHDRI:
                    // Leave ambient to project settings; user can have an HDRI skybox.
                    // Add a soft key so subjects aren’t flat.
                    CreateKeyFillRim(rc.Config.useShadows);
                    break;
            }
        }

        private void CreateStudioLights(bool useShadows)
        {
            // Key
            var key = CreateLight("Key", new Vector3(2.5f, 2.5f, -2.5f), new Vector3(25f, -30f, 0f), 1.2f, useShadows);
            key.transform.SetParent(lightRoot, false);

            // Fill
            var fill = CreateLight("Fill", new Vector3(-3.0f, 1.5f, -2.0f), new Vector3(15f, 35f, 0f), 0.6f, false);
            fill.transform.SetParent(lightRoot, false);

            // Rim
            var rim = CreateLight("Rim", new Vector3(0f, 2.0f, 2.5f), new Vector3(10f, 180f, 0f), 0.8f, false);
            rim.transform.SetParent(lightRoot, false);
        }

        private void CreateKeyFillRim(bool useShadows)
        {
            var key = CreateLight("Key", new Vector3(2.5f, 2.0f, -2.0f), new Vector3(20f, -30f, 0f), 1.0f, useShadows);
            key.transform.SetParent(lightRoot, false);

            var fill = CreateLight("Fill", new Vector3(-2.5f, 1.5f, -1.5f), new Vector3(10f, 30f, 0f), 0.5f, false);
            fill.transform.SetParent(lightRoot, false);
        }

        private Light CreateLight(string name, Vector3 pos, Vector3 euler, float intensity, bool castShadows)
        {
            var go = new GameObject($"LG_{name}");
            var lt = go.AddComponent<Light>();
            lt.type = LightType.Directional;
            lt.color = Color.white;
            lt.intensity = intensity;
            lt.shadows = castShadows ? LightShadows.Soft : LightShadows.None;
            go.transform.position = pos;
            go.transform.rotation = Quaternion.Euler(euler);
            return lt;
        }

        // Expose camera for renderer service if needed
        public Camera GetCamera() => camera;
    }
}
