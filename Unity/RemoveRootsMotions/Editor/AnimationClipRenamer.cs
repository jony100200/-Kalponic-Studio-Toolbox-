using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.Linq;

public class AnimationClipRenamer : EditorWindow
{
    [MenuItem("Tools/Kalponic Studio/Rename Animation Clips")]
    public static void ShowWindow()
    {
        GetWindow<AnimationClipRenamer>("Rename Animation Clips");
    }

    private AnimationClip[] animationClips;
    private DefaultAsset sourceFolder;
    private string suffixToRemove = "_Duplicate_NoRootTz";

    private void OnGUI()
    {
        GUILayout.Label("Select Source Folder or Animation Clips to Rename", EditorStyles.boldLabel);

        // Source folder field
        GUILayout.Label("Source Folder", EditorStyles.boldLabel);
        sourceFolder = (DefaultAsset)EditorGUILayout.ObjectField(new GUIContent("Source Folder", "Drag a folder here to load all animation clips from it."), sourceFolder, typeof(DefaultAsset), false);

        if (GUILayout.Button(new GUIContent("Load from Source Folder", "Load all animation clips from the selected folder.")))
        {
            LoadFromSourceFolder();
        }

        if (GUILayout.Button(new GUIContent("Load Selected Animation Clips", "Load the selected animation clips.")))
        {
            LoadSelectedAnimationClips();
        }

        if (animationClips != null && animationClips.Length > 0)
        {
            GUILayout.Space(10);
            GUILayout.Label("Suffix to Remove", EditorStyles.boldLabel);
            suffixToRemove = EditorGUILayout.TextField(new GUIContent("Suffix to Remove", "Enter the suffix to remove from the animation names (e.g., '_Duplicate_NoRootTz')."), suffixToRemove);

            if (GUILayout.Button(new GUIContent("Rename Loaded Animation Clips", "Rename the loaded animation clips by removing the specified suffix.")))
            {
                RenameLoadedClips();
            }

            GUILayout.Space(10);
            GUILayout.Label("Loaded Animation Clips:", EditorStyles.boldLabel);
            foreach (var clip in animationClips)
            {
                string proposedName = string.IsNullOrEmpty(suffixToRemove) ? clip.name : clip.name.Replace(suffixToRemove, "");
                GUILayout.Label(clip.name + " -> " + proposedName);
            }
        }
    }

    private void LoadSelectedAnimationClips()
    {
        HashSet<AnimationClip> selectedClips = new HashSet<AnimationClip>();
        foreach (var obj in Selection.objects)
        {
            if (obj is AnimationClip clip)
            {
                selectedClips.Add(clip);
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

        animationClips = selectedClips.ToArray();
        Debug.Log("Loaded " + animationClips.Length + " animation clips from folder: " + folderPath);
    }

    private void RenameLoadedClips()
    {
        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (var clip in animationClips)
            {
                string path = AssetDatabase.GetAssetPath(clip);
                string newName = string.IsNullOrEmpty(suffixToRemove) ? clip.name : clip.name.Replace(suffixToRemove, "");
                AssetDatabase.RenameAsset(path, newName);
                Debug.Log("Renamed: " + path + " to " + newName + ".anim");
            }
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
        }
        AssetDatabase.Refresh();
        Debug.Log("Renamed all loaded animation clips.");
    }
}