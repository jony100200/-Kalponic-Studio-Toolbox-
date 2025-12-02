using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;
using System.Linq;

public class RemoveRootMotion : EditorWindow
{
    // Add the option to open this window from the Unity editor menu
    [MenuItem("Tools/Remove Root Motion")]
    public static void ShowWindow()
    {
        GetWindow<RemoveRootMotion>("Remove Root Motion");
    }

    private AnimationClip[] animationClips; // Array to store selected animation clips
    private DefaultAsset sourceFolder;
    private string saveFolder = "Assets/NoRMClips"; // Default folder path to save duplicated clips

    private void OnGUI()
    {
        // Title label
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

        // Check if any animation clips have been loaded
        if (animationClips != null && animationClips.Length > 0)
        {
            GUILayout.Space(10); // Add some space

            // Folder path label and text field
            GUILayout.Label("Save Duplicated Clips To", EditorStyles.boldLabel);
            saveFolder = EditorGUILayout.TextField(new GUIContent("Folder Path", "Specify the folder path where the duplicated clips will be saved."), saveFolder);

            // Button to duplicate clips and remove Root motion
            if (GUILayout.Button(new GUIContent("Remove Root Motion from Animation Clips", "Duplicate the selected clips and remove the root motion from the duplicated clips.")))
            {
                DuplicateAndRemoveRootMotionFromClips();
            }

            GUILayout.Space(10); // Add some space

            // Display the names of the loaded animation clips
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

    // Duplicate the selected clips and remove the Root motion from the duplicated clips
    private void DuplicateAndRemoveRootMotionFromClips()
    {
        // Ensure the base save folder exists in the asset database
        string baseFolderPath = saveFolder;
        if (!AssetDatabase.IsValidFolder(baseFolderPath))
        {
            string parentFolder = System.IO.Path.GetDirectoryName(baseFolderPath).Replace("\\", "/");
            string folderName = System.IO.Path.GetFileName(baseFolderPath);
            AssetDatabase.CreateFolder(parentFolder, folderName);
        }

        foreach (var clip in animationClips)
        {
            // Get the path of the original clip
            string path = AssetDatabase.GetAssetPath(clip);
            // Generate a new path for the duplicated clip
            string newPath = Path.Combine(saveFolder, clip.name + "_NoRootTz.anim");
            newPath = AssetDatabase.GenerateUniqueAssetPath(newPath);
            // Copy the original clip to the new path
            AssetDatabase.CopyAsset(path, newPath);
            AssetDatabase.Refresh();

            // Load the duplicated clip
            AnimationClip newClip = AssetDatabase.LoadAssetAtPath<AnimationClip>(newPath);
            // Remove Root T.z from the duplicated clip
            RemoveRootTZFromClip(newClip);
        }
        Debug.Log("Duplicated and removed Root T.z from all selected animation clips.");
    }

    // Remove the Root T.z curve from the given animation clip
    private void RemoveRootTZFromClip(AnimationClip clip)
    {
        // Get all curve bindings (properties) in the clip
        var bindings = AnimationUtility.GetCurveBindings(clip);
        foreach (var binding in bindings)
        {
            // Check if the binding is for Root T.z or m_LocalPosition.z
            if (binding.propertyName == "RootT.z" || binding.propertyName == "m_LocalPosition.z")
            {
                // Remove the curve by setting it to null
                AnimationUtility.SetEditorCurve(clip, binding, null);
                Debug.Log("Removed Root T.z from: " + clip.name);
            }
        }
    }
}

