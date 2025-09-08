// Assets/KalponicGames/Editor/Thumbnailer/PrefabFramer.cs
// Computes bounds, applies orientation, and frames camera to fit subject with margin.

using System.Linq;
using UnityEngine;

namespace KalponicGames
{
    public sealed class PrefabFramer : IPrefabFramer
    {
        private readonly ISceneStager sceneStager;

        public PrefabFramer(ISceneStager sceneStager)
        {
            this.sceneStager = sceneStager;
        }

        public void FrameSubject(ThumbnailRunConfig rc, GameObject instance)
        {
            var cam = sceneStager.GetCamera();
            if (cam == null || instance == null) return;

            // 1) Subject orientation
            ApplyOrientation(rc, instance);

            // 2) Optional normalize scale
            if (rc.Config.normalizeScale)
            {
                NormalizeScale(instance);
            }

            // 3) Light skinned mesh preparation (less intrusive)
            PrepareSkinnedMeshesLight(instance);

            // 4) Compute tight world bounds
            var bounds = ComputeWorldBounds(instance);
            var center = bounds.center;

            // 5) Position camera and fit using original proven logic
            if (cam.orthographic)
            {
                FrameOrthographic(cam, bounds, rc.Config.margin);
            }
            else
            {
                FramePerspective(cam, bounds, rc.Config.margin);
            }

            // 6) Look-at and clip planes
            cam.transform.LookAt(center);
            var dist = Vector3.Distance(cam.transform.position, center);
            cam.nearClipPlane = Mathf.Max(0.01f, dist - bounds.extents.magnitude * 2f);
            cam.farClipPlane  = dist + bounds.extents.magnitude * 2f;
        }

        // ------------------------------------------------------------
        // Skinned Mesh Handling
        // ------------------------------------------------------------

        private struct SkinnedMeshState
        {
            public SkinnedMeshRenderer renderer;
            public bool originalUpdateWhenOffscreen;
        }

        private SkinnedMeshState[] PrepareSkinnedMeshes(GameObject instance)
        {
            var skinnedRenderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>();
            var states = new SkinnedMeshState[skinnedRenderers.Length];

            for (int i = 0; i < skinnedRenderers.Length; i++)
            {
                var smr = skinnedRenderers[i];
                states[i] = new SkinnedMeshState
                {
                    renderer = smr,
                    originalUpdateWhenOffscreen = smr.updateWhenOffscreen
                };
                
                // Force update when offscreen to get accurate bounds
                smr.updateWhenOffscreen = true;
            }

            // Sample default pose if animator exists
            var animator = instance.GetComponentInChildren<Animator>();
            if (animator != null && animator.isActiveAndEnabled)
            {
                animator.Update(0f); // Sample default pose
            }

            return states;
        }

        private void RestoreSkinnedMeshes(SkinnedMeshState[] states)
        {
            foreach (var state in states)
            {
                if (state.renderer != null)
                {
                    state.renderer.updateWhenOffscreen = state.originalUpdateWhenOffscreen;
                }
            }
        }

        /// <summary>
        /// Prepares skinned meshes for accurate bounds calculation in both URP and Built-in.
        /// Forces animator to sample default pose so bounds reflect actual mesh position.
        /// This is critical for proper camera framing of characters and rigged objects.
        /// </summary>
        private static void PrepareSkinnedMeshesLight(GameObject instance)
        {
            // Find animator component to sample default pose
            var animator = instance.GetComponentInChildren<Animator>();
            if (animator != null && animator.isActiveAndEnabled)
            {
                // Sample at time 0 to ensure consistent default pose
                // This forces skinned mesh bounds to update correctly
                animator.Update(0f);
            }

            // Ensure skinned mesh renderers update their bounds when off-screen
            // This is necessary because bounds calculation happens during rendering
            var skinnedRenderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>();
            foreach (var smr in skinnedRenderers)
            {
                // Force update when offscreen for accurate bounds during thumbnail capture
                // Without this, bounds may be stale or incorrect, leading to bad framing
                smr.updateWhenOffscreen = true;
                
                // Force immediate bounds update
                smr.forceMatrixRecalculationPerRender = true;
            }
        }

        // ------------------------------------------------------------
        // Orientation & scale
        // ------------------------------------------------------------

