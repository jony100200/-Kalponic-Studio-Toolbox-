using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;

public class KSSpriteEffects : EditorWindow
{
    [MenuItem("Tools/Kalponic Studio/KS Sprite Effects")]
    public static void ShowWindow()
    {
        GetWindow<KSSpriteEffects>("KS Sprite Effects");
    }

    private DefaultAsset inputFolder;
    private DefaultAsset outputFolder;
    private Material selectedMaterial;

    private void OnGUI()
    {
        GUILayout.Label("KS Sprite Effects", EditorStyles.boldLabel);
        GUILayout.Label("Apply a shader to all sprites in a folder and save the results.", EditorStyles.wordWrappedLabel);

        // Input folder
        inputFolder = (DefaultAsset)EditorGUILayout.ObjectField("Input Folder", inputFolder, typeof(DefaultAsset), false);

        // Output folder
        outputFolder = (DefaultAsset)EditorGUILayout.ObjectField("Output Folder", outputFolder, typeof(DefaultAsset), false);

        // Material selection
        selectedMaterial = (Material)EditorGUILayout.ObjectField("Effect Material", selectedMaterial, typeof(Material), false);

        if (GUILayout.Button("Apply Effects and Save"))
        {
            ApplyEffects();
        }
    }

    private void ApplyEffects()
    {
        if (inputFolder == null || outputFolder == null || selectedMaterial == null)
        {
            Debug.LogError("Please assign input folder, output folder, and material.");
            return;
        }

        string inputPath = AssetDatabase.GetAssetPath(inputFolder);
        string outputPath = AssetDatabase.GetAssetPath(outputFolder);

        if (!AssetDatabase.IsValidFolder(inputPath) || !AssetDatabase.IsValidFolder(outputPath))
        {
            Debug.LogError("Invalid folders selected.");
            return;
        }

        // Find all sprite assets
        string[] spriteGuids = AssetDatabase.FindAssets("t:Sprite", new[] { inputPath });

        if (spriteGuids.Length == 0)
        {
            Debug.Log("No sprites found in input folder.");
            return;
        }

        // Use the selected material
        Material effectMaterial = selectedMaterial;

        AssetDatabase.StartAssetEditing();

        foreach (string guid in spriteGuids)
        {
            string spritePath = AssetDatabase.GUIDToAssetPath(guid);
            Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);

            if (sprite != null && sprite.texture != null)
            {
                // Apply shader to texture
                Texture2D originalTexture = sprite.texture;
                Texture2D processedTexture = ApplyShaderToTexture(originalTexture, effectMaterial);

                if (processedTexture != null)
                {
                    // Save new texture
                    string fileName = Path.GetFileNameWithoutExtension(spritePath) + "_effect.png";
                    string savePath = Path.Combine(outputPath, fileName).Replace("\\", "/");

                    byte[] pngData = processedTexture.EncodeToPNG();
                    File.WriteAllBytes(savePath, pngData);

                    AssetDatabase.ImportAsset(savePath);
                    AssetDatabase.Refresh();

                    Debug.Log("Processed and saved: " + savePath);
                }
            }
        }

        AssetDatabase.StopAssetEditing();
        AssetDatabase.Refresh();

        Debug.Log("All sprites processed.");
    }

    private Texture2D ApplyShaderToTexture(Texture2D original, Material mat)
    {
        // Create a temporary render texture
        RenderTexture rt = RenderTexture.GetTemporary(original.width, original.height, 0, RenderTextureFormat.ARGB32);
        Graphics.Blit(original, rt, mat);

        // Read back to texture
        Texture2D result = new Texture2D(original.width, original.height, TextureFormat.ARGB32, false);
        RenderTexture.active = rt;
        result.ReadPixels(new Rect(0, 0, original.width, original.height), 0, 0);
        result.Apply();

        RenderTexture.active = null; // Reset active render texture
        RenderTexture.ReleaseTemporary(rt);
        return result;
    }
}