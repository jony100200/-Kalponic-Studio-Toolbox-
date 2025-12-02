using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class AnimationController : MonoBehaviour
{
    public Animator animator; // Reference to the Animator component
    public string[] animationNames; // Array of animation names
    private int currentAnimationIndex = 0; // Index of the currently playing animation
    public TextMeshProUGUI currentAnimationText; // TextMeshPro component to display current animation name

    private void Start()
    {
        // Start with the first animation in the array
        PlayAnimation(animationNames[currentAnimationIndex]);
        UpdateCurrentAnimationText();
    }

    private void Update()
    {
        // Check for button press (you can change this to any input method you prefer)
        if (Input.GetKeyDown(KeyCode.Space))
        {
            // Increment animation index or loop back to 0 if reached the end
            currentAnimationIndex = (currentAnimationIndex + 1) % animationNames.Length;

            // Play the next animation
            PlayAnimation(animationNames[currentAnimationIndex]);

            // Update UI
            UpdateCurrentAnimationText();
        }
    }

    private void PlayAnimation(string animationName)
    {
        // Play the specified animation
        animator.Play(animationName, -1, 0f);
    }

    private void UpdateCurrentAnimationText()
    {
        // Update the UI text to display the name of the currently playing animation
        if (currentAnimationText != null)
        {
            currentAnimationText.text = "Current Animation: " + animationNames[currentAnimationIndex];
        }
    }
}