        private static void ApplyOrientation(ThumbnailRunConfig rc, GameObject instance)
        {
            // GUARD: Respect multi-angle rotation when side-scroller mode is active
            // If Side or Back angles are enabled, skip orientation override to preserve 
            // the angle-specific rotation set by ThumbnailController.ApplyAngleRotation()
            if (rc.Config.captureAngleSide || rc.Config.captureAngleBack)
            {
                // Multi-angle mode active - preserve existing rotation set by controller
                return;
            }

            // Apply standard orientation presets (Front/Top/Isometric/Custom)
            switch (rc.Config.orientation)
            {
                case ThumbnailConfig.Orientation.Front:
                    instance.transform.rotation = Quaternion.identity;
                    break;
                case ThumbnailConfig.Orientation.Top:
                    instance.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                    break;
                case ThumbnailConfig.Orientation.Isometric:
                    instance.transform.rotation = Quaternion.Euler(30f, 45f, 0f);
                    break;
                case ThumbnailConfig.Orientation.Custom:
                    instance.transform.rotation = Quaternion.Euler(rc.Config.customEuler);
                    break;
            }
        }

        private static void NormalizeScale(GameObject instance)
        {
            var b = ComputeWorldBounds(instance);
            var largest = Mathf.Max(b.size.x, Mathf.Max(b.size.y, b.size.z));
            if (largest <= 1e-6f) return;

            float target = 1f; // target largest dimension in world units (KISS)
            float factor = target / largest;

            var t = instance.transform;
            t.localScale = t.localScale * factor;
        }

        // ------------------------------------------------------------
        // Bounds
        // ------------------------------------------------------------

        private static Bounds ComputeWorldBounds(GameObject root)
        {
            var renderers = root.GetComponentsInChildren<Renderer>(true)
                                .Where(r => r.enabled && r.gameObject.activeInHierarchy)
                                .ToArray();

            if (renderers.Length > 0)
            {
                var b = new Bounds(renderers[0].bounds.center, Vector3.zero);
                foreach (var r in renderers) b.Encapsulate(r.bounds);
                return b;
            }

            // Fallback: colliders
            var cols = root.GetComponentsInChildren<Collider>(true);
            if (cols.Length > 0)
            {
                var b = new Bounds(cols[0].bounds.center, Vector3.zero);
                foreach (var c in cols) b.Encapsulate(c.bounds);
                return b;
            }

            // Ultimate fallback
            return new Bounds(root.transform.position, Vector3.one);
        }

        // ------------------------------------------------------------
        // Fit: Orthographic & Perspective
        // ------------------------------------------------------------

        private static void FrameOrthographic(Camera cam, Bounds b, float margin)
        {
            // Place camera straight in -Z, look-at set later.
            var center = b.center;
            float sizeX = b.extents.x;
            float sizeY = b.extents.y;

            // For ortho, orthographicSize is half of vertical size to fit
            float halfHeight = Mathf.Max(sizeY, sizeX * cam.pixelHeight / Mathf.Max(1, cam.pixelWidth));
            cam.orthographicSize = halfHeight * (1f + Mathf.Clamp01(margin));

            // Distance doesn’t affect coverage in ortho, but keep it sensible
            float dist = b.extents.magnitude * 2f + 2f;
            cam.transform.position = center + new Vector3(0f, 0f, -dist);
        }

        private static void FramePerspective(Camera cam, Bounds b, float margin)
        {
            var center = b.center;
            var extents = b.extents;
            float fovRad = cam.fieldOfView * Mathf.Deg2Rad;

            // Fit vertically by default
            float radiusY = extents.y;
            float fitDistY = radiusY / Mathf.Tan(fovRad * 0.5f);

            // Also check horizontal FOV
            float hfov = 2f * Mathf.Atan(Mathf.Tan(fovRad * 0.5f) * cam.aspect);
            float radiusX = extents.x;
            float fitDistX = radiusX / Mathf.Tan(hfov * 0.5f);

            float dist = Mathf.Max(fitDistX, fitDistY) * (1f + Mathf.Clamp01(margin)) + extents.z;

            cam.transform.position = center + new Vector3(0f, 0f, -dist);
        }

        // ------------------------------------------------------------
        // View-Aligned Fitting (Fixes clipping issues)
        // ------------------------------------------------------------

