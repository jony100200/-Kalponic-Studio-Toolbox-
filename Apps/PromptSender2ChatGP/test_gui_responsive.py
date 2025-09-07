#!/usr/bin/env python3
"""
GUI Testing Utility for Prompt Sequencer
Demonstrates scrollable interface and responsive design
"""

import customtkinter as ctk
import tkinter as tk

def create_test_window():
    """Create a test window to demonstrate scrollable features"""
    
    # Setup
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Scrollable GUI Test")
    root.geometry("600x400")
    root.minsize(400, 300)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    # Main scrollable frame
    scrollable_frame = ctk.CTkScrollableFrame(
        root,
        orientation="vertical",
        height=350,
        corner_radius=0,
        scrollbar_button_color=("gray75", "gray25")
    )
    scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    scrollable_frame.grid_columnconfigure(0, weight=1)
    
    # Add content to demonstrate scrolling
    content_items = [
        ("Global Controls", "Window targeting and automation control"),
        ("Status Panel", "Real-time state and progress tracking"),
        ("Text Mode Settings", "Configure text prompt processing"),
        ("Image Mode Settings", "Configure image + text automation"),
        ("Timing Controls", "Delays, jitter, and grace periods"),
        ("File Organization", "Automatic sent/failed file management"),
        ("Activity Log", "Comprehensive logging and export"),
        ("Window Focus", "Enhanced keyboard-based targeting"),
        ("Retry Logic", "Robust error handling and recovery"),
        ("Manual Intervention", "Fallback to user assistance")
    ]
    
    for i, (title, description) in enumerate(content_items):
        # Create frame for each section
        section_frame = ctk.CTkFrame(scrollable_frame)
        section_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(section_frame, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Description
        desc_label = ctk.CTkLabel(section_frame, text=description, text_color="gray70")
        desc_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Add some controls
        controls_frame = ctk.CTkFrame(section_frame)
        controls_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        ctk.CTkEntry(controls_frame, placeholder_text=f"Setting for {title}").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(controls_frame, text="Configure", width=80).pack(side="right", padx=5, pady=5)
    
    # Status bar
    status_bar = ctk.CTkFrame(root, height=25)
    status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
    
    def update_size_info():
        width = root.winfo_width()
        height = root.winfo_height()
        status_label.configure(text=f"Window: {width}x{height} • Scroll to see all content • Resize to test responsiveness")
        root.after(1000, update_size_info)
    
    status_label = ctk.CTkLabel(
        status_bar, 
        text="Resize window to test responsiveness", 
        font=ctk.CTkFont(size=11),
        text_color="gray60"
    )
    status_label.pack(side="left", padx=10, pady=2)
    
    # Start size monitoring
    update_size_info()
    
    # Resize handler
    def on_resize(event):
        if event.widget == root:
            new_height = max(200, root.winfo_height() - 100)
            scrollable_frame.configure(height=new_height)
    
    root.bind("<Configure>", on_resize)
    
    # Instructions
    instructions = ctk.CTkLabel(
        scrollable_frame,
        text="🎯 GUI Responsiveness Test\n\n" +
             "• Resize this window to see responsive behavior\n" +
             "• Use mouse wheel to scroll through content\n" +
             "• Try different window sizes and ratios\n" +
             "• Notice how controls adapt to available space\n\n" +
             "This demonstrates the same responsive design used in the main Prompt Sequencer application.",
        font=ctk.CTkFont(size=12),
        justify="left"
    )
    instructions.grid(row=len(content_items), column=0, sticky="ew", padx=10, pady=20)
    
    return root

if __name__ == "__main__":
    app = create_test_window()
    print("🎯 Starting GUI Responsiveness Test...")
    print("💡 Try resizing the window and scrolling to test responsiveness!")
    app.mainloop()
