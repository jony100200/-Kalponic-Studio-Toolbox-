"""
KS PDF Studio - Dark Theme Demo
Demonstrates the dark theme interface with good color harmony.

Author: Kalponic Studio
Version: 2.0.0
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from main_gui import DarkTheme


def create_demo_window():
    """Create a demo window showing the dark theme."""
    root = tk.Tk()
    root.title("KS PDF Studio - Dark Theme Demo")
    root.geometry("1000x700")

    # Apply dark theme
    DarkTheme.apply_theme(root)

    # Create main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 20))

    title_label = ttk.Label(header_frame, text="KS PDF Studio v2.0",
                           font=('Arial', 20, 'bold'))
    title_label.pack(side=tk.LEFT)

    subtitle_label = ttk.Label(header_frame,
                              text="AI-Powered Tutorial Creation with Dark Theme",
                              font=('Arial', 10))
    subtitle_label.pack(side=tk.LEFT, padx=(20, 0))

    # Demo sections
    sections_frame = ttk.Frame(main_frame)
    sections_frame.pack(fill=tk.BOTH, expand=True)

    # Left panel - Editor demo
    left_panel = ttk.LabelFrame(sections_frame, text="Markdown Editor",
                               padding=10)
    left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    # Toolbar
    toolbar = ttk.Frame(left_panel)
    toolbar.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(toolbar, text="📄 New").pack(side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text="📂 Open").pack(side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text="💾 Save").pack(side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text="🤖 Enhance").pack(side=tk.LEFT, padx=2)

    # Editor
    editor = scrolledtext.ScrolledText(left_panel, wrap=tk.WORD,
                                     font=('Consolas', 10), height=20)
    editor.pack(fill=tk.BOTH, expand=True)

    # Sample content
    sample_markdown = """# Getting Started with Python

## Introduction

Python is a powerful programming language that's easy to learn and use.

## Basic Syntax

```python
def hello_world():
    print("Hello, KS PDF Studio!")
    return True

# Call the function
hello_world()
```

## Key Features

- **Simple Syntax**: Clean and readable code
- **Versatile**: Web development, data science, AI
- **Large Community**: Extensive libraries and support

## Next Steps

1. Install Python from python.org
2. Learn basic syntax
3. Build your first project
4. Join the community

> **Tip**: Practice regularly to master Python programming!

---

*Created with KS PDF Studio - AI-Powered Tutorial Creation*
"""

    editor.insert('1.0', sample_markdown)

    # Right panel - Preview/AI demo
    right_panel = ttk.Frame(sections_frame)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Notebook for different views
    notebook = ttk.Notebook(right_panel)
    notebook.pack(fill=tk.BOTH, expand=True)

    # PDF Preview tab
    preview_tab = ttk.Frame(notebook)
    notebook.add(preview_tab, text="PDF Preview")

    preview_controls = ttk.Frame(preview_tab)
    preview_controls.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(preview_controls, text="🔄 Refresh").pack(side=tk.LEFT, padx=2)
    ttk.Button(preview_controls, text="📖 Open PDF").pack(side=tk.LEFT, padx=2)

    preview_text = scrolledtext.ScrolledText(preview_tab, wrap=tk.WORD,
                                           font=('Arial', 10), height=15)
    preview_text.pack(fill=tk.BOTH, expand=True)
    preview_text.insert('1.0', "PDF preview will appear here...\n\nClick 'Refresh' to generate preview from the markdown content.")

    # AI Enhancement tab
    ai_tab = ttk.Frame(notebook)
    notebook.add(ai_tab, text="AI Enhancement")

    ai_controls = ttk.Frame(ai_tab)
    ai_controls.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(ai_controls, text="AI Enhancement Options:",
              font=('Arial', 10, 'bold')).pack(anchor='w')

    # Checkboxes
    options = [
        "Auto-expand thin sections",
        "Suggest relevant images",
        "Add practical examples",
        "Generate exercises",
        "Improve writing quality"
    ]

    for option in options:
        chk = ttk.Checkbutton(ai_controls, text=option)
        chk.pack(anchor='w', pady=1)

    ttk.Button(ai_controls, text="🚀 Enhance Content",
              style='Accent.TButton').pack(pady=(10, 0))

    ai_results = scrolledtext.ScrolledText(ai_tab, wrap=tk.WORD,
                                         font=('Arial', 10), height=10)
    ai_results.pack(fill=tk.BOTH, expand=True)
    ai_results.insert('1.0', "AI enhancement results will appear here...\n\nThe AI will analyze your content and provide suggestions for improvement.")

    # Status bar
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill=tk.X, pady=(20, 0))

    ttk.Label(status_frame, text="Ready").pack(side=tk.LEFT)
    ttk.Label(status_frame, text="Ln 1, Col 1").pack(side=tk.RIGHT)

    # Color palette info
    info_frame = ttk.LabelFrame(main_frame, text="Dark Theme Color Palette",
                               padding=10)
    info_frame.pack(fill=tk.X, pady=(20, 0))

    colors_info = """
🎨 Dark Theme Features:
• Muted color palette for eye comfort
• High contrast for readability
• Consistent color harmony
• Professional appearance

Color Scheme:
• Background: Deep charcoal (#1e1e1e)
• Secondary: Medium gray (#2d2d2d)
• Text: Light gray (#e0e0e0)
• Accent: Muted blue (#4a9eff)
• Borders: Subtle gray (#404040)
"""

    info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD,
                                        font=('Consolas', 9), height=8)
    info_text.pack(fill=tk.BOTH, expand=True)
    info_text.insert('1.0', colors_info.strip())
    info_text.config(state=tk.DISABLED)

    # Configure accent button style
    style = ttk.Style()
    style.configure('Accent.TButton', background=DarkTheme.COLORS['fg_accent'],
                   foreground='white', font=('Arial', 10, 'bold'))

    return root


def main():
    """Main demo function."""
    root = create_demo_window()

    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    print("🎨 KS PDF Studio Dark Theme Demo")
    print("Showing dark theme with muted colors for eye comfort")
    print("Close the window to exit the demo")

    root.mainloop()


if __name__ == "__main__":
    main()