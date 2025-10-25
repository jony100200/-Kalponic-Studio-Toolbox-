# Prompt Sequencer

A powerful GUI application for automating prompt sequences to AI applications like ChatGPT, Stable Diffusion, ComfyUI, and more.

## Features

### 🎯 **Responsive Design**
- **Scrollable Interface:** Adapts to any screen size and resolution
- **Dynamic Window Sizing:** Automatically adjusts to optimal size for your screen
- **Grid-Based Layout:** Professional, resizable components
- **Status Bar:** Real-time window size and scroll guidance

### 📋 **Two Operating Modes:**
- Text Mode: Process folders of .txt files with multiple prompts
- Image + Text Mode: Process image folders with optional global text prompts
  - **Single Folder Mode:** Process one folder at a time (classic behavior)
  - **Queue Mode:** Add multiple folders to a queue for batch processing

### 🔒 **Reliable Automation:**
- Enhanced window detection and focusing with keyboard sequences
- Multiple focus strategies (Browser/Electron, Generic, Tab Navigation)
- Clipboard safety (saves and restores original content)
- Retry mechanisms with exponential backoff
- Pause/Resume functionality with manual intervention fallback

### 🧠 **Smart Processing:**
- Automatic file organization (moves processed files to sent_prompts/sent_images)
- Failed files moved to dedicated failed folders
- Configurable delays and jitter for natural timing
- Progress tracking and status indicators
- Verification system for input box focus

### 📊 **Comprehensive Logging:**
- Real-time scrollable activity panel
- Detailed file logging with timestamps
- Export functionality for logs

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
# OR
run.bat
```

## Usage

### Global Setup
1. Set target window by entering a substring of the window title
2. Use "Find Windows" to see available windows
3. Test window focusing with "Test Focus" - uses enhanced keyboard navigation
4. Configure initial delay before starting

### Text Mode
1. Select a folder containing .txt files
2. Each file represents a category and can contain multiple prompts
3. Prompts can be separated by `---` or blank lines
4. Configure timing settings (paste grace, generation wait, jitter)
5. Enable/disable auto-Enter after pasting

### Image + Text Mode

#### Single Folder Mode (Classic)
1. Select folder containing images (jpg, png, bmp, gif, webp)
2. Optionally select a global prompt .txt file
3. Configure timing and behavior settings

#### Queue Mode (New!)
1. Select "Queue Mode (Multiple Folders)" radio button
2. Click "Add Folder" to add image folders to the queue:
   - Choose an image folder
   - Optionally choose a prompt file for that folder
3. Use queue management buttons:
   - **Remove:** Delete selected queue item
   - **Clear All:** Empty the entire queue
   - **Move Up/Down:** Reorder queue items
4. Click "Start" to process all folders sequentially

**Queue Benefits:**
- Set up overnight batch jobs across multiple themed folders
- Different prompts for different image categories
- Example: Nature → nature_prompts.txt, Medieval → medieval_prompts.txt
- Process hundreds of images across multiple themes automatically
4. Images are pasted first, followed by text (if enabled)
   - **Important:** Adjust the "Image Upload Delay" slider in Image Mode Settings to ensure sufficient time for image upload to complete before text is pasted

## Enhanced Window Focus System

The application now uses keyboard-based focus strategies instead of unreliable mouse coordinates:

### 🎯 **Focus Strategies:**
1. **Browser/Electron Strategy:** `Ctrl+L` → `Tab` sequences
2. **Generic Strategy:** `Ctrl+K`, `/`, `Ctrl+F` fallbacks  
3. **Tab Navigation:** Smart tab cycling for complex UIs

### ✅ **Verification System:**
- Uses `<<<TEST>>>` marker to verify input box focus
- Automatic retry with different strategies
- Manual intervention mode when automated focus fails

### 🔄 **Retry Logic:**
- Up to 2-3 attempts per strategy with increasing delays
- Automatic fallback between different focus methods
- "Resume After Manual Fix" option for edge cases

## Configuration

Settings are automatically saved to `settings.json` and persist between sessions.

**Image Mode Timing:**
- **Image Upload Delay:** User-adjustable slider and entry field (0-10 seconds) to set the time to wait after pasting an image before text is pasted. This allows sufficient time for image upload to complete in AI applications like ChatGPT. Default: 3 seconds.

## File Organization

- Processed text files → `sent_prompts/`
- Processed images → `sent_images/`
- Failed files → `sent_prompts/failed/` or `sent_images/failed/`
- Logs → `logs/prompt_sequencer_YYYYMMDD.log`

## Testing & Utilities

### CLI Commands:
```bash
# Check dependencies
python cli.py deps

# List available windows
python cli.py windows

# Test window focus with enhanced strategies
python cli.py focus --window "ChatGPT"

# Test individual focus strategies
python cli.py strategies --window "Firefox"

# Create sample test files
python cli.py sample_prompts

# Test responsive GUI design
python cli.py test_gui

# Show current configuration
python cli.py config
```

## Responsive Design

The application automatically adapts to different screen sizes:

- **Auto Window Sizing:** Calculates optimal size (80% of screen)
- **Minimum Size Enforcement:** Never smaller than 800x600
- **Maximum Size Limits:** Caps at 1200x900 for usability
- **Dynamic Content:** Scrollable interface for all content
- **Real-time Adaptation:** Responds to window resizing
- **Status Feedback:** Shows current window dimensions

## Keyboard Safety

The application includes pyautogui's built-in failsafe - move your mouse to the top-left corner of the screen to emergency stop automation.

## Queue Mode (Dynamic enqueue & auto-remove)

- The queue supports dynamic enqueueing: you can add folders while processing is running. When the GUI is running a queue, items are placed into a live `queue.Queue` (stored on `config.image_queue_obj`) so the worker thread picks them up immediately.
- Each queue item receives a unique `id` on creation. When the sequencer finishes processing a folder it calls back with the item's `id`, and the GUI removes that exact entry from the visible list and the persisted `config.image_queue_items` list.
- Removing an item via the GUI rebuilds the live queue from `config.image_queue_items` so order and runtime queue remain in sync. Note: if the sequencer has already dequeued an item and is actively processing it, removing it from the GUI will not cancel the in-flight processing; the item has already been consumed by the worker thread.

If you want cancellation of active items, we can add a cancel flag and cooperative-check in the worker loop.
