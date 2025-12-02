using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;
using System.Linq;

public class AnimationClipDuplicator : EditorWindow
{
    [MenuItem("Tools/Kalponic Studio/Duplicate Animation Clips")]
    public static void ShowWindow()
    {
        GetWindow<AnimationClipDuplicator>("Duplicate Animation Clips");
    }

    private AnimationClip[] animationClips;
    private DefaultAsset sourceFolder;
    private string duplicateFolder = "Assets/DuplicatedClips";

    private void OnGUI()
    {
        GUILayout.Label("Select Source Folder or Animation Clips/FBX Files", EditorStyles.boldLabel);

        // Source folder field
        GUILayout.Label("Source Folder", EditorStyles.boldLabel);
        sourceFolder = (DefaultAsset)EditorGUILayout.ObjectField(new GUIContent("Source Folder", "Drag a folder here to load all animation clips and FBX files from it."), sourceFolder, typeof(DefaultAsset), false);

        if (GUILayout.Button(new GUIContent("Load from Source Folder", "Load all animation clips and clips from FBX files in the selected folder.")))
        {
            LoadFromSourceFolder();
        }

        if (GUILayout.Button(new GUIContent("Load Selected Animation Clips or FBX Files", "Load the animation clips from selected assets (clips or FBX files containing clips).")))
        {
            LoadSelectedAnimationClips();
        }

        if (animationClips != null && animationClips.Length > 0)
        {
            GUILayout.Space(10);
            GUILayout.Label("Save Duplicated Clips To", EditorStyles.boldLabel);
            duplicateFolder = EditorGUILayout.TextField(new GUIContent("Duplicate Folder Path", "Specify the folder path where the duplicated clips will be saved."), duplicateFolder);

            if (GUILayout.Button(new GUIContent("Duplicate Animation Clips", "Duplicate the selected animation clips and save them in organized subfolders.")))
            {
                DuplicateAnimationClips();
            }

            GUILayout.Space(10);
            GUILayout.Label("Loaded Animation Clips:", EditorStyles.boldLabel);
            foreach (var clip in animationClips)
            {
                GUILayout.Label(clip.name);
            }
        }
    }

    private void LoadSelectedAnimationClips()
    {
        HashSet<AnimationClip> selectedClips = new HashSet<AnimationClip>();
        foreach (var obj in Selection.objects)
        {
            string path = AssetDatabase.GetAssetPath(obj);
            Object[] assets = AssetDatabase.LoadAllAssetsAtPath(path);
            foreach (var asset in assets)
            {
                if (asset is AnimationClip clip)
                {
                    selectedClips.Add(clip);
                }
            }
        }
        animationClips = selectedClips.ToArray();
        Debug.Log("Loaded " + animationClips.Length + " animation clips.");
    }

    private void LoadFromSourceFolder()
    {
        if (sourceFolder == null)
        {
            Debug.LogError("No source folder selected.");
            return;
        }

        string folderPath = AssetDatabase.GetAssetPath(sourceFolder);
        if (!AssetDatabase.IsValidFolder(folderPath))
        {
            Debug.LogError("Selected object is not a valid folder.");
            return;
        }

        HashSet<AnimationClip> selectedClips = new HashSet<AnimationClip>();

        // Find all AnimationClip assets in the folder
        string[] clipGuids = AssetDatabase.FindAssets("t:AnimationClip", new[] { folderPath });
        foreach (string guid in clipGuids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            AnimationClip clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (clip != null)
            {
                selectedClips.Add(clip);
            }
        }

        // Find all Model assets (FBX) in the folder and extract their AnimationClips
        string[] modelGuids = AssetDatabase.FindAssets("t:Model", new[] { folderPath });
        foreach (string guid in modelGuids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            Object[] assets = AssetDatabase.LoadAllAssetsAtPath(path);
            foreach (var asset in assets)
            {
                if (asset is AnimationClip clip)
                {
                    selectedClips.Add(clip);
                }
            }
        }

        animationClips = selectedClips.ToArray();
        Debug.Log("Loaded " + animationClips.Length + " animation clips from folder: " + folderPath);
    }

    private void DuplicateAnimationClips()
    {
        // Ensure the base duplicate folder exists in the asset database
        string baseFolderPath = duplicateFolder;
        if (!AssetDatabase.IsValidFolder(baseFolderPath))
        {
            string parentFolder = System.IO.Path.GetDirectoryName(baseFolderPath).Replace("\\", "/");
            string folderName = System.IO.Path.GetFileName(baseFolderPath);
            AssetDatabase.CreateFolder(parentFolder, folderName);
        }

        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (var clip in animationClips)
            {
                // Get the source asset path
                string sourcePath = AssetDatabase.GetAssetPath(clip);
                // Get the source file name (without extension) for prefix
                string sourceFileName = System.IO.Path.GetFileNameWithoutExtension(sourcePath);

                // Duplicate the clip
                AnimationClip duplicatedClip = new AnimationClip();
                EditorUtility.CopySerialized(clip, duplicatedClip);

                string duplicatePath = Path.Combine(duplicateFolder, sourceFileName + "_" + clip.name + "_Duplicate.anim").Replace("\\", "/");
                duplicatePath = AssetDatabase.GenerateUniqueAssetPath(duplicatePath);
                AssetDatabase.CreateAsset(duplicatedClip, duplicatePath);

                Debug.Log("Duplicated: " + clip.name + " from " + sourcePath + " to " + duplicatePath);
            }
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
        }
        AssetDatabase.SaveAssets();
        Debug.Log("Duplicated all selected animation clips.");
    }
}