        private static void FrameOrthographicViewAligned(Camera cam, Bounds b, float margin)
        {
            var center = b.center;
            
            // Position camera first
            float dist = b.extents.magnitude * 2f + 2f;
            cam.transform.position = center + new Vector3(0f, 0f, -dist);
            cam.transform.LookAt(center);

            // Get all 8 corners of the bounds
            var corners = GetBoundsCorners(b);
            
            // Transform corners to camera space
            var camMatrix = cam.worldToCameraMatrix;
            float minX = float.MaxValue, maxX = float.MinValue;
            float minY = float.MaxValue, maxY = float.MinValue;

            foreach (var corner in corners)
            {
                var camSpaceCorner = camMatrix.MultiplyPoint3x4(corner);
                minX = Mathf.Min(minX, camSpaceCorner.x);
                maxX = Mathf.Max(maxX, camSpaceCorner.x);
                minY = Mathf.Min(minY, camSpaceCorner.y);
                maxY = Mathf.Max(maxY, camSpaceCorner.y);
            }

            // Calculate required ortho size with margin and overscan
            float sizeX = (maxX - minX) * 0.5f;
            float sizeY = (maxY - minY) * 0.5f;
            float overscan = 1.05f; // 5% overscan
            float worldPad = 0.1f;   // 2px equivalent world-space pad

            cam.orthographicSize = Mathf.Max(sizeY, sizeX / cam.aspect) * (1f + margin) * overscan + worldPad;
        }

        private static void FramePerspectiveViewAligned(Camera cam, Bounds b, float margin)
        {
            var center = b.center;
            float fovRad = cam.fieldOfView * Mathf.Deg2Rad;
            
            // Start with a reasonable distance
            float startDist = b.extents.magnitude * 3f;
            cam.transform.position = center + new Vector3(0f, 0f, -startDist);
            cam.transform.LookAt(center);

            // Get all 8 corners of the bounds
            var corners = GetBoundsCorners(b);
            
            // Iterate to find the minimum distance that fits all corners
            float dist = startDist;
            for (int iteration = 0; iteration < 3; iteration++)
            {
                cam.transform.position = center + new Vector3(0f, 0f, -dist);
                var camMatrix = cam.worldToCameraMatrix;
                
                float maxViolation = 0f;
                
                foreach (var corner in corners)
                {
                    var camSpaceCorner = camMatrix.MultiplyPoint3x4(corner);
                    if (camSpaceCorner.z > 0) // In front of camera
                    {
                        // Check against FOV constraints
                        float halfHeight = Mathf.Tan(fovRad * 0.5f) * camSpaceCorner.z;
                        float halfWidth = halfHeight * cam.aspect;
                        
                        float violationX = Mathf.Max(0f, Mathf.Abs(camSpaceCorner.x) - halfWidth);
                        float violationY = Mathf.Max(0f, Mathf.Abs(camSpaceCorner.y) - halfHeight);
                        
                        maxViolation = Mathf.Max(maxViolation, violationX, violationY);
                    }
                }
                
                if (maxViolation > 0.01f)
                {
                    dist *= 1.2f; // Increase distance by 20%
                }
                else
                {
                    break; // All corners fit
                }
            }
            
            // Apply margin, overscan, and world pad
            float overscan = 1.05f; // 5% overscan
            float finalDist = dist * (1f + margin) * overscan + b.extents.z + 0.1f;
            
            cam.transform.position = center + new Vector3(0f, 0f, -finalDist);
        }

        private static Vector3[] GetBoundsCorners(Bounds bounds)
        {
            var center = bounds.center;
            var extents = bounds.extents;
            
            return new Vector3[]
            {
                center + new Vector3(-extents.x, -extents.y, -extents.z),
                center + new Vector3(-extents.x, -extents.y,  extents.z),
                center + new Vector3(-extents.x,  extents.y, -extents.z),
                center + new Vector3(-extents.x,  extents.y,  extents.z),
                center + new Vector3( extents.x, -extents.y, -extents.z),
                center + new Vector3( extents.x, -extents.y,  extents.z),
                center + new Vector3( extents.x,  extents.y, -extents.z),
                center + new Vector3( extents.x,  extents.y,  extents.z)
            };
        }
    }
}
