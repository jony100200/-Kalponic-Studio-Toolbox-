namespace PilotBir.Player
{
    using UnityEngine;
    using UnityEngine.Events;

    /// <summary>
    /// Player controller that handles input and movement with banking effects.
    /// Designed to be reusable across projects.
    /// </summary>
    public class PlayerMovement : MonoBehaviour
    {
        [Header("Movement Settings")]
        [Tooltip("Speed at which the player moves")]
        [SerializeField] private float speed = 5f;
        
        [Tooltip("Banking value that controls the tilt when moving")]
        [SerializeField] private float bankingValue = 90f;

        [Header("Input Settings")]
        [Tooltip("Camera used for touch-to-world conversion")]
        [SerializeField] private Camera inputCamera;

        private Rigidbody playerRigidbody;
        private Camera mainCamera;
        private Vector3 movement;
        private Vector3 rotation;
        private Vector3 velocity;
        private Vector3 lastPosition;
        private Vector3 touchPosition;

        private float distance;

        // Events for movement and rotation changes
        public UnityEvent<Vector3> OnPlayerMoved;
        public UnityEvent<Quaternion> OnPlayerRotated;

        private void Awake()
        {
            playerRigidbody = GetComponent<Rigidbody>();
            mainCamera = Camera.main;

            // Calculate initial distance between the player and the camera
            distance = (mainCamera.transform.position - transform.position).y;
        }

        private void FixedUpdate()
        {
            // Calculate the velocity for banking effect
            velocity = transform.position - lastPosition;

            if (Application.isMobilePlatform)
            {
                ProcessTouchInput();
            }
            else
            {
                ProcessKeyboardInput();
            }

            // Store the last position for the next frame's velocity calculation
            lastPosition = transform.position;
        }

        private void ProcessKeyboardInput()
        {
            // Get movement input from the old input system (WASD or Arrow keys)
            float horizontalInput = Input.GetAxis("Horizontal");
            float verticalInput = Input.GetAxis("Vertical");

            // Create the movement vector
            movement = new Vector3(horizontalInput, 0, verticalInput).normalized;

            // Move the player based on the input
            MovePlayer(movement);
        }

        private void ProcessTouchInput()
        {
            // Get the mouse position (can be used as touch position for testing on PC)
            touchPosition = Input.mousePosition;
            touchPosition.z = distance;

            // Convert the touch position into world space
            Vector3 screenToWorld = mainCamera.ScreenToWorldPoint(touchPosition);
            movement = (screenToWorld - transform.position).normalized;

            // Move the player towards the touch position
            MovePlayer(movement);
        }

        private void MovePlayer(Vector3 movement)
        {
            // Lerp to smooth the movement
            Vector3 newPosition = Vector3.Lerp(transform.position, transform.position + movement, speed * Time.fixedDeltaTime);
            playerRigidbody.MovePosition(newPosition);

            // Banking (rotation effect based on velocity)
            rotation.z = -velocity.x * bankingValue;
            Quaternion newRotation = Quaternion.Euler(rotation);
            playerRigidbody.MoveRotation(newRotation);

            // Fire events
            OnPlayerMoved?.Invoke(newPosition);
            OnPlayerRotated?.Invoke(newRotation);
        }

        private void OnValidate()
        {
            // Auto-find camera if not assigned
            if (inputCamera == null)
                inputCamera = Camera.main;
        }

        // Public properties for controlled access
        public float Speed => speed;
        public float BankingValue => bankingValue;
    }
}
