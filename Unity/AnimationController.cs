using UnityEngine;
using TMPro;

public class AnimationController : MonoBehaviour
{
    public Animator animator; // Reference to the Animator component
    public AnimationClip[] animations; // Array of AnimationClips (must be in the Animator Controller)
    private int currentAnimationIndex = 0; // Index of the currently playing animation
    public TextMeshProUGUI currentAnimationText; // TextMeshPro component to display current animation name
    public bool autoPlay = false; // Enable automatic cycling
    public float autoPlayDelay = 2f; // Delay between animations in seconds
    private float lastPlayTime;

    private void Start()
    {
        // Start with the first animation in the array
        PlayAnimation(currentAnimationIndex);
        UpdateCurrentAnimationText();
        lastPlayTime = Time.time;
    }

    private void Update()
    {
        // Toggle auto-play with P key
        if (Input.GetKeyDown(KeyCode.P))
        {
            autoPlay = !autoPlay;
            Debug.Log("Auto-play " + (autoPlay ? "enabled" : "disabled"));
        }

        if (autoPlay)
        {
            if (Time.time - lastPlayTime >= autoPlayDelay)
            {
                // Increment animation index or loop back to 0 if reached the end
                currentAnimationIndex = (currentAnimationIndex + 1) % animations.Length;

                // Play the next animation
                PlayAnimation(currentAnimationIndex);

                // Update UI
                UpdateCurrentAnimationText();

                lastPlayTime = Time.time;
            }
        }
        else
        {
            // Check for button press (you can change this to any input method you prefer)
            if (Input.GetKeyDown(KeyCode.Space))
            {
                // Increment animation index or loop back to 0 if reached the end
                currentAnimationIndex = (currentAnimationIndex + 1) % animations.Length;

                // Play the next animation
                PlayAnimation(currentAnimationIndex);

                // Update UI
                UpdateCurrentAnimationText();
            }
        }
    }

    private void PlayAnimation(int index)
    {
        // Play the animation by name (clip must be in the Animator Controller)
        animator.Play(animations[index].name);
    }

    private void UpdateCurrentAnimationText()
    {
        // Update the UI text to display the name of the currently playing animation
        if (currentAnimationText != null)
        {
            currentAnimationText.text =animations[currentAnimationIndex].name;
        }
    }
}
