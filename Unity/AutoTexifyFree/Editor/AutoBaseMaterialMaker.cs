using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections;
using System;

namespace KalponicGames
{
#if UNITY_EDITOR
    public class AutoBaseMaterialMaker : EditorWindow
    {
        private string textureFolder = "Assets/Textures";
        private string materialsFolder = "";
        private int gridSize = 5;
        private float spacing = 2.0f;
        private PrimitiveType previewMeshType = PrimitiveType.Plane;
        private Shader materialShader;
        private bool isProcessing = false;
        private bool createPreviews = true;
        private bool recursiveSearch = false;
        private bool cancelRequested = false;
        private object coroutineRef = null; // keep as object for compatibility

        [MenuItem("Kalponic Tools/Auto Base Material Maker")]
        public static void ShowWindow()
        {
            GetWindow<AutoBaseMaterialMaker>("Auto Base Material Maker");
        }

        private void OnEnable()
        {
            materialShader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
        }

        private void OnGUI()
        {
            // ==== Editor Coroutine Package Check ====
            Type coroutineType = Type.GetType("Unity.EditorCoroutines.Editor.EditorCoroutineUtility, Unity.EditorCoroutines.Editor");
            if (coroutineType == null)
            {
                EditorGUILayout.HelpBox(
                    "Editor Coroutines package is missing!\n\n" +
                    "Go to Window → Package Manager → Add package by name…\n" +
                    "and enter:\n\ncom.unity.editorcoroutines\n\n" +
                    "This is required for the tool to work.",
                    MessageType.Error
                );
                return;
            }

            EditorGUILayout.LabelField(
                new GUIContent("Texture Folder", "The folder containing your source textures (PNG, JPG, JPEG, TGA)."),
                EditorStyles.boldLabel
            );
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.TextField(
                new GUIContent("", "The folder containing your source textures (PNG, JPG, JPEG, TGA)."),
                textureFolder
            );
            if (GUILayout.Button(new GUIContent("Pick Folder", "Select the folder with textures you want to use."), GUILayout.MaxWidth(100)))
            {
                string selectedPath = EditorUtility.OpenFolderPanel("Select Texture Folder", "Assets", "");
                if (!string.IsNullOrEmpty(selectedPath) && selectedPath.StartsWith(Application.dataPath))
                    textureFolder = "Assets" + selectedPath.Substring(Application.dataPath.Length);
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space();

            EditorGUILayout.LabelField(
                new GUIContent("Materials Save Folder", "Folder to save all generated materials. Defaults to 'Materials' subfolder if left blank."),
                EditorStyles.boldLabel
            );
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.TextField(
                new GUIContent("", "Folder to save all generated materials. Defaults to 'Materials' subfolder if left blank."),
                string.IsNullOrEmpty(materialsFolder) ? "(default: Materials subfolder)" : materialsFolder
            );
            if (GUILayout.Button(new GUIContent("Pick Save Folder", "Choose a custom folder to save generated materials."), GUILayout.MaxWidth(120)))
            {
                string savePath = EditorUtility.OpenFolderPanel("Select Materials Save Folder", "Assets", "");
                if (!string.IsNullOrEmpty(savePath) && savePath.StartsWith(Application.dataPath))
                    materialsFolder = "Assets" + savePath.Substring(Application.dataPath.Length);
            }
            if (GUILayout.Button(new GUIContent("Reset", "Reset to default materials save folder."), GUILayout.MaxWidth(60)))
            {
                materialsFolder = "";
            }
            EditorGUILayout.EndHorizontal();

            gridSize = EditorGUILayout.IntField(
                new GUIContent("Grid Size", "Number of preview meshes per row in the scene."),
                gridSize
            );
            spacing = EditorGUILayout.FloatField(
                new GUIContent("Spacing", "Distance between each preview mesh in the grid."),
                spacing
            );
            previewMeshType = (PrimitiveType)EditorGUILayout.EnumPopup(
                new GUIContent("Preview Mesh", "Primitive mesh type (plane, cube, sphere, etc.) used for material previews."),
                previewMeshType
            );
            materialShader = EditorGUILayout.ObjectField(
                new GUIContent("Material Shader", "Shader used for the generated materials. Pick the correct shader for your pipeline."),
                materialShader, typeof(Shader), false
            ) as Shader;

            EditorGUILayout.Space();
            createPreviews = EditorGUILayout.Toggle(
                new GUIContent("Create Preview Meshes", "If checked, will spawn preview meshes in the scene for each material."),
                createPreviews
            );
            recursiveSearch = EditorGUILayout.Toggle(
                new GUIContent("Recursive Search (include subfolders)", "If checked, searches for textures in all subfolders (not just the main folder)."),
                recursiveSearch
            );

            EditorGUILayout.Space();

            GUI.enabled = !isProcessing;
            if (GUILayout.Button(new GUIContent("Generate Materials & Preview", "Create materials from all textures and optionally preview them in the scene.")))
            {
                StartCoroutine();
            }
            GUI.enabled = isProcessing;
            if (isProcessing)
            {
                if (GUILayout.Button(new GUIContent("Cancel", "Stop the current material generation process.")))
                {
                    cancelRequested = true;
                }
            }
            GUI.enabled = true;

            EditorGUILayout.Space();

            if (GUILayout.Button(new GUIContent("Delete All Previews In Scene", "Deletes all preview meshes created by this tool from the scene. Does NOT delete your materials or textures.")))
            {
                DeleteAllPreviewObjects();
            }
        }

        // This dynamic call avoids compile error if package is missing
        private void StartCoroutine()
        {
            if (isProcessing) return;
            cancelRequested = false;

            // Use reflection to start coroutine so script compiles even if package missing
            Type coroutineType = Type.GetType("Unity.EditorCoroutines.Editor.EditorCoroutineUtility, Unity.EditorCoroutines.Editor");
            if (coroutineType != null)
            {
                var startMethod = coroutineType.GetMethod("StartCoroutineOwnerless", new Type[] { typeof(IEnumerator) });
                coroutineRef = startMethod.Invoke(null, new object[] { GenerateMaterialsCoroutine() });
            }
        }

        private IEnumerator GenerateMaterialsCoroutine()
        {
            isProcessing = true;

            string finalMaterialsFolder = GetMaterialsFolder();

            // Gather texture files (recursive if checked)
            var searchOption = recursiveSearch ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
            string[] files = Directory.GetFiles(textureFolder, "*.*", searchOption);
            string[] allowedExt = new[] { ".png", ".jpg", ".jpeg", ".tga" };
            var textures = Array.FindAll(files, path => Array.Exists(allowedExt, a => a == Path.GetExtension(path).ToLower()));

            int row = 0, col = 0;
            int total = textures.Length;
            int created = 0, skipped = 0;

            for (int i = 0; i < total; i++)
            {
                if (cancelRequested)
                {
                    EditorUtility.ClearProgressBar();
                    EditorUtility.DisplayDialog("Cancelled", $"Operation cancelled.\nMaterials created: {created}\nSkipped: {skipped}", "OK");
                    isProcessing = false;
                    coroutineRef = null;
                    yield break;
                }

                EditorUtility.DisplayProgressBar("Generating Materials", $"Processing texture {i + 1}/{total}", (float)i / total);

                string texPath = textures[i].Replace("\\", "/");
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(texPath);

                if (tex == null)
                {
                    skipped++;
                    yield return null;
                    continue;
                }

                string matName = tex.name + "_Mat.mat";
                string matPath = Path.Combine(finalMaterialsFolder, matName).Replace("\\", "/");

                if (File.Exists(matPath))
                {
                    skipped++;
                    yield return null;
                    continue;
                }

                var mat = CreateMaterial(tex, materialShader);
                AssetDatabase.CreateAsset(mat, matPath);

                if (createPreviews)
                {
                    CreatePreviewObject(tex.name, mat, row, col, spacing, previewMeshType);

                    col++;
                    if (col >= gridSize)
                    {
                        col = 0;
                        row++;
                    }
                }

                created++;
                yield return null;
            }

            EditorUtility.ClearProgressBar();
            AssetDatabase.SaveAssets();
            EditorUtility.DisplayDialog("Done!", $"Materials created: {created}\nSkipped: {skipped}\nSaved to: {finalMaterialsFolder}", "OK");
            Debug.Log($"All base materials created in '{finalMaterialsFolder}' and preview meshes added! Created: {created}, Skipped: {skipped}");

            isProcessing = false;
            coroutineRef = null;
        }

        private string GetMaterialsFolder()
        {
            if (!string.IsNullOrEmpty(materialsFolder))
                return materialsFolder;

            string defaultFolder = Path.Combine(textureFolder, "Materials").Replace("\\", "/");
            if (!AssetDatabase.IsValidFolder(defaultFolder))
                AssetDatabase.CreateFolder(textureFolder, "Materials");
            return defaultFolder;
        }

        private Material CreateMaterial(Texture2D texture, Shader shader)
        {
            var mat = new Material(shader ?? Shader.Find("Standard"));
            if (shader != null && shader.name == "Universal Render Pipeline/Lit")
                mat.SetTexture("_BaseMap", texture);
            else
                mat.mainTexture = texture;
            mat.name = texture.name + "_Mat";
            return mat;
        }

        private void CreatePreviewObject(string baseName, Material material, int row, int col, float objSpacing, PrimitiveType meshType)
        {
            var go = GameObject.CreatePrimitive(meshType);
            go.transform.position = new Vector3(col * objSpacing, 0, -row * objSpacing);
            go.GetComponent<Renderer>().sharedMaterial = material;
            go.name = baseName + "_Preview";
        }

        private void DeleteAllPreviewObjects()
        {
            int deleted = 0;
            foreach (var obj in GameObject.FindObjectsByType<GameObject>(FindObjectsSortMode.None))
            {
                if (obj.name.EndsWith("_Preview"))
                {
                    DestroyImmediate(obj);
                    deleted++;
                }
            }
            Debug.Log($"All preview objects deleted. Count: {deleted}");
            EditorUtility.DisplayDialog("Cleanup Complete", $"Deleted {deleted} preview objects.", "OK");
        }
    }
#endif
}
